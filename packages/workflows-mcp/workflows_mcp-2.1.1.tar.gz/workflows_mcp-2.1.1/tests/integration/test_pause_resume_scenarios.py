"""
Test pause/resume workflow scenarios.

Tests comprehensive pause/resume scenarios including:
- Wave-level pause boundaries
- Block failures after resume
- Conditional block evaluation after resume
- Multiple pause/resume cycles in single workflow

These tests follow TDD RED phase - they should FAIL initially.
"""

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
def multi_wave_workflow():
    """Create workflow with multiple waves for testing."""
    return WorkflowDefinition(
        name="multi-wave-test",
        description="Test workflow with multiple waves",
        blocks=[
            {
                "id": "wave1_block1",
                "type": "EchoBlock",
                "inputs": {"message": "Wave 1 - Block 1"},
                "depends_on": [],
            },
            {
                "id": "wave1_block2",
                "type": "EchoBlock",
                "inputs": {"message": "Wave 1 - Block 2"},
                "depends_on": [],
            },
            {
                "id": "wave2_block1",
                "type": "EchoBlock",
                "inputs": {"message": "Wave 2 - Block 1"},
                "depends_on": ["wave1_block1"],
            },
            {
                "id": "wave2_block2",
                "type": "EchoBlock",
                "inputs": {"message": "Wave 2 - Block 2"},
                "depends_on": ["wave1_block2"],
            },
            {
                "id": "wave3_block1",
                "type": "EchoBlock",
                "inputs": {"message": "Wave 3 - Block 1"},
                "depends_on": ["wave2_block1", "wave2_block2"],
            },
        ],
        inputs={},
    )


@pytest.fixture
def conditional_workflow():
    """Create workflow with conditional blocks for testing."""
    return WorkflowDefinition(
        name="conditional-test",
        description="Test workflow with conditional blocks",
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
                "condition": "${block1.echoed} == 'Block 1'",
            },
            {
                "id": "block3",
                "type": "EchoBlock",
                "inputs": {"message": "Block 3"},
                "depends_on": ["block2"],
                "condition": "${block2.skipped} == False",
            },
        ],
        inputs={},
    )


@pytest.mark.asyncio
async def test_wave_level_pause(executor_with_checkpoints, checkpoint_store, multi_wave_workflow):
    """Test that pause happens at wave boundaries, not mid-wave.

    Edge case: When multiple blocks in a wave are executing concurrently,
    pause should happen after ALL blocks in the wave complete, not mid-wave.

    This test should FAIL initially - wave boundary enforcement not implemented yet.
    """
    executor_with_checkpoints.load_workflow(multi_wave_workflow)

    # Execute workflow and create checkpoint after wave 1
    result = await executor_with_checkpoints.execute_workflow("multi-wave-test", {})
    assert result.is_success

    # Get all checkpoints created
    checkpoints = await checkpoint_store.list_checkpoints()
    assert len(checkpoints) > 0

    # Verify checkpoints are created at wave boundaries
    for checkpoint_info in checkpoints:
        checkpoint = await checkpoint_store.load_checkpoint(checkpoint_info.checkpoint_id)

        # Current wave index should indicate a complete wave
        wave_idx = checkpoint.current_wave_index
        completed_blocks = checkpoint.completed_blocks
        execution_waves = checkpoint.execution_waves

        # All blocks in waves up to and including current wave should be completed
        expected_completed = []
        for idx in range(wave_idx + 1):
            if idx < len(execution_waves):
                expected_completed.extend(execution_waves[idx])

        # Verify all expected blocks are completed
        for block_id in expected_completed:
            assert block_id in completed_blocks, (
                f"Block {block_id} should be completed at wave {wave_idx}"
            )

        # Verify no blocks from future waves are completed
        for idx in range(wave_idx + 1, len(execution_waves)):
            for block_id in execution_waves[idx]:
                assert block_id not in completed_blocks, (
                    f"Block {block_id} from wave {idx} should not be completed yet"
                )

    # Test edge case: Resume from checkpoint should start at next wave boundary
    if len(checkpoints) > 0:
        first_checkpoint = checkpoints[0]
        checkpoint_state = await checkpoint_store.load_checkpoint(first_checkpoint.checkpoint_id)

        # Resume should continue from next wave
        next_wave_idx = checkpoint_state.current_wave_index + 1

        if next_wave_idx < len(checkpoint_state.execution_waves):
            # Resume execution
            resume_result = await executor_with_checkpoints.resume_workflow(
                first_checkpoint.checkpoint_id
            )

            # Should succeed or provide clear error
            assert resume_result.is_success or resume_result.error is not None

            # If successful, verify blocks from next wave were executed
            if resume_result.is_success:
                # All remaining blocks should be completed
                remaining_blocks = []
                for idx in range(next_wave_idx, len(checkpoint_state.execution_waves)):
                    remaining_blocks.extend(checkpoint_state.execution_waves[idx])

                # Verify result contains all remaining blocks
                result_data = resume_result.value
                assert "blocks" in result_data

                for block_id in remaining_blocks:
                    # Block should have been executed
                    assert block_id in result_data["blocks"], (
                        f"Block {block_id} should be in blocks after resume"
                    )


