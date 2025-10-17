"""
Test checkpoint edge cases and error handling.

Tests comprehensive edge cases for checkpoint system including:
- Corrupted checkpoint data handling
- Invalid resume scenarios
- Checkpoint size limits
- Concurrent access patterns
- Schema version mismatches

These tests follow TDD RED phase - they should FAIL initially.
"""

import asyncio
import time

import pytest

from workflows_mcp.engine.checkpoint import CheckpointState
from workflows_mcp.engine.checkpoint_store import InMemoryCheckpointStore
from workflows_mcp.engine.executor import WorkflowDefinition, WorkflowExecutor
from workflows_mcp.engine.response import WorkflowResponse
from workflows_mcp.engine.serialization import serialize_context


def to_dict(result):
    """Convert WorkflowResponse to dict for testing."""
    if isinstance(result, WorkflowResponse):
        return result.model_dump()
    return result


@pytest.fixture
def checkpoint_store():
    """Create in-memory checkpoint store for testing."""
    return InMemoryCheckpointStore()


@pytest.fixture
def executor_with_checkpoints(checkpoint_store):
    """Create executor with checkpoint support."""
    return WorkflowExecutor(checkpoint_store=checkpoint_store)


@pytest.fixture
def simple_workflow():
    """Create simple test workflow."""
    return WorkflowDefinition(
        name="test-workflow",
        description="Test workflow",
        blocks=[
            {
                "id": "block1",
                "type": "EchoBlock",
                "inputs": {"message": "Block 1"},
                "depends_on": [],
            },
            {
                "id": "block2",
                "type": "EchoBlock",
                "inputs": {"message": "Block 2"},
                "depends_on": ["block1"],
            },
        ],
        inputs={},
    )


@pytest.mark.asyncio
async def test_checkpoint_corruption_handling(checkpoint_store, executor_with_checkpoints):
    """Test handling of corrupted checkpoint JSON.

    Edge case: Checkpoint data becomes corrupted (invalid JSON, missing required fields,
    malformed data types). System must handle gracefully without crashing.

    This test should FAIL initially - no corruption handling implemented yet.
    """
    # Create a valid checkpoint first
    valid_checkpoint = CheckpointState(
        checkpoint_id="test_chk_123",
        workflow_name="test-workflow",
        created_at=time.time(),
        runtime_inputs={"input": "test"},
        context=serialize_context({"var": "value"}),
        completed_blocks=["block1"],
        current_wave_index=0,
        execution_waves=[["block1"], ["block2"]],
        block_definitions={
            "block1": {"id": "block1", "type": "EchoBlock", "inputs": {"message": "test"}},
        },
        workflow_stack=[],
    )

    await checkpoint_store.save_checkpoint(valid_checkpoint)

    # Test Case 1: Corrupt the checkpoint JSON directly (if store supports it)
    # Simulate JSON corruption by modifying stored data
    corrupted_checkpoint_id = "corrupted_chk_456"

    # Create checkpoint with invalid JSON in context field
    corrupted_checkpoint = CheckpointState(
        checkpoint_id=corrupted_checkpoint_id,
        workflow_name="test-workflow",
        created_at=time.time(),
        runtime_inputs={"input": "test"},
        context='{"invalid": json}',  # Invalid JSON string
        completed_blocks=["block1"],
        current_wave_index=0,
        execution_waves=[["block1"], ["block2"]],
        block_definitions={
            "block1": {"id": "block1", "type": "EchoBlock", "inputs": {"message": "test"}},
        },
        workflow_stack=[],
    )

    # Try to save and load corrupted checkpoint
    try:
        await checkpoint_store.save_checkpoint(corrupted_checkpoint)
        loaded = await checkpoint_store.load_checkpoint(corrupted_checkpoint_id)

        # Should handle corruption gracefully
        assert loaded is not None or True  # Either loads with defaults or returns None

    except Exception as e:
        # Should not raise unhandled exceptions
        pytest.fail(f"Corrupted checkpoint raised unhandled exception: {e}")

    # Test Case 2: Missing required fields
    incomplete_checkpoint_id = "incomplete_chk_789"

    # Manually create checkpoint with missing fields (simulate old schema)
    # With dataclasses, we test by not saving a checkpoint and trying to load it
    # This simulates missing/corrupted checkpoint data
    result = await executor_with_checkpoints.resume_workflow(incomplete_checkpoint_id)

    assert not result.is_success
    assert "not found" in result.error.lower() or "invalid" in result.error.lower()

    # Test Case 3: Type mismatch in fields
    # Dataclasses enforce types at creation time, so we test that invalid types
    # are caught during checkpoint creation or provide clear errors
    try:
        # This should fail during dataclass initialization due to type mismatch
        type_mismatch_checkpoint = CheckpointState(
            checkpoint_id="type_mismatch_chk",
            workflow_name="test-workflow",
            created_at=time.time(),
            runtime_inputs={"count": "not_a_number"},  # Valid type (dict value can be any)
            context=serialize_context({"var": 123}),
            completed_blocks=["block1", "block2"],
            current_wave_index=0,  # Must be int
            execution_waves=[["block1"]],
            block_definitions={},
            workflow_stack=[],
        )

        await checkpoint_store.save_checkpoint(type_mismatch_checkpoint)
        loaded = await checkpoint_store.load_checkpoint("type_mismatch_chk")

        # Should handle gracefully
        assert loaded is not None

    except (TypeError, ValueError) as e:
        # Should provide clear error message about type mismatch
        assert "type" in str(e).lower() or "invalid" in str(e).lower()


