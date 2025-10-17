"""Tests for checkpoint serialization system.

Following TDD: Write tests FIRST, then implement.
"""

from datetime import datetime
from pathlib import Path


def test_serialize_basic_types():
    """Basic JSON types must serialize unchanged."""
    from workflows_mcp.engine.serialization import serialize_context

    context = {
        "string": "value",
        "integer": 42,
        "float": 3.14,
        "boolean": True,
        "list": [1, 2, 3],
        "dict": {"nested": "value"},
    }
    result = serialize_context(context)
    assert result == context


def test_serialize_path_to_string():
    """Path objects must convert to strings."""
    from workflows_mcp.engine.serialization import serialize_context

    context = {"path": Path("/tmp/test")}
    result = serialize_context(context)
    assert result["path"] == "/tmp/test"
    assert isinstance(result["path"], str)


def test_serialize_datetime_to_iso():
    """Datetime objects must convert to ISO format."""
    from workflows_mcp.engine.serialization import serialize_context

    now = datetime(2025, 1, 1, 12, 0, 0)
    context = {"timestamp": now}
    result = serialize_context(context)
    assert result["timestamp"] == "2025-01-01T12:00:00"


def test_skip_executor_reference():
    """Executor reference must be filtered out by caller before serialization."""
    from workflows_mcp.engine.serialization import serialize_context

    executor = object()
    full_context = {"__executor__": executor, "data": "keep", "other": 123}

    # Caller (executor) filters out __executor__ before serialization
    context_to_serialize = {k: v for k, v in full_context.items() if k != "__executor__"}
    result = serialize_context(context_to_serialize)

    assert "__executor__" not in result
    assert "data" in result
    assert result["data"] == "keep"
    assert result["other"] == 123


def test_deserialize_restores_executor():
    """Caller must add back executor reference after deserialization."""
    from workflows_mcp.engine.serialization import deserialize_context

    serialized = {"data": "value", "num": 42}
    executor = object()

    # Deserialize returns the context as-is
    result = deserialize_context(serialized, executor)

    # Caller (executor) adds __executor__ back
    result["__executor__"] = executor

    assert result["__executor__"] is executor
    assert result["data"] == "value"


def test_validate_checkpoint_size_accepts_small():
    """Small checkpoints must be accepted."""
    import time

    from workflows_mcp.engine.checkpoint import CheckpointState
    from workflows_mcp.engine.serialization import validate_checkpoint_size

    state = CheckpointState(
        checkpoint_id="test",
        workflow_name="test",
        created_at=time.time(),
        runtime_inputs={},
        context={"small": "data"},
        completed_blocks=[],
        current_wave_index=0,
        execution_waves=[],
        block_definitions={},
        workflow_stack=[],
    )

    assert validate_checkpoint_size(state, max_size_mb=10.0) is True


def test_validate_checkpoint_size_rejects_large():
    """Large checkpoints must be rejected."""
    import time

    from workflows_mcp.engine.checkpoint import CheckpointState
    from workflows_mcp.engine.serialization import validate_checkpoint_size

    # Create ~15MB of data
    large_data = "x" * (15 * 1024 * 1024)

    state = CheckpointState(
        checkpoint_id="test",
        workflow_name="test",
        created_at=time.time(),
        runtime_inputs={},
        context={"large": large_data},
        completed_blocks=[],
        current_wave_index=0,
        execution_waves=[],
        block_definitions={},
        workflow_stack=[],
    )

    assert validate_checkpoint_size(state, max_size_mb=10.0) is False
