"""Tests for JSON state management executors."""

import json
from pathlib import Path

import pytest

from workflows_mcp.engine.executors_state import (
    MergeJSONStateExecutor,
    MergeJSONStateInput,
    ReadJSONStateExecutor,
    ReadJSONStateInput,
    WriteJSONStateExecutor,
    WriteJSONStateInput,
)

# ============================================================================
# ReadJSONState Tests
# ============================================================================


@pytest.mark.asyncio
async def test_read_json_state_success(tmp_path: Path) -> None:
    """Test reading existing JSON state file."""
    # Create test file
    state_file = tmp_path / "state.json"
    state_data = {"key": "value", "count": 42}
    state_file.write_text(json.dumps(state_data, indent=2))

    # Execute
    executor = ReadJSONStateExecutor()
    inputs = ReadJSONStateInput(path=str(state_file))
    result = await executor.execute(inputs, {})

    # Verify
    assert result.is_success
    assert result.value.data == state_data
    assert result.value.found is True
    assert result.value.path == str(state_file)


@pytest.mark.asyncio
async def test_read_json_state_missing_optional(tmp_path: Path) -> None:
    """Test reading missing file returns empty dict when not required."""
    state_file = tmp_path / "missing.json"

    # Execute
    executor = ReadJSONStateExecutor()
    inputs = ReadJSONStateInput(path=str(state_file), required=False)
    result = await executor.execute(inputs, {})

    # Verify
    assert result.is_success
    assert result.value.data == {}
    assert result.value.found is False


@pytest.mark.asyncio
async def test_read_json_state_missing_required(tmp_path: Path) -> None:
    """Test reading missing required file fails."""
    state_file = tmp_path / "missing.json"

    # Execute
    executor = ReadJSONStateExecutor()
    inputs = ReadJSONStateInput(path=str(state_file), required=True)
    result = await executor.execute(inputs, {})

    # Verify
    assert not result.is_success
    assert "not found" in result.error.lower()


@pytest.mark.asyncio
async def test_read_json_state_invalid_json(tmp_path: Path) -> None:
    """Test reading invalid JSON fails."""
    state_file = tmp_path / "invalid.json"
    state_file.write_text("not valid json {")

    # Execute
    executor = ReadJSONStateExecutor()
    inputs = ReadJSONStateInput(path=str(state_file))
    result = await executor.execute(inputs, {})

    # Verify
    assert not result.is_success
    assert "invalid json" in result.error.lower()


@pytest.mark.asyncio
async def test_read_json_state_not_dict(tmp_path: Path) -> None:
    """Test reading JSON array fails (must be object)."""
    state_file = tmp_path / "array.json"
    state_file.write_text("[1, 2, 3]")

    # Execute
    executor = ReadJSONStateExecutor()
    inputs = ReadJSONStateInput(path=str(state_file))
    result = await executor.execute(inputs, {})

    # Verify
    assert not result.is_success
    assert "object" in result.error.lower()


# ============================================================================
# WriteJSONState Tests
# ============================================================================


@pytest.mark.asyncio
async def test_write_json_state_success(tmp_path: Path) -> None:
    """Test writing JSON state file."""
    state_file = tmp_path / "output.json"
    state_data = {"key": "value", "nested": {"count": 42}}

    # Execute
    executor = WriteJSONStateExecutor()
    inputs = WriteJSONStateInput(path=str(state_file), data=state_data)
    result = await executor.execute(inputs, {})

    # Verify
    assert result.is_success
    assert result.value.success is True
    assert result.value.path == str(state_file)
    assert result.value.size_bytes > 0

    # Verify file contents
    written_data = json.loads(state_file.read_text())
    assert written_data == state_data


@pytest.mark.asyncio
async def test_write_json_state_creates_parents(tmp_path: Path) -> None:
    """Test writing creates parent directories."""
    state_file = tmp_path / "nested" / "dirs" / "state.json"
    state_data = {"test": "data"}

    # Execute
    executor = WriteJSONStateExecutor()
    inputs = WriteJSONStateInput(path=str(state_file), data=state_data, create_parents=True)
    result = await executor.execute(inputs, {})

    # Verify
    assert result.is_success
    assert state_file.exists()


@pytest.mark.asyncio
async def test_write_json_state_no_parents_fails(tmp_path: Path) -> None:
    """Test writing without parent creation fails."""
    state_file = tmp_path / "missing" / "state.json"
    state_data = {"test": "data"}

    # Execute
    executor = WriteJSONStateExecutor()
    inputs = WriteJSONStateInput(path=str(state_file), data=state_data, create_parents=False)
    result = await executor.execute(inputs, {})

    # Verify
    assert not result.is_success
    assert "parent directory missing" in result.error.lower()


@pytest.mark.asyncio
async def test_write_json_state_overwrites(tmp_path: Path) -> None:
    """Test writing overwrites existing file."""
    state_file = tmp_path / "state.json"
    state_file.write_text(json.dumps({"old": "data"}))

    new_data = {"new": "data"}

    # Execute
    executor = WriteJSONStateExecutor()
    inputs = WriteJSONStateInput(path=str(state_file), data=new_data)
    result = await executor.execute(inputs, {})

    # Verify
    assert result.is_success
    written_data = json.loads(state_file.read_text())
    assert written_data == new_data


# ============================================================================
# MergeJSONState Tests
# ============================================================================