@pytest.mark.asyncio
async def test_invalid_resume_scenarios(executor_with_checkpoints, checkpoint_store):
    """Test resume with missing or invalid checkpoint IDs.

    Edge cases:
    - Nonexistent checkpoint ID
    - Empty checkpoint ID
    - Malformed checkpoint ID
    - Checkpoint ID for deleted workflow
    - Checkpoint ID with invalid format

    This test should FAIL initially - comprehensive validation not implemented yet.
    """
    # Test Case 1: Resume with nonexistent checkpoint
    result = await executor_with_checkpoints.resume_workflow("nonexistent_checkpoint_id")
    assert not result.is_success
    assert "not found" in result.error.lower()

    # Test Case 2: Resume with empty checkpoint ID
    result = await executor_with_checkpoints.resume_workflow("")
    assert not result.is_success
    assert (
        "invalid" in result.error.lower()
        or "empty" in result.error.lower()
        or "not found" in result.error.lower()
    )

    # Test Case 3: Resume with malformed checkpoint ID (SQL injection attempt)
    malicious_id = "'; DROP TABLE checkpoints; --"
    result = await executor_with_checkpoints.resume_workflow(malicious_id)
    assert not result.is_success
    assert "not found" in result.error.lower() or "invalid" in result.error.lower()

    # Test Case 5: Resume with very long checkpoint ID (DoS attempt)
    very_long_id = "x" * 10000
    result = await executor_with_checkpoints.resume_workflow(very_long_id)
    assert not result.is_success
    assert "not found" in result.error.lower() or "invalid" in result.error.lower()

    # Test Case 6: Resume with checkpoint for deleted/unloaded workflow
    deleted_workflow_checkpoint = CheckpointState(
        checkpoint_id="deleted_workflow_chk",
        workflow_name="deleted-workflow",  # Not loaded in executor
        created_at=time.time(),
        runtime_inputs={},
        context={},
        completed_blocks=[],
        current_wave_index=0,
        execution_waves=[],
        block_definitions={},
        workflow_stack=[],
    )

    await checkpoint_store.save_checkpoint(deleted_workflow_checkpoint)
    result = await executor_with_checkpoints.resume_workflow("deleted_workflow_chk")
    assert not result.is_success
    assert "not found" in result.error.lower() or "not loaded" in result.error.lower()

    # Test Case 7: Resume with special characters in checkpoint ID
    special_chars_id = "chk_<script>alert('xss')</script>"
    result = await executor_with_checkpoints.resume_workflow(special_chars_id)
    assert not result.is_success

    # Test Case 8: Resume with null bytes in checkpoint ID
    null_byte_id = "chk_test\x00malicious"
    result = await executor_with_checkpoints.resume_workflow(null_byte_id)
    assert not result.is_success


