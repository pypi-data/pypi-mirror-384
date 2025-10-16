# Loppers

Simplified library for extracting source file skeletons using tree-sitter queries.

Removes function implementations while preserving structure and signatures.

**Requires tree-sitter >= 0.25**

## Features

- ✅ **Functions & Methods** - All regular and async functions
- ✅ **Constructors** - Python `__init__`, Java/TS `constructor()`
- ✅ **Arrow Functions** - JavaScript/TypeScript arrow functions
- ✅ **Class Methods** - Instance, static, class methods
- ✅ **Docstrings** - Python docstrings preserved
- ✅ **Decorators** - Preserved (Python, Java)
- ✅ **Type Hints** - Fully typed library
- ✅ **11 Languages** - Python, JS/TS, Java, Go, Rust, C/C++, C#, Ruby, PHP

See [HANDLED_CASES.md](HANDLED_CASES.md) for comprehensive list of supported cases.

## Installation

### With uv (recommended)

```bash
# Install from source
uv pip install -e .

# Or sync with pyproject.toml
uv sync

# Install with dev dependencies
uv sync --extra dev
```

### With pip

```bash
pip install tree-sitter>=0.25.0 tree-sitter-language-pack
```

## Usage

```python
from loppers import extract

source: str = '''
def calculate(x: int, y: int) -> int:
    """Calculate sum."""
    result: int = x + y
    return result
'''

skeleton: str = extract(source, "python")
print(skeleton)
```

Output:
```python
def calculate(x: int, y: int) -> int:
    """Calculate sum."""
```

## Supported Languages

- Python (with docstring preservation)
- JavaScript / TypeScript (including arrow functions)
- Java (including constructors)
- Go
- Rust
- C / C++
- C#
- Ruby
- PHP

## Development

### Setup

```bash
# Create environment and install dev dependencies
uv sync --extra dev
```

### Testing with pytest

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run with coverage
uv run pytest --cov=loppers --cov-report=html

# Run specific test
uv run pytest test_loppers.py::TestSkeletonExtractor::test_python_extraction

# Run with markers
uv run pytest -m "not slow"
```

### Code Quality with ruff

```bash
# Check code style
uv run ruff check .

# Fix issues automatically
uv run ruff check . --fix

# Format code (included in check --fix)
uv run ruff format .

# Run all checks
uv run ruff check . && uv run ruff format .
```

### How It Works

Uses tree-sitter queries to find and remove function/method body nodes while keeping:
- Function signatures
- Class definitions
- Import statements
- **Python docstrings**
- Comments

## API

### `extract(source_code: str, language: str) -> str`

Extract skeleton from source code.

**Args:**
- `source_code`: Source code to process
- `language`: Programming language

**Returns:** Skeleton with implementations removed

**Raises:**
- `ValueError`: If language not supported

### `SkeletonExtractor(language: str)`

Create extractor for a specific language.

**Methods:**
- `extract(source_code: str) -> str`: Extract skeleton

**Raises:**
- `ValueError`: If language not supported

## Adding Languages

To add a new language, extend `LANGUAGE_CONFIGS` with a tree-sitter query:

```python
LANGUAGE_CONFIGS["newlang"] = LanguageConfig(
    name="newlang",
    body_query="(function_definition body: (block) @body)",
)
```

Find the correct query for your language by exploring the tree-sitter grammar.

## Type Hints

This project uses comprehensive type hints throughout. All functions are fully typed.

```python
# Example of type hints in use
def extract(source_code: str, language: str) -> str:
    """Extract skeleton from source code."""
    extractor: SkeletonExtractor = SkeletonExtractor(language)
    return extractor.extract(source_code)
```

## Configuration Files

- **pyproject.toml**: Project metadata, dependencies, pytest, and ruff configuration
- **HANDLED_CASES.md**: Comprehensive list of supported cases
- **.gitignore**: Git ignore rules
- **UV_GUIDE.md**: uv package manager quick reference
- **DEVELOPMENT.md**: Detailed development guide

```
.
├── loppers.py              # Core library (typed)
├── examples.py             # Usage examples (typed)
├── test_loppers.py         # Unit tests (typed)
├── pyproject.toml          # uv/pip + pytest + ruff config
├── .gitignore              # Git ignore rules
├── README.md               # This file
├── UV_GUIDE.md             # uv quick reference
└── requirements.txt        # Legacy requirements
```

## tree-sitter API Changes (>= 0.25)

Key changes in the code for tree-sitter >= 0.25:
- Language wrapping: `Language(tree_sitter_language_pack.get_language(...))`
- Parser language assignment: `parser.language = lang` (property instead of `set_language()`)

## References

- [tree-sitter](https://tree-sitter.github.io/)
- [tree-sitter-language-pack](https://github.com/grantjenks/py-tree-sitter-language-pack)
- [uv - Python packaging](https://github.com/astral-sh/uv)
- [pytest](https://docs.pytest.org/)
- [ruff](https://github.com/astral-sh/ruff)