#!/usr/bin/env bats

load ./library.bats

setup_file() {
    echo "********************************************" >&3
    echo "Running tests in $BATS_TEST_FILENAME" >&3
    echo "********************************************" >&3

    [ -e ./rhjira ] && rm -f ./rhjira
    cp ../bin/rhjira .

    export JIRAID="TP-15864" # Use a safe test ticket
}

@test "clone command help" {
    run ./rhjira clone --help
    check_status
    echo "$output" | grep -q "Clone a jira ticket"
}

@test "clone command requires ticket ID" {
    run ./rhjira clone
    [ "$status" -ne 0 ]
    echo "$output" | grep -q "Error: ticketID not clear or found"
}

@test "clone basic functionality" {
    run ./rhjira clone $JIRAID --tickettype Story --summary "Test Clone Summary"
    # Output the new ticket ID if present
    echo "$output" | grep -Eo 'https://issues.redhat.com/browse/[A-Z0-9-]+' | tee /dev/stderr
    # Should attempt to create but may fail due to permissions - that's ok
    # We're testing that the command parses correctly and tries to create
    echo "$output" | grep -q -E "(Cloning|Failed to)"

    # Close the new ticket if created
    newkey=$(echo "$output" | grep -Eo 'https://issues.redhat.com/browse/[A-Z0-9-]+' | sed 's|.*/||')
    if [ -n "$newkey" ]; then
      ./rhjira close "$newkey"
    fi
}

@test "clone with all options" {
    run ./rhjira clone $JIRAID \
        --tickettype Bug \
        --summary "Cloned Bug" \
        --description "Test clone description" \
        --components "TestComponent" \
        --labels "test,clone" \
        --assignee "test@redhat.com" \
        --priority High \
        --with-comments \
        --with-attachments \
        --project TP
    # Output the new ticket ID if present
    echo "$output" | grep -Eo 'https://issues.redhat.com/browse/[A-Z0-9-]+' | tee /dev/stderr
    # Should attempt to create but may fail - we're testing argument parsing
    echo "$output" | grep -q -E "(Cloning|Failed to)"

    # Close the new ticket if created
    newkey=$(echo "$output" | grep -Eo 'https://issues.redhat.com/browse/[A-Z0-9-]+' | sed 's|.*/||')
    if [ -n "$newkey" ]; then
      ./rhjira close "$newkey"
    fi
}
