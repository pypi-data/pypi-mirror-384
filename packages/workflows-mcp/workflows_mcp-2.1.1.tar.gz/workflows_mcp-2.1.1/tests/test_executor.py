"""Tests for WorkflowExecutor orchestration and execution logic.

Tests the complete workflow execution lifecycle including:
- Basic workflow execution
- Variable resolution (inputs, blocks, metadata)
- Conditional execution (skip blocks based on conditions)
- Workflow composition (ExecuteWorkflow blocks)
- Checkpoint and resume functionality
- Parallel execution (wave-based)
"""

import pytest

from workflows_mcp.engine.executor import WorkflowDefinition


class TestBasicExecution:
    """Tests for basic workflow execution."""

    @pytest.mark.asyncio
    async def test_execute_single_block_workflow(self, executor):
        """Test execution of workflow with single block."""
        workflow_def = WorkflowDefinition(
            name="test-single-block",
            description="Single block test",
            blocks=[{"id": "echo1", "type": "EchoBlock", "inputs": {"message": "Hello World"}}],
        )

        executor.load_workflow(workflow_def)
        response = await executor.execute_workflow("test-single-block")

        assert response.status == "success"
        assert "echo1" in response.blocks
        assert response.blocks["echo1"]["outputs"]["echoed"] == "Echo: Hello World"

    @pytest.mark.asyncio
    async def test_execute_multi_block_linear_workflow(self, executor):
        """Test execution of workflow with linear dependencies: A → B → C."""
        workflow_def = WorkflowDefinition(
            name="test-linear",
            description="Linear dependency test",
            blocks=[
                {"id": "block1", "type": "EchoBlock", "inputs": {"message": "First"}},
                {
                    "id": "block2",
                    "type": "EchoBlock",
                    "inputs": {"message": "Second"},
                    "depends_on": ["block1"],
                },
                {
                    "id": "block3",
                    "type": "EchoBlock",
                    "inputs": {"message": "Third"},
                    "depends_on": ["block2"],
                },
            ],
        )

        executor.load_workflow(workflow_def)
        response = await executor.execute_workflow("test-linear")

        assert response.status == "success"
        assert len(response.blocks) == 3
        # Verify execution order via metadata
        assert response.blocks["block1"]["metadata"]["execution_order"] == 0
        assert response.blocks["block2"]["metadata"]["execution_order"] == 1
        assert response.blocks["block3"]["metadata"]["execution_order"] == 2

    @pytest.mark.asyncio
    async def test_execute_parallel_blocks(self, executor):
        """Test execution of independent blocks in parallel."""
        workflow_def = WorkflowDefinition(
            name="test-parallel",
            description="Parallel execution test",
            blocks=[
                {"id": "block1", "type": "EchoBlock", "inputs": {"message": "Parallel 1"}},
                {"id": "block2", "type": "EchoBlock", "inputs": {"message": "Parallel 2"}},
                {"id": "block3", "type": "EchoBlock", "inputs": {"message": "Parallel 3"}},
            ],
        )

        executor.load_workflow(workflow_def)
        response = await executor.execute_workflow("test-parallel")

        assert response.status == "success"
        assert len(response.blocks) == 3
        # All blocks should be in wave 0 (execution_order can be any within same wave)
        assert response.blocks["block1"]["metadata"]["wave"] == 0
        assert response.blocks["block2"]["metadata"]["wave"] == 0
        assert response.blocks["block3"]["metadata"]["wave"] == 0

    @pytest.mark.asyncio
    async def test_execute_diamond_pattern(self, executor):
        """Test execution of diamond pattern: A → B,C → D."""
        workflow_def = WorkflowDefinition(
            name="test-diamond",
            description="Diamond pattern test",
            blocks=[
                {"id": "start", "type": "EchoBlock", "inputs": {"message": "Start"}},
                {
                    "id": "branch1",
                    "type": "EchoBlock",
                    "inputs": {"message": "Branch 1"},
                    "depends_on": ["start"],
                },
                {
                    "id": "branch2",
                    "type": "EchoBlock",
                    "inputs": {"message": "Branch 2"},
                    "depends_on": ["start"],
                },
                {
                    "id": "end",
                    "type": "EchoBlock",
                    "inputs": {"message": "End"},
                    "depends_on": ["branch1", "branch2"],
                },
            ],
        )

        executor.load_workflow(workflow_def)
        response = await executor.execute_workflow("test-diamond")

        assert response.status == "success"
        assert len(response.blocks) == 4
        # Verify wave structure
        assert response.blocks["start"]["metadata"]["wave"] == 0
        assert response.blocks["branch1"]["metadata"]["wave"] == 1
        assert response.blocks["branch2"]["metadata"]["wave"] == 1
        assert response.blocks["end"]["metadata"]["wave"] == 2

    @pytest.mark.asyncio
    async def test_execute_workflow_not_found(self, executor):
        """Test error when workflow not found."""
        response = await executor.execute_workflow("non-existent-workflow")

        assert response.status == "failure"
        assert "not found" in response.error.lower()

    @pytest.mark.asyncio
    async def test_execute_workflow_with_runtime_inputs(self, executor):
        """Test workflow execution with runtime inputs."""
        workflow_def = WorkflowDefinition(
            name="test-inputs",
            description="Runtime inputs test",
            blocks=[
                {
                    "id": "echo",
                    "type": "EchoBlock",
                    "inputs": {"message": "${inputs.user_message}"},
                }
            ],
            inputs={"user_message": {"type": "string", "default": "Default message"}},
        )

        executor.load_workflow(workflow_def)
        response = await executor.execute_workflow(
            "test-inputs", runtime_inputs={"user_message": "Custom message"}
        )

        assert response.status == "success"
        assert response.blocks["echo"]["outputs"]["echoed"] == "Echo: Custom message"


