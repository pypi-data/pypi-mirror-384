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

# $ticketID is a ticketID that is created in createwithtemplate and can
# be used in other tests in this file
#
# ie) ticketID=$(cat ${BATS_FILE_TMPDIR}/ticketID)

@test "createwithtemplate" {
	url=$(./rhjira create -T ./rhel-template-good --noeditor)
	run grep "${JIRAURL}/${JIRAPROJECT}-" <<< "$url"
	check_status

	ticketID=$(echo "$url" | rev  | cut -d "/" -f1 | rev)
	./rhjira close $ticketID
	showoutput=$(./rhjira show $ticketID)
	run grep "Status: Closed" <<< "$showoutput"
	check_status

	echo "$ticketID" >> ${BATS_FILE_TMPDIR}/ticketID

	erroroutput=$(./rhjira create -T ./rhel-template-badversion --noeditor) || true
	echo "$erroroutput"
	run grep "To re-run the command" <<< "$erroroutput"
	check_status
}

@test "addComment" {
	ticketID=$(cat ${BATS_FILE_TMPDIR}/ticketID)
	showoutput=$(./rhjira show $ticketID)
	numcommentsorig=$(echo "$showoutput" | grep -e "---------" | cut -d" " -f2 | xargs)

	# showoutput should not contain comment.txt
	showoutput=$(./rhjira show $ticketID)
	comment=$(cat ./comment.txt)
	grep "$comment" <<< "$showoutput" || true
	retval=$?
	run [ "$retval" -eq 0 ]
	check_status

	# output should contain comment.txt
	./rhjira comment -f ./comment.txt --noeditor $ticketID
	showoutput=$(./rhjira show $ticketID)
	grep "$comment" <<< "$showoutput"
	retval=$?
	run [ "$retval" -eq 0 ]
	check_status

	# add another two comments for a total of three
	./rhjira comment -f ./comment.txt --noeditor $ticketID
	./rhjira comment -f ./comment.txt --noeditor $ticketID
	showoutput=$(./rhjira show $ticketID)
	numcomments=$(echo "$showoutput" | grep -e "---------" | cut -d" " -f2 | xargs)
	numnewcomments=$(($numcomments - $numcommentsorig))

	# verify three comments were added
	run [ $(($numcomments - $numcommentsorig)) -eq 3 ]
	check_status
}

@test "listTestdefault" {
	# this is a default list, there should be 50 entries (starting at 0) and
	# the headers should be  "#  Issue     summary"
	run ./rhjira list "summary is not empty"
	check_status
	numentries=$(echo "$output" | wc -l)
	# default is 50 + the header
	[ "$numentries" -eq 51 ]
	check_status
}

@test "listTest10" {
	run ./rhjira list --numentries 10 "summary is not empty"
	check_status
	numentries=$(echo "$output" | wc -l)
	# 10 + the header
	[ "$numentries" -eq 11 ]
	check_status
}

@test "listTest10noheader" {
	run ./rhjira list --numentries 10 --noheader "summary is not empty"
	check_status
	numentries=$(echo "$output" | wc -l)
	# 10 (no header!)
	[ "$numentries" -eq 10 ]
	check_status
}

@test "listTest10affectsversions" {
	run ./rhjira list --numentries 10 --fields versions,summary "summary is not empty"
	check_status
	numentries=$(echo "$output" | wc -l)
	# 10 + the header
	[ "$numentries" -eq 11 ]
	check_status
}

#@test "listWithName" {
	# for some reason customfield searches stopped working.  Even older versions
	# of rhjira will return a 400 error
	#run ./rhjira list --noheader --numentries 1 "'customfield_12323641' is not empty"
	#customfield="$output"
	#check_status
	#run ./rhjira list --noheader --numentries 1 "'Workaround' is not empty"
	#name="$output"
	#check_status
	#[ "$customfield" == "$name" ]
	#check_status
#}
