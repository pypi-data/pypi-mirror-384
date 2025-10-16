load ./library.bats

setup_file() {
	echo "********************************************" >&3
	echo "Running comprehensive tests in $BATS_TEST_FILENAME" >&3
	echo "********************************************" >&3

	[ -e ./rhjira ] && rm -f ./rhjira
	cp ../bin/rhjira .

	export JIRAPROJECT=TP
}

# Error Handling Tests
@test "error_handling_invalid_ticket" {
	run ./rhjira show "INVALID-12345"
	[ "$status" -eq 1 ]
	[[ "${output}" =~ "Failed to lookup ticket" ]]
}

@test "error_handling_invalid_credentials" {
	[ -z "$GITLAB_USER_LOGIN" ] && return 0
	local OLD_TOKEN=$JIRA_TOKEN
	JIRA_TOKEN="invalid_token" run ./rhjira list "summary is not empty"
	[ "$status" -eq 1 ]
	[[ "${output}" =~ "Failed to login" ]]
	export JIRA_TOKEN=$OLD_TOKEN
}

# Command Line Argument Tests
@test "cli_no_arguments" {
	run ./rhjira
	[ "$status" -eq 1 ]
	[[ "${output}" =~ "Usage:" ]]
}

@test "cli_invalid_command" {
	run ./rhjira invalidcommand
	[ "$status" -eq 1 ]
	[[ "${output}" =~ "Usage:" ]]
}

@test "project_info" {
	# Test components listing
	run ./rhjira info --project ${JIRAPROJECT} components
	[ "$status" -eq 0 ]

	# Test versions listing
	run ./rhjira info --project ${JIRAPROJECT} versions
	[ "$status" -eq 0 ]
}

@test "rate_limiting" {
	# Test multiple rapid requests to ensure rate limiting
	for i in {1..3}; do
		run ./rhjira list --numentries 1 "project = ${JIRAPROJECT}"
		[ "$status" -eq 0 ]
	done
}

@test "token_management" {
	[ -z "$GITLAB_USER_LOGIN" ] && return 0
	# Save current token
	local OLD_TOKEN=$JIRA_TOKEN

	# Test with no token
	unset JIRA_TOKEN
	run ./rhjira list "summary is not empty"
	[ "$status" -eq 1 ]
	[[ "${output}" =~ "JIRA_TOKEN was not set" ]]

	# Restore token
	export JIRA_TOKEN=$OLD_TOKEN
}