class TestVariableResolution:
    """Tests for variable resolution system."""

    @pytest.mark.asyncio
    async def test_resolve_inputs_namespace(self, executor):
        """Test ${inputs.field} variable resolution."""
        workflow_def = WorkflowDefinition(
            name="test-inputs-vars",
            description="Inputs variable resolution",
            blocks=[
                {
                    "id": "echo",
                    "type": "EchoBlock",
                    "inputs": {"message": "${inputs.project_name} - ${inputs.version}"},
                }
            ],
            inputs={
                "project_name": {"type": "string", "default": "TestProject"},
                "version": {"type": "string", "default": "1.0.0"},
            },
        )

        executor.load_workflow(workflow_def)
        response = await executor.execute_workflow("test-inputs-vars")

        assert response.status == "success"
        assert response.blocks["echo"]["outputs"]["echoed"] == "Echo: TestProject - 1.0.0"

    @pytest.mark.asyncio
    async def test_resolve_blocks_outputs_namespace(self, executor):
        """Test ${blocks.block_id.outputs.field} variable resolution."""
        workflow_def = WorkflowDefinition(
            name="test-blocks-vars",
            description="Blocks output variable resolution",
            blocks=[
                {"id": "block1", "type": "EchoBlock", "inputs": {"message": "First"}},
                {
                    "id": "block2",
                    "type": "EchoBlock",
                    "inputs": {"message": "${blocks.block1.outputs.echoed}"},
                    "depends_on": ["block1"],
                },
            ],
        )

        executor.load_workflow(workflow_def)
        response = await executor.execute_workflow("test-blocks-vars")

        assert response.status == "success"
        assert response.blocks["block2"]["outputs"]["echoed"] == "Echo: Echo: First"

    @pytest.mark.asyncio
    async def test_resolve_blocks_metadata_namespace(self, executor):
        """Test ${blocks.block_id.metadata.field} variable resolution."""
        workflow_def = WorkflowDefinition(
            name="test-blocks-metadata",
            description="Blocks metadata variable resolution",
            blocks=[
                {"id": "block1", "type": "EchoBlock", "inputs": {"message": "Test"}},
                {
                    "id": "block2",
                    "type": "EchoBlock",
                    "inputs": {"message": "Wave ${blocks.block1.metadata.wave} completed"},
                    "depends_on": ["block1"],
                },
            ],
        )

        executor.load_workflow(workflow_def)
        response = await executor.execute_workflow("test-blocks-metadata")

        assert response.status == "success"
        assert "Wave 0 completed" in response.blocks["block2"]["outputs"]["echoed"]

    @pytest.mark.asyncio
    async def test_resolve_metadata_namespace(self, executor):
        """Test ${metadata.field} variable resolution."""
        workflow_def = WorkflowDefinition(
            name="test-metadata",
            description="Metadata variable resolution",
            blocks=[
                {
                    "id": "echo",
                    "type": "EchoBlock",
                    "inputs": {"message": "Workflow: ${metadata.workflow_name}"},
                }
            ],
        )

        executor.load_workflow(workflow_def)
        response = await executor.execute_workflow("test-metadata")

        assert response.status == "success"
        assert "Workflow: test-metadata" in response.blocks["echo"]["outputs"]["echoed"]

    @pytest.mark.asyncio
    async def test_nested_variable_resolution(self, executor):
        """Test nested variable references across multiple blocks."""
        workflow_def = WorkflowDefinition(
            name="test-nested",
            description="Nested variable resolution",
            blocks=[
                {"id": "block1", "type": "EchoBlock", "inputs": {"message": "Level 1"}},
                {
                    "id": "block2",
                    "type": "EchoBlock",
                    "inputs": {"message": "${blocks.block1.outputs.echoed}"},
                    "depends_on": ["block1"],
                },
                {
                    "id": "block3",
                    "type": "EchoBlock",
                    "inputs": {"message": "${blocks.block2.outputs.echoed}"},
                    "depends_on": ["block2"],
                },
            ],
        )

        executor.load_workflow(workflow_def)
        response = await executor.execute_workflow("test-nested")

        assert response.status == "success"
        # Should be: "Echo: Echo: Echo: Level 1"
        assert response.blocks["block3"]["outputs"]["echoed"].count("Echo:") == 3


