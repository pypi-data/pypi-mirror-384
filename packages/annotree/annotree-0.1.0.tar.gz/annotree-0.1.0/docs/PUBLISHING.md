# Publishing to PyPI - Step by Step Guide

This guide will walk you through publishing your `annotree` package to PyPI.

## Prerequisites

1. **Create PyPI Account**
   - Go to https://pypi.org/account/register/
   - Verify your email address
   - Set up two-factor authentication (recommended)

2. **Create TestPyPI Account** (for testing)
   - Go to https://test.pypi.org/account/register/

3. **Generate API Tokens**
   - PyPI: https://pypi.org/manage/account/token/
   - TestPyPI: https://test.pypi.org/manage/account/token/
   - Save these tokens securely!

## Step 1: Customize Package Metadata

Before publishing, update these files with your information:

### setup.py
```python
author="Your Name",
author_email="your.email@example.com",
url="https://github.com/yourusername/annotree",
```

### pyproject.toml
```toml
authors = [
    {name = "Your Name", email = "your.email@example.com"}
]
```

### annotree/__init__.py
```python
__author__ = "Your Name"
```

## Step 2: Install Build Tools

### Using uv (recommended)

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install build tools
uv pip install build twine
```

### Using pip

```bash
pip install --upgrade build twine
```

## Step 3: Build the Package

### Using uv (recommended)

```bash
# Clean previous builds
rm -rf build/ dist/ *.egg-info

# Build with uv (faster)
uv build
```

### Using build

```bash
# Clean previous builds
rm -rf build/ dist/ *.egg-info

# Build the package
python -m build
```

This creates two files in the `dist/` directory:
- `annotree-0.1.0.tar.gz` (source distribution)
- `annotree-0.1.0-py3-none-any.whl` (wheel distribution)

## Step 4: Test Upload to TestPyPI

### Using uv (recommended)

```bash
uv publish --repository testpypi
```

### Using twine

**Using API token:**

```bash
python -m twine upload --repository testpypi dist/*
```

When prompted:
- Username: `__token__`
- Password: Your TestPyPI API token (including the `pypi-` prefix)

**Or configure ~/.pypirc:**

```ini
[distutils]
index-servers =
    pypi
    testpypi

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-your-test-token-here

[pypi]
repository = https://upload.pypi.org/legacy/
username = __token__
password = pypi-your-production-token-here
```

Then simply:
```bash
python -m twine upload --repository testpypi dist/*
```

## Step 5: Test Installation from TestPyPI

```bash
pip install --index-url https://test.pypi.org/simple/ --no-deps annotree
```

Test it:
```bash
annotree --help
```

## Step 6: Upload to Production PyPI

Once you've verified everything works:

### Using uv (recommended)

```bash
uv publish
```

### Using twine

```bash
python -m twine upload dist/*
```

Or with explicit repository:
```bash
python -m twine upload --repository pypi dist/*
```

## Step 7: Verify Installation

```bash
pip install annotree
annotree --help
```

## Version Updates

When releasing a new version:

1. **Update version numbers** in:
   - `setup.py`
   - `pyproject.toml`
   - `annotree/__init__.py`

2. **Update CHANGELOG** in README.md

3. **Build and upload**:
   ```bash
   rm -rf build/ dist/ *.egg-info
   python -m build
   python -m twine upload dist/*
   ```

## Automated Publishing with GitHub Actions

Create `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.x'
      - name: Install dependencies
        run: |
          pip install build twine
      - name: Build package
        run: python -m build
      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: twine upload dist/*
```

Add your PyPI token as a GitHub secret named `PYPI_API_TOKEN`.

## Checklist Before Publishing

- [ ] All tests pass
- [ ] README.md is complete and accurate
- [ ] LICENSE file is included
- [ ] Version number is updated
- [ ] Author information is correct
- [ ] GitHub repository URL is correct
- [ ] requirements.txt lists all dependencies
- [ ] Code is clean and well-documented
- [ ] Examples work correctly
- [ ] Tested on TestPyPI first

## Common Issues

### "File already exists"
You cannot overwrite existing versions on PyPI. Increment your version number.

### "Invalid or non-existent authentication"
Make sure you're using `__token__` as the username and your full token (including `pypi-` prefix) as the password.

### "Package has invalid metadata"
Run `python -m build` and check for errors. Ensure all required fields in setup.py are filled.

### Import errors after installation
Make sure your package structure is correct and all `__init__.py` files are present.

## Resources

- [Python Packaging Guide](https://packaging.python.org/)
- [PyPI Help](https://pypi.org/help/)
- [Twine Documentation](https://twine.readthedocs.io/)
- [setuptools Documentation](https://setuptools.pypa.io/)
