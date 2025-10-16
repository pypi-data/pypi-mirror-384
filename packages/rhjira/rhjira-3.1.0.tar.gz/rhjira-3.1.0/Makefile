venv:
	@echo "Run:"
	@echo "python3 -m venv .venv && source .venv/bin/activate"
	@echo "pip install -e ."
	@echo "pip install .[dev]"

build:
	python3 -m pip install --upgrade build twine
	python3 -m build

pushtest: build
	grep "^version" pyproject.toml | awk -F\" '{print $2}'
	version=$(grep "^version" pyproject.toml | awk -F\" '{print $2}')
	python3 -m twine upload --repository testpypi dist/*$${version}*

pushpypi: build
	grep "^version" pyproject.toml | awk -F\" '{print $2}'
	version=$(grep "^version" pyproject.toml | awk -F\" '{print $2}')
	python3 -m twine upload dist/*

.PHONY: linter
linter:
ifdef STAGED_FILES
	echo "Running Ruff on staged files..."; \
	ruff check $(STAGED_FILES) || exit 1; \
	echo "\nRunning MyPy on staged files..."; \
	python -m mypy $(STAGED_FILES) || exit 1
else
	echo "Running Ruff..."; \
	ruff check src/ bin/rhjira || exit 1; \
	echo "\nRunning MyPy..."; \
	python -m mypy src/ bin/rhjira || exit 1
endif