class TestConditionalExecution:
    """Tests for conditional block execution."""

    @pytest.mark.asyncio
    async def test_skip_block_when_condition_false(self, executor):
        """Test block is skipped when condition evaluates to false."""
        workflow_def = WorkflowDefinition(
            name="test-condition-skip",
            description="Conditional skip test",
            blocks=[
                {"id": "block1", "type": "EchoBlock", "inputs": {"message": "Always run"}},
                {
                    "id": "block2",
                    "type": "EchoBlock",
                    "inputs": {"message": "Should skip"},
                    "condition": "False",  # Always false
                    "depends_on": ["block1"],
                },
                {
                    "id": "block3",
                    "type": "EchoBlock",
                    "inputs": {"message": "Should run"},
                    "depends_on": ["block2"],
                },
            ],
        )

        executor.load_workflow(workflow_def)
        response = await executor.execute_workflow("test-condition-skip")

        assert response.status == "success"
        # Block 2 should be marked as skipped
        assert response.blocks["block2"]["outputs"]["skipped"] is True
        assert response.blocks["block2"]["metadata"]["status"] == "skipped"
        # Block 3 should still run (downstream blocks continue after skip)
        assert response.blocks["block3"]["outputs"]["echoed"] == "Echo: Should run"

    @pytest.mark.asyncio
    async def test_execute_block_when_condition_true(self, executor):
        """Test block executes when condition evaluates to true."""
        workflow_def = WorkflowDefinition(
            name="test-condition-execute",
            description="Conditional execute test",
            blocks=[
                {
                    "id": "block1",
                    "type": "EchoBlock",
                    "inputs": {"message": "Should run"},
                    "condition": "True",  # Always true
                }
            ],
        )

        executor.load_workflow(workflow_def)
        response = await executor.execute_workflow("test-condition-execute")

        assert response.status == "success"
        assert response.blocks["block1"]["outputs"]["echoed"] == "Echo: Should run"
        assert response.blocks["block1"]["outputs"].get("skipped", False) is False

    @pytest.mark.asyncio
    async def test_condition_with_workflow_input(self, executor):
        """Test condition with variable reference from workflow inputs."""
        workflow_def = WorkflowDefinition(
            name="test-condition-input",
            description="Conditional with input variable",
            blocks=[
                {
                    "id": "block1",
                    "type": "EchoBlock",
                    "inputs": {"message": "Conditional execution"},
                    # Condition references workflow input
                    "condition": "${inputs.should_run}",
                },
            ],
            inputs={"should_run": {"type": "bool", "default": True}},
        )

        executor.load_workflow(workflow_def)
        response = await executor.execute_workflow("test-condition-input")

        assert response.status == "success"
        # Block should execute because condition is True
        assert response.blocks["block1"]["outputs"]["echoed"] == "Echo: Conditional execution"

    @pytest.mark.asyncio
    async def test_invalid_condition_expression(self, executor):
        """Test error when condition expression is invalid."""
        workflow_def = WorkflowDefinition(
            name="test-invalid-condition",
            description="Invalid condition test",
            blocks=[
                {
                    "id": "block1",
                    "type": "EchoBlock",
                    "inputs": {"message": "Test"},
                    "condition": "invalid python expression !!!",
                }
            ],
        )

        executor.load_workflow(workflow_def)
        response = await executor.execute_workflow("test-invalid-condition")

        assert response.status == "failure"
        assert "condition" in response.error.lower()


