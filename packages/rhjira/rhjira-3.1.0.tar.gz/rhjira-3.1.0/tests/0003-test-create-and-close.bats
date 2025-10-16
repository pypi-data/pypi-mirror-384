load ./library.bats

setup_file() {
	echo "********************************************" >&3
	echo "Running tests in $BATS_TEST_FILENAME" >&3
	echo "********************************************" >&3

	[ -e ./rhjira ] && rm -f ./rhjira
	cp ../bin/rhjira .

	export JIRAPROJECT=TP
	export JIRAURL="https://issues.redhat.com/browse"
}

@test "openandclose" {
	# create a feature

	# PRARIT FIX ME: update when Contributors is enabled in TP
	url=$(./rhjira create --affectsversion "1.0.0 Beta" --components "Documentation"  --description "Feature test\nThe quick brown giraffe\nran out of curds and whey" --fixversion "2.6.0"  --priority "Minor" --project "${JIRAPROJECT}" --summary "Test Feature -- do not track or use" --tickettype "Feature" --noeditor)
	run grep "${JIRAURL}/${JIRAPROJECT}-" <<< "$url"
	check_status

	featureID=$(echo "$url" | rev  | cut -d "/" -f1 | rev)
	echo "      feature ID: $featureID" >&3
	echo "featureID: $featureID" >> ${BATS_FILE_TMPDIR}/test_issues
	run grep "${JIRAPROJECT}-" <<< "$featureID"
	check_status

	# PRARIT FIX ME: update when Contributors is enabled in TP
	url=$(./rhjira create --affectsversion "1.0.0 Beta" --components "Documentation"  --description "Epic test\nThe quick brown giraffe\nran out of curds and whey" --fixversion "2.6.0"  --priority "Minor" --project "${JIRAPROJECT}" --summary "Test Epic -- do not track or use" --tickettype "Epic" --epicname "Epic test" --noeditor)
	run grep "${JIRAURL}/${JIRAPROJECT}-" <<< "$url"
	check_status

	epicID=$(echo "$url" | rev  | cut -d "/" -f1 | rev)
	echo "      epic ID: $epicID" >&3
	echo "epicID: $epicID" >> ${BATS_FILE_TMPDIR}/test_issues
	run grep "${JIRAPROJECT}-" <<< "$epicID"
	check_status

	# PRARIT FIX ME: update when Contributors is enabled in TP
	url=$(./rhjira create --affectsversion "1.0.0 Beta" --components "Internal Tools" --description "Story test\nThe quick brown giraffe\nran out of curds and whey" --fixversion "2.6.0"  --priority "Minor" --project "${JIRAPROJECT}" --summary "Test Story -- do not track or use" --tickettype "Story" --epiclink "$epicID" --noeditor)
	run grep "${JIRAURL}/${JIRAPROJECT}-" <<< "$url"
	check_status

	storyID=$(echo "$url" | rev  | cut -d "/" -f1 | rev)
	echo "      story ID: $storyID" >&3
	echo "storyID: $storyID" >> ${BATS_FILE_TMPDIR}/test_issues
	run grep "${JIRAPROJECT}-" <<< "$storyID"
	check_status

	# PRARIT FIX ME: update when Contributors is enabled in TP
	url=$(./rhjira create --affectsversion "1.0.0 Beta" --components "Bugzilla General" --description "Bug test\nThe quick brown giraffe\nran out of curds and whey" --fixversion "2.6.0"  --priority "Minor" --project "${JIRAPROJECT}" --summary "Test Bug -- do not track or use" --tickettype "Bug" --noeditor)
	run grep "${JIRAURL}/${JIRAPROJECT}-" <<< "$url"
	check_status

	bugID=$(echo "$url" | rev  | cut -d "/" -f1 | rev)
	echo "      bug ID: $bugID" >&3
	echo "bugID: $bugID" >> ${BATS_FILE_TMPDIR}/test_issues
	run grep "${JIRAPROJECT}-" <<< "$bugID"
	check_status

	# close a bug
	run ./rhjira close "$bugID"
	check_status
	# close a story
	run ./rhjira close "$storyID"
	check_status
	# close an epic
	run ./rhjira close "$epicID"
	check_status
	# close a feature
	run ./rhjira close "$featureID"
	check_status
}

