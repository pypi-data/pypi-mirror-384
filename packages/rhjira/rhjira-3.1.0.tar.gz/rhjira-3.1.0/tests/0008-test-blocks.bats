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

@test "testblocks" {
    # Create a story
    url=$(./rhjira create --components "Documentation" --description "Story test\nThe quick brown giraffe\nran out of curds and whey" --priority "Minor" --project "${JIRAPROJECT}" --summary "Test Story for Blocks -- do not track or use" --tickettype "Story" --noeditor)
    run grep "${JIRAURL}/${JIRAPROJECT}-" <<< "$url"
    check_status

    storyID=$(echo "$url" | rev | cut -d "/" -f1 | rev)
    echo "      story ID: $storyID" >&3
    echo "storyID: $storyID" >> ${BATS_FILE_TMPDIR}/test_issues
    run grep "${JIRAPROJECT}-" <<< "$storyID"
    check_status

    # Create first task that blocks the story
    url=$(./rhjira create --components "Documentation" --description "Task that blocks story\nThe quick brown giraffe\nran out of curds and whey" --priority "Minor" --project "${JIRAPROJECT}" --summary "Task that blocks story -- do not track or use" --tickettype "Task" --blocks "$storyID" --noeditor)
    run grep "${JIRAURL}/${JIRAPROJECT}-" <<< "$url"
    check_status

    blocking_taskID=$(echo "$url" | rev | cut -d "/" -f1 | rev)
    echo "      blocking task ID: $blocking_taskID" >&3
    echo "blocking_taskID: $blocking_taskID" >> ${BATS_FILE_TMPDIR}/test_issues
    run grep "${JIRAPROJECT}-" <<< "$blocking_taskID"
    check_status

    # Create second task that is blocked by the story
    url=$(./rhjira create --components "Documentation" --description "Task blocked by story\nThe quick brown giraffe\nran out of curds and whey" --priority "Minor" --project "${JIRAPROJECT}" --summary "Task blocked by story -- do not track or use" --tickettype "Task" --isblockedby "$storyID" --noeditor)
    run grep "${JIRAURL}/${JIRAPROJECT}-" <<< "$url"
    check_status

    blocked_taskID=$(echo "$url" | rev | cut -d "/" -f1 | rev)
    echo "      blocked task ID: $blocked_taskID" >&3
    echo "blocked_taskID: $blocked_taskID" >> ${BATS_FILE_TMPDIR}/test_issues
    run grep "${JIRAPROJECT}-" <<< "$blocked_taskID"
    check_status

    # Verify the relationships
    showoutput=$(./rhjira show "$blocking_taskID")
    run grep "Blocks:.*$storyID" <<< "$showoutput"
    check_status

    showoutput=$(./rhjira show "$storyID")
    run grep "Is Blocked By:.*$blocking_taskID" <<< "$showoutput"
    check_status
    run grep "Blocks:.*$blocked_taskID" <<< "$showoutput"
    check_status

    showoutput=$(./rhjira show "$blocked_taskID")
    run grep "Is Blocked By:.*$storyID" <<< "$showoutput"
    check_status

    # Clean up - close all issues
    run ./rhjira close "$blocking_taskID"
    check_status
    run ./rhjira close "$storyID"
    check_status
    run ./rhjira close "$blocked_taskID"
    check_status
} 