class TestWorkflowOutputs:
    """Tests for workflow-level output declarations."""

    @pytest.mark.asyncio
    async def test_workflow_outputs_from_blocks(self, executor):
        """Test workflow outputs reference block outputs."""
        workflow_def = WorkflowDefinition(
            name="test-outputs",
            description="Workflow outputs test",
            blocks=[
                {"id": "block1", "type": "EchoBlock", "inputs": {"message": "Result 1"}},
                {"id": "block2", "type": "EchoBlock", "inputs": {"message": "Result 2"}},
            ],
            outputs={
                "first_result": "${blocks.block1.outputs.echoed}",
                "second_result": "${blocks.block2.outputs.echoed}",
            },
        )

        executor.load_workflow(workflow_def)
        response = await executor.execute_workflow("test-outputs")

        assert response.status == "success"
        assert response.outputs["first_result"] == "Echo: Result 1"
        assert response.outputs["second_result"] == "Echo: Result 2"

    @pytest.mark.asyncio
    async def test_workflow_outputs_from_inputs(self, executor):
        """Test workflow outputs reference workflow inputs."""
        workflow_def = WorkflowDefinition(
            name="test-outputs-inputs",
            description="Workflow outputs from inputs",
            blocks=[{"id": "echo", "type": "EchoBlock", "inputs": {"message": "Test"}}],
            inputs={"project_name": {"type": "string", "default": "MyProject"}},
            outputs={"project": "${inputs.project_name}"},
        )

        executor.load_workflow(workflow_def)
        response = await executor.execute_workflow("test-outputs-inputs")

        assert response.status == "success"
        assert response.outputs["project"] == "MyProject"


