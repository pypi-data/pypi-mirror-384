"""Serialization utilities for checkpoint data.

Handles conversion between Python objects and JSON-serializable formats,
with special handling for non-JSON types like Path and datetime.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from workflows_mcp.engine.checkpoint import CheckpointState


def _serialize_value(value: Any, _visited: set[int] | None = None) -> Any:
    """Recursively serialize a value to JSON-compatible format.

    Args:
        value: Value to serialize
        _visited: Internal set to track visited objects for circular reference detection

    Returns:
        JSON-serializable value

    Raises:
        ValueError: If circular reference is detected
    """
    # Initialize visited set for circular reference detection
    if _visited is None:
        _visited = set()

    if isinstance(value, Path):
        return str(value)
    elif isinstance(value, datetime):
        return value.isoformat()
    elif isinstance(value, dict):
        # Check for circular reference
        obj_id = id(value)
        if obj_id in _visited:
            raise ValueError("Circular reference detected")
        _visited.add(obj_id)
        try:
            dict_result = {k: _serialize_value(v, _visited) for k, v in value.items()}
            return dict_result
        finally:
            _visited.discard(obj_id)
    elif isinstance(value, (list, tuple)):
        # Check for circular reference
        obj_id = id(value)
        if obj_id in _visited:
            raise ValueError("Circular reference detected")
        _visited.add(obj_id)
        try:
            list_result = [_serialize_value(item, _visited) for item in value]
            return list_result
        finally:
            _visited.discard(obj_id)
    else:
        return value


def serialize_context(context: dict[str, Any]) -> dict[str, Any]:
    """Serialize workflow context to JSON-compatible format.

    Converts special types:
    - Path → str
    - datetime → ISO format string
    - Recursively handles nested dictionaries

    Note: The context passed should already exclude __internal__ namespace.

    Args:
        context: Raw workflow context with potentially non-JSON types
                (should contain only inputs, metadata, blocks namespaces)

    Returns:
        JSON-serializable dictionary
    """
    result = _serialize_value(context)
    # Type safety: context is a dict, so _serialize_value will return a dict
    assert isinstance(result, dict)
    return result


def deserialize_context(serialized: dict[str, Any], executor: Any) -> dict[str, Any]:
    """Deserialize context from checkpoint.

    Note: The serialized context contains only inputs, metadata, and blocks.
    The __internal__ namespace is NOT included in checkpoints and must be
    reconstructed by the caller.

    Args:
        serialized: JSON-deserialized context (inputs, metadata, blocks)
        executor: Executor instance (not used directly, caller adds to __internal__)

    Returns:
        Context dictionary with three namespaces (inputs, metadata, blocks)
        Note: Caller must add __internal__ namespace with executor and workflow_stack
    """
    # Just return the deserialized context as-is
    # Caller is responsible for adding __internal__ namespace
    return serialized.copy()


def validate_checkpoint_size(state: CheckpointState, max_size_mb: float) -> bool:
    """Validate checkpoint size is within acceptable limits.

    Args:
        state: Checkpoint state to validate
        max_size_mb: Maximum allowed size in megabytes

    Returns:
        True if size is acceptable, False otherwise
    """
    # Serialize state to JSON to measure size
    serialized = {
        "checkpoint_id": state.checkpoint_id,
        "workflow_name": state.workflow_name,
        "created_at": state.created_at,
        "runtime_inputs": state.runtime_inputs,
        "context": serialize_context(state.context),
        "completed_blocks": state.completed_blocks,
        "current_wave_index": state.current_wave_index,
        "execution_waves": state.execution_waves,
        "block_definitions": state.block_definitions,
        "workflow_stack": state.workflow_stack,
    }

    # Convert to JSON string and measure bytes
    json_str = json.dumps(serialized)
    size_bytes = len(json_str.encode("utf-8"))
    size_mb = size_bytes / (1024 * 1024)

    return size_mb <= max_size_mb
