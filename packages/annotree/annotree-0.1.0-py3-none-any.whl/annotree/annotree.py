# Core tree generation logic with .treeignore and .gitignore support

from itertools import islice
from pathlib import Path

from gitignore_parser import parse_gitignore

# Tree symbols
SPACE = "    "
BRANCH = "│   "
TEE = "├─ "
LAST = "└─ "
EMPTY = "└─ ..."


def get_first_line(file_path):
    """
    Extract the first line from a file.

    Args:
        file_path (Path): Path to the file.

    Returns:
        str: The first line of the file or an error message.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            first_line = (
                file.readline().strip().replace("#", "").replace('"', "").replace("<!-- ", "").replace(" -->", "")
            )
            if not first_line:
                return " No description available."
            return first_line if first_line.startswith(" ") else f" {first_line}"
    except Exception as e:
        return f" Error reading file: {e}"


def get_folder_description(folder_path):
    """
    Extract description from __init__.py if it exists in the folder.

    Args:
        folder_path (Path): Path to the folder.

    Returns:
        str: The description from __init__.py or "No description available."
    """
    init_file_path = folder_path / "__init__.py"
    if init_file_path.exists():
        return get_first_line(init_file_path)
    return " No description available."


def tree(
    dir_path: Path,
    ignore_file: str = None,
    level: int = -1,
    limit_to_directories: bool = False,
    length_limit: int = 1000,
    output_file: str = "tree_structure.txt",
    annotation_start: int = 42,
):
    """
    Generate and save a visual tree structure of a directory, respecting ignore rules.

    Args:
        dir_path (Path): Path to the directory to analyze.
        ignore_file (str): Path to ignore file (.gitignore, .treeignore, etc.).
                          If None, searches for .treeignore then .gitignore in dir_path.
                          If still not found, no files are ignored.
        level (int): Depth level for tree traversal. Default is -1 (no limit).
        limit_to_directories (bool): If True, only include directories. Default is False.
        length_limit (int): Maximum number of lines to write to the output file. Default is 1000.
        output_file (str): Path to the output file where the tree structure will be saved. Default is "tree_structure.txt".
        annotation_start (int): Column position for description alignment. Default is 42.

    Returns:
        tuple: A tuple containing (directories_count, files_count)
    """
    dir_path = Path(dir_path)

    # Auto-detect ignore file if not specified
    if ignore_file is None:
        # Try .treeignore first, then .gitignore
        treeignore = dir_path / ".treeignore"
        gitignore_path = dir_path / ".gitignore"

        if treeignore.exists():
            ignore_file = str(treeignore)
        elif gitignore_path.exists():
            ignore_file = str(gitignore_path)

    # Create an ignore function
    if ignore_file and Path(ignore_file).exists():
        gitignore = parse_gitignore(ignore_file, base_dir=dir_path)
    else:
        gitignore = lambda x: False  # Don't ignore anything

    files = 0
    directories = 0
    output_lines = []

    def inner(directory: Path, prefix: str = "", level: int = -1):
        nonlocal files, directories
        if level == 0:
            return
        # Get directories and files separately
        try:
            contents = [p for p in directory.iterdir() if not gitignore(str(p))]
        except PermissionError:
            return

        directories_list = [p for p in contents if p.is_dir()]
        files_list = [p for p in contents if p.is_file()]

        # Sort directories and files separately
        directories_list.sort(key=lambda p: p.name)
        files_list.sort(key=lambda p: p.name)

        # Combine sorted lists
        sorted_contents = directories_list + files_list

        pointers = [TEE] * (len(sorted_contents) - 1) + [LAST]
        for pointer, path in zip(pointers, sorted_contents):
            if path.is_dir():
                description = get_folder_description(path)
                line = prefix + pointer + path.name
                line = line.ljust(annotation_start) + f"#{description}"
                output_lines.append(line)
                directories += 1
                extension = BRANCH if pointer == TEE else SPACE
                yield from inner(path, prefix=prefix + extension, level=level - 1)

                # Check if folder is empty or all children are ignored
                try:
                    if not any(not gitignore(str(item)) for item in path.iterdir()):
                        output_lines.append(prefix + extension + EMPTY)
                except PermissionError:
                    pass
                output_lines.append(prefix + extension)

            elif not limit_to_directories:
                # Skip annotation for __init__.py since it's already used for folder description
                if path.name == "__init__.py":
                    line = prefix + pointer + path.name
                else:
                    description = get_first_line(path)
                    line = prefix + pointer + path.name
                    line = line.ljust(annotation_start) + f"#{description}"
                output_lines.append(line)
                files += 1

    output_lines.append(dir_path.name)
    iterator = inner(dir_path, level=level)
    for line in islice(iterator, length_limit):
        output_lines.append(line)
    if next(iterator, None):
        output_lines.append(f"... length_limit, {length_limit}, reached, counted:")
    output_lines.append(f"\n{directories} directories" + (f", {files} files" if files else ""))

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))

    return directories, files
