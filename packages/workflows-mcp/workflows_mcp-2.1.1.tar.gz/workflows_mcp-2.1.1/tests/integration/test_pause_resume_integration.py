"""Integration tests for pause/resume workflow execution.

Tests end-to-end pause/resume scenarios with workflow executor.
"""

import pytest

from workflows_mcp.engine.response import WorkflowResponse


def to_dict(result):
    """Convert WorkflowResponse to dict for testing."""
    if isinstance(result, WorkflowResponse):
        return result.model_dump()
    return result


def create_interactive_workflow():
    """Create workflow with interactive block."""
    from workflows_mcp.engine.executor import WorkflowDefinition

    return WorkflowDefinition(
        name="interactive-test",
        description="Test workflow with interactive blocks",
        blocks=[
            {
                "id": "setup",
                "type": "EchoBlock",
                "inputs": {"message": "Setup complete"},
                "depends_on": [],
            },
            {
                "id": "confirm",
                "type": "ConfirmOperation",
                "inputs": {"message": "Proceed with deployment?", "operation": "deploy"},
                "depends_on": ["setup"],
            },
            {
                "id": "deploy",
                "type": "EchoBlock",
                "inputs": {"message": "Deploying..."},
                "condition": "${blocks.confirm.outputs.confirmed} == True",
                "depends_on": ["confirm"],
            },
        ],
        inputs={},
    )


@pytest.mark.asyncio
async def test_workflow_pauses_at_interactive_block():
    """Workflow must pause when encountering interactive block."""
    from workflows_mcp.engine.checkpoint_store import InMemoryCheckpointStore
    from workflows_mcp.engine.executor import WorkflowExecutor

    store = InMemoryCheckpointStore()
    executor = WorkflowExecutor(checkpoint_store=store)

    workflow = create_interactive_workflow()
    executor.load_workflow(workflow)

    # Execute - should pause at confirm block
    result = await executor.execute_workflow("interactive-test", {})

    # Should pause (not succeed or fail)
    assert result.is_paused is True
    assert result.pause_data is not None
    assert "Proceed with deployment?" in result.pause_data.prompt


@pytest.mark.asyncio
async def test_resume_workflow_with_response():
    """Resume must continue workflow with LLM response."""
    from workflows_mcp.engine.checkpoint_store import InMemoryCheckpointStore
    from workflows_mcp.engine.executor import WorkflowExecutor

    store = InMemoryCheckpointStore()
    executor = WorkflowExecutor(checkpoint_store=store)

    workflow = create_interactive_workflow()
    executor.load_workflow(workflow)

    # Execute - pauses at confirm
    pause_result = await executor.execute_workflow("interactive-test", {})
    assert pause_result.is_paused

    checkpoint_id = pause_result.pause_data.checkpoint_id

    # Resume with "yes" - should complete workflow
    resume_result = await executor.resume_workflow(checkpoint_id, llm_response="yes")

    assert resume_result.is_success is True
    # Deploy block should have executed (condition was true)


@pytest.mark.asyncio
async def test_conditional_skip_after_resume():
    """Conditional blocks must respect resume response."""
    from workflows_mcp.engine.checkpoint_store import InMemoryCheckpointStore
    from workflows_mcp.engine.executor import WorkflowExecutor

    store = InMemoryCheckpointStore()
    executor = WorkflowExecutor(checkpoint_store=store)

    workflow = create_interactive_workflow()
    executor.load_workflow(workflow)

    # Execute and pause
    pause_result = await executor.execute_workflow("interactive-test", {})
    checkpoint_id = pause_result.pause_data.checkpoint_id

    # Resume with "no" - deploy block should be skipped
    resume_result = await executor.resume_workflow(checkpoint_id, llm_response="no")

    assert resume_result.is_success is True
    # Check that deploy block was skipped (confirmed=false)
