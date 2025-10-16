#!/usr/bin/env bats

load ./library.bats

# List of options to fuzz
OPTIONS=(
  "--status"
  "--resolution"
  "--priority"
  "--assignee"
  "--components"
)

# List of random/invalid values to try
VALUES=(
  "???"
  "1234567890"
  "NULL"
  "CLOSED"
  "open; rm -rf /"
  "$(head -c 32 /dev/urandom | base64)"
  "DROP TABLE users;"
  "a very very very very very very very very very very very very long string"
)

# Number of fuzz iterations
FUZZ_ITER=20

@test "fuzz edit command for error handling" {
  export JIRAID="TP-15864" # Use a safe test ticket

  for i in $(seq 1 $FUZZ_ITER); do
    # Pick a random option and value
    opt_idx=$(( RANDOM % ${#OPTIONS[@]} ))
    val_idx=$(( RANDOM % ${#VALUES[@]} ))
    option="${OPTIONS[$opt_idx]}"
    value="${VALUES[$val_idx]}"

    # Compose the command
    cmd="./rhjira edit $JIRAID $option \"$value\" --noeditor"

    echo "Fuzz iteration $i: $cmd" >&3

    # Run the command and capture output
    run bash -c "$cmd"

    # Check: Should not crash, should exit non-zero for bad input
    if [ "$status" -eq 0 ]; then
      echo "Warning: Command succeeded unexpectedly: $cmd" >&3
    fi

    # Check for stack traces or unhandled exceptions
    echo "$output" | grep -E -i 'Traceback|Exception|Error:|stack trace' && \
      echo "FAIL: Unhandled error for: $cmd" >&3 && exit 1

    # Optionally, check for your custom error message
    echo "$output" | grep -q "Failed to" || \
      (echo "FAIL: No error message for: $cmd" >&3 && exit 1)
  done
} 
