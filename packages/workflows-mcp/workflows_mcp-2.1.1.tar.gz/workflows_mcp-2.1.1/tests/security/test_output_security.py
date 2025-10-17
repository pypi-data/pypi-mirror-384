"""
Security validation tests for file-based outputs.

Tests cover:
- Path traversal prevention
- Absolute path restrictions
- Symlink blocking
- File size limits
- Path validation in safe vs unsafe modes
"""

from pathlib import Path

import pytest

from workflows_mcp.engine.blocks_bash import (
    OutputNotFoundError,
    OutputSecurityError,
    validate_output_path,
)


class TestPathTraversalPrevention:
    """Test that path traversal attacks are prevented."""

    def test_reject_relative_path_traversal(self, tmp_path: Path) -> None:
        """Test that ../ in relative paths is rejected."""
        # Create file outside working directory
        parent = tmp_path.parent
        outside_file = parent / "outside.txt"
        outside_file.write_text("malicious")

        # Attempt traversal
        with pytest.raises(OutputSecurityError, match="Path escapes working directory"):
            validate_output_path("test", "../outside.txt", tmp_path, unsafe=False)

    def test_reject_nested_path_traversal(self, tmp_path: Path) -> None:
        """Test that multiple ../ levels are rejected."""
        # Create file two levels up
        grandparent = tmp_path.parent.parent
        outside_file = grandparent / "outside.txt"
        outside_file.write_text("malicious")

        # Attempt deep traversal
        with pytest.raises(OutputSecurityError, match="Path escapes working directory"):
            validate_output_path("test", "../../outside.txt", tmp_path, unsafe=False)

    def test_reject_hidden_traversal_in_path(self, tmp_path: Path) -> None:
        """Test that ../ hidden in middle of path is rejected."""
        # Create file outside working directory
        parent = tmp_path.parent
        outside_file = parent / "outside.txt"
        outside_file.write_text("malicious")

        # Attempt traversal with subdirectory prefix
        subdir = tmp_path / "subdir"
        subdir.mkdir()

        with pytest.raises(OutputSecurityError, match="Path escapes working directory"):
            validate_output_path("test", "subdir/../../outside.txt", tmp_path, unsafe=False)

    def test_accept_safe_relative_paths(self, tmp_path: Path) -> None:
        """Test that safe relative paths within working_dir are accepted."""
        # Create nested structure
        subdir = tmp_path / "sub1" / "sub2"
        subdir.mkdir(parents=True)
        safe_file = subdir / "file.txt"
        safe_file.write_text("safe")

        # Should succeed
        result = validate_output_path("test", "sub1/sub2/file.txt", tmp_path, unsafe=False)
        assert result == safe_file

    def test_reject_traversal_then_return(self, tmp_path: Path) -> None:
        """Test that going up then back down is still rejected if it escapes."""
        # Create file outside
        parent = tmp_path.parent
        sibling = parent / "sibling"
        sibling.mkdir(exist_ok=True)
        outside_file = sibling / "file.txt"
        outside_file.write_text("malicious")

        # Attempt to traverse up then into sibling directory
        with pytest.raises(OutputSecurityError, match="Path escapes working directory"):
            validate_output_path("test", "../sibling/file.txt", tmp_path, unsafe=False)


class TestAbsolutePathRestrictions:
    """Test absolute path handling in safe vs unsafe modes."""

    def test_reject_absolute_path_in_safe_mode(self, tmp_path: Path) -> None:
        """Test that absolute paths are rejected in safe mode."""
        test_file = tmp_path / "file.txt"
        test_file.write_text("content")

        with pytest.raises(OutputSecurityError, match="Absolute paths not allowed in safe mode"):
            validate_output_path("test", str(test_file), tmp_path, unsafe=False)

    def test_allow_absolute_path_in_unsafe_mode(self, tmp_path: Path) -> None:
        """Test that absolute paths are allowed in unsafe mode."""
        test_file = tmp_path / "file.txt"
        test_file.write_text("content")

        # Should succeed with unsafe=True
        result = validate_output_path("test", str(test_file), tmp_path, unsafe=True)
        assert result == test_file

    def test_reject_absolute_path_outside_working_dir_in_safe_mode(self, tmp_path: Path) -> None:
        """Test that absolute paths outside working_dir are rejected even with unsafe."""
        # Create file outside working directory
        outside = tmp_path.parent / "outside"
        outside.mkdir(exist_ok=True)
        outside_file = outside / "file.txt"
        outside_file.write_text("content")

        # Safe mode should reject absolute paths entirely
        with pytest.raises(OutputSecurityError, match="Absolute paths not allowed in safe mode"):
            validate_output_path("test", str(outside_file), tmp_path, unsafe=False)

    def test_allow_absolute_path_outside_in_unsafe_mode(self, tmp_path: Path) -> None:
        """Test that absolute paths outside working_dir work in unsafe mode."""
        # Create file outside working directory
        outside = tmp_path.parent / "outside"
        outside.mkdir(exist_ok=True)
        outside_file = outside / "file.txt"
        outside_file.write_text("content")

        # Unsafe mode should allow it
        result = validate_output_path("test", str(outside_file), tmp_path, unsafe=True)
        assert result == outside_file


