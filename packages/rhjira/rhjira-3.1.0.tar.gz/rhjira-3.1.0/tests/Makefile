run:
	bats -x -T --print-output-on-failure *.bats
	pytest test_util.py -v

run-one:
	if [ -z "$(TESTS)" ]; then \
		echo "Error: make run-one TESTS=...";\
		exit 1;\
	fi
	bats -x -T --print-output-on-failure $(TESTS)

no-dump-run:
	bats -x -T --print-output-on-failure 000[23456789]*.bats
	pytest test_util.py -v