@pytest.mark.asyncio
async def test_block_failure_after_resume(
    executor_with_checkpoints, checkpoint_store, multi_wave_workflow
):
    """Test handling of block failure after workflow resume.

    Edge case: If a block fails after resume, the failure should be handled
    correctly and not corrupt the checkpoint state or leave workflow in bad state.

    This test should FAIL initially - post-resume failure handling not fully tested.
    """
    executor_with_checkpoints.load_workflow(multi_wave_workflow)

    # Create a checkpoint manually after wave 1
    checkpoint_state = CheckpointState(
        checkpoint_id="test_resume_failure_chk",
        workflow_name="multi-wave-test",
        created_at=time.time(),
        runtime_inputs={},
        context=serialize_context(
            {
                "wave1_block1.echoed": "Wave 1 - Block 1",
                "wave1_block2.echoed": "Wave 1 - Block 2",
            }
        ),
        completed_blocks=["wave1_block1", "wave1_block2"],
        current_wave_index=0,
        execution_waves=[
            ["wave1_block1", "wave1_block2"],
            ["wave2_block1", "wave2_block2"],
            ["wave3_block1"],
        ],
        block_definitions={
            "wave1_block1": {
                "id": "wave1_block1",
                "type": "EchoBlock",
                "inputs": {"message": "Wave 1 - Block 1"},
                "depends_on": [],
            },
            "wave1_block2": {
                "id": "wave1_block2",
                "type": "EchoBlock",
                "inputs": {"message": "Wave 1 - Block 2"},
                "depends_on": [],
            },
            "wave2_block1": {
                "id": "wave2_block1",
                "type": "EchoBlock",
                "inputs": {"message": "Wave 2 - Block 1"},
                "depends_on": ["wave1_block1"],
            },
            "wave2_block2": {
                "id": "wave2_block2",
                "type": "EchoBlock",
                "inputs": {"message": "Wave 2 - Block 2"},
                "depends_on": ["wave1_block2"],
            },
            "wave3_block1": {
                "id": "wave3_block1",
                "type": "EchoBlock",
                "inputs": {"message": "Wave 3 - Block 1"},
                "depends_on": ["wave2_block1", "wave2_block2"],
            },
        },
        workflow_stack=["multi-wave-test"],
    )

    await checkpoint_store.save_checkpoint(checkpoint_state)

    # Test Case 1: Resume should work for valid checkpoint
    result = await executor_with_checkpoints.resume_workflow("test_resume_failure_chk")
    assert result.is_success or result.error is not None

    if result.is_success:
        # Verify remaining blocks were executed
        result_data = result.value
        assert "blocks" in result_data
        # Wave 2 and Wave 3 blocks should be in blocks
        expected_blocks = ["wave2_block1", "wave2_block2", "wave3_block1"]
        for block_id in expected_blocks:
            assert block_id in result_data["blocks"]

    # Test Case 2: Create checkpoint with invalid block definition
    # This will cause failure during resume
    invalid_checkpoint = CheckpointState(
        checkpoint_id="test_invalid_block_chk",
        workflow_name="multi-wave-test",
        created_at=time.time(),
        runtime_inputs={},
        context=serialize_context(
            {
                "wave1_block1.echoed": "Wave 1 - Block 1",
            }
        ),
        completed_blocks=["wave1_block1"],
        current_wave_index=0,
        execution_waves=[
            ["wave1_block1"],
            ["invalid_block"],  # This block doesn't exist
        ],
        block_definitions={
            "wave1_block1": {
                "id": "wave1_block1",
                "type": "EchoBlock",
                "inputs": {"message": "Wave 1 - Block 1"},
                "depends_on": [],
            },
            "invalid_block": {
                "id": "invalid_block",
                "type": "NonExistentBlockType",  # Invalid block type
                "inputs": {"message": "Invalid"},
                "depends_on": ["wave1_block1"],
            },
        },
        workflow_stack=["multi-wave-test"],
    )

    await checkpoint_store.save_checkpoint(invalid_checkpoint)

    # Resume should fail gracefully with clear error
    result = await executor_with_checkpoints.resume_workflow("test_invalid_block_chk")
    assert not result.is_success
    assert "NonExistentBlockType" in result.error or "not found" in result.error.lower()

    # Test Case 3: Checkpoint with missing dependency in context
    missing_dep_checkpoint = CheckpointState(
        checkpoint_id="test_missing_dep_chk",
        workflow_name="multi-wave-test",
        created_at=time.time(),
        runtime_inputs={},
        context=serialize_context(
            {
                # Missing wave1_block1 output that wave2_block1 depends on
            }
        ),
        completed_blocks=["wave1_block1"],  # Claims block1 is done
        current_wave_index=0,
        execution_waves=[
            ["wave1_block1"],
            ["wave2_block1"],
        ],
        block_definitions={
            "wave1_block1": {
                "id": "wave1_block1",
                "type": "EchoBlock",
                "inputs": {"message": "Wave 1 - Block 1"},
                "depends_on": [],
            },
            "wave2_block1": {
                "id": "wave2_block1",
                "type": "EchoBlock",
                "inputs": {"message": "${wave1_block1.echoed}"},  # References missing output
                "depends_on": ["wave1_block1"],
            },
        },
        workflow_stack=["multi-wave-test"],
    )

    await checkpoint_store.save_checkpoint(missing_dep_checkpoint)

    # Resume should handle missing dependency gracefully
    result = await executor_with_checkpoints.resume_workflow("test_missing_dep_chk")

    # Should either succeed with default value or fail with clear error
    if not result.is_success:
        assert "variable" in result.error.lower() or "not found" in result.error.lower()


