# annotree package - Generate annotated file trees with descriptions from file comments

"""
annotree - Generate annotated file tree structures with descriptions from file comments.

This package provides tools to create visual directory tree structures that include
descriptions extracted from the first line of each file, making it easy to document
project structures.
"""

from .annotree import tree, get_first_line, get_folder_description

__version__ = "0.1.0"
__author__ = "Your Name"
__all__ = ["tree", "get_first_line", "get_folder_description"]