# this test is useful if you need to debug.  You can use the 'skip' command
# to avoid creation of tickets, and then uncomment this test.  Of course ;)
# you need to have tickets to run on. :)
#@test "onlyrunonskip" {
#	echo "featureID: TP-14861" >> ${BATS_FILE_TMPDIR}/test_issues
#	echo "epicID: TP-14862" >> ${BATS_FILE_TMPDIR}/test_issues
#	echo "storyID: TP-14863" >> ${BATS_FILE_TMPDIR}/test_issues
#	echo "bugID: TP-14864" >> ${BATS_FILE_TMPDIR}/test_issues
#	cat ${BATS_FILE_TMPDIR}/test_issues >&3
#	run [ 1 == 1 ]
#	check_status
#}

# testing all the edit features is a bit tricky because each one would
# require an 'rhjira show'.  I've batched these together so that only
# a handful of shows are necessary.

@test "editfeature1" {
	# read issue IDs from previous run
	featureID=$(grep "featureID:" ${BATS_FILE_TMPDIR}/test_issues | cut -d":" -f2 | xargs)
	epicID=$(grep "epicID:" ${BATS_FILE_TMPDIR}/test_issues | cut -d":" -f2 | xargs)
	storyID=$(grep "storyID:" ${BATS_FILE_TMPDIR}/test_issues | cut -d":" -f2 | xargs)
	bugID=$(grep "bugID:" ${BATS_FILE_TMPDIR}/test_issues | cut -d":" -f2 | xargs)

	# Edit features: First batch
	./rhjira edit  --affectsversion "4.9" --noeditor $featureID
	./rhjira edit  --components "Documentation" --noeditor $featureID
	# PRARIT FIX ME: update when Contributors is enabled in TP $featureID
	#./rhjira edit  --contributors "prarit@redhat.com" --noeditor $featureID
	./rhjira edit  --fixversion "4.11" --noeditor $featureID
	./rhjira edit  --priority "Normal" --noeditor $featureID
	./rhjira edit  --summary "Updated Feature" --noeditor $featureID

	showoutput=$(./rhjira show $featureID)

	affectsversions=$(echo "$showoutput" | grep "Affects Versions:")
	run [ "$affectsversions" == "Affects Versions: 4.9" ]
	check_status

	component=$(echo "$showoutput" | grep "Components:")
	run [ "$component" == "Components: Documentation" ]
	check_status

	# PRARIT FIX ME: update when Contributors is enabled in TP
	#contributors=$(echo "$showoutput" | grep "Contributors:")
	#run [ "$contributors" == "Contributors: prarit@redhat.com" ]
	#check_status

	fixversion=$(echo "$showoutput" | grep "Fix Versions:")
	run [ "$fixversion" == "Fix Versions: 4.11" ]
	check_status

	priority=$(echo "$showoutput" | grep "Priority:")
	run [ "$priority" == "Priority: Normal" ]
	check_status

	summary=$(head -1 <<< "$showoutput")
	run [ "$summary" == "${featureID}: Updated Feature" ]
	check_status
}

