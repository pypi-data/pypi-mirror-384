load ./library.bats

setup_file() {
	echo "********************************************" >&3
	echo "Running tests in $BATS_TEST_FILENAME" >&3
	echo "********************************************" >&3

	[ -e ./rhjira ] && rm -f ./rhjira
	cp ../bin/rhjira .

	# storyoutput is available as a global variable in this file
	export STORYOUTPUT=$(removeShowLinks TP-14703)
}

@test "IDandSummary" {
	# the first line of output is the ID: Summary
	line=$(echo "$STORYOUTPUT" | head -1)
	run [ "$line" == "TP-14703: rhjira Story test" ]
	check_status
}

@test "description" {
	text="===================================
story test test
line 1
line 2
line 3
line 4
==================================="
	testtext=$(getDescription "$STORYOUTPUT")
	echo "$text"
	echo "$testtext"
	run [ "$testtext" == "$text" ]
	check_status
}

@test "tickettype" {
	line=$(echo "$STORYOUTPUT" | grep "Ticket Type:")
	run [ "$line" == "Ticket Type: Story" ]
	check_status
}

@test "status" {
	line=$(echo "$STORYOUTPUT" | grep "Status:")
	run [ "$line" == "Status: Closed (Done)" ]
	check_status
}

@test "creator" {
	line=$(echo "$STORYOUTPUT" | grep "Creator:")
	run [ "$line" == "Creator: prarit@redhat.com" ]
	check_status
}

@test "assignee" {
	line=$(echo "$STORYOUTPUT" | grep "Assignee:")
	run [ "$line" == "Assignee: prarit@redhat.com" ]
	check_status
}

@test "component" {
	line=$(echo "$STORYOUTPUT" | grep "Components:")
	run [ "$line" == "Components: Automation, Dev Console" ]
	check_status
}

@test "affectsversion" {
	line=$(echo "$STORYOUTPUT" | grep "Affects Versions:")
		echo "line=$line"
	run [ "$line" == "Affects Versions: 4.11" ]
	check_status
}

@test "fixversion" {
	line=$(echo "$STORYOUTPUT" | grep "Fix Versions:")
	run [ "$line" == "Fix Versions: 4.11" ]
	check_status
}

@test "priority" {
	line=$(echo "$STORYOUTPUT" | grep "Priority:")
	run [ "$line" == "Priority: Normal" ]
	check_status
}

@test "contributors" {
	line=$(echo "$STORYOUTPUT" | grep "Contributors:")
	run [ "$line" == "Contributors: " ]
	check_status
}

@test "releaseblocker" {
	line=$(echo "$STORYOUTPUT" | grep "Release Blocker:")
	run [ "$line" == "Release Blocker: " ]
	check_status
}

@test "severity" {
	line=$(echo "$STORYOUTPUT" | grep "Severity:")
	run [ "$line" == "Severity: " ]
	check_status
}

@test "epiclink" {
	line=$(echo "$STORYOUTPUT" | grep "Epic Link:")
	run [ "$line" == "Epic Link: TP-14704 rhjira test Epic (Closed)" ]
	check_status
}

# This is a story, so there's only an epic link
#@test "parentlink" {
#	line=$(echo "$STORYOUTPUT" | grep "Parent Link:")
#	echo "|$line|"
#	run [ "$line" == "Parent Link: " ]
#	check_status
#}

@test "gitpullrequest" {
	line=$(echo "$STORYOUTPUT" | grep "Git Pull Request:")
	run [ "$line" == "Git Pull Request: https://red.ht/kwf" ]
	check_status
}

@test "nocomments flag" {
	# Test that normal output has comments
	output=$(removeShowLinks AIPCC-1291)
	run grep -q "Comments" <<< "$output"
	check_status

	# Test that --nocomments flag suppresses comments
	nocomments_output=$(./rhjira show --nocomments AIPCC-1291 | sed 's/\x1b\[[0-9;]*m//g' | sed 's/\x1b\]8;;[^\a]*\a//g')
	run grep "Comments" <<< "$nocomments_output"
	[ "$status" -ne 0 ]
}
