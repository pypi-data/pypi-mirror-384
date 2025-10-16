.PHONY: all lint format lint-fix test help

# Default target executed when no arguments are given to make
all: help

######################
# TESTING AND COVERAGE
######################

# Define a variable for the test file path.
TEST ?= tests/unit

test:
	uv run pytest $(TEST) -v

######################
# LINTING AND FORMATTING
######################

# Define a variable for Python and notebook files.
lint format: PYTHON_FILES=.
lint_diff format_diff: PYTHON_FILES=$(shell git diff --relative=. --name-only --diff-filter=d main | grep -E '\.py$$|\.ipynb$$')

lint lint_diff:
	[ "$(PYTHON_FILES)" = "" ] ||	uv run ruff format $(PYTHON_FILES) --check
	[ "$(PYTHON_FILES)" = "" ] ||	uv run ruff check $(PYTHON_FILES)

format format_diff:
	[ "$(PYTHON_FILES)" = "" ] || uv run ruff format $(PYTHON_FILES)
	[ "$(PYTHON_FILES)" = "" ] || uv run ruff check --fix $(PYTHON_FILES)

lint-fix:
	uv run ruff format $(PYTHON_FILES)
	uv run ruff check --fix $(PYTHON_FILES)

######################
# HELP
######################

help:
	@echo '===================='
	@echo '-- LINTING --'
	@echo 'format                       - run code formatters'
	@echo 'lint                         - run linters'
	@echo 'lint-fix                     - run linters and fix issues'
	@echo '-- TESTS --'
	@echo 'test                         - run tests'
	@echo 'test TEST=<test_file>        - run specific test file'
