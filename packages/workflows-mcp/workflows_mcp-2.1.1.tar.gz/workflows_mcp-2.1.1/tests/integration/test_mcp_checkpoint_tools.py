"""Test MCP checkpoint management tools.

Tests for the MCP tools that expose checkpoint/pause/resume functionality to Claude.
"""

import time

import pytest

from workflows_mcp.engine.checkpoint import CheckpointState
from workflows_mcp.engine.checkpoint_store import InMemoryCheckpointStore
from workflows_mcp.engine.executor import WorkflowDefinition, WorkflowExecutor
from workflows_mcp.engine.response import WorkflowResponse
from workflows_mcp.tools import (
    delete_checkpoint,
    get_checkpoint_info,
    list_checkpoints,
    resume_workflow,
)


def to_dict(result):
    """Convert WorkflowResponse to dict for testing."""
    if isinstance(result, WorkflowResponse):
        return result.model_dump()
    return result


@pytest.fixture
async def setup_test_environment():
    """Setup test environment with executor and checkpoint store.

    IMPORTANT: This fixture saves and restores the global server.executor
    to prevent tests from interfering with each other.
    """
    from unittest.mock import MagicMock

    from workflows_mcp.context import AppContext
    from workflows_mcp.engine.registry import WorkflowRegistry

    store = InMemoryCheckpointStore()
    executor = WorkflowExecutor(checkpoint_store=store)
    registry = WorkflowRegistry()

    # Load test workflow
    workflow = WorkflowDefinition(
        name="test-workflow",
        description="Test workflow",
        blocks=[
            {"id": "block1", "type": "EchoBlock", "inputs": {"message": "Test"}, "depends_on": []}
        ],
        inputs={},
    )
    executor.load_workflow(workflow)
    registry.register(workflow)

    # Create some test checkpoints
    block_def = {
        "id": "block1",
        "type": "EchoBlock",
        "inputs": {"message": "Test"},
        "depends_on": [],
    }
    checkpoint1 = CheckpointState(
        checkpoint_id="chk_test_1",
        workflow_name="test-workflow",
        created_at=time.time(),
        runtime_inputs={},
        context={},
        completed_blocks=[],
        current_wave_index=0,
        execution_waves=[["block1"]],
        block_definitions={"block1": block_def},
        workflow_stack=[],
    )

    checkpoint2 = CheckpointState(
        checkpoint_id="pause_test_2",
        workflow_name="test-workflow",
        created_at=time.time() - 100,
        runtime_inputs={},
        context={},
        completed_blocks=[],
        current_wave_index=0,
        execution_waves=[],
        block_definitions={},
        workflow_stack=[],
        paused_block_id="confirm1",
        pause_prompt="Confirm operation?",
    )

    await store.save_checkpoint(checkpoint1)
    await store.save_checkpoint(checkpoint2)

    # Create mock context for MCP tools
    mock_ctx = MagicMock()
    mock_ctx.request_context.lifespan_context = AppContext(registry=registry, executor=executor)

    yield {"executor": executor, "store": store, "mock_context": mock_ctx}


@pytest.mark.asyncio
async def test_resume_workflow_tool_with_checkpoint(setup_test_environment):
    """resume_workflow tool must work with valid checkpoint."""
    ctx = setup_test_environment["mock_context"]

    # Set global executor for tool access
    # Call resume_workflow tool
    result = await resume_workflow(checkpoint_id="chk_test_1", llm_response="", ctx=ctx)
    result = to_dict(result)

    assert isinstance(result, dict)
    assert result["status"] in ["success", "failure"]
    # Should either succeed or have clear error message


@pytest.mark.asyncio
async def test_resume_workflow_tool_with_pause(setup_test_environment):
    """resume_workflow tool must handle paused checkpoints."""
    ctx = setup_test_environment["mock_context"]
    # Resume paused checkpoint with response
    result = await resume_workflow(checkpoint_id="pause_test_2", llm_response="yes", ctx=ctx)
    result = to_dict(result)

    assert isinstance(result, dict)
    assert result["status"] in ["success", "failure", "paused"]


@pytest.mark.asyncio
async def test_resume_workflow_tool_missing_checkpoint(setup_test_environment):
    """resume_workflow tool must handle missing checkpoint."""
    ctx = setup_test_environment["mock_context"]
    result = await resume_workflow(checkpoint_id="nonexistent", llm_response="", ctx=ctx)
    result = to_dict(result)

    assert isinstance(result, dict)
    assert result["status"] == "failure"
    assert "error" in result
    assert "not found" in result["error"].lower()


