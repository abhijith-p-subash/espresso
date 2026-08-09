.PHONY: help install dev run test lint format check build clean

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

install:  ## Install the app
	pip install -e .

dev:  ## Install with dev and build extras
	pip install -e ".[dev,build]"

run:  ## Run from source with debug logging
	python -m espresso --log-level DEBUG

test:  ## Run the test suite
	pytest

lint:  ## Lint and check formatting
	ruff check .
	ruff format --check .

format:  ## Auto-fix lint and formatting
	ruff check --fix .
	ruff format .

check: lint test  ## Everything CI runs

build:  ## Build a standalone binary for this platform
	pyinstaller Espresso.spec --noconfirm

clean:  ## Remove build and cache artefacts
	rm -rf build dist *.egg-info src/*.egg-info
	rm -rf .pytest_cache .ruff_cache
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
