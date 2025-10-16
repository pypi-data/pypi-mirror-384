import json
from unittest import TestCase
from unittest.mock import MagicMock, patch

from jira import JIRA, JIRAError

from rhjira.util import handle_jira_error, retry_jira_operation


class TestRetryJiraOperation(TestCase):
    def setUp(self) -> None:
        self.mock_jira = MagicMock(spec=JIRA)
        self.mock_operation = MagicMock()

    def test_successful_operation(self) -> None:
        """Test that a successful operation returns the expected result."""
        expected_result = "success"
        self.mock_operation.return_value = expected_result

        result = retry_jira_operation(self.mock_operation, self.mock_jira, "arg1", "arg2")

        self.assertEqual(result, expected_result)
        self.mock_operation.assert_called_once_with(self.mock_jira, "arg1", "arg2")

    @patch('rhjira.util.login.login')
    def test_auth_error_with_successful_retry(self, mock_login: MagicMock) -> None:
        """Test that an auth error is handled and retried successfully."""
        # First call fails with auth error, second succeeds
        mock_response = MagicMock()
        mock_response.text = json.dumps({"errorMessages": ["Authentication failed"]})
        jira_error = JIRAError(status_code=401, response=mock_response)
        exception = Exception("Test error")
        exception.__cause__ = jira_error

        self.mock_operation.side_effect = [exception, "success"]
        mock_login.return_value = self.mock_jira

        result = retry_jira_operation(self.mock_operation, self.mock_jira, "arg1", "arg2")

        self.assertEqual(result, "success")
        self.assertEqual(self.mock_operation.call_count, 2)
        mock_login.assert_called_once()

    @patch('rhjira.util.login.login')
    def test_auth_error_max_retries_exceeded(self, mock_login: MagicMock) -> None:
        """Test that max retries are enforced for auth errors."""
        # All calls fail with auth error
        mock_response = MagicMock()
        mock_response.text = json.dumps({"errorMessages": ["Authentication failed"]})
        jira_error = JIRAError(status_code=401, response=mock_response)
        exception = Exception("Test error")
        exception.__cause__ = jira_error

        self.mock_operation.side_effect = exception
        mock_login.return_value = self.mock_jira

        with self.assertRaises(Exception): # noqa B017
            retry_jira_operation(self.mock_operation, self.mock_jira, "arg1", "arg2")

        self.assertEqual(self.mock_operation.call_count, 3)  # Max retries
        self.assertEqual(mock_login.call_count, 2)  # Called twice for retries

    def test_non_auth_error(self) -> None:
        """Test that non-auth errors are not retried."""
        self.mock_operation.side_effect = JIRAError(status_code=404, text="Not found")

        with self.assertRaises(JIRAError):
            retry_jira_operation(self.mock_operation, self.mock_jira, "arg1", "arg2")

        self.mock_operation.assert_called_once()


class TestHandleJiraError(TestCase):
    def setUp(self) -> None:
        self.mock_response = MagicMock()

    def test_jira_error_with_error_messages(self) -> None:
        """Test handling of JIRAError with errorMessages."""
        error_messages = ["Error 1", "Error 2"]
        self.mock_response.text = json.dumps({"errorMessages": error_messages})
        jira_error = JIRAError(status_code=400, response=self.mock_response)
        exception = Exception("Test error")
        exception.__cause__ = jira_error

        result = handle_jira_error(exception, "test operation")

        self.assertFalse(result)  # Not an auth error
        # Note: We can't easily test the print output, but we can verify the function returns False

    def test_jira_error_with_errors(self) -> None:
        """Test handling of JIRAError with errors field."""
        errors = {
            "components": "is not valid",
            "versions": "is not valid",
            "fixVersions": "is not valid"
        }
        self.mock_response.text = json.dumps({"errors": errors})
        jira_error = JIRAError(status_code=400, response=self.mock_response)
        exception = Exception("Test error")
        exception.__cause__ = jira_error

        result = handle_jira_error(exception, "test operation", "TEST-PROJ")

        self.assertFalse(result)  # Not an auth error

    def test_jira_error_json_decode_error(self) -> None:
        """Test handling of JIRAError with invalid JSON response."""
        self.mock_response.text = "invalid json"
        jira_error = JIRAError(status_code=400, response=self.mock_response)
        exception = Exception("Test error")
        exception.__cause__ = jira_error

        result = handle_jira_error(exception, "test operation")

        self.assertFalse(result)  # Not an auth error

    def test_non_jira_error(self) -> None:
        """Test handling of non-JIRAError exception."""
        exception = Exception("Test error")

        result = handle_jira_error(exception, "test operation")

        self.assertFalse(result)  # Not an auth error

    def test_auth_error(self) -> None:
        """Test handling of authentication error (401)."""
        self.mock_response.text = json.dumps({"errorMessages": ["Authentication failed"]})
        jira_error = JIRAError(status_code=401, response=self.mock_response)
        exception = Exception("Test error")
        exception.__cause__ = jira_error

        result = handle_jira_error(exception, "test operation")

        self.assertTrue(result)  # Is an auth error