@test "editfeature2" {
	# read issue IDs from previous run
	featureID=$(grep "featureID:" ${BATS_FILE_TMPDIR}/test_issues | cut -d":" -f2 | xargs)
	epicID=$(grep "epicID:" ${BATS_FILE_TMPDIR}/test_issues | cut -d":" -f2 | xargs)
	storyID=$(grep "storyID:" ${BATS_FILE_TMPDIR}/test_issues | cut -d":" -f2 | xargs)
	bugID=$(grep "bugID:" ${BATS_FILE_TMPDIR}/test_issues | cut -d":" -f2 | xargs)

	# Edit features: Second batch

	# PRARIT FIX ME: update when Contributors is enabled in TP
	# add multiple contributors
	#./rhjira edit  --contributors "prarit@redhat.com,rhel-ai-jira-bot" --noeditor $featureID

	# clear affectsversion field
	./rhjira edit  --affectsversion "" --noeditor $featureID
	# clear fixversion field
	./rhjira edit  --fixversion "" --noeditor $featureID

	showoutput=$(./rhjira show $featureID)

	# PRARIT FIX ME: update when Contributors is enabled in TP
	#contributors=$(echo "$showoutput" | grep "Contributors:")
	#run [ "$contributors" == "Contributors: prarit@redhat.com, rhel-ai-jira-bot" ]
	#check_status

	affectsversions=$(echo "$showoutput" | grep "Affects Versions:")
	echo "affectsversions=$affectsversions"
	run [ "$affectsversions" == "Affects Versions: " ]
	check_status

	fixversion=$(echo "$showoutput" | grep "Fix Versions:")
	echo "fixversion=$fixversion"
	run [ "$fixversion" == "Fix Versions: " ]
	check_status
}

@test "editfeature3" {
	# read issue IDs from previous run
	featureID=$(grep "featureID:" ${BATS_FILE_TMPDIR}/test_issues | cut -d":" -f2 | xargs)
	epicID=$(grep "epicID:" ${BATS_FILE_TMPDIR}/test_issues | cut -d":" -f2 | xargs)
	storyID=$(grep "storyID:" ${BATS_FILE_TMPDIR}/test_issues | cut -d":" -f2 | xargs)
	bugID=$(grep "bugID:" ${BATS_FILE_TMPDIR}/test_issues | cut -d":" -f2 | xargs)

	# PRARIT fix me.  This currently does not work in the code.
	# clear contributors
	#./rhjira edit --contributors "" --noeditor $featureID
	#showoutput=$(./rhjira show $featureID)

	#contributors=$(echo "$showoutput" | grep "Contributors:")
	#run [ "$contributors" == "Contributors: " ]
	#check_status

	# Modify description
	text="===================================
Hello world
Goodbye world
==================================="
	./rhjira edit --description "Hello world\nGoodbye world" --noeditor $featureID
	showoutput=$(./rhjira show $featureID)
	testtext=$(getDescription "$showoutput")
	echo "$text"
	echo "$testtext"
	run [ "$testtext" == "$text" ]
	check_status
}

@test "editepic1" {
	# read issue IDs from previous run
	featureID=$(grep "featureID:" ${BATS_FILE_TMPDIR}/test_issues | cut -d":" -f2 | xargs)
	epicID=$(grep "epicID:" ${BATS_FILE_TMPDIR}/test_issues | cut -d":" -f2 | xargs)
	storyID=$(grep "storyID:" ${BATS_FILE_TMPDIR}/test_issues | cut -d":" -f2 | xargs)
	bugID=$(grep "bugID:" ${BATS_FILE_TMPDIR}/test_issues | cut -d":" -f2 | xargs)

	# Edit epics: First batch
	./rhjira edit --affectsversion "4.9" --noeditor $epicID
	./rhjira edit --components "Documentation" --noeditor $epicID
	# PRARIT FIX ME: update when Contributors is enabled in TP
	#./rhjira edit --contributors "prarit@redhat.com" --noeditor $epicID
	./rhjira edit --fixversion "4.11" --noeditor $epicID
	./rhjira edit --priority "Normal" --noeditor $epicID
	./rhjira edit --summary "Updated Epic" --noeditor $epicID
	./rhjira edit --epicname "Updated Epic Name" --noeditor $epicID

	showoutput=$(./rhjira show $epicID)

	affectsversions=$(echo "$showoutput" | grep "Affects Versions:")
	run [ "$affectsversions" == "Affects Versions: 4.9" ]
	check_status

	components=$(echo "$showoutput" | grep "Components:")
	run [ "$components" == "Components: Documentation" ]
	check_status

	# PRARIT FIX ME: update when Contributors is enabled in TP
	#contributors=$(echo "$showoutput" | grep "Contributors:")
	#run [ "$contributors" == "Contributors: prarit@redhat.com" ]
	#check_status

	fixversion=$(echo "$showoutput" | grep "Fix Versions:")
	run [ "$fixversion" == "Fix Versions: 4.11" ]
	check_status

	priority=$(echo "$showoutput" | grep "Priority:")
	run [ "$priority" == "Priority: Normal" ]
	check_status

	summary=$(head -1 <<< "$showoutput")
	run [ "$summary" == "${epicID}: Updated Epic" ]
	check_status

	epicname=$(echo "$showoutput" | grep "Epic Name:")
	run [ "$epicname" == "Epic Name: Updated Epic Name" ]
	check_status
}

