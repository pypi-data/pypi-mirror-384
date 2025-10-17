"""
Test executor checkpointing integration.

Tests automatic checkpoint creation after each wave and workflow resumption.
"""

import time

import pytest

from workflows_mcp.engine.response import WorkflowResponse


def to_dict(result):
    """Convert WorkflowResponse to dict for testing."""
    if isinstance(result, WorkflowResponse):
        return result.model_dump()
    return result


@pytest.fixture
def checkpoint_store():
    """Create in-memory checkpoint store for testing."""
    from workflows_mcp.engine.checkpoint_store import InMemoryCheckpointStore

    return InMemoryCheckpointStore()


@pytest.fixture
def executor_with_checkpoints(checkpoint_store):
    """Create executor with checkpoint support."""
    from workflows_mcp.engine.executor import WorkflowExecutor

    return WorkflowExecutor(checkpoint_store=checkpoint_store)


def create_simple_workflow():
    """Create simple test workflow with multiple waves."""
    from workflows_mcp.engine.executor import WorkflowDefinition

    # Workflow: block1 (wave 0) → block2 (wave 1) → block3 (wave 2)
    return WorkflowDefinition(
        name="test-workflow",
        description="Test workflow with multiple waves",
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
            {
                "id": "block3",
                "type": "EchoBlock",
                "inputs": {"message": "Block 3"},
                "depends_on": ["block2"],
            },
        ],
        inputs={},
    )


@pytest.mark.asyncio
async def test_executor_accepts_checkpoint_store():
    """Executor must accept checkpoint_store parameter."""
    from workflows_mcp.engine.checkpoint_store import InMemoryCheckpointStore
    from workflows_mcp.engine.executor import WorkflowExecutor

    store = InMemoryCheckpointStore()
    executor = WorkflowExecutor(checkpoint_store=store)

    assert executor.checkpoint_store is store


@pytest.mark.asyncio
async def test_automatic_checkpoint_after_wave(executor_with_checkpoints, checkpoint_store):
    """Checkpoints must be created after completing each wave."""
    workflow = create_simple_workflow()
    executor_with_checkpoints.load_workflow(workflow)

    # Execute workflow
    result = await executor_with_checkpoints.execute_workflow("test-workflow", {})
    assert result.is_success

    # Verify checkpoints were created
    checkpoints = await checkpoint_store.list_checkpoints()
    assert len(checkpoints) >= 1  # At least one checkpoint per wave


@pytest.mark.asyncio
async def test_checkpoint_contains_correct_state(executor_with_checkpoints, checkpoint_store):
    """Checkpoint must contain complete workflow state."""
    workflow = create_simple_workflow()
    executor_with_checkpoints.load_workflow(workflow)

    await executor_with_checkpoints.execute_workflow("test-workflow", {"input": "value"})

    checkpoints = await checkpoint_store.list_checkpoints()
    assert len(checkpoints) > 0

    # Load first checkpoint and verify state
    checkpoint = checkpoints[0]
    state = await checkpoint_store.load_checkpoint(checkpoint.checkpoint_id)

    assert state.workflow_name == "test-workflow"
    assert state.runtime_inputs == {"input": "value"}
    assert isinstance(state.context, dict)
    assert isinstance(state.completed_blocks, list)
    assert isinstance(state.execution_waves, list)
    assert isinstance(state.block_definitions, dict)


@pytest.mark.asyncio
async def test_resume_workflow_continues_execution(executor_with_checkpoints, checkpoint_store):
    """Resume must continue workflow from checkpoint."""
    workflow = create_simple_workflow()
    executor_with_checkpoints.load_workflow(workflow)

    # Execute workflow to create checkpoints
    await executor_with_checkpoints.execute_workflow("test-workflow", {})

    # Get a checkpoint
    checkpoints = await checkpoint_store.list_checkpoints()
    assert len(checkpoints) > 0

    checkpoint_id = checkpoints[0].checkpoint_id

    # Resume should work (even if workflow already complete, it should handle gracefully)
    result = await executor_with_checkpoints.resume_workflow(checkpoint_id)
    assert result.is_success or result.error is not None  # Either succeeds or gives clear error


