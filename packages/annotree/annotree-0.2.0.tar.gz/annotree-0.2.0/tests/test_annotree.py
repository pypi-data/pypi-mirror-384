# Unit tests for annotree core functionality

"""
Basic tests for annotree functionality.
"""

import tempfile
from pathlib import Path

import pytest

from annotree import get_first_line, get_folder_description, tree


def test_get_first_line():
    """Test extracting first line from a file."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".py") as f:
        f.write("# This is a test comment\n")
        f.write("def test():\n")
        f.write("    pass\n")
        temp_path = Path(f.name)

    try:
        result = get_first_line(temp_path)
        assert "This is a test comment" in result
    finally:
        temp_path.unlink()


def test_get_first_line_empty():
    """Test extracting first line from an empty file."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".py") as f:
        f.write("\n")
        temp_path = Path(f.name)

    try:
        result = get_first_line(temp_path)
        assert "No description available" in result
    finally:
        temp_path.unlink()


def test_get_folder_description_with_init():
    """Test getting folder description from __init__.py."""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir)
        init_file = temp_path / "__init__.py"
        init_file.write_text("# Test package\n")

        result = get_folder_description(temp_path)
        assert "Test package" in result


def test_get_folder_description_no_init():
    """Test getting folder description without __init__.py."""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir)

        result = get_folder_description(temp_path)
        assert "No description available" in result


def test_tree_generation():
    """Test basic tree generation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir)

        # Create some test files and directories
        (temp_path / "test.py").write_text("# Test file\n")
        (temp_path / "subdir").mkdir()
        (temp_path / "subdir" / "another.py").write_text("# Another test\n")

        output_file = temp_path / "tree_output.txt"

        dirs, files = tree(dir_path=temp_path, output_file=str(output_file))

        assert output_file.exists()
        assert dirs >= 1
        assert files >= 2

        content = output_file.read_text()
        assert "test.py" in content or "another.py" in content


def test_tree_with_depth_limit():
    """Test tree generation with depth limit."""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir)

        # Create nested directories
        (temp_path / "level1").mkdir()
        (temp_path / "level1" / "level2").mkdir()
        (temp_path / "level1" / "level2" / "level3").mkdir()
        (temp_path / "level1" / "level2" / "level3" / "test.txt").write_text("deep")

        output_file = temp_path / "tree_output.txt"

        dirs, files = tree(dir_path=temp_path, level=2, output_file=str(output_file))

        assert output_file.exists()
        content = output_file.read_text()

        # Should include level1 and level2, but not level3
        assert "level1" in content
        assert "level2" in content


def test_tree_directories_only():
    """Test tree generation with directories only."""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir)

        # Create files and directories
        (temp_path / "test.py").write_text("# Test file\n")
        (temp_path / "subdir").mkdir()

        output_file = temp_path / "tree_output.txt"

        dirs, files = tree(dir_path=temp_path, limit_to_directories=True, output_file=str(output_file))

        assert output_file.exists()
        assert dirs >= 1
        assert files == 0  # Should be 0 when limit_to_directories is True


def test_embed_tree_in_file():
    """Test embedding tree into a file between tags."""
    from annotree import embed_tree_in_file

    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir)

        # Create a simple file structure
        (temp_path / "test.py").write_text("# Test file\n")
        (temp_path / "subdir").mkdir()
        (temp_path / "subdir" / "another.py").write_text("# Another test\n")

        # Create a target file with tags
        target_file = temp_path / "README.md"
        target_file.write_text(
            "# My Project\n\n## File Structure\n\n<!-- ANNOTREE:START -->\n<!-- ANNOTREE:END -->\n\n## More content\n"
        )

        # Embed the tree
        changed = embed_tree_in_file(
            target_file=target_file,
            dir_path=temp_path,
            annotate=False,
        )

        assert changed is True
        content = target_file.read_text()

        # Should contain the tags and a code block
        assert "<!-- ANNOTREE:START -->" in content
        assert "<!-- ANNOTREE:END -->" in content
        assert "```text" in content
        assert "test.py" in content or "subdir" in content

        # Test no change when running again
        changed_again = embed_tree_in_file(
            target_file=target_file,
            dir_path=temp_path,
            annotate=False,
        )
        assert changed_again is False


def test_embed_tree_no_tags():
    """Test embedding when tags are missing."""
    from annotree import embed_tree_in_file

    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir)

        # Create a target file WITHOUT tags
        target_file = temp_path / "README.md"
        target_file.write_text("# My Project\n\nNo tags here.\n")

        # Try to embed - should return False
        changed = embed_tree_in_file(
            target_file=target_file,
            dir_path=temp_path,
        )

        assert changed is False
        # Original content should be unchanged
        assert target_file.read_text() == "# My Project\n\nNo tags here.\n"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