class TestSymlinkBlocking:
    """Test that symlinks are blocked for security."""

    def test_reject_direct_symlink(self, tmp_path: Path) -> None:
        """Test that direct symlink references are rejected."""
        # Create target and symlink
        target = tmp_path / "target.txt"
        target.write_text("content")
        symlink = tmp_path / "link.txt"
        symlink.symlink_to(target)

        # Should reject symlink
        with pytest.raises(OutputSecurityError, match="Symlinks not allowed"):
            validate_output_path("test", "link.txt", tmp_path, unsafe=False)

    def test_reject_symlink_in_unsafe_mode(self, tmp_path: Path) -> None:
        """Test that symlinks are rejected even in unsafe mode."""
        # Create target and symlink
        target = tmp_path / "target.txt"
        target.write_text("content")
        symlink = tmp_path / "link.txt"
        symlink.symlink_to(target)

        # Symlinks should be rejected even with unsafe=True
        with pytest.raises(OutputSecurityError, match="Symlinks not allowed"):
            validate_output_path("test", "link.txt", tmp_path, unsafe=True)

    def test_reject_symlink_to_outside_directory(self, tmp_path: Path) -> None:
        """Test that symlink pointing outside working_dir is rejected."""
        # Create target outside working directory
        outside = tmp_path.parent / "outside.txt"
        outside.write_text("malicious")

        # Create symlink inside working directory
        symlink = tmp_path / "link.txt"
        symlink.symlink_to(outside)

        # Should reject symlink (symlink check comes before path traversal check)
        with pytest.raises(OutputSecurityError, match="Symlinks not allowed"):
            validate_output_path("test", "link.txt", tmp_path, unsafe=False)


class TestFileSizeLimits:
    """Test that file size limits are enforced."""

    def test_accept_file_at_size_limit(self, tmp_path: Path) -> None:
        """Test that file exactly at 10MB limit is accepted."""
        # Create file exactly 10MB
        file_10mb = tmp_path / "exact.txt"
        file_10mb.write_bytes(b"x" * (10 * 1024 * 1024))

        # Should succeed
        result = validate_output_path("test", "exact.txt", tmp_path, unsafe=False)
        assert result == file_10mb

    def test_reject_file_over_size_limit(self, tmp_path: Path) -> None:
        """Test that file over 10MB is rejected."""
        # Create file over 10MB
        file_11mb = tmp_path / "large.txt"
        file_11mb.write_bytes(b"x" * (11 * 1024 * 1024))

        # Should reject
        with pytest.raises(OutputSecurityError, match="File too large"):
            validate_output_path("test", "large.txt", tmp_path, unsafe=False)

    def test_reject_large_file_in_unsafe_mode(self, tmp_path: Path) -> None:
        """Test that size limit is enforced even in unsafe mode."""
        # Create file over 10MB
        file_11mb = tmp_path / "large.txt"
        file_11mb.write_bytes(b"x" * (11 * 1024 * 1024))

        # Size limit should apply even with unsafe=True
        with pytest.raises(OutputSecurityError, match="File too large"):
            validate_output_path("test", "large.txt", tmp_path, unsafe=True)

    def test_accept_small_file(self, tmp_path: Path) -> None:
        """Test that small files are accepted."""
        # Create small file
        small_file = tmp_path / "small.txt"
        small_file.write_text("small content")

        # Should succeed
        result = validate_output_path("test", "small.txt", tmp_path, unsafe=False)
        assert result == small_file

    def test_accept_empty_file(self, tmp_path: Path) -> None:
        """Test that empty files are accepted."""
        # Create empty file
        empty_file = tmp_path / "empty.txt"
        empty_file.write_text("")

        # Should succeed
        result = validate_output_path("test", "empty.txt", tmp_path, unsafe=False)
        assert result == empty_file


class TestDirectoryAndFileTypeValidation:
    """Test validation of file types."""

    def test_reject_directory(self, tmp_path: Path) -> None:
        """Test that directories are rejected."""
        # Create directory
        test_dir = tmp_path / "testdir"
        test_dir.mkdir()

        # Should reject directory
        with pytest.raises(OutputSecurityError, match="Path is not a file"):
            validate_output_path("test", "testdir", tmp_path, unsafe=False)

    def test_reject_directory_in_unsafe_mode(self, tmp_path: Path) -> None:
        """Test that directories are rejected even in unsafe mode."""
        # Create directory
        test_dir = tmp_path / "testdir"
        test_dir.mkdir()

        # Directories should be rejected even with unsafe=True
        with pytest.raises(OutputSecurityError, match="Path is not a file"):
            validate_output_path("test", "testdir", tmp_path, unsafe=True)

    def test_accept_regular_file(self, tmp_path: Path) -> None:
        """Test that regular files are accepted."""
        # Create regular file
        regular_file = tmp_path / "file.txt"
        regular_file.write_text("content")

        # Should succeed
        result = validate_output_path("test", "file.txt", tmp_path, unsafe=False)
        assert result == regular_file