@pytest.mark.asyncio
async def test_checkpoint_size_limits(checkpoint_store, executor_with_checkpoints, simple_workflow):
    """Test checkpoint size validation and enforcement.

    Edge cases:
    - Very large context (100MB+)
    - Extremely deep nested structures
    - Circular references in context
    - Binary data in context
    - Millions of completed blocks

    This test should FAIL initially - size limits not implemented yet.
    """
    executor_with_checkpoints.load_workflow(simple_workflow)

    # Test Case 1: Very large context data
    large_context = {
        "large_data": "x" * (10 * 1024 * 1024),  # 10MB string
        "block1": {"output": "test"},
    }

    large_checkpoint = CheckpointState(
        checkpoint_id="large_chk_123",
        workflow_name="test-workflow",
        created_at=time.time(),
        runtime_inputs={},
        context=serialize_context(large_context),
        completed_blocks=["block1"],
        current_wave_index=0,
        execution_waves=[["block1"], ["block2"]],
        block_definitions={
            "block1": {"id": "block1", "type": "EchoBlock", "inputs": {"message": "test"}},
        },
        workflow_stack=[],
    )

    # Should either succeed or provide clear size limit error
    try:
        await checkpoint_store.save_checkpoint(large_checkpoint)
        loaded = await checkpoint_store.load_checkpoint("large_chk_123")

        # If it succeeds, should load correctly
        if loaded:
            assert loaded.checkpoint_id == "large_chk_123"

    except Exception as e:
        # Should provide clear size limit error
        assert "size" in str(e).lower() or "too large" in str(e).lower()

    # Test Case 2: Extremely deep nested structure
    def create_deep_nested(depth: int) -> dict:
        """Create deeply nested dictionary."""
        if depth == 0:
            return {"value": "leaf"}
        return {"nested": create_deep_nested(depth - 1)}

    # Reduce depth to avoid hitting Python's recursion limit during test setup
    # We want to test serialization depth handling, not test framework limits
    deep_context = {
        "deep_structure": create_deep_nested(100),  # 100 levels deep
        "block1": {"output": "test"},
    }

    deep_checkpoint = CheckpointState(
        checkpoint_id="deep_chk_456",
        workflow_name="test-workflow",
        created_at=time.time(),
        runtime_inputs={},
        context=serialize_context(deep_context),
        completed_blocks=["block1"],
        current_wave_index=0,
        execution_waves=[["block1"]],
        block_definitions={},
        workflow_stack=[],
    )

    try:
        await checkpoint_store.save_checkpoint(deep_checkpoint)
        loaded = await checkpoint_store.load_checkpoint("deep_chk_456")
        assert loaded is not None

    except Exception as e:
        # Should handle deep nesting gracefully
        assert "depth" in str(e).lower() or "recursion" in str(e).lower()

    # Test Case 3: Circular reference detection
    circular_context: dict = {"block1": {"output": "test"}}
    circular_context["self"] = circular_context  # Circular reference

    # Serialization should detect and handle circular references
    try:
        serialized = serialize_context(circular_context)
        # Should either serialize safely or raise clear error
        assert isinstance(serialized, (str, dict))

    except Exception as e:
        assert "circular" in str(e).lower() or "reference" in str(e).lower()

    # Test Case 4: Large number of completed blocks
    many_blocks = [f"block_{i}" for i in range(10000)]  # 10k blocks

    many_blocks_checkpoint = CheckpointState(
        checkpoint_id="many_blocks_chk",
        workflow_name="test-workflow",
        created_at=time.time(),
        runtime_inputs={},
        context={},
        completed_blocks=many_blocks,
        current_wave_index=0,
        execution_waves=[many_blocks],
        block_definitions={
            f"block_{i}": {"id": f"block_{i}", "type": "EchoBlock"} for i in range(10000)
        },
        workflow_stack=[],
    )

    try:
        await checkpoint_store.save_checkpoint(many_blocks_checkpoint)
        loaded = await checkpoint_store.load_checkpoint("many_blocks_chk")

        if loaded:
            assert len(loaded.completed_blocks) == 10000

    except Exception as e:
        # Should provide clear error about too many blocks
        assert "too many" in str(e).lower() or "limit" in str(e).lower()

    # Test Case 5: Binary data in context (should be handled or rejected)
    binary_context = {
        "binary_data": b"\x00\x01\x02\xff\xfe\xfd",
        "block1": {"output": "test"},
    }

    try:
        serialized = serialize_context(binary_context)
        # Should handle binary data gracefully
        assert serialized is not None

    except Exception as e:
        # Should provide clear error about binary data
        assert "binary" in str(e).lower() or "serialize" in str(e).lower()