@test "editepic2" {
	# read issue IDs from previous run
	featureID=$(grep "featureID:" ${BATS_FILE_TMPDIR}/test_issues | cut -d":" -f2 | xargs)
	epicID=$(grep "epicID:" ${BATS_FILE_TMPDIR}/test_issues | cut -d":" -f2 | xargs)
	storyID=$(grep "storyID:" ${BATS_FILE_TMPDIR}/test_issues | cut -d":" -f2 | xargs)
	bugID=$(grep "bugID:" ${BATS_FILE_TMPDIR}/test_issues | cut -d":" -f2 | xargs)

	# Edit epics: Second batch

	# PRARIT FIX ME: update when Contributors is enabled in TP
	# add multiple contributors
	#./rhjira edit --contributors "prarit@redhat.com,rhel-ai-jira-bot" --noeditor $epicID

	# clear affectsversion field
	./rhjira edit --affectsversion "" --noeditor $epicID
	# clear fixversion field
	./rhjira edit --fixversion "" --noeditor $epicID

	showoutput=$(./rhjira show $epicID)

	# PRARIT FIX ME: update when Contributors is enabled in TP
	#contributors=$(echo "$showoutput" | grep "Contributors:")
	#run [ "$contributors" == "Contributors: prarit@redhat.com, rhel-ai-jira-bot" ]
	#check_status

	affectsversions=$(echo "$showoutput" | grep "Affects Versions:")
	echo "affectsversions=$affectsversions"
	run [ "$affectsversions" == "Affects Versions: " ]
	check_status

	fixversion=$(echo "$showoutput" | grep "Fix Versions:")
	echo "fixversion=$fixversion"
	run [ "$fixversion" == "Fix Versions: " ]
	check_status
}

@test "editepic3" {
	# read issue IDs from previous run
	featureID=$(grep "featureID:" ${BATS_FILE_TMPDIR}/test_issues | cut -d":" -f2 | xargs)
	epicID=$(grep "epicID:" ${BATS_FILE_TMPDIR}/test_issues | cut -d":" -f2 | xargs)
	storyID=$(grep "storyID:" ${BATS_FILE_TMPDIR}/test_issues | cut -d":" -f2 | xargs)
	bugID=$(grep "bugID:" ${BATS_FILE_TMPDIR}/test_issues | cut -d":" -f2 | xargs)

	# PRARIT fix me.  This currently does not work in the code.
	# clear contributors
	#./rhjira edit --contributors "" --noeditor $epicID
	#showoutput=$(./rhjira show $epicID)

	#contributors=$(echo "$showoutput" | grep "Contributors:")
	#run [ "$contributors" == "Contributors: " ]
	#check_status

	# Modify description
	text="===================================
Hello world
Goodbye world
==================================="
	./rhjira edit --description "Hello world\nGoodbye world" --noeditor $epicID
	showoutput=$(./rhjira show $epicID)
	testtext=$(getDescription "$showoutput")
	echo "$text"
	echo "$testtext"
	run [ "$testtext" == "$text" ]
	check_status

	# create a parent feature
	url=$(./rhjira create --components "Documentation" --description "Epic Parent link test -- do not use or track" --project "${JIRAPROJECT}" --summary "Test Feature -- do not track or use" --tickettype "Feature" --noeditor)
	run grep "$JIRAURL/${JIRAPROJECT}-" <<< "$url"
	check_status

	parentfeatureID=$(echo "$url" | rev  | cut -d "/" -f1 | rev)
	echo "The parent URL is :$url"

	# close the parent feature
	run ./rhjira close "$parentfeatureID"
	check_status

	./rhjira edit --parentlink "$parentfeatureID" --noeditor $epicID
	showoutput=$(removeShowLinks $epicID)
	parentlink=$(echo "$showoutput" | grep "Parent Link:")
	run [ "$parentlink" == "Parent Link: $parentfeatureID Test Feature -- do not track or use (Closed)" ]
	check_status
}

