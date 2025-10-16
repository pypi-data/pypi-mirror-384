# Welcom to Annotree 🌳

[![PyPI version](https://badge.fury.io/py/annotree.svg)](https://badge.fury.io/py/annotree)
[![Python Support](https://img.shields.io/pypi/pyversions/annotree.svg)](https://pypi.org/project/annotree/)

**Annotree generates annotated file trees that read like your code is documenting itself — while preserving Python-style annotations.**
It automatically extracts descriptions from file comments, docstrings, and `__init__.py` headers, keeping your project’s natural Python annotation style intact.
Perfect for **README files, documentation, and quick project overviews**.

---

## ⚡ Key Features

- 🧠 **Automatic Annotations** – Pulls descriptions from first lines, comments, or `__init__.py` docstrings
- 📁 **Directory Descriptions** – Folders inherit descriptions from `__init__.py`
- 🚫 **Smart Ignore Support** – Honors `.treeignore` or `.gitignore` automatically
- 🎨 **Clean, Aligned Output** – Beautiful tree structure with readable annotations
- ⚙️ **Customizable** – Control depth, output format, and annotation alignment
- 🐍 **Python API & CLI** – Use as a library or from the command line

---

## 💻 Installation

### Using uv (recommended)
```bash
uv pip install annotree
````

### Using pip

```bash
pip install annotree
```

### For Development

```bash
git clone https://github.com/yourusername/annotree.git
cd annotree
uv pip install -e .
```

---

## 🚀 Usage

### Command Line

```bash
# Generate tree in current directory
annotree

# Specify output file
annotree -o structure.txt

# Use specific ignore file
annotree -i .gitignore

# Limit depth
annotree -l 3

# Show directories only
annotree -d

# Customize annotation alignment
annotree -a 60 -o tree.txt
```

### Python API

```python
from pathlib import Path
from annotree import tree

# Basic usage
tree(Path.cwd(), output_file="tree.txt")

# Custom options
tree(
    Path.cwd(),
    ignore_file=".treeignore",
    level=3,
    output_file="tree.txt",
    annotation_start=50
)

# Directories only
tree(Path.cwd(), limit_to_directories=True, output_file="dirs_only.txt")
```

---

## 📄 .treeignore

Create a `.treeignore` file in your project root to filter files specifically for Annotree (independent of `.gitignore`):

```
__pycache__/
*.pyc
.pytest_cache/
.venv/
node_modules/
dist/
build/
```

* If `.treeignore` exists, Annotree uses it automatically.
* Otherwise, `.gitignore` is respected if present.

---

## 🎨 Example Output

```
my-project
├─ src                                  # Main application source code
│   ├─ __init__.py                      # Package initialization
│   ├─ main.py                          # Application entry point
│   └─ utils                            # Utility functions and helpers
│       ├─ __init__.py                  # Utils package initialization
│       └─ helpers.py                   # Common helper functions
├─ tests                                # Test suite
│   └─ test_main.py                     # Tests for main module
└─ README.md                            # Project documentation

2 directories, 6 files
```

---

## 🤝 Contributing

Contributions welcome! Feel free to submit a Pull Request or open an Issue.

---

## 📜 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🔗 Links

* **PyPI**: [https://pypi.org/project/annotree/](https://pypi.org/project/annotree/)
* **GitHub**: [https://github.com/yourusername/annotree](https://github.com/yourusername/annotree)
* **Issues**: [https://github.com/yourusername/annotree/issues](https://github.com/yourusername/annotree/issues)
