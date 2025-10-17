# Development Guide

Development setup and workflow for Loppers.

## Prerequisites

- Python 3.8+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

## Setup

### With uv

```bash
# Clone and enter directory
git clone https://github.com/yourusername/loppers.git
cd loppers

# Sync dependencies including dev tools
uv sync --extra dev
```

### With pip

```bash
pip install -e ".[dev]"
```

## Testing with pytest

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest test_loppers.py

# Run specific test class
uv run pytest test_loppers.py::TestSkeletonExtractor

# Run specific test
uv run pytest test_loppers.py::TestSkeletonExtractor::test_python_extraction

# Run with markers (if defined)
uv run pytest -m "not slow"
```

### Test Coverage

```bash
# Generate coverage report
uv run pytest --cov=loppers --cov-report=html

# View coverage in terminal
uv run pytest --cov=loppers --cov-report=term-missing
```

### Test Configuration

Tests are configured in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
minversion = "7.0"
testpaths = ["tests", "."]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --strict-markers --tb=short"
markers = [
    "slow: marks tests as slow",
    "integration: marks tests as integration tests",
]
```

## Code Quality with ruff

### Checking Code

```bash
# Check for linting issues
uv run ruff check .

# Check specific file
uv run ruff check loppers.py

# Show all issues with details
uv run ruff check . --show-settings
```

### Fixing Issues

```bash
# Fix issues automatically
uv run ruff check . --fix

# Fix only specific rules
uv run ruff check . --fix --select E,W

# Format code
uv run ruff format .
```

### Ruff Configuration

Configuration in `pyproject.toml`:

```toml
[tool.ruff]
target-version = "py38"
line-length = 100
fix = true

[tool.ruff.lint]
select = [
    "E",      # pycodestyle errors
    "W",      # pycodestyle warnings
    "F",      # pyflakes
    "I",      # isort
    "C4",     # flake8-comprehensions
    "UP",     # pyupgrade
    "ARG",    # flake8-unused-arguments
    "SIM",    # flake8-simplify
    "RUF",    # ruff-specific rules
    "D",      # pydocstyle (Google style)
]
ignore = [
    "E203",   # whitespace before ':'
    "D104",   # missing docstring in public package
    "D100",   # missing docstring in public module
]
```

### Ruff Rules

- **E/W**: PEP 8 style violations
- **F**: PyFlakes (undefined names, unused imports)
- **I**: isort (import sorting)
- **C4**: flake8-comprehensions
- **UP**: pyupgrade (use modern Python syntax)
- **ARG**: flake8-unused-arguments
- **SIM**: flake8-simplify
- **RUF**: Ruff-specific rules
- **D**: pydocstyle (docstring conventions)

## Type Checking

Type hints are included throughout the codebase. To add mypy checking:

```bash
pip install mypy
mypy loppers.py
```

## Development Workflow

### 1. Make Changes

Edit code in `loppers.py`, `examples.py`, or tests.

### 2. Check Code Quality

```bash
# Run all checks
uv run ruff check . --fix
uv run ruff format .
```

### 3. Run Tests

```bash
# Run tests with coverage
uv run pytest --cov=loppers --cov-report=term-missing
```

### 4. Build and Install

```bash
# Reinstall in editable mode
uv pip install -e .
```

## Common Tasks

### Add a New Language

1. Update `LANGUAGE_CONFIGS` in `loppers.py` with query
2. Add test in `test_loppers.py`
3. Update `README.md` supported languages list
4. Run `uv run pytest` to verify

### Update Dependencies

```bash
# Update lockfile
uv lock

# Or upgrade all dependencies
uv sync --upgrade
```

### Build Distribution

```bash
# Build wheel and sdist
uv build

# Or use hatch
uv run hatch build
```

### Publish to PyPI

```bash
# Build
uv build

# Publish
uv run hatch publish
```

## Debugging

### Enable Verbose Output

```bash
# Pytest verbose
uv run pytest -vv

# Pytest with full traceback
uv run pytest --tb=long
```

### Debug with print statements

```python
# Add print statements in code
print(f"DEBUG: {variable}")

# Run tests with output capture disabled
uv run pytest -s
```

## Pre-commit Hook (Optional)

Create `.git/hooks/pre-commit`:

```bash
#!/bin/bash
set -e

echo "Running ruff..."
uv run ruff check . --fix
uv run ruff format .

echo "Running pytest..."
uv run pytest

echo "All checks passed!"
```

Make executable: `chmod +x .git/hooks/pre-commit`

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [ruff documentation](https://github.com/astral-sh/ruff)
- [uv documentation](https://docs.astral.sh/uv/)
- [tree-sitter documentation](https://tree-sitter.github.io/)