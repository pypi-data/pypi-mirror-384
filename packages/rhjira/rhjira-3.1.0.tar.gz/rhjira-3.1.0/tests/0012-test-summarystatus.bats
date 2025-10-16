#!/usr/bin/env bats

load ./library.bats

setup_file() {
    echo "********************************************" >&3
    echo "Running tests in $BATS_TEST_FILENAME" >&3
    echo "********************************************" >&3

    [ -e ./rhjira ] && rm -f ./rhjira
    cp ../bin/rhjira .
}


@test "test summarystatus field functionality" {
	# Use an existing Feature ticket for testing (Status Summary only available for Features and Epics)
	ticketID="AIPCC-1291"

	echo "Using ticket: $ticketID" >&3

	# Get current status summary if any
	showoutput=$(./rhjira show $ticketID)
	run grep -q "Status Summary:" <<< "$showoutput"
	check_status

	# Use edit with --noeditor to add/update entry
	./rhjira edit --summarystatus "Test status: Working on implementation" --noeditor $ticketID

	# Show that it now has an entry
	showoutput=$(./rhjira show $ticketID)
	run grep -q "Status Summary: Test status: Working on implementation" <<< "$showoutput"
	check_status

	# Clear the status summary field
	./rhjira edit --summarystatus "" --noeditor $ticketID

	echo "Test completed successfully for ticket: $ticketID" >&3
}
