load ./library.bats

setup_file() {
	echo "********************************************" >&3
	echo "Running tests in $BATS_TEST_FILENAME" >&3
	echo "********************************************" >&3

	[ -e ./rhjira ] && rm -f ./rhjira
	cp ../bin/rhjira .

	export epicid="TP-14858"
	export bugid="TP-14864"
	export featureid="TP-14861"
}

@test "clearandset Epic" {
	# array entries are parameter, start of line (ex. "Ticket Type:"), the test value,
	# the cleared value, the set value
	r1=("assignee" "Assignee:" "prarit@redhat.com" "Assignee:" "Assignee: prarit@redhat.com")
	r2=("components" "Components:" "Documentation, test1" "Components:" "Components: Documentation, test1")
	r3=("affectsversion" "Affects Versions:" "1.0.0 Beta, 4.11" "Affects Versions:" "Affects Versions: 1.0.0 Beta, 4.11")
	r4=("fixversion" "Fix Versions:" "1.0.0 Beta, 4.11" "Fix Versions:" "Fix Versions: 1.0.0 Beta, 4.11")
	r5=("contributors" "Contributors:" "prarit@redhat.com, rhel-ai-jira-bot" "Contributors:" "Contributors: prarit@redhat.com, rhel-ai-jira-bot")
	r6=("releaseblocker" "Release Blocker:" "Rejected" "Release Blocker:" "Release Blocker: Rejected")
	# Links are not shown when the field is empty
	r8=("parentlink" "Parent Link:" "TP-14861" "" "Parent Link: TP-14861 Updated Feature (Closed)")

	all_rows=(r1 r2 r3 r4 r5 r6 r8)

	# Loop through each record
	for row_name in "${all_rows[@]}"; do
		eval "row=(\"\${${row_name}[@]}\")"
		parameter="${row[0]}"
		header="${row[1]}"
		value="${row[2]}"
		clearedvalue="${row[3]}"
		setvalue="${row[4]}"

		echo "Running $parameter test" >&3
		./rhjira edit --${parameter} "" --noeditor $epicid
		grepstr=$(removeShowLinks $epicid | grep "$header" || true)
		echo "***********"
		echo "Clearing $parameter"
		echo "grepstr = |$grepstr|"
		echo "parameter=$parameter header=$header value=$value clearedvalue=$clearedvalue"
		echo "***********"
		if [ -n "$clearedvalue" ]; then
			run [ "$grepstr" == "${clearedvalue} " ]
			check_status
		else
			run [ "$grepstr" == "" ]
			check_status
		fi

		echo "Setting $parameter"
		./rhjira edit --${parameter} "${value}" --noeditor $epicid
		grepstr=$(removeShowLinks $epicid | grep "$header")
		echo "***********"
		echo "Setting $parameter"
		echo "grepstr = |$grepstr|"
		echo "parameter=$parameter header=$header value=$value setvalue=|$setvalue|"
		echo "***********"
		run [ "$grepstr" == "${setvalue}" ]
		check_status
	done
}

@test "clearandset Bug" {
	# array entries are parameter, start of line (ex. "Ticket Type:"), the test value,
	# the cleared value, the set value
	r1=("assignee" "Assignee:" "prarit@redhat.com" "Assignee:" "Assignee: prarit@redhat.com")
	r2=("components" "Components:" "Documentation, test1" "Components:" "Components: Documentation, test1")
	r3=("affectsversion" "Affects Versions:" "1.0.0 Beta, 4.11" "Affects Versions:" "Affects Versions: 1.0.0 Beta, 4.11")
	r4=("fixversion" "Fix Versions:" "1.0.0 Beta, 4.11" "Fix Versions:" "Fix Versions: 1.0.0 Beta, 4.11")
	r5=("contributors" "Contributors:" "prarit@redhat.com, rhel-ai-jira-bot" "Contributors:" "Contributors: prarit@redhat.com, rhel-ai-jira-bot")
	r6=("releaseblocker" "Release Blocker:" "Rejected" "Release Blocker:" "Release Blocker: Rejected")
	# severity cannot be set in TP
	r9=("epiclink" "Epic Link:" $epicid "" "Epic Link: $epicid Test Epic -- do not track or use (Closed)")
	r10=("gitpullrequest" "Git Pull Request:" "https://redhat.com" "Git Pull Request:" "Git Pull Request: https://redhat.com")

	all_rows=(r1 r2 r3 r4 r5 r6 r9 r10)

	# Loop through each record
	for row_name in "${all_rows[@]}"; do
		eval "row=(\"\${${row_name}[@]}\")"
		parameter="${row[0]}"
		header="${row[1]}"
		value="${row[2]}"
		clearedvalue="${row[3]}"
		setvalue="${row[4]}"

		echo "Running $parameter test" >&3
		./rhjira edit --${parameter} "" --noeditor $bugid
		grepstr=$(removeShowLinks $bugid | grep "$header" || true)
		echo "***********"
		echo "Clearing $parameter"
		echo "grepstr = |$grepstr|"
		echo "parameter=$parameter header=$header value=$value clearedvalue=$clearedvalue"
		echo "***********"
		if [ -n "$clearedvalue" ]; then
			run [ "$grepstr" == "${clearedvalue} " ]
			check_status
		else
			run [ "$grepstr" == "" ]
			check_status
		fi

		echo "Setting $parameter on $bugid"
		./rhjira edit --${parameter} "${value}" --noeditor $bugid
		grepstr=$(removeShowLinks $bugid | grep "$header" || true)
		echo "***********"
		echo "Setting $parameter"
		echo "grepstr = |$grepstr|"
		echo "parameter=$parameter header=$header value=$value setvalue=|$setvalue|"
		echo "***********"
		run [ "$grepstr" == "${setvalue}" ]
		check_status
	done
}