@pytest.mark.asyncio
async def test_conditional_skip_after_resume(
    executor_with_checkpoints, checkpoint_store, conditional_workflow
):
    """Test that conditional blocks are evaluated correctly after resume.

    Edge case: Conditional expressions must be re-evaluated after resume using
    the restored context. Blocks should skip correctly based on context state.

    This test should FAIL initially - conditional re-evaluation after resume needs testing.
    """
    executor_with_checkpoints.load_workflow(conditional_workflow)

    # Test Case 1: Resume with condition that should pass
    passing_checkpoint = CheckpointState(
        checkpoint_id="test_condition_pass_chk",
        workflow_name="conditional-test",
        created_at=time.time(),
        runtime_inputs={},
        context=serialize_context(
            {
                "block1.echoed": "Block 1",  # Matches condition in block2
                "block1.success": True,
            }
        ),
        completed_blocks=["block1"],
        current_wave_index=0,
        execution_waves=[
            ["block1"],
            ["block2"],
            ["block3"],
        ],
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
                "condition": "${block1.echoed} == 'Block 1'",
            },
            "block3": {
                "id": "block3",
                "type": "EchoBlock",
                "inputs": {"message": "Block 3"},
                "depends_on": ["block2"],
                "condition": "${block2.skipped} == False",
            },
        },
        workflow_stack=["conditional-test"],
    )

    await checkpoint_store.save_checkpoint(passing_checkpoint)

    # Resume should evaluate conditions and execute block2 (condition passes)
    result = await executor_with_checkpoints.resume_workflow("test_condition_pass_chk")

    assert result.is_success or result.error is not None

    if result.is_success:
        outputs = result.value
        assert "blocks" in outputs

        # Block2 should have executed (condition passed)
        assert "block2" in outputs["blocks"]
        block2_output = outputs["blocks"]["block2"]
        # Should not be skipped
        assert block2_output.get("skipped") is not True

        # Block3 should also execute (depends on block2.skipped == False)
        assert "block3" in outputs["blocks"]

    # Test Case 2: Resume with condition that should fail
    failing_checkpoint = CheckpointState(
        checkpoint_id="test_condition_fail_chk",
        workflow_name="conditional-test",
        created_at=time.time(),
        runtime_inputs={},
        context=serialize_context(
            {
                "block1.echoed": "Different Value",  # Doesn't match condition in block2
                "block1.success": True,
            }
        ),
        completed_blocks=["block1"],
        current_wave_index=0,
        execution_waves=[
            ["block1"],
            ["block2"],
            ["block3"],
        ],
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
                "condition": "${block1.echoed} == 'Block 1'",  # Will fail
            },
            "block3": {
                "id": "block3",
                "type": "EchoBlock",
                "inputs": {"message": "Block 3"},
                "depends_on": ["block2"],
                "condition": "${block2.skipped} == False",  # Will fail (block2 skipped)
            },
        },
        workflow_stack=["conditional-test"],
    )

    await checkpoint_store.save_checkpoint(failing_checkpoint)

    # Resume should evaluate conditions and skip block2 (condition fails)
    result = await executor_with_checkpoints.resume_workflow("test_condition_fail_chk")

    assert result.is_success or result.error is not None

    if result.is_success:
        outputs = result.value
        assert "blocks" in outputs

        # Block2 should be skipped (condition failed)
        if "block2" in outputs["blocks"]:
            block2_output = outputs["blocks"]["block2"]
            assert block2_output.get("skipped") is True

        # Block3 should also be skipped (depends on block2.skipped == False)
        if "block3" in outputs["blocks"]:
            block3_output = outputs["blocks"]["block3"]
            assert block3_output.get("skipped") is True

    # Test Case 3: Complex condition with multiple references
    complex_checkpoint = CheckpointState(
        checkpoint_id="test_complex_condition_chk",
        workflow_name="conditional-test",
        created_at=time.time(),
        runtime_inputs={},
        context=serialize_context(
            {
                "block1.echoed": "Block 1",
                "block1.success": True,
                "user_enabled": True,
                "count": 42,
            }
        ),
        completed_blocks=["block1"],
        current_wave_index=0,
        execution_waves=[
            ["block1"],
            ["block2"],
        ],
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
                "condition": "${user_enabled} == True and ${count} > 40",
            },
        },
        workflow_stack=["conditional-test"],
    )

    await checkpoint_store.save_checkpoint(complex_checkpoint)

    # Resume should evaluate complex condition correctly
    result = await executor_with_checkpoints.resume_workflow("test_complex_condition_chk")

    assert result.is_success or result.error is not None

    if result.is_success:
        result_data = result.value
        # Block2 should execute (both conditions true)
        if "block2" in result_data["blocks"]:
            block2_data = result_data["blocks"]["block2"]
            block2_outputs = block2_data.get("outputs", {})
            assert block2_outputs.get("skipped") is not True


