load ./library.bats

setup_file() {
    echo "********************************************" >&3
    echo "Running tests in $BATS_TEST_FILENAME" >&3
    echo "********************************************" >&3

    [ -e ./rhjira ] && rm -f ./rhjira
    cp ../bin/rhjira .

    export JIRAID="TP-15864"

    RESOLUTIONS=$(./rhjira info --project TP resolutions | cut -d"-" -f1 )
    export RESOLUTIONS
}

@test "openbug" {
	echo "$RESOLUTIONS" | while read resolution
	do
		echo "Running $resolution test" >&3
		./rhjira edit $JIRAID --noeditor --status "In Progress"
		./rhjira edit $JIRAID --noeditor --status Closed --resolution "$resolution"
		result=$(./rhjira show $JIRAID | grep "Status:")
		run [ "$result" == "Status: Closed ($resolution)" ]
		check_status
	done
}

# compare edit vs close commands
@test "closevsedit" {
	run ./rhjira edit $JIRAID --status "In Progress" --noeditor
	check_status
	run ./rhjira close $JIRAID
	check_status

	run ./rhjira edit $JIRAID --status "In Progress" --noeditor
	check_status
	run ./rhjira edit $JIRAID --status "Closed" --noeditor
	check_status
}