@test "editstory1" {
	# read issue IDs from previous run
	featureID=$(grep "featureID:" ${BATS_FILE_TMPDIR}/test_issues | cut -d":" -f2 | xargs)
	epicID=$(grep "epicID:" ${BATS_FILE_TMPDIR}/test_issues | cut -d":" -f2 | xargs)
	storyID=$(grep "storyID:" ${BATS_FILE_TMPDIR}/test_issues | cut -d":" -f2 | xargs)
	bugID=$(grep "bugID:" ${BATS_FILE_TMPDIR}/test_issues | cut -d":" -f2 | xargs)

	# Edit stories: First batch $storyID
	./rhjira edit --affectsversion "4.9" --noeditor $storyID
	./rhjira edit --components "Documentation" --noeditor $storyID
	# PRARIT FIX ME: update when Contributors is enabled in TP
	#./rhjira edit --contributors "prarit@redhat.com" --noeditor $storyID
	./rhjira edit --fixversion "4.11" --noeditor $storyID
	./rhjira edit --priority "Normal" --noeditor $storyID
	./rhjira edit --summary "Updated Story" --noeditor $storyID
	./rhjira edit --gitpullrequest "https://red.ht/GitLabSSO" --noeditor $storyID

	showoutput=$(./rhjira show $storyID)

	affectsversions=$(echo "$showoutput" | grep "Affects Versions:")
	run [ "$affectsversions" == "Affects Versions: 4.9" ]
	check_status

	component=$(echo "$showoutput" | grep "Components:")
	run [ "$component" == "Components: Documentation" ]
	check_status

	# PRARIT FIX ME: update when Contributors is enabled in TP
	#contributors=$(echo "$showoutput" | grep "Contributors:")
	#run [ "$contributors" == "Contributors: prarit@redhat.com" ]
	#check_status

	fixversion=$(echo "$showoutput" | grep "Fix Versions:")
	run [ "$fixversion" == "Fix Versions: 4.11" ]
	check_status

	priority=$(echo "$showoutput" | grep "Priority:")
	run [ "$priority" == "Priority: Normal" ]
	check_status

	summary=$(head -1 <<< "$showoutput")
	run [ "$summary" == "${storyID}: Updated Story" ]
	check_status

	gitpullrequest=$(echo "$showoutput" | grep "Git Pull Request:" )
	run [ "$gitpullrequest" == "Git Pull Request: https://red.ht/GitLabSSO" ]
	check_status
}

@test "editstory2" {
	# read issue IDs from previous run
	featureID=$(grep "featureID:" ${BATS_FILE_TMPDIR}/test_issues | cut -d":" -f2 | xargs)
	epicID=$(grep "epicID:" ${BATS_FILE_TMPDIR}/test_issues | cut -d":" -f2 | xargs)
	storyID=$(grep "storyID:" ${BATS_FILE_TMPDIR}/test_issues | cut -d":" -f2 | xargs)
	bugID=$(grep "bugID:" ${BATS_FILE_TMPDIR}/test_issues | cut -d":" -f2 | xargs)

	# Edit stories: Second batch

	# add multiple contributors
	#./rhjira edit --contributors "prarit@redhat.com,rhel-ai-jira-bot" --noeditor $storyID

	# clear affectsversion field
	./rhjira edit --affectsversion "" --noeditor $storyID
	# clear fixversion field
	./rhjira edit --fixversion "" --noeditor $storyID

	showoutput=$(./rhjira show $storyID)

	# PRARIT FIX ME: update when Contributors is enabled in TP
	#contributors=$(echo "$showoutput" | grep "Contributors:")
	#run [ "$contributors" == "Contributors: prarit@redhat.com, rhel-ai-jira-bot" ]
	#check_status

	affectsversions=$(echo "$showoutput" | grep "Affects Versions:")
	echo "affectsversions=$affectsversions"
	run [ "$affectsversions" == "Affects Versions: " ]
	check_status

	fixversion=$(echo "$showoutput" | grep "Fix Versions:")
	echo "fixversion=$fixversion"
	run [ "$fixversion" == "Fix Versions: " ]
	check_status
}

