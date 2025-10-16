# Quick Start Guide

## Installation

### Using uv (recommended)

```bash
uv pip install annotree
```

### Using pip

```bash
pip install annot2. **Build the package**:
   ```bash
   uv pip install build twine
   uv build
   # or
   python -m build
   ```

5. **Upload to TestPyPI first**:
   ```bash
   uv publish --repository testpypi
   # or
   python -m twine upload --repository testpypi dist/*
   ```

6. **Upload to PyPI**:
   ```bash
   uv publish
   # or
   python -m twine upload dist/*
   ```r Development

```bash
cd /home/yue/projects/annotree
uv pip install -e .
```

### From PyPI (once published)

```bash
uv pip install annotree
# or
pip install annotree
```

## Quick Test

### 1. Test the CLI

```bash
# Show help
annotree --help

# Generate tree for current directory (auto-detects .treeignore or .gitignore)
annotree

# Generate with custom output
annotree . -o my_tree.txt

# Use specific ignore file
annotree . -i .treeignore -o filtered_tree.txt

# Or use .gitignore
annotree . -i .gitignore -o filtered_tree.txt

# Limit depth to 2 levels
annotree . -l 2 -o shallow_tree.txt

# Only show directories
annotree . -d -o dirs_only.txt
```

### 2. Test with Python API

```python
from pathlib import Path
from annotree import tree

# Basic usage
tree(Path.cwd(), output_file="test_tree.txt")

# With options
tree(
    Path.cwd(),
    ignore_file=".gitignore",
    level=3,
    output_file="custom_tree.txt"
)
```

### 3. Run Examples

```bash
# Basic example
python examples/basic_example.py

# Advanced example with custom settings
python examples/advanced_example.py

# Directories only
python examples/directories_only.py

# Analyze specific directory
python examples/custom_project.py /path/to/project
```

## Package Structure

```
annotree/
├── annotree/              # Main package
│   ├── __init__.py        # Package initialization
│   ├── annotree.py        # Core tree generation logic
│   └── __main__.py        # CLI entry point
├── examples/              # Usage examples
│   ├── basic_example.py
│   ├── advanced_example.py
│   ├── directories_only.py
│   ├── custom_project.py
│   └── README.md
├── setup.py               # Package setup (pip)
├── pyproject.toml         # Modern package configuration
├── requirements.txt       # Dependencies
├── requirements-dev.txt   # Development dependencies
├── README.md              # Full documentation
├── PUBLISHING.md          # PyPI publishing guide
├── LICENSE                # MIT License
├── MANIFEST.in            # Files to include in distribution
└── .gitignore             # Git ignore rules
```

## Next Steps

### Before Publishing to PyPI

1. **Update author information** in:
   - `setup.py` (line 12-13)
   - `pyproject.toml` (line 17)
   - `annotree/__init__.py` (line 11)

2. **Update repository URL** in:
   - `setup.py` (line 16, 34-36)
   - `pyproject.toml` (line 38-40)
   - `README.md` (badge links)

3. **Test thoroughly**:
   ```bash
   # Run all examples
   python examples/basic_example.py
   python examples/advanced_example.py
   python examples/directories_only.py
   
   # Test CLI
   annotree --help
   annotree . -o test.txt
   ```

4. **Build the package**:
   ```bash
   pip install build twine
   python -m build
   ```

5. **Upload to TestPyPI first**:
   ```bash
   python -m twine upload --repository testpypi dist/*
   ```

6. **Upload to PyPI**:
   ```bash
   python -m twine upload dist/*
   ```

See [PUBLISHING.md](PUBLISHING.md) for detailed instructions.

## Features to Highlight

- ✨ **Automatic annotations** from file comments
- 📁 **Folder descriptions** from `__init__.py`
- 🚫 **Gitignore support** for clean output
- 🎨 **Beautiful formatting** with tree symbols
- ⚙️ **Highly customizable** options
- 🐍 **Both CLI and API** available

## Common Use Cases

### 1. Document Project Structure
```bash
# Auto-detects .treeignore or .gitignore
annotree . -o docs/structure.txt
```

### 2. Use .treeignore for tree-specific filtering
```bash
# Create .treeignore with patterns
echo "__pycache__/" > .treeignore
echo "dist/" >> .treeignore
annotree . -o clean_tree.txt
```

### 3. Quick Overview (directories only)
```bash
annotree . -d -o overview.txt
```

### 3. Shallow Structure (2 levels)
```bash
annotree . -l 2 -o shallow.txt
```

### 4. Large Projects (limit output)
```bash
annotree . --limit 500 -o limited.txt
```

## Tips

1. **Add descriptions to your files**: Put meaningful comments in the first line
   ```python
   # User authentication service
   class AuthService:
       pass
   ```

2. **Use `__init__.py` for folders**: Add descriptions to folders
   ```python
   # Utility functions and helpers
   ```

3. **Create a `.treeignore`**: Like `.gitignore` but specifically for tree generation

4. **Adjust annotation alignment**: Use `-a` to set where annotations start
   ```bash
   annotree . -a 60  # Annotations start at column 60
   ```

## Troubleshooting

### ImportError: No module named 'gitignore_parser'
```bash
pip install gitignore-parser
```

### Permission denied errors
The tool skips directories it can't read. This is normal for protected system directories.

### Annotations not aligned
Use the `-a` flag to adjust the column position:
```bash
annotree . -a 50  # Try different values
```

## Getting Help

- Check the [README.md](README.md) for full documentation
- Look at [examples/](examples/) for code samples
- Run `annotree --help` for CLI options
- See [PUBLISHING.md](PUBLISHING.md) for publishing info