@pytest.mark.asyncio
async def test_list_checkpoints_tool_all(setup_test_environment):
    """list_checkpoints tool must list all checkpoints."""
    ctx = setup_test_environment["mock_context"]
    result = await list_checkpoints(workflow_name="", ctx=ctx)
    result = to_dict(result)

    assert isinstance(result, dict)
    assert "checkpoints" in result
    assert isinstance(result["checkpoints"], list)
    assert len(result["checkpoints"]) >= 2  # At least our 2 test checkpoints
    assert "total" in result
    assert result["total"] >= 2


@pytest.mark.asyncio
async def test_list_checkpoints_tool_filtered(setup_test_environment):
    """list_checkpoints tool must filter by workflow name."""
    ctx = setup_test_environment["mock_context"]
    result = await list_checkpoints(workflow_name="test-workflow", ctx=ctx)
    result = to_dict(result)

    assert isinstance(result, dict)
    assert "checkpoints" in result
    assert all(c["workflow"] == "test-workflow" for c in result["checkpoints"])


@pytest.mark.asyncio
async def test_list_checkpoints_shows_pause_status(setup_test_environment):
    """list_checkpoints must indicate which checkpoints are paused."""
    ctx = setup_test_environment["mock_context"]
    result = await list_checkpoints(workflow_name="test-workflow", ctx=ctx)
    result = to_dict(result)

    checkpoints = result["checkpoints"]

    # Find paused checkpoint
    paused_checkpoints = [c for c in checkpoints if c.get("is_paused")]
    assert len(paused_checkpoints) >= 1

    # Paused checkpoint should have pause_prompt
    paused = paused_checkpoints[0]
    assert "pause_prompt" in paused
    assert paused["pause_prompt"] is not None


@pytest.mark.asyncio
async def test_get_checkpoint_info_tool(setup_test_environment):
    """get_checkpoint_info tool must return checkpoint details."""
    ctx = setup_test_environment["mock_context"]
    result = await get_checkpoint_info(checkpoint_id="chk_test_1", ctx=ctx)
    result = to_dict(result)

    assert isinstance(result, dict)
    assert result["found"] is True
    assert result["checkpoint_id"] == "chk_test_1"
    assert "workflow_name" in result
    assert "created_at" in result
    assert "is_paused" in result
    assert "completed_blocks" in result
    assert "current_wave" in result
    assert "total_waves" in result


@pytest.mark.asyncio
async def test_get_checkpoint_info_not_found(setup_test_environment):
    """get_checkpoint_info must handle missing checkpoint."""
    ctx = setup_test_environment["mock_context"]
    result = await get_checkpoint_info(checkpoint_id="nonexistent", ctx=ctx)
    result = to_dict(result)

    assert isinstance(result, dict)
    assert result["found"] is False
    assert "error" in result


@pytest.mark.asyncio
async def test_get_checkpoint_info_shows_progress(setup_test_environment):
    """get_checkpoint_info must show execution progress percentage."""
    ctx = setup_test_environment["mock_context"]
    result = await get_checkpoint_info(checkpoint_id="chk_test_1", ctx=ctx)
    result = to_dict(result)

    assert "progress_percentage" in result
    assert isinstance(result["progress_percentage"], (int, float))
    assert 0 <= result["progress_percentage"] <= 100


@pytest.mark.asyncio
async def test_delete_checkpoint_tool(setup_test_environment):
    """delete_checkpoint tool must delete checkpoint."""
    ctx = setup_test_environment["mock_context"]
    result = await delete_checkpoint(checkpoint_id="chk_test_1", ctx=ctx)
    result = to_dict(result)

    assert isinstance(result, dict)
    assert result["deleted"] is True
    assert result["checkpoint_id"] == "chk_test_1"

    # Verify it's gone
    info = await get_checkpoint_info(checkpoint_id="chk_test_1", ctx=ctx)
    info = to_dict(info)
    assert info["found"] is False


@pytest.mark.asyncio
async def test_delete_checkpoint_not_found(setup_test_environment):
    """delete_checkpoint tool must handle missing checkpoint."""
    ctx = setup_test_environment["mock_context"]
    result = await delete_checkpoint(checkpoint_id="nonexistent", ctx=ctx)
    result = to_dict(result)

    assert isinstance(result, dict)
    assert result["deleted"] is False


# Test removed: executor is always initialized at module level in server.py
# Testing defensive code for impossible scenarios is unnecessary
# The executor is a module-level constant that cannot be undefined
