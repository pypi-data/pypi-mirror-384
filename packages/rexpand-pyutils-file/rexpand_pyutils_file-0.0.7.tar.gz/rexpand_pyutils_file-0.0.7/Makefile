.PHONY: install test lint clean build publish venv

VENV_NAME := .venv
PYTHON := python3
VENV_BIN := $(VENV_NAME)/bin
VENV_PYTHON := $(VENV_BIN)/python

# Create virtual environment
venv:
	$(PYTHON) -m venv $(VENV_NAME)
	@echo "To activate virtual environment, run: source $(VENV_NAME)/bin/activate"

# Install package in development mode
install: venv
	$(VENV_PYTHON) -m pip install --upgrade pip
	$(VENV_PYTHON) -m pip install -e ".[dev]"

# Run tests
test:
	$(VENV_PYTHON) -m pytest tests/ -v

# Run linting
lint:
	$(VENV_PYTHON) -m flake8 rexpand_pyutils_matching tests
	$(VENV_PYTHON) -m black --check rexpand_pyutils_matching tests
	$(VENV_PYTHON) -m mypy rexpand_pyutils_matching tests

# Format code
format:
	$(VENV_PYTHON) -m black rexpand_pyutils_matching tests

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete

# Deep clean (includes venv)
clean-all: clean
	rm -rf $(VENV_NAME)

# Build package
build: clean
	$(VENV_PYTHON) -m build

# Upload to PyPI
publish: build
	$(VENV_PYTHON) -m twine upload dist/*

# Run all checks before commit
pre-commit: lint test 
