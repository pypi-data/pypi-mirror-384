"""
Core tests for custom file-based outputs functionality.

Tests cover:
- Basic output reading and type conversion
- Variable resolution in .outputs. namespace
- Context storage and retrieval
- Edge cases (empty files, missing outputs, etc.)
"""

import json
from pathlib import Path

import pytest

from workflows_mcp.engine.blocks_bash import Shell


class TestCustomOutputsBasics:
    """Test basic custom output reading and type conversion."""

    @pytest.mark.asyncio
    async def test_string_output_basic(self, tmp_path: Path) -> None:
        """Test reading string output from file."""
        # Create scratch directory and output file
        scratch_dir = tmp_path / ".scratch"
        scratch_dir.mkdir()
        output_file = scratch_dir / "output.txt"
        output_file.write_text("hello world")

        # Create block with string output
        outputs = {
            "message": {
                "type": "string",
                "path": ".scratch/output.txt",
                "required": True,
            }
        }

        block = Shell(
            id="test_block",
            inputs={"command": "echo 'test'", "working_dir": str(tmp_path)},
            outputs=outputs,
        )

        result = await block.execute({})

        assert result.is_success
        assert result.value.message == "hello world"

    @pytest.mark.asyncio
    async def test_int_output_conversion(self, tmp_path: Path) -> None:
        """Test int type conversion."""
        scratch_dir = tmp_path / ".scratch"
        scratch_dir.mkdir()
        output_file = scratch_dir / "count.txt"
        output_file.write_text("42")

        outputs = {"count": {"type": "int", "path": ".scratch/count.txt", "required": True}}

        block = Shell(
            id="test_block",
            inputs={"command": "echo 'test'", "working_dir": str(tmp_path)},
            outputs=outputs,
        )

        result = await block.execute({})

        assert result.is_success
        assert result.value.count == 42
        assert isinstance(result.value.count, int)

    @pytest.mark.asyncio
    async def test_float_output_conversion(self, tmp_path: Path) -> None:
        """Test float type conversion."""
        scratch_dir = tmp_path / ".scratch"
        scratch_dir.mkdir()
        output_file = scratch_dir / "coverage.txt"
        output_file.write_text("87.5")

        outputs = {
            "coverage": {
                "type": "float",
                "path": ".scratch/coverage.txt",
                "required": True,
            }
        }

        block = Shell(
            id="test_block",
            inputs={"command": "echo 'test'", "working_dir": str(tmp_path)},
            outputs=outputs,
        )

        result = await block.execute({})

        assert result.is_success
        assert result.value.coverage == 87.5
        assert isinstance(result.value.coverage, float)

    @pytest.mark.asyncio
    async def test_bool_output_conversion(self, tmp_path: Path) -> None:
        """Test bool type conversion."""
        scratch_dir = tmp_path / ".scratch"
        scratch_dir.mkdir()

        # Test true value
        output_file = scratch_dir / "success.txt"
        output_file.write_text("true")

        outputs = {
            "success": {
                "type": "bool",
                "path": ".scratch/success.txt",
                "required": True,
            }
        }

        block = Shell(
            id="test_block",
            inputs={"command": "echo 'test'", "working_dir": str(tmp_path)},
            outputs=outputs,
        )

        result = await block.execute({})

        assert result.is_success
        assert result.value.success is True
        assert isinstance(result.value.success, bool)

    @pytest.mark.asyncio
    async def test_json_output_parsing(self, tmp_path: Path) -> None:
        """Test JSON output parsing."""
        scratch_dir = tmp_path / ".scratch"
        scratch_dir.mkdir()

        # Create JSON output
        test_data = {
            "results": [
                {"name": "test1", "passed": True},
                {"name": "test2", "passed": False},
            ],
            "summary": {"total": 2, "passed": 1, "failed": 1},
        }
        output_file = scratch_dir / "results.json"
        output_file.write_text(json.dumps(test_data))

        outputs = {
            "test_results": {
                "type": "json",
                "path": ".scratch/results.json",
                "required": True,
            }
        }

        block = Shell(
            id="test_block",
            inputs={"command": "echo 'test'", "working_dir": str(tmp_path)},
            outputs=outputs,
        )

        result = await block.execute({})

        assert result.is_success
        assert result.value.test_results == test_data

    @pytest.mark.asyncio
    async def test_multiple_outputs(self, tmp_path: Path) -> None:
        """Test block with multiple custom outputs."""
        scratch_dir = tmp_path / ".scratch"
        scratch_dir.mkdir()

        # Create multiple output files
        (scratch_dir / "count.txt").write_text("10")
        (scratch_dir / "message.txt").write_text("success")
        (scratch_dir / "percentage.txt").write_text("95.5")

        outputs = {
            "count": {"type": "int", "path": ".scratch/count.txt"},
            "message": {"type": "string", "path": ".scratch/message.txt"},
            "percentage": {"type": "float", "path": ".scratch/percentage.txt"},
        }

        block = Shell(
            id="test_block",
            inputs={"command": "echo 'test'", "working_dir": str(tmp_path)},
            outputs=outputs,
        )

        result = await block.execute({})

        assert result.is_success
        assert result.value.count == 10
        assert result.value.message == "success"
        assert result.value.percentage == 95.5


