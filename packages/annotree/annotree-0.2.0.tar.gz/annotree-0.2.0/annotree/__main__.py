# Command-line interface for annotree

"""
Command-line interface for annotree.
"""

import argparse
from pathlib import Path

from .annotree import tree


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Generate an annotated file tree structure with descriptions from file comments."
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory to analyze (default: current directory)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="tree_structure.txt",
        help="Output file path (default: tree_structure.txt)",
    )
    parser.add_argument(
        "-i",
        "--ignore",
        help="Path to ignore file (.gitignore, .treeignore, etc.). If not specified, auto-detects .treeignore or .gitignore",
    )
    parser.add_argument(
        "-l",
        "--level",
        type=int,
        default=-1,
        help="Maximum depth level (default: -1, no limit)",
    )
    parser.add_argument(
        "-d",
        "--directories-only",
        action="store_true",
        help="Only show directories",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=1000,
        help="Maximum number of lines (default: 1000)",
    )
    parser.add_argument(
        "-a",
        "--annotation-start",
        type=int,
        default=42,
        help="Column position for annotations (default: 42)",
    )
    parser.add_argument(
        "--no-annotate",
        action="store_true",
        help="Disable annotations (useful for compact pre-commit updates)",
    )
    parser.add_argument(
        "--embed",
        help="Path to a file to embed the tree into between tags (e.g., README.md).",
    )
    parser.add_argument(
        "--start-tag",
        default="<!-- ANNOTREE:START -->",
        help="Start tag for embedding (default: '<!-- ANNOTREE:START -->')",
    )
    parser.add_argument(
        "--end-tag",
        default="<!-- ANNOTREE:END -->",
        help="End tag for embedding (default: '<!-- ANNOTREE:END -->')",
    )

    args = parser.parse_args()

    dir_path = Path(args.directory)
    if not dir_path.exists():
        print(f"Error: Directory '{dir_path}' does not exist.")
        return 1

    if not dir_path.is_dir():
        print(f"Error: '{dir_path}' is not a directory.")
        return 1

    print(f"Generating tree structure for: {dir_path.absolute()}")

    # If embedding requested, skip writing to output file and embed directly
    if args.embed:
        from .annotree import embed_tree_in_file

        target = Path(args.embed)
        print(f"Embedding tree into: {target}")
        changed = embed_tree_in_file(
            target_file=target,
            dir_path=dir_path,
            start_tag=args.start_tag,
            end_tag=args.end_tag,
            ignore_file=args.ignore,
            level=args.level,
            limit_to_directories=args.directories_only,
            length_limit=args.limit,
            annotation_start=args.annotation_start,
            annotate=not args.no_annotate,
        )
        if changed:
            print("✓ Embedded tree into file (file updated).")
        else:
            print("No changes made when embedding (tags missing or no diff).")
    else:
        # Normal file output mode
        print(f"Output file: {args.output}")

        dirs, files = tree(
            dir_path=dir_path,
            ignore_file=args.ignore,
            level=args.level,
            limit_to_directories=args.directories_only,
            length_limit=args.limit,
            output_file=args.output,
            annotation_start=args.annotation_start,
            annotate=not args.no_annotate,
        )

        print(f"✓ Tree structure saved to '{args.output}'")
        print(f"  {dirs} directories, {files} files")

    return 0


if __name__ == "__main__":
    exit(main())