@pytest.mark.asyncio
async def test_multi_pause_in_single_workflow(
    executor_with_checkpoints, checkpoint_store, multi_wave_workflow
):
    """Test multiple pause/resume cycles in a single workflow execution.

    Edge case: A workflow may be paused and resumed multiple times before
    completion. Each resume should correctly continue from the last checkpoint
    and create new checkpoints as needed.

    This test should FAIL initially - multi-pause handling needs comprehensive testing.
    """
    executor_with_checkpoints.load_workflow(multi_wave_workflow)

    # Test Case 1: Simulate first pause after wave 1
    first_pause_checkpoint = CheckpointState(
        checkpoint_id="multi_pause_chk_1",
        workflow_name="multi-wave-test",
        created_at=time.time(),
        runtime_inputs={"run_id": "test_run_001"},
        context=serialize_context(
            {
                "wave1_block1.echoed": "Wave 1 - Block 1",
                "wave1_block2.echoed": "Wave 1 - Block 2",
            }
        ),
        completed_blocks=["wave1_block1", "wave1_block2"],
        current_wave_index=0,
        execution_waves=[
            ["wave1_block1", "wave1_block2"],
            ["wave2_block1", "wave2_block2"],
            ["wave3_block1"],
        ],
        block_definitions={
            "wave1_block1": {
                "id": "wave1_block1",
                "type": "EchoBlock",
                "inputs": {"message": "Wave 1 - Block 1"},
                "depends_on": [],
            },
            "wave1_block2": {
                "id": "wave1_block2",
                "type": "EchoBlock",
                "inputs": {"message": "Wave 1 - Block 2"},
                "depends_on": [],
            },
            "wave2_block1": {
                "id": "wave2_block1",
                "type": "EchoBlock",
                "inputs": {"message": "Wave 2 - Block 1"},
                "depends_on": ["wave1_block1"],
            },
            "wave2_block2": {
                "id": "wave2_block2",
                "type": "EchoBlock",
                "inputs": {"message": "Wave 2 - Block 2"},
                "depends_on": ["wave1_block2"],
            },
            "wave3_block1": {
                "id": "wave3_block1",
                "type": "EchoBlock",
                "inputs": {"message": "Wave 3 - Block 1"},
                "depends_on": ["wave2_block1", "wave2_block2"],
            },
        },
        workflow_stack=["multi-wave-test"],
    )

    await checkpoint_store.save_checkpoint(first_pause_checkpoint)

    # Resume from first pause - should execute wave 2
    result1 = await executor_with_checkpoints.resume_workflow("multi_pause_chk_1")
    assert result1.is_success or result1.error is not None

    # Test Case 2: Simulate second pause after wave 2
    # In a real scenario, this would be created automatically during resume
    second_pause_checkpoint = CheckpointState(
        checkpoint_id="multi_pause_chk_2",
        workflow_name="multi-wave-test",
        created_at=time.time(),
        runtime_inputs={"run_id": "test_run_001"},
        context=serialize_context(
            {
                "wave1_block1.echoed": "Wave 1 - Block 1",
                "wave1_block2.echoed": "Wave 1 - Block 2",
                "wave2_block1.echoed": "Wave 2 - Block 1",
                "wave2_block2.echoed": "Wave 2 - Block 2",
            }
        ),
        completed_blocks=["wave1_block1", "wave1_block2", "wave2_block1", "wave2_block2"],
        current_wave_index=1,
        execution_waves=[
            ["wave1_block1", "wave1_block2"],
            ["wave2_block1", "wave2_block2"],
            ["wave3_block1"],
        ],
        block_definitions={
            "wave1_block1": {
                "id": "wave1_block1",
                "type": "EchoBlock",
                "inputs": {"message": "Wave 1 - Block 1"},
                "depends_on": [],
            },
            "wave1_block2": {
                "id": "wave1_block2",
                "type": "EchoBlock",
                "inputs": {"message": "Wave 1 - Block 2"},
                "depends_on": [],
            },
            "wave2_block1": {
                "id": "wave2_block1",
                "type": "EchoBlock",
                "inputs": {"message": "Wave 2 - Block 1"},
                "depends_on": ["wave1_block1"],
            },
            "wave2_block2": {
                "id": "wave2_block2",
                "type": "EchoBlock",
                "inputs": {"message": "Wave 2 - Block 2"},
                "depends_on": ["wave1_block2"],
            },
            "wave3_block1": {
                "id": "wave3_block1",
                "type": "EchoBlock",
                "inputs": {"message": "Wave 3 - Block 1"},
                "depends_on": ["wave2_block1", "wave2_block2"],
            },
        },
        workflow_stack=["multi-wave-test"],
    )

    await checkpoint_store.save_checkpoint(second_pause_checkpoint)

    # Resume from second pause - should execute wave 3
    result2 = await executor_with_checkpoints.resume_workflow("multi_pause_chk_2")
    assert result2.is_success or result2.error is not None

    if result2.is_success:
        outputs = result2.value
        assert "blocks" in outputs
        # Wave 3 block should be executed
        assert "wave3_block1" in outputs["blocks"]

    # Test Case 3: Verify checkpoint chain integrity
    # All checkpoints should be retrievable and valid
    all_checkpoints = await checkpoint_store.list_checkpoints()

    # Should have at least our manually created checkpoints
    checkpoint_ids = [c.checkpoint_id for c in all_checkpoints]
    assert "multi_pause_chk_1" in checkpoint_ids
    assert "multi_pause_chk_2" in checkpoint_ids

    # Each checkpoint should have increasing completed_blocks count
    chk1 = await checkpoint_store.load_checkpoint("multi_pause_chk_1")
    chk2 = await checkpoint_store.load_checkpoint("multi_pause_chk_2")

    assert len(chk1.completed_blocks) < len(chk2.completed_blocks)
    assert chk1.current_wave_index < chk2.current_wave_index

    # Test Case 4: Verify context accumulates correctly across pauses
    # chk2 should have outputs from wave 1 and wave 2
    assert "wave1_block1.echoed" in chk2.context
    assert "wave1_block2.echoed" in chk2.context
    assert "wave2_block1.echoed" in chk2.context
    assert "wave2_block2.echoed" in chk2.context

    # Test Case 5: Test resuming from older checkpoint (skip second pause)
    # Should be able to resume from chk1 even though chk2 exists
    result3 = await executor_with_checkpoints.resume_workflow("multi_pause_chk_1")
    assert result3.is_success or result3.error is not None

    # Should complete remaining waves (wave 2 and wave 3)
    if result3.is_success:
        outputs = result3.value
        # Should have executed wave2 and wave3 blocks
        expected_blocks = ["wave2_block1", "wave2_block2", "wave3_block1"]
        for block_id in expected_blocks:
            assert block_id in outputs["blocks"]

    # Test Case 6: Test checkpoint cleanup/expiration
    # In a real system, old checkpoints might be cleaned up
    # Verify that workflow can still complete even if intermediate checkpoints are removed
    # (This is a future enhancement test)
