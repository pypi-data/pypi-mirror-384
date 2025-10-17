"""Tests for block utilities."""

import json
import tempfile
import time
from pathlib import Path

from workflows_mcp.engine.block_utils import (
    ExecutionTimer,
    FileOperations,
    JSONOperations,
    PathResolver,
)


def test_path_resolver_absolute():
    """Test path resolution with absolute path."""
    result = PathResolver.resolve_and_validate("/tmp/test.txt", allow_traversal=True)

    assert result.is_success
    # On macOS, /tmp is a symlink to /private/tmp, so we need to resolve() for comparison
    assert result.value == Path("/tmp/test.txt").resolve()


def test_path_resolver_relative():
    """Test path resolution with relative path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        working_dir = Path(tmpdir)
        result = PathResolver.resolve_and_validate("data/file.txt", working_dir=working_dir)

        assert result.is_success
        # Compare resolved paths to handle symlinks
        assert result.value == (working_dir / "data/file.txt").resolve()


def test_path_resolver_traversal_protection():
    """Test path traversal protection."""
    with tempfile.TemporaryDirectory() as tmpdir:
        working_dir = Path(tmpdir)
        result = PathResolver.resolve_and_validate(
            "../../../etc/passwd", working_dir=working_dir, allow_traversal=False
        )

        assert not result.is_success
        assert "escapes working directory" in result.error


def test_path_resolver_allow_traversal():
    """Test path resolution with traversal allowed."""
    with tempfile.TemporaryDirectory() as tmpdir:
        working_dir = Path(tmpdir)
        result = PathResolver.resolve_and_validate(
            "../outside.txt", working_dir=working_dir, allow_traversal=True
        )

        # Should succeed when allow_traversal=True
        assert result.is_success


def test_path_resolver_symlink_protection():
    """Test symlink protection."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create a regular file
        regular_file = tmpdir_path / "regular.txt"
        regular_file.write_text("content")

        # Create a symlink
        symlink_file = tmpdir_path / "symlink.txt"
        symlink_file.symlink_to(regular_file)

        # Should reject symlinks
        result = PathResolver.resolve_and_validate(str(symlink_file), working_dir=tmpdir_path)

        assert not result.is_success
        assert "Symlinks not allowed" in result.error


def test_file_operations_read_write():
    """Test file read/write operations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "test.txt"
        content = "Hello, World!"

        # Write
        write_result = FileOperations.write_text(file_path, content)
        assert write_result.is_success
        assert write_result.value > 0

        # Read
        read_result = FileOperations.read_text(file_path)
        assert read_result.is_success
        assert read_result.value == content


def test_file_operations_encoding():
    """Test file operations with different encodings."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "utf16.txt"
        content = "Hello with unicode: 你好"

        # Write with UTF-16
        write_result = FileOperations.write_text(file_path, content, encoding="utf-16")
        assert write_result.is_success

        # Read with UTF-16
        read_result = FileOperations.read_text(file_path, encoding="utf-16")
        assert read_result.is_success
        assert read_result.value == content


def test_file_operations_create_parents():
    """Test automatic parent directory creation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "nested" / "dirs" / "file.txt"
        content = "test"

        # Should create parent directories
        write_result = FileOperations.write_text(file_path, content, create_parents=True)
        assert write_result.is_success

        # Verify file exists
        assert file_path.exists()
        assert file_path.read_text() == content


def test_file_operations_file_not_found():
    """Test reading non-existent file."""
    result = FileOperations.read_text(Path("/nonexistent/file.txt"))

    assert not result.is_success
    assert "not found" in result.error.lower()


def test_file_operations_permissions():
    """Test file permission setting."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "perms.txt"
        content = "test"

        # Write with specific permissions
        write_result = FileOperations.write_text(file_path, content, mode=0o644)
        assert write_result.is_success

        # Check permissions (on Unix systems)
        import platform

        if platform.system() != "Windows":
            stat_info = file_path.stat()
            # Get last 3 octal digits (user, group, other permissions)
            perms = oct(stat_info.st_mode)[-3:]
            assert perms == "644"


def test_file_operations_size_limit():
    """Test file size limit enforcement."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "large.txt"
        content = "x" * 1000  # 1000 bytes

        # Write file
        FileOperations.write_text(file_path, content)

        # Read with size limit (should fail)
        result = FileOperations.read_text(file_path, max_size_bytes=100)
        assert not result.is_success
        assert "too large" in result.error.lower()

        # Read with sufficient size limit (should succeed)
        result = FileOperations.read_text(file_path, max_size_bytes=2000)
        assert result.is_success


def test_json_operations():
    """Test JSON read/write operations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "test.json"
        data = {"key": "value", "number": 42, "nested": {"inner": "data"}}

        # Write
        write_result = JSONOperations.write_json(file_path, data)
        assert write_result.is_success

        # Read
        read_result = JSONOperations.read_json(file_path)
        assert read_result.is_success
        assert read_result.value == data