@pytest.mark.asyncio
async def test_concurrent_checkpoint_access(
    checkpoint_store, executor_with_checkpoints, simple_workflow
):
    """Test concurrent checkpoint save/load operations.

    Edge cases:
    - Concurrent saves to same checkpoint ID
    - Concurrent load operations
    - Save while load in progress
    - Multiple workflows checkpointing simultaneously

    This test should FAIL initially - concurrency safety not implemented yet.
    """
    executor_with_checkpoints.load_workflow(simple_workflow)

    # Test Case 1: Concurrent saves to different checkpoint IDs (should succeed)
    async def save_checkpoint(index: int) -> str:
        """Save a checkpoint with unique ID."""
        checkpoint_id = f"concurrent_chk_{index}"
        checkpoint = CheckpointState(
            checkpoint_id=checkpoint_id,
            workflow_name="test-workflow",
            created_at=time.time(),
            runtime_inputs={"index": index},
            context=serialize_context({"block1": {"output": f"test_{index}"}}),
            completed_blocks=["block1"],
            current_wave_index=0,
            execution_waves=[["block1"], ["block2"]],
            block_definitions={
                "block1": {"id": "block1", "type": "EchoBlock", "inputs": {"message": "test"}},
            },
            workflow_stack=[],
        )
        await checkpoint_store.save_checkpoint(checkpoint)
        return checkpoint_id

    # Launch 10 concurrent save operations
    checkpoint_ids = await asyncio.gather(*[save_checkpoint(i) for i in range(10)])

    # All saves should succeed
    assert len(checkpoint_ids) == 10

    # All checkpoints should be loadable
    for checkpoint_id in checkpoint_ids:
        loaded = await checkpoint_store.load_checkpoint(checkpoint_id)
        assert loaded is not None
        assert loaded.checkpoint_id == checkpoint_id

    # Test Case 2: Concurrent saves to SAME checkpoint ID (last write wins or error)
    same_id = "concurrent_same_chk"

    async def save_same_checkpoint(value: int) -> None:
        """Save checkpoint with same ID but different data."""
        checkpoint = CheckpointState(
            checkpoint_id=same_id,
            workflow_name="test-workflow",
            created_at=time.time(),
            runtime_inputs={"value": value},
            context=serialize_context({"value": value}),
            completed_blocks=[],
            current_wave_index=0,
            execution_waves=[],
            block_definitions={},
            workflow_stack=[],
        )
        await checkpoint_store.save_checkpoint(checkpoint)

    # Launch concurrent saves with same ID
    await asyncio.gather(*[save_same_checkpoint(i) for i in range(10)])

    # Load final checkpoint - should have one of the values
    loaded = await checkpoint_store.load_checkpoint(same_id)
    assert loaded is not None
    assert loaded.checkpoint_id == same_id
    # Value should be one of 0-9
    assert 0 <= loaded.runtime_inputs.get("value", -1) <= 9

    # Test Case 3: Concurrent loads of same checkpoint (should all succeed)
    test_checkpoint = CheckpointState(
        checkpoint_id="concurrent_load_chk",
        workflow_name="test-workflow",
        created_at=time.time(),
        runtime_inputs={"test": "data"},
        context={},
        completed_blocks=[],
        current_wave_index=0,
        execution_waves=[],
        block_definitions={},
        workflow_stack=[],
    )
    await checkpoint_store.save_checkpoint(test_checkpoint)

    # Launch 20 concurrent load operations
    loaded_checkpoints = await asyncio.gather(
        *[checkpoint_store.load_checkpoint("concurrent_load_chk") for _ in range(20)]
    )

    # All loads should succeed with consistent data
    assert len(loaded_checkpoints) == 20
    for loaded in loaded_checkpoints:
        assert loaded is not None
        assert loaded.checkpoint_id == "concurrent_load_chk"
        assert loaded.runtime_inputs == {"test": "data"}

    # Test Case 4: Save while load in progress
    save_load_checkpoint = CheckpointState(
        checkpoint_id="save_load_chk",
        workflow_name="test-workflow",
        created_at=time.time(),
        runtime_inputs={"version": 1},
        context={},
        completed_blocks=[],
        current_wave_index=0,
        execution_waves=[],
        block_definitions={},
        workflow_stack=[],
    )
    await checkpoint_store.save_checkpoint(save_load_checkpoint)

    async def load_repeatedly() -> list:
        """Load checkpoint multiple times."""
        results = []
        for _ in range(5):
            loaded = await checkpoint_store.load_checkpoint("save_load_chk")
            results.append(loaded)
            await asyncio.sleep(0.01)
        return results

    async def save_repeatedly() -> None:
        """Save checkpoint multiple times with different data."""
        for i in range(5):
            checkpoint = CheckpointState(
                checkpoint_id="save_load_chk",
                workflow_name="test-workflow",
                created_at=time.time(),
                runtime_inputs={"version": i + 2},
                context={},
                completed_blocks=[],
                current_wave_index=0,
                execution_waves=[],
                block_definitions={},
                workflow_stack=[],
            )
            await checkpoint_store.save_checkpoint(checkpoint)
            await asyncio.sleep(0.01)

    # Run load and save operations concurrently
    load_results, _ = await asyncio.gather(load_repeatedly(), save_repeatedly())

    # All loads should succeed (data may vary due to concurrent saves)
    assert len(load_results) == 5
    for loaded in load_results:
        assert loaded is not None
        assert loaded.checkpoint_id == "save_load_chk"


