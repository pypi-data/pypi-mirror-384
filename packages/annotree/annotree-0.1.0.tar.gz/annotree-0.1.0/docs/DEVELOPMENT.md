# Development Guide

## Setup with uv (Recommended)

[uv](https://github.com/astral-sh/uv) is a fast Python package installer and resolver.

### Install uv

```bash
# On macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or with pip
pip install uv
```

### Install annotree for development

```bash
# Clone the repository
git clone https://github.com/yourusername/annotree.git
cd annotree

# Create virtual environment and install with uv
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in editable mode with dev dependencies
uv pip install -e ".[dev]"
```

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=annotree --cov-report=html

# Run specific test file
pytest tests/test_annotree.py -v
```

### Code Formatting

```bash
# Format code with black
black annotree/ tests/ examples/

# Or use ruff (faster)
ruff format annotree/ tests/ examples/
```

### Linting

```bash
# Lint with ruff
ruff check annotree/ tests/ examples/

# Auto-fix issues
ruff check --fix annotree/ tests/ examples/
```

### Testing the CLI

```bash
# Test CLI
annotree --help
annotree . -o test_output.txt

# Test with .treeignore
echo "__pycache__/" > .treeignore
echo "dist/" >> .treeignore
annotree . -o filtered_tree.txt
```

### Running Examples

```bash
python examples/basic_example.py
python examples/advanced_example.py
python examples/directories_only.py
```

## Building and Publishing

### Build the package

```bash
# Install build tools
uv pip install build twine

# Clean previous builds
rm -rf build/ dist/ *.egg-info

# Build with uv
uv build

# Or use build
python -m build
```

### Publish to PyPI

```bash
# Upload to TestPyPI first
uv publish --repository testpypi

# Or with twine
python -m twine upload --repository testpypi dist/*

# Then upload to PyPI
uv publish

# Or with twine
python -m twine upload dist/*
```

## Project Structure

```
annotree/
├── annotree/           # Main package
│   ├── __init__.py
│   ├── annotree.py     # Core logic
│   └── __main__.py     # CLI entry point
├── tests/              # Test suite
├── examples/           # Usage examples
├── docs/               # Documentation
├── pyproject.toml      # Modern Python project config (uv-compatible)
├── README.md           # Main readme
└── LICENSE             # MIT license
```

## Using .treeignore

The `.treeignore` file works like `.gitignore` but is specifically for tree generation:

1. Create `.treeignore` in your project root
2. Add patterns to ignore (same syntax as `.gitignore`)
3. `annotree` will auto-detect and use it

**Priority:** `.treeignore` > `.gitignore` > no filtering

## Tips

### Fast Development Cycle

```bash
# Watch for changes and run tests
pytest-watch

# Or use uv's built-in tools
uv pip install pytest-watch
ptw
```

### Update Dependencies

```bash
# Update all dependencies
uv pip install --upgrade -e ".[dev]"

# Update specific package
uv pip install --upgrade gitignore-parser
```

### Version Bumping

1. Update version in:
   - `pyproject.toml`
   - `annotree/__init__.py`

2. Create git tag:
   ```bash
   git tag -a v0.2.0 -m "Release version 0.2.0"
   git push origin v0.2.0
   ```

## Common Issues

### uv not found
```bash
# Make sure uv is in PATH
export PATH="$HOME/.cargo/bin:$PATH"
```

### Import errors
```bash
# Reinstall in editable mode
uv pip install -e .
```

### Tests failing
```bash
# Make sure you're in the right environment
which python
python --version
```

## Resources

- [uv documentation](https://github.com/astral-sh/uv)
- [Python Packaging Guide](https://packaging.python.org/)
- [pytest documentation](https://docs.pytest.org/)
- [Ruff documentation](https://docs.astral.sh/ruff/)