class TestMissingFileHandling:
    """Test handling of missing files."""

    def test_reject_missing_file(self, tmp_path: Path) -> None:
        """Test that missing files raise OutputNotFoundError."""
        with pytest.raises(OutputNotFoundError, match="File not found"):
            validate_output_path("test", "nonexistent.txt", tmp_path, unsafe=False)

    def test_reject_missing_file_in_unsafe_mode(self, tmp_path: Path) -> None:
        """Test that missing files are rejected even in unsafe mode."""
        with pytest.raises(OutputNotFoundError, match="File not found"):
            validate_output_path("test", "nonexistent.txt", tmp_path, unsafe=True)

    def test_reject_missing_nested_file(self, tmp_path: Path) -> None:
        """Test that missing files in nested paths raise error."""
        # Create parent directory but not the file
        subdir = tmp_path / "subdir"
        subdir.mkdir()

        with pytest.raises(OutputNotFoundError, match="File not found"):
            validate_output_path("test", "subdir/nonexistent.txt", tmp_path, unsafe=False)


class TestEnvironmentVariableExpansion:
    """Test environment variable expansion in paths."""

    def test_expand_scratch_env_var(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that $SCRATCH is expanded correctly."""
        # Set environment variable
        monkeypatch.setenv("SCRATCH", ".scratch")

        # Create directory and file
        scratch_dir = tmp_path / ".scratch"
        scratch_dir.mkdir()
        test_file = scratch_dir / "output.txt"
        test_file.write_text("content")

        # Validate path with env var
        result = validate_output_path("test", "$SCRATCH/output.txt", tmp_path, unsafe=False)
        assert result == test_file

    def test_expand_custom_env_var(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that custom environment variables are expanded."""
        # Set environment variable
        monkeypatch.setenv("CUSTOM_DIR", "custom")

        # Create directory and file
        custom_dir = tmp_path / "custom"
        custom_dir.mkdir()
        test_file = custom_dir / "output.txt"
        test_file.write_text("content")

        # Validate path with env var
        result = validate_output_path("test", "$CUSTOM_DIR/output.txt", tmp_path, unsafe=False)
        assert result == test_file

    def test_env_var_expansion_with_path_traversal_blocked(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that env var expansion doesn't bypass path traversal checks."""
        # Set environment variable to traverse up
        monkeypatch.setenv("MALICIOUS", "..")

        # Create file outside
        parent = tmp_path.parent
        outside_file = parent / "outside.txt"
        outside_file.write_text("malicious")

        # Attempt traversal via env var
        with pytest.raises(OutputSecurityError, match="Path escapes working directory"):
            validate_output_path("test", "$MALICIOUS/outside.txt", tmp_path, unsafe=False)


class TestPathValidationErrorMessages:
    """Test that error messages are clear and helpful."""

    def test_absolute_path_error_message(self, tmp_path: Path) -> None:
        """Test that absolute path error includes helpful message."""
        test_file = tmp_path / "file.txt"
        test_file.write_text("content")

        with pytest.raises(OutputSecurityError) as exc_info:
            validate_output_path("my_output", str(test_file), tmp_path, unsafe=False)

        error_msg = str(exc_info.value)
        assert "my_output" in error_msg
        assert "Absolute paths not allowed" in error_msg
        assert "unsafe: true" in error_msg

    def test_path_traversal_error_message(self, tmp_path: Path) -> None:
        """Test that path traversal error includes helpful message."""
        parent = tmp_path.parent
        outside_file = parent / "outside.txt"
        outside_file.write_text("content")

        with pytest.raises(OutputSecurityError) as exc_info:
            validate_output_path("my_output", "../outside.txt", tmp_path, unsafe=False)

        error_msg = str(exc_info.value)
        assert "my_output" in error_msg
        assert "Path escapes working directory" in error_msg

    def test_file_not_found_error_message(self, tmp_path: Path) -> None:
        """Test that file not found error includes output name."""
        with pytest.raises(OutputNotFoundError) as exc_info:
            validate_output_path("my_output", "nonexistent.txt", tmp_path, unsafe=False)

        error_msg = str(exc_info.value)
        assert "my_output" in error_msg
        assert "File not found" in error_msg

    def test_size_limit_error_message(self, tmp_path: Path) -> None:
        """Test that size limit error includes helpful details."""
        large_file = tmp_path / "large.txt"
        large_file.write_bytes(b"x" * (11 * 1024 * 1024))

        with pytest.raises(OutputSecurityError) as exc_info:
            validate_output_path("my_output", "large.txt", tmp_path, unsafe=False)

        error_msg = str(exc_info.value)
        assert "my_output" in error_msg
        assert "File too large" in error_msg
        assert "bytes" in error_msg