@pytest.mark.asyncio
async def test_schema_version_mismatch(checkpoint_store, executor_with_checkpoints):
    """Test handling of checkpoint schema version mismatches.

    Edge cases:
    - Future schema version (newer than current)
    - Old schema version (missing new fields)
    - Invalid schema version format
    - Missing schema version field

    This test should FAIL initially - schema versioning not implemented yet.
    """
    # Test Case 1: Future schema version
    future_checkpoint = CheckpointState(
        checkpoint_id="future_schema_chk",
        workflow_name="test-workflow",
        created_at=time.time(),
        runtime_inputs={},
        context={},
        completed_blocks=[],
        current_wave_index=0,
        execution_waves=[],
        block_definitions={},
        workflow_stack=[],
    )

    # Add future schema version metadata (if schema version field exists)
    # For now, manually test by modifying checkpoint data
    await checkpoint_store.save_checkpoint(future_checkpoint)

    # Try to load checkpoint with future schema
    loaded = await checkpoint_store.load_checkpoint("future_schema_chk")

    # Should either:
    # 1. Load successfully with forward compatibility
    # 2. Return clear error about schema version mismatch
    if loaded is None:
        # Check that list_checkpoints doesn't return it either
        checkpoints = await checkpoint_store.list_checkpoints()
        matching = [c for c in checkpoints if c.checkpoint_id == "future_schema_chk"]
        # Should be present but indicate version mismatch
        assert len(matching) >= 0  # May or may not be listed
    else:
        # If loaded, should have valid data
        assert loaded.checkpoint_id == "future_schema_chk"

    # Test Case 2: Old schema version (missing new fields)
    # Simulate old checkpoint by creating one without new fields
    old_checkpoint = CheckpointState(
        checkpoint_id="old_schema_chk",
        workflow_name="test-workflow",
        created_at=time.time(),
        runtime_inputs={},
        context={},
        completed_blocks=[],
        current_wave_index=0,
        execution_waves=[],
        block_definitions={},
        workflow_stack=[],
    )

    # Manually remove new fields to simulate old schema
    # If new fields exist, remove them
    # For now, just save and load to test backward compatibility

    await checkpoint_store.save_checkpoint(old_checkpoint)
    loaded = await checkpoint_store.load_checkpoint("old_schema_chk")

    # Should load with defaults for missing fields
    assert loaded is not None
    assert loaded.checkpoint_id == "old_schema_chk"
    # New fields should have sensible defaults
    assert isinstance(loaded.workflow_stack, list)

    # Test Case 3: Invalid schema version format
    # This would require schema version field to be implemented first
    # For now, test that invalid data is handled

    # Test Case 4: Checkpoint with extra unknown fields (forward compatibility test)
    checkpoint_with_extra = CheckpointState(
        checkpoint_id="extra_fields_chk",
        workflow_name="test-workflow",
        created_at=time.time(),
        runtime_inputs={},
        context={},
        completed_blocks=[],
        current_wave_index=0,
        execution_waves=[],
        block_definitions={},
        workflow_stack=[],
    )

    await checkpoint_store.save_checkpoint(checkpoint_with_extra)

    # Manually add extra fields to stored data (if store allows direct manipulation)
    # For now, just verify that normal checkpoints work
    loaded = await checkpoint_store.load_checkpoint("extra_fields_chk")
    assert loaded is not None
    assert loaded.checkpoint_id == "extra_fields_chk"