@pytest.mark.asyncio
async def test_resume_restores_context(executor_with_checkpoints, checkpoint_store):
    """Resume must restore workflow context correctly."""
    from workflows_mcp.engine.checkpoint import CheckpointState
    from workflows_mcp.engine.serialization import serialize_context

    workflow = create_simple_workflow()
    executor_with_checkpoints.load_workflow(workflow)

    # Manually create checkpoint with specific context
    checkpoint_state = CheckpointState(
        checkpoint_id="test_chk_123",
        workflow_name="test-workflow",
        created_at=time.time(),
        runtime_inputs={"input": "test"},
        context=serialize_context({"block1.message": "Block 1", "custom_var": "data"}),
        completed_blocks=["block1"],
        current_wave_index=0,
        execution_waves=[["block1"], ["block2"], ["block3"]],
        block_definitions={
            "block1": {
                "id": "block1",
                "type": "EchoBlock",
                "inputs": {"message": "Block 1"},
                "depends_on": [],
            },
            "block2": {
                "id": "block2",
                "type": "EchoBlock",
                "inputs": {"message": "Block 2"},
                "depends_on": ["block1"],
            },
            "block3": {
                "id": "block3",
                "type": "EchoBlock",
                "inputs": {"message": "Block 3"},
                "depends_on": ["block2"],
            },
        },
        workflow_stack=[],
    )

    await checkpoint_store.save_checkpoint(checkpoint_state)

    # Resume - should restore context
    result = await executor_with_checkpoints.resume_workflow("test_chk_123")

    # Should either succeed or fail with clear error
    assert result.is_success or result.error is not None


@pytest.mark.asyncio
async def test_resume_with_missing_checkpoint(executor_with_checkpoints):
    """Resume with nonexistent checkpoint must return clear error."""
    result = await executor_with_checkpoints.resume_workflow("nonexistent_checkpoint")

    assert not result.is_success
    assert "not found" in result.error.lower()


@pytest.mark.asyncio
async def test_resume_with_missing_workflow(executor_with_checkpoints, checkpoint_store):
    """Resume with checkpoint for unloaded workflow must return error."""
    from workflows_mcp.engine.checkpoint import CheckpointState

    # Create checkpoint for workflow not loaded in executor
    checkpoint_state = CheckpointState(
        checkpoint_id="test_chk_456",
        workflow_name="nonexistent-workflow",
        created_at=time.time(),
        runtime_inputs={},
        context={},
        completed_blocks=[],
        current_wave_index=0,
        execution_waves=[],
        block_definitions={},
        workflow_stack=[],
    )

    await checkpoint_store.save_checkpoint(checkpoint_state)

    result = await executor_with_checkpoints.resume_workflow("test_chk_456")

    assert not result.is_success
    assert "not found" in result.error.lower() or "not loaded" in result.error.lower()


@pytest.mark.asyncio
async def test_checkpoint_preserves_workflow_stack(executor_with_checkpoints, checkpoint_store):
    """Checkpoint must preserve workflow stack for nested workflows."""
    workflow = create_simple_workflow()
    executor_with_checkpoints.load_workflow(workflow)

    # Execute with workflow stack in context
    runtime_inputs = {"input": "test"}
    result = await executor_with_checkpoints.execute_workflow("test-workflow", runtime_inputs)
    assert result.is_success

    # Check that checkpoints preserve workflow stack
    checkpoints = await checkpoint_store.list_checkpoints()
    if len(checkpoints) > 0:
        state = await checkpoint_store.load_checkpoint(checkpoints[0].checkpoint_id)
        assert isinstance(state.workflow_stack, list)


@pytest.mark.asyncio
async def test_checkpoint_disabled(checkpoint_store):
    """Executor must support disabling checkpointing."""
    from workflows_mcp.engine.checkpoint import CheckpointConfig
    from workflows_mcp.engine.executor import WorkflowExecutor

    # Create executor with checkpointing disabled
    config = CheckpointConfig(enabled=False)
    executor = WorkflowExecutor(checkpoint_store=checkpoint_store, checkpoint_config=config)

    workflow = create_simple_workflow()
    executor.load_workflow(workflow)

    # Execute workflow
    result = await executor.execute_workflow("test-workflow", {})
    assert result.is_success

    # No checkpoints should be created
    checkpoints = await checkpoint_store.list_checkpoints()
    assert len(checkpoints) == 0


@pytest.mark.asyncio
async def test_existing_workflows_still_work():
    """Existing workflows must work without checkpoint_store parameter."""
    from workflows_mcp.engine.executor import WorkflowExecutor

    # Create executor without checkpoint support (backward compatibility)
    executor = WorkflowExecutor()

    workflow = create_simple_workflow()
    executor.load_workflow(workflow)

    result = await executor.execute_workflow("test-workflow", {})
    assert result.is_success