@test "editstory3" {
	# read issue IDs from previous run
	featureID=$(grep "featureID:" ${BATS_FILE_TMPDIR}/test_issues | cut -d":" -f2 | xargs)
	epicID=$(grep "epicID:" ${BATS_FILE_TMPDIR}/test_issues | cut -d":" -f2 | xargs)
	storyID=$(grep "storyID:" ${BATS_FILE_TMPDIR}/test_issues | cut -d":" -f2 | xargs)
	bugID=$(grep "bugID:" ${BATS_FILE_TMPDIR}/test_issues | cut -d":" -f2 | xargs)

	# PRARIT fix me.  This currently does not work in the code.
	# clear contributors
	#./rhjira edit --contributors "" --noeditor $storyID
	#showoutput=$(./rhjira show $storyID)

	#contributors=$(echo "$showoutput" | grep "Contributors:")
	#run [ "$contributors" == "Contributors: " ]
	#check_status

	# Modify description
	text="===================================
Hello world
Goodbye world
==================================="
	./rhjira edit --description "Hello world\nGoodbye world" --noeditor $storyID
	showoutput=$(./rhjira show $storyID)
	testtext=$(getDescription "$showoutput")
	echo "$text"
	echo "$testtext"
	run [ "$testtext" == "$text" ]
	check_status

	# create a parent epic
	url=$(./rhjira create --components "Documentation" --description "Epic Parent link test -- do not use or track" --project "${JIRAPROJECT}" --summary "Test Epic -- do not track or use" --tickettype "Epic" --epicname "test do not use" --noeditor)
	run grep "${JIRAURL}/${JIRAPROJECT}-" <<< "$url"
	check_status

	parentepicID=$(echo "$url" | rev  | cut -d "/" -f1 | rev)

	# close the parent epic
	run ./rhjira close "$parentepicID"
	check_status

	./rhjira edit --epiclink "$parentepicID" --noeditor $storyID
	showoutput=$(removeShowLinks $storyID)
	epiclink=$(echo "$showoutput" | grep "Epic Link:")
	run [ "$epiclink" == "Epic Link: $parentepicID Test Epic -- do not track or use (Closed)" ]
	check_status
}

@test "editbug1" {
	# read issue IDs from previous run
	featureID=$(grep "featureID:" ${BATS_FILE_TMPDIR}/test_issues | cut -d":" -f2 | xargs)
	epicID=$(grep "epicID:" ${BATS_FILE_TMPDIR}/test_issues | cut -d":" -f2 | xargs)
	storyID=$(grep "storyID:" ${BATS_FILE_TMPDIR}/test_issues | cut -d":" -f2 | xargs)
	bugID=$(grep "bugID:" ${BATS_FILE_TMPDIR}/test_issues | cut -d":" -f2 | xargs)

	# Edit stories: First batch $bugID
	./rhjira edit --affectsversion "4.9" --noeditor $bugID
	./rhjira edit --components "Documentation" --noeditor $bugID
	# PRARIT FIX ME: update when Contributors is enabled in TP
	#./rhjira edit --contributors "prarit@redhat.com" --noeditor $bugID
	./rhjira edit --fixversion "4.11" --noeditor $bugID
	./rhjira edit --priority "Normal" --noeditor $bugID
	./rhjira edit --summary "Updated Bug" --noeditor $bugID
	./rhjira edit --gitpullrequest "https://red.ht/GitLabSSO" --noeditor $bugID

	showoutput=$(./rhjira show $bugID)

	affectsversions=$(echo "$showoutput" | grep "Affects Versions:")
	run [ "$affectsversions" == "Affects Versions: 4.9" ]
	check_status

	component=$(echo "$showoutput" | grep "Components:")
	run [ "$component" == "Components: Documentation" ]
	check_status

	# PRARIT FIX ME: update when Contributors is enabled in TP
	#contributors=$(echo "$showoutput" | grep "Contributors:")
	#run [ "$contributors" == "Contributors: prarit@redhat.com" ]
	#check_status

	fixversion=$(echo "$showoutput" | grep "Fix Versions:")
	run [ "$fixversion" == "Fix Versions: 4.11" ]
	check_status

	priority=$(echo "$showoutput" | grep "Priority:")
	run [ "$priority" == "Priority: Normal" ]
	check_status

	summary=$(head -1 <<< "$showoutput")
	run [ "$summary" == "${bugID}: Updated Bug" ]
	check_status

	gitpullrequest=$(echo "$showoutput" | grep "Git Pull Request:" )
	run [ "$gitpullrequest" == "Git Pull Request: https://red.ht/GitLabSSO" ]
	check_status
}

