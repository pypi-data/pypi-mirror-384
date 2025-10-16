from unittest.mock import MagicMock, patch

from jira import Issue, JIRA
import pytest

from rhjira.show import defaultShowText


@pytest.fixture(autouse=False)
def mock_jira() -> JIRA:
    return MagicMock(spec=JIRA)

@pytest.fixture(autouse=False)
def mock_issue() -> Issue:
    issue = MagicMock(spec=Issue)
    issue.key = "RHEL-1234"

    # Create fields as a MagicMock
    fields = MagicMock()
    fields.summary = "Test Issue"
    fields.description = "Test Description"
    fields.issuetype = MagicMock()
    fields.issuetype.name = "Bug"
    fields.status = MagicMock()
    fields.status.name = "In Progress"
    fields.creator = MagicMock()
    fields.creator.name = "testuser"
    fields.assignee = None
    fields.components = []
    fields.versions = []
    fields.fixVersions = []
    fields.priority = MagicMock()
    fields.priority.name = "High"
    fields.customfield_12315950 = []  # Contributors
    fields.customfield_12319743 = None  # Release Blocker
    fields.customfield_12316142 = None  # Severity
    fields.customfield_12310220 = []  # Git Pull Request
    fields.issuelinks = []
    fields.comment = None

    issue.fields = fields
    return issue

@patch('rhjira.show.util.getissue')
def test_format_link_with_epic(mock_getissue: MagicMock,
                               mock_jira: JIRA,
                               mock_issue: Issue) -> None:
    # Setup epic link
    mock_issue.fields.customfield_12311140 = "RHEL-5678"

    # Mock epic issue
    epic = MagicMock(spec=Issue)
    epic.fields = MagicMock()
    epic.fields.summary = "Epic Summary"
    epic.fields.status = MagicMock()
    epic.fields.status.name = "In Progress"
    epic.fields.status.statusCategory = MagicMock()
    epic.fields.status.statusCategory.name = "In Progress"
    mock_getissue.return_value = epic

    output = defaultShowText(mock_jira, mock_issue)
    assert "Epic Link:" in output
    assert "RHEL-5678" in output
    assert "Epic Summary" in output
    assert "In Progress" in output

@patch('rhjira.show.util.getissue')
def test_format_link_with_parent(mock_getissue: MagicMock,
                                 mock_jira: JIRA,
                                 mock_issue: Issue) -> None:
    # Setup parent link for Epic type
    mock_issue.fields.issuetype.name = "Epic"  # type: ignore[attr-defined]
    mock_issue.fields.customfield_12313140 = "RHEL-5678"
    mock_issue.fields.customfield_12311141 = "Epic Name"  # Epic name field

    # Mock parent issue
    parent = MagicMock(spec=Issue)
    parent.fields = MagicMock()
    parent.fields.summary = "Parent Summary"
    parent.fields.status = MagicMock()
    parent.fields.status.name = "To Do"
    parent.fields.status.statusCategory = MagicMock()
    parent.fields.status.statusCategory.name = "To Do"
    mock_getissue.return_value = parent

    output = defaultShowText(mock_jira, mock_issue)
    assert "Parent Link:" in output
    assert "RHEL-5678" in output
    assert "Parent Summary" in output
    assert "To Do" in output

def test_format_link_with_blocks(mock_jira: JIRA, mock_issue: Issue) -> None:
    # Setup blocking link
    block_issue = MagicMock()
    block_issue.key = "RHEL-5678"
    block_issue.raw = {
        "fields": {
            "summary": "Blocking Issue",
            "status": {
                "name": "Done",
                "statusCategory": {"name": "Done"}
            }
        }
    }
    link = MagicMock()
    link.type.outward = "blocks"
    link.outwardIssue = block_issue
    mock_issue.fields.issuelinks = [link]

    output = defaultShowText(mock_jira, mock_issue)
    assert "Blocks:" in output
    assert "RHEL-5678" in output
    assert "Blocking Issue" in output
    assert "Done" in output

def test_format_link_with_is_blocked_by(mock_jira: JIRA, mock_issue: Issue) -> None:
    # Setup blocked by link
    blocker_issue = MagicMock()
    blocker_issue.key = "RHEL-5678"
    blocker_issue.raw = {
        "fields": {
            "summary": "Blocker Issue",
            "status": {
                "name": "In Progress",
                "statusCategory": {"name": "In Progress"}
            }
        }
    }
    link = MagicMock()
    link.type.inward = "is blocked by"
    link.inwardIssue = blocker_issue
    mock_issue.fields.issuelinks = [link]

    output = defaultShowText(mock_jira, mock_issue)
    assert "Is Blocked By:" in output
    assert "RHEL-5678" in output
    assert "Blocker Issue" in output
    assert "In Progress" in output

@patch('rhjira.show.util.searchissues')
def test_format_link_with_child_issues(mock_searchissues: MagicMock,
                                       mock_jira: JIRA,
                                       mock_issue: Issue) -> None:
    # Setup child issues
    mock_issue.fields.issuetype.name = "Feature"  # type: ignore[attr-defined]
    child = MagicMock(spec=Issue)
    child.key = "RHEL-5678"
    child.fields = MagicMock()
    child.fields.summary = "Child Issue"
    child.fields.status = MagicMock()
    child.fields.status.name = "To Do"
    child.fields.status.statusCategory = MagicMock()
    child.fields.status.statusCategory.name = "To Do"
    mock_searchissues.return_value = [child]

    output = defaultShowText(mock_jira, mock_issue)
    assert "Child Issue:" in output
    assert "RHEL-5678" in output
    assert "Child Issue" in output
    assert "To Do" in output

@patch('rhjira.show.util.getissue')
def test_format_link_without_links(mock_getissue: MagicMock,
                                   mock_jira: JIRA,
                                   mock_issue: Issue) -> None:
    # Ensure no links are set
    mock_issue.fields.customfield_12311140 = None
    mock_issue.fields.customfield_12313140 = None
    mock_issue.fields.issuelinks = []
    mock_issue.fields.issuetype.name = "Bug"  # type: ignore[attr-defined]

    output = defaultShowText(mock_jira, mock_issue)
    assert "Epic Link:" not in output
    assert "Parent Link:" not in output
    assert "Blocks:" not in output
    assert "Is Blocked By:" not in output
    assert "Child Issue:" not in output