def test_json_operations_required():
    """Test JSON read with required flag."""
    # File doesn't exist, required=False (should return empty dict)
    result = JSONOperations.read_json(Path("/nonexistent.json"), required=False)
    assert result.is_success
    assert result.value == {}

    # File doesn't exist, required=True (should fail)
    result = JSONOperations.read_json(Path("/nonexistent.json"), required=True)
    assert not result.is_success
    assert "not found" in result.error.lower()


def test_json_operations_invalid_json():
    """Test reading invalid JSON."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "invalid.json"
        file_path.write_text("not valid json {")

        result = JSONOperations.read_json(file_path)
        assert not result.is_success
        assert "invalid json" in result.error.lower()


def test_json_operations_non_object():
    """Test reading JSON that's not an object."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "array.json"
        file_path.write_text(json.dumps([1, 2, 3]))

        result = JSONOperations.read_json(file_path)
        assert not result.is_success
        assert "must contain an object" in result.error


def test_json_deep_merge():
    """Test JSON deep merge."""
    base = {"a": 1, "b": {"c": 2, "d": 3}, "e": [1, 2]}
    updates = {"b": {"d": 4, "e": 5}, "f": 6}

    result = JSONOperations.deep_merge(base, updates)

    assert result == {"a": 1, "b": {"c": 2, "d": 4, "e": 5}, "e": [1, 2], "f": 6}


def test_json_deep_merge_nested():
    """Test deep merge with multiple nesting levels."""
    base = {"level1": {"level2": {"level3": {"value": "old"}}}}
    updates = {"level1": {"level2": {"level3": {"value": "new", "extra": "data"}}}}

    result = JSONOperations.deep_merge(base, updates)

    assert result == {"level1": {"level2": {"level3": {"value": "new", "extra": "data"}}}}


def test_json_deep_merge_list_replacement():
    """Test that lists are replaced, not merged."""
    base = {"items": [1, 2, 3]}
    updates = {"items": [4, 5]}

    result = JSONOperations.deep_merge(base, updates)

    # Lists should be replaced, not merged
    assert result == {"items": [4, 5]}


def test_json_deep_merge_empty():
    """Test deep merge with empty dicts."""
    base = {"a": 1}
    updates = {}

    result = JSONOperations.deep_merge(base, updates)
    assert result == {"a": 1}

    base = {}
    updates = {"b": 2}

    result = JSONOperations.deep_merge(base, updates)
    assert result == {"b": 2}


def test_execution_timer():
    """Test execution timer."""
    timer = ExecutionTimer()
    time.sleep(0.01)  # 10ms

    elapsed = timer.elapsed_ms()
    assert elapsed >= 10  # At least 10ms
    assert elapsed < 100  # Less than 100ms (generous upper bound)


def test_execution_timer_multiple_calls():
    """Test that timer continues to count."""
    timer = ExecutionTimer()
    time.sleep(0.01)  # 10ms

    first_elapsed = timer.elapsed_ms()
    time.sleep(0.01)  # Another 10ms

    second_elapsed = timer.elapsed_ms()

    # Second reading should be larger
    assert second_elapsed > first_elapsed
    assert second_elapsed >= 20  # At least 20ms total


def test_path_resolver_default_working_dir():
    """Test path resolver with default working directory."""
    # Should use cwd when working_dir not specified
    result = PathResolver.resolve_and_validate("file.txt")

    assert result.is_success
    assert result.value == Path.cwd() / "file.txt"


def test_file_operations_is_directory():
    """Test that reading a directory fails."""
    with tempfile.TemporaryDirectory() as tmpdir:
        dir_path = Path(tmpdir)

        result = FileOperations.read_text(dir_path)
        assert not result.is_success
        assert "not a file" in result.error.lower()


def test_json_operations_formatting():
    """Test that JSON output is formatted."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "formatted.json"
        data = {"z": 1, "a": 2, "m": 3}

        JSONOperations.write_json(file_path, data)

        content = file_path.read_text()

        # Should be indented
        assert "  " in content  # Has indentation
        # Should be sorted
        lines = content.strip().split("\n")
        # First key should be "a" (sorted)
        assert '"a"' in lines[1]


def test_json_operations_unicode():
    """Test JSON operations with unicode characters."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "unicode.json"
        data = {"message": "Hello 世界", "emoji": "🚀"}

        # Write
        write_result = JSONOperations.write_json(file_path, data)
        assert write_result.is_success

        # Read
        read_result = JSONOperations.read_json(file_path)
        assert read_result.is_success
        assert read_result.value == data