@test "editbug2" {
	# read issue IDs from previous run
	featureID=$(grep "featureID:" ${BATS_FILE_TMPDIR}/test_issues | cut -d":" -f2 | xargs)
	epicID=$(grep "epicID:" ${BATS_FILE_TMPDIR}/test_issues | cut -d":" -f2 | xargs)
	storyID=$(grep "storyID:" ${BATS_FILE_TMPDIR}/test_issues | cut -d":" -f2 | xargs)
	bugID=$(grep "bugID:" ${BATS_FILE_TMPDIR}/test_issues | cut -d":" -f2 | xargs)

	# Edit stories: Second batch

	# add multiple contributors
	./rhjira edit --contributors "prarit@redhat.com,rhel-ai-jira-bot" --noeditor $bugID

	# clear affectsversion field
	./rhjira edit --affectsversion "" --noeditor $bugID
	# clear fixversion field
	./rhjira edit --fixversion "" --noeditor $bugID

	showoutput=$(./rhjira show $bugID)

	# PRARIT FIX ME: update when Contributors is enabled in TP
	#contributors=$(echo "$showoutput" | grep "Contributors:")
	#run [ "$contributors" == "Contributors: prarit@redhat.com, rhel-ai-jira-bot" ]
	#check_status

	affectsversions=$(echo "$showoutput" | grep "Affects Versions:")
	echo "affectsversions=$affectsversions"
	run [ "$affectsversions" == "Affects Versions: " ]
	check_status

	fixversion=$(echo "$showoutput" | grep "Fix Versions:")
	echo "fixversion=$fixversion"
	run [ "$fixversion" == "Fix Versions: " ]
	check_status
}

@test "editbug3" {
	# read issue IDs from previous run
	featureID=$(grep "featureID:" ${BATS_FILE_TMPDIR}/test_issues | cut -d":" -f2 | xargs)
	epicID=$(grep "epicID:" ${BATS_FILE_TMPDIR}/test_issues | cut -d":" -f2 | xargs)
	storyID=$(grep "storyID:" ${BATS_FILE_TMPDIR}/test_issues | cut -d":" -f2 | xargs)
	bugID=$(grep "bugID:" ${BATS_FILE_TMPDIR}/test_issues | cut -d":" -f2 | xargs)

	# PRARIT fix me.  This currently does not work in the code.
	# clear contributors
	#./rhjira edit --contributors "" --noeditor $bugID
	#showoutput=$(./rhjira show $bugID)

	#contributors=$(echo "$showoutput" | grep "Contributors:")
	#run [ "$contributors" == "Contributors: " ]
	#check_status

	# Modify description
	text="===================================
Hello world
Goodbye world
==================================="
	./rhjira edit --description "Hello world\nGoodbye world" --noeditor $bugID
	showoutput=$(./rhjira show $bugID)
	testtext=$(getDescription "$showoutput")
	echo "$text"
	echo "$testtext"
	run [ "$testtext" == "$text" ]
	check_status

	# bugs do not link to epics.
}