class TestErrorHandling:
    """Tests for error handling and failure scenarios."""

    @pytest.mark.asyncio
    async def test_missing_dependency_block(self, executor):
        """Test error when block depends on non-existent block."""
        workflow_def = WorkflowDefinition(
            name="test-missing-dep",
            description="Missing dependency test",
            blocks=[
                {
                    "id": "block1",
                    "type": "EchoBlock",
                    "inputs": {"message": "Test"},
                    "depends_on": ["non_existent_block"],
                }
            ],
        )

        executor.load_workflow(workflow_def)
        response = await executor.execute_workflow("test-missing-dep")

        assert response.status == "failure"
        assert "not found" in response.error.lower()

    @pytest.mark.asyncio
    async def test_cyclic_dependency_detection(self, executor):
        """Test detection of cyclic dependencies."""
        workflow_def = WorkflowDefinition(
            name="test-cycle",
            description="Cyclic dependency test",
            blocks=[
                {
                    "id": "block1",
                    "type": "EchoBlock",
                    "inputs": {"message": "A"},
                    "depends_on": ["block2"],
                },
                {
                    "id": "block2",
                    "type": "EchoBlock",
                    "inputs": {"message": "B"},
                    "depends_on": ["block1"],
                },
            ],
        )

        executor.load_workflow(workflow_def)
        response = await executor.execute_workflow("test-cycle")

        assert response.status == "failure"
        assert "cyclic" in response.error.lower()

    @pytest.mark.asyncio
    async def test_invalid_block_type(self, executor):
        """Test error when block type is not registered."""
        workflow_def = WorkflowDefinition(
            name="test-invalid-type",
            description="Invalid block type test",
            blocks=[
                {"id": "block1", "type": "NonExistentBlockType", "inputs": {"message": "Test"}}
            ],
        )

        executor.load_workflow(workflow_def)
        response = await executor.execute_workflow("test-invalid-type")

        assert response.status == "failure"
        # Should mention block type not found
        assert "NonExistentBlockType" in response.error or "not found" in response.error.lower()

    @pytest.mark.asyncio
    async def test_missing_required_variable(self, executor):
        """Test error when required variable is missing."""
        workflow_def = WorkflowDefinition(
            name="test-missing-var",
            description="Missing variable test",
            blocks=[
                {
                    "id": "block1",
                    "type": "EchoBlock",
                    # Reference non-existent input
                    "inputs": {"message": "${inputs.non_existent_field}"},
                }
            ],
        )

        executor.load_workflow(workflow_def)
        response = await executor.execute_workflow("test-missing-var")

        assert response.status == "failure"
        # Should mention variable resolution failure
        assert "variable" in response.error.lower() or "non_existent_field" in response.error


class TestMetadata:
    """Tests for workflow execution metadata."""

    @pytest.mark.asyncio
    async def test_metadata_includes_execution_time(self, executor):
        """Test metadata includes execution time."""
        workflow_def = WorkflowDefinition(
            name="test-metadata-time",
            description="Metadata timing test",
            blocks=[{"id": "echo", "type": "EchoBlock", "inputs": {"message": "Test"}}],
        )

        executor.load_workflow(workflow_def)
        response = await executor.execute_workflow("test-metadata-time")

        assert response.status == "success"
        assert "execution_time_seconds" in response.metadata
        assert response.metadata["execution_time_seconds"] >= 0

    @pytest.mark.asyncio
    async def test_metadata_includes_workflow_name(self, executor):
        """Test metadata includes workflow name."""
        workflow_def = WorkflowDefinition(
            name="test-metadata-name",
            description="Metadata name test",
            blocks=[{"id": "echo", "type": "EchoBlock", "inputs": {"message": "Test"}}],
        )

        executor.load_workflow(workflow_def)
        response = await executor.execute_workflow("test-metadata-name")

        assert response.status == "success"
        assert response.metadata["workflow_name"] == "test-metadata-name"

    @pytest.mark.asyncio
    async def test_block_metadata_includes_wave_and_order(self, executor):
        """Test block metadata includes wave and execution order."""
        workflow_def = WorkflowDefinition(
            name="test-block-metadata",
            description="Block metadata test",
            blocks=[
                {"id": "block1", "type": "EchoBlock", "inputs": {"message": "First"}},
                {
                    "id": "block2",
                    "type": "EchoBlock",
                    "inputs": {"message": "Second"},
                    "depends_on": ["block1"],
                },
            ],
        )

        executor.load_workflow(workflow_def)
        response = await executor.execute_workflow("test-block-metadata")

        assert response.status == "success"
        # Block 1 metadata
        assert response.blocks["block1"]["metadata"]["wave"] == 0
        assert response.blocks["block1"]["metadata"]["execution_order"] == 0
        assert response.blocks["block1"]["metadata"]["status"] == "success"
        # Block 2 metadata
        assert response.blocks["block2"]["metadata"]["wave"] == 1
        assert response.blocks["block2"]["metadata"]["execution_order"] == 1
        assert response.blocks["block2"]["metadata"]["status"] == "success"
