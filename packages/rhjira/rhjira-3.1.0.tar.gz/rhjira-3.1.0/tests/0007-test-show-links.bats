#!/usr/bin/env bats

load ./library.bats

setup_file() {
	echo "********************************************" >&3
	echo "Running tests in $BATS_TEST_FILENAME" >&3
	echo "********************************************" >&3

	[ -e ./rhjira ] && rm -f ./rhjira
	cp ../bin/rhjira .
	export FEATUREID="AIPCC-1394"
	export FEATURENAME="upgrade platform to support torch 2.7 (Closed)"
	export EPICID="AIPCC-1537"
	export EPICNAME="build torch-2.7 (Closed)"
	export STORYID="AIPCC-1538"
	export STORYNAME="CUDA torch-2.7 (Closed)"
	export TASKID="AIPCC-1539"
	export TASKNAME="torch-2.7: Mirror CUDA 12.8 components (Closed)"
}

@test "feature_links" {
	OUTPUT=$(removeShowLinks "$FEATUREID")
	run grep "Blocks: AIPCC-1363 NVIDIA Blackwell support (Closed)" <<< "$OUTPUT"

	check_status
}

@test "epic_links" {
	OUTPUT=$(removeShowLinks "$EPICID")
	run grep "Parent Link: $FEATUREID $FEATURENAME" <<< "$OUTPUT"
	check_status
}

@test "story_links" {
	OUTPUT=$(removeShowLinks "$STORYID")
	run grep "Epic Link: $EPICID $EPICNAME" <<< "$OUTPUT"
	check_status

	run grep "Is Blocked By: $TASKID $TASKNAME" <<< "$OUTPUT"
	check_status
}

@test "task_links" {
	OUTPUT=$(removeShowLinks "$TASKID")
	run grep "Blocks: $STORYID $STORYNAME" <<< "$OUTPUT"
	check_status
}

#@test "nolinks" {
#	OUTPUT=$(removeShowLinks RHEL-9999)
#	run echo "$OUTPUT" | grep -E "Epic Link:|Parent Link:|Blocks:|Is Blocked By:|Child Issue:"
#	[ "$status" -eq 1 ]  # grep should fail (not find anything)
#}
