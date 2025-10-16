#!/usr/bin/env bats

check_status() {
	if [ -z "$status" ]; then
		echo -e "\n\n\n Error no 'run' command detected!\n\n\n"
		exit 1
	fi
	if [ "$status" -eq 0 ]; then
		return 0
	fi

	echo "ERROR ERROR ERROR ERROR (see Last output below...)"
	exit 1
}

grepdumpdata() {
	local grepstr=$1

	field=$(echo "$grepstr" | cut -d "|" -f2 | cut -d "\\" -f1)
	echo "grepdumpdata field = |$field|"
	[ "$field" != "" ] || return 1

	fieldout=$(./rhjira dump --showcustomfields --showemptyfields --fields "$field" RHEL-56971)

	echo "grepdumpdata command = ./rhjira dump --showcustomfields --showemptyfields --fields \"$field\" RHEL-56971"
	echo "grepdumpdata grpstr = |$grepstr|"
	echo "grepdumpdata fieldout: $fieldout"

	echo "test 1: TESTOUTPUT ..."
	grep "$grepstr" $TESTOUTPUT || return 1
	echo "test 2: fieldout ..."
	grep "$grepstr" <<< "$fieldout" || return 1

	return 0
}

getDescription() {
	local output
	local lines
	local first
	local last
	local testout
	output="$1"
	lines=$(echo "$output" | grep -n "^=")
	first=$(echo "$lines" | head -1 | cut -d":" -f1)
	last=$(echo "$lines" | tail -1 | cut -d":" -f1)
	echo "$output" | sed -n "${first},${last}p"
}

removeShowLinks() {
	./rhjira show $1 | sed 's/\x1b\[[0-9;]*m//g' | sed 's/\x1b\]8;;[^\a]*\a//g'
}
