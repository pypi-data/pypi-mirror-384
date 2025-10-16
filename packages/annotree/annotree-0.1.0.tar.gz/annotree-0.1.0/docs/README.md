# annotree

[![PyPI version](https://badge.fury.io/py/annotree.svg)](https://badge.fury.io/py/annotree)
[![Python Support](https://img.shields.io/pypi/pyversions/annotree.svg)](https://pypi.org/project/annotree/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Generate beautiful, annotated file tree structures with descriptions extracted from file comments. Perfect for documentation, README files, and project overviews!

## Features

✨ **Automatic Annotations** - Extracts descriptions from the first line of each file  
📁 **Directory Descriptions** - Reads folder descriptions from `__init__.py` files  
🚫 **Gitignore Support** - Respects `.gitignore` rules to filter unwanted files  
🎨 **Clean Output** - Beautiful tree structure with aligned annotations  
⚙️ **Customizable** - Control depth, output format, and annotation positioning  
🐍 **Python API & CLI** - Use as a library or command-line tool  

## Installation

```bash
pip install annotree
```

## Quick Start

### Command Line Usage

Generate a tree for the current directory:

```bash
annotree
```

Specify a directory and output file:

```bash
annotree /path/to/project -o project_structure.txt
```

Use a `.gitignore` file to filter:

```bash
annotree . -i .gitignore -o tree.txt
```

Advanced options:

```bash
annotree . \
  --output docs/structure.txt \
  --ignore .gitignore \
  --level 3 \
  --annotation-start 50 \
  --limit 500
```

### Python API Usage

```python
from pathlib import Path
from annotree import tree

# Basic usage
tree(Path.cwd(), output_file="tree.txt")

# With gitignore support
tree(
    dir_path=Path("./my-project"),
    ignore_file=".gitignore",
    output_file="project_tree.txt"
)

# Advanced options
tree(
    dir_path=Path.cwd(),
    ignore_file=".gitignore",
    level=3,  # Max depth
    limit_to_directories=False,
    length_limit=1000,
    output_file="annotated_tree.txt",
    annotation_start=50  # Column for annotations
)
```

## How It Works

`annotree` reads the first line of each file and uses it as a description. It recognizes common comment styles:

**Python files:**
```python
# This is a utility module for data processing
def process_data():
    pass
```

**JavaScript/TypeScript:**
```javascript
// Authentication service for user login
export class AuthService {
    // ...
}
```

**HTML:**
```html
<!-- Homepage template with hero section -->
<html>
    <!-- ... -->
</html>
```

For directories, it reads the first line from `__init__.py` (if present).

## Example Output

```
my-project
├─ src                                  # Main application source code
│   ├─ __init__.py                      # Package initialization
│   ├─ main.py                          # Application entry point
│   ├─ utils                            # Utility functions and helpers
│   │   ├─ __init__.py                  # Utils package initialization
│   │   ├─ helpers.py                   # Common helper functions
│   │   └─ validators.py                # Input validation utilities
│   │   
│   └─ models                           # Data models and schemas
│       ├─ __init__.py                  # Models package initialization
│       ├─ user.py                      # User model definition
│       └─ product.py                   # Product model definition
│       
├─ tests                                # Test suite
│   ├─ test_main.py                     # Tests for main module
│   └─ test_utils.py                    # Tests for utilities
│   
├─ README.md                            # Project documentation
└─ requirements.txt                     # Python dependencies

4 directories, 11 files
```

## CLI Options

```
positional arguments:
  directory             Directory to analyze (default: current directory)

optional arguments:
  -h, --help            Show this help message and exit
  -o, --output OUTPUT   Output file path (default: tree_structure.txt)
  -i, --ignore IGNORE   Path to .gitignore file for filtering
  -l, --level LEVEL     Maximum depth level (default: -1, no limit)
  -d, --directories-only
                        Only show directories
  --limit LIMIT         Maximum number of lines (default: 1000)
  -a, --annotation-start ANNOTATION_START
                        Column position for annotations (default: 42)
```

## API Reference

### `tree(dir_path, ignore_file=None, level=-1, ...)`

Generate and save a visual tree structure of a directory.

**Parameters:**
- `dir_path` (Path): Path to the directory to analyze
- `ignore_file` (str, optional): Path to .gitignore file
- `level` (int): Maximum depth (-1 for unlimited)
- `limit_to_directories` (bool): Only show directories
- `length_limit` (int): Maximum lines in output
- `output_file` (str): Output file path
- `annotation_start` (int): Column for annotation alignment

**Returns:**
- `tuple`: (directories_count, files_count)

### `get_first_line(file_path)`

Extract and clean the first line from a file.

### `get_folder_description(folder_path)`

Get description from a folder's `__init__.py` file.

## Publishing to PyPI

To publish this package to PyPI (after customizing with your details):

1. **Install build tools:**
   ```bash
   pip install build twine
   ```

2. **Update package metadata:**
   - Edit `setup.py` and `pyproject.toml`
   - Add your name, email, and GitHub repository
   - Update the version number

3. **Build the package:**
   ```bash
   python -m build
   ```

4. **Upload to TestPyPI (recommended first):**
   ```bash
   python -m twine upload --repository testpypi dist/*
   ```

5. **Upload to PyPI:**
   ```bash
   python -m twine upload dist/*
   ```

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/annotree.git
cd annotree

# Install in editable mode
pip install -e .

# Install development dependencies
pip install pytest black flake8
```

### Run Tests

```bash
pytest tests/
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Credits

Tree generation logic inspired by [this Stack Overflow answer](https://stackoverflow.com/questions/9727673/list-directory-tree-structure-in-python).

## Changelog

### 0.1.0 (2025-10-16)
- Initial release
- Basic tree generation with annotations
- Gitignore support
- CLI and Python API
- Customizable output formatting