class TestCustomOutputsEdgeCases:
    """Test edge cases for custom outputs."""

    @pytest.mark.asyncio
    async def test_empty_string_output(self, tmp_path: Path) -> None:
        """Test empty file as string output."""
        scratch_dir = tmp_path / ".scratch"
        scratch_dir.mkdir()
        output_file = scratch_dir / "empty.txt"
        output_file.write_text("")

        outputs = {"result": {"type": "string", "path": ".scratch/empty.txt"}}

        block = Shell(
            id="test_block",
            inputs={"command": "echo 'test'", "working_dir": str(tmp_path)},
            outputs=outputs,
        )

        result = await block.execute({})

        assert result.is_success
        assert result.value.result == ""

    @pytest.mark.asyncio
    async def test_whitespace_handling(self, tmp_path: Path) -> None:
        """Test that whitespace is trimmed correctly."""
        scratch_dir = tmp_path / ".scratch"
        scratch_dir.mkdir()
        output_file = scratch_dir / "output.txt"
        output_file.write_text("  \n  hello  \n  ")

        outputs = {"message": {"type": "string", "path": ".scratch/output.txt"}}

        block = Shell(
            id="test_block",
            inputs={"command": "echo 'test'", "working_dir": str(tmp_path)},
            outputs=outputs,
        )

        result = await block.execute({})

        assert result.is_success
        assert result.value.message == "hello"

    @pytest.mark.asyncio
    async def test_invalid_int_conversion_fails(self, tmp_path: Path) -> None:
        """Test that invalid int conversion fails gracefully."""
        scratch_dir = tmp_path / ".scratch"
        scratch_dir.mkdir()
        output_file = scratch_dir / "count.txt"
        output_file.write_text("not a number")

        outputs = {"count": {"type": "int", "path": ".scratch/count.txt", "required": True}}

        block = Shell(
            id="test_block",
            inputs={"command": "echo 'test'", "working_dir": str(tmp_path)},
            outputs=outputs,
        )

        result = await block.execute({})

        assert not result.is_success
        assert "Cannot parse as int" in result.error

    @pytest.mark.asyncio
    async def test_invalid_json_fails(self, tmp_path: Path) -> None:
        """Test that invalid JSON fails gracefully."""
        scratch_dir = tmp_path / ".scratch"
        scratch_dir.mkdir()
        output_file = scratch_dir / "data.json"
        output_file.write_text("{invalid json}")

        outputs = {"data": {"type": "json", "path": ".scratch/data.json", "required": True}}

        block = Shell(
            id="test_block",
            inputs={"command": "echo 'test'", "working_dir": str(tmp_path)},
            outputs=outputs,
        )

        result = await block.execute({})

        assert not result.is_success
        assert "Cannot parse as JSON" in result.error

    @pytest.mark.asyncio
    async def test_optional_output_with_invalid_type(self, tmp_path: Path) -> None:
        """Test that optional output with invalid type doesn't fail workflow."""
        scratch_dir = tmp_path / ".scratch"
        scratch_dir.mkdir()
        output_file = scratch_dir / "count.txt"
        output_file.write_text("not a number")

        outputs = {
            "count": {
                "type": "int",
                "path": ".scratch/count.txt",
                "required": False,
            }
        }

        block = Shell(
            id="test_block",
            inputs={"command": "echo 'test'", "working_dir": str(tmp_path)},
            outputs=outputs,
        )

        result = await block.execute({})

        # Should succeed because output is optional
        assert result.is_success
        assert not hasattr(result.value, "count")