@pytest.mark.asyncio
async def test_merge_json_state_creates_new(tmp_path: Path) -> None:
    """Test merging creates new file if missing."""
    state_file = tmp_path / "state.json"
    updates = {"key": "value", "count": 42}

    # Execute
    executor = MergeJSONStateExecutor()
    inputs = MergeJSONStateInput(path=str(state_file), updates=updates, create_if_missing=True)
    result = await executor.execute(inputs, {})

    # Verify
    assert result.is_success
    assert result.value.created is True
    assert result.value.merged_data == updates


@pytest.mark.asyncio
async def test_merge_json_state_merges_existing(tmp_path: Path) -> None:
    """Test merging updates existing file."""
    state_file = tmp_path / "state.json"
    existing_data = {"key1": "value1", "nested": {"a": 1, "b": 2}}
    state_file.write_text(json.dumps(existing_data))

    updates = {"key2": "value2", "nested": {"b": 20, "c": 3}}

    # Execute
    executor = MergeJSONStateExecutor()
    inputs = MergeJSONStateInput(path=str(state_file), updates=updates)
    result = await executor.execute(inputs, {})

    # Verify
    assert result.is_success
    assert result.value.created is False

    # Check deep merge
    expected = {
        "key1": "value1",
        "key2": "value2",
        "nested": {"a": 1, "b": 20, "c": 3},
    }
    assert result.value.merged_data == expected


@pytest.mark.asyncio
async def test_merge_json_state_replaces_lists(tmp_path: Path) -> None:
    """Test merging replaces lists (doesn't append)."""
    state_file = tmp_path / "state.json"
    existing_data = {"items": [1, 2, 3]}
    state_file.write_text(json.dumps(existing_data))

    updates = {"items": [4, 5]}

    # Execute
    executor = MergeJSONStateExecutor()
    inputs = MergeJSONStateInput(path=str(state_file), updates=updates)
    result = await executor.execute(inputs, {})

    # Verify
    assert result.is_success
    assert result.value.merged_data == {"items": [4, 5]}


@pytest.mark.asyncio
async def test_merge_json_state_missing_no_create_fails(tmp_path: Path) -> None:
    """Test merging fails if file missing and create_if_missing=False."""
    state_file = tmp_path / "state.json"
    updates = {"key": "value"}

    # Execute
    executor = MergeJSONStateExecutor()
    inputs = MergeJSONStateInput(path=str(state_file), updates=updates, create_if_missing=False)
    result = await executor.execute(inputs, {})

    # Verify
    assert not result.is_success
    assert "not found" in result.error.lower()


@pytest.mark.asyncio
async def test_merge_json_state_deep_nested(tmp_path: Path) -> None:
    """Test deep nested merge."""
    state_file = tmp_path / "state.json"
    existing_data = {"level1": {"level2": {"level3": {"a": 1, "b": 2}}, "other": "value"}}
    state_file.write_text(json.dumps(existing_data))

    updates = {"level1": {"level2": {"level3": {"b": 20, "c": 3}}}}

    # Execute
    executor = MergeJSONStateExecutor()
    inputs = MergeJSONStateInput(path=str(state_file), updates=updates)
    result = await executor.execute(inputs, {})

    # Verify
    assert result.is_success
    expected = {
        "level1": {
            "level2": {"level3": {"a": 1, "b": 20, "c": 3}},
            "other": "value",
        }
    }
    assert result.value.merged_data == expected


@pytest.mark.asyncio
async def test_merge_json_state_creates_parents(tmp_path: Path) -> None:
    """Test merging creates parent directories."""
    state_file = tmp_path / "nested" / "dirs" / "state.json"
    updates = {"test": "data"}

    # Execute
    executor = MergeJSONStateExecutor()
    inputs = MergeJSONStateInput(path=str(state_file), updates=updates, create_parents=True)
    result = await executor.execute(inputs, {})

    # Verify
    assert result.is_success
    assert state_file.exists()


# ============================================================================
# Edge Cases and Security
# ============================================================================


@pytest.mark.asyncio
async def test_state_executors_handle_unicode(tmp_path: Path) -> None:
    """Test state executors handle Unicode correctly."""
    state_file = tmp_path / "unicode.json"
    unicode_data = {"emoji": "🚀", "chinese": "你好", "arabic": "مرحبا"}

    # Write
    executor_write = WriteJSONStateExecutor()
    inputs_write = WriteJSONStateInput(path=str(state_file), data=unicode_data)
    result_write = await executor_write.execute(inputs_write, {})
    assert result_write.is_success

    # Read
    executor_read = ReadJSONStateExecutor()
    inputs_read = ReadJSONStateInput(path=str(state_file))
    result_read = await executor_read.execute(inputs_read, {})
    assert result_read.is_success
    assert result_read.value.data == unicode_data


@pytest.mark.asyncio
async def test_state_executors_timing_metadata(tmp_path: Path) -> None:
    """Test state executors include timing metadata."""
    state_file = tmp_path / "state.json"
    state_data = {"test": "data"}

    # Execute
    executor = WriteJSONStateExecutor()
    inputs = WriteJSONStateInput(path=str(state_file), data=state_data)
    result = await executor.execute(inputs, {})

    # Verify metadata
    assert result.is_success
    assert "execution_time_ms" in result.metadata
    assert result.metadata["execution_time_ms"] >= 0
