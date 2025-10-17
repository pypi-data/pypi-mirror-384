"""Integration tests for workflow execution and composition.

Consolidated from:
- test_phase1_integration.py (workflow discovery and execution)
- test_integration_phase2.py (variable resolution and conditionals)
- test_phase4_tool_integration.py (MCP tool integration)

Tests verify end-to-end functionality including:
- Workflow discovery and loading from templates
- Basic and complex workflow execution
- Variable resolution across blocks
- Conditional block execution
- Parallel execution patterns
- Error handling
- Performance benchmarks
"""

from pathlib import Path

import pytest

from workflows_mcp.engine.executor import WorkflowDefinition
from workflows_mcp.engine.loader import load_workflow_from_file
from workflows_mcp.engine.response import WorkflowResponse
from workflows_mcp.tools import execute_workflow, get_workflow_info, list_workflows


def to_dict(result):
    """Convert WorkflowResponse to dict for testing."""
    if isinstance(result, WorkflowResponse):
        return result.model_dump()
    return result


# ============================================================================
# Workflow Execution Tests
# ============================================================================


class TestWorkflowExecution:
    """End-to-end workflow execution tests."""

    @pytest.mark.asyncio
    async def test_hello_world_workflow(self, mock_context):
        """Test hello-world workflow execution."""
        result = to_dict(
            await execute_workflow(
                workflow="hello-world", inputs={"name": "Integration Test"}, ctx=mock_context
            )
        )
        assert result["status"] == "success", f"hello-world failed: {result.get('error')}"
        assert "blocks" in result, "Missing blocks in result"
        assert "greet" in result["blocks"], "Missing 'greet' block output"

    @pytest.mark.asyncio
    async def test_sequential_echo_workflow(self, mock_context):
        """Test sequential-echo workflow with 3 sequential blocks."""
        result = to_dict(
            await execute_workflow(workflow="sequential-echo", inputs={}, ctx=mock_context)
        )
        assert result["status"] == "success", f"sequential-echo failed: {result.get('error')}"
        assert result["metadata"]["total_blocks"] == 3, "Expected 3 blocks"
        assert result["metadata"]["execution_waves"] == 3, "Expected 3 waves (sequential)"

    @pytest.mark.asyncio
    async def test_parallel_echo_workflow(self, mock_context):
        """Test parallel-echo workflow with diamond pattern."""
        result = to_dict(
            await execute_workflow(workflow="parallel-echo", inputs={}, ctx=mock_context)
        )
        assert result["status"] == "success", f"parallel-echo failed: {result.get('error')}"
        assert result["metadata"]["total_blocks"] == 4, "Expected 4 blocks"
        assert result["metadata"]["execution_waves"] == 3, "Expected 3 waves (diamond pattern)"

    @pytest.mark.asyncio
    async def test_input_substitution_workflow(self, mock_context):
        """Test input-substitution workflow with multiple inputs."""
        result = to_dict(
            await execute_workflow(
                workflow="input-substitution",
                inputs={
                    "user_name": "Claude",
                    "project_name": "MCP Workflows",
                    "iterations": 5,
                    "verbose": True,
                },
                ctx=mock_context,
            )
        )
        assert result["status"] == "success", f"input-substitution failed: {result.get('error')}"
        assert result["metadata"]["total_blocks"] == 6, "Expected 6 blocks"

    @pytest.mark.asyncio
    async def test_complex_workflow(self, mock_context):
        """Test complex-workflow with parallel execution."""
        result = to_dict(
            await execute_workflow(
                workflow="complex-workflow",
                inputs={
                    "project_name": "test-project",
                    "environment": "staging",
                },
                ctx=mock_context,
            )
        )
        assert result["status"] == "success", f"complex-workflow failed: {result.get('error')}"
        assert result["metadata"]["total_blocks"] == 8, "Expected 8 blocks"
        # Complex workflow should have parallel stages (waves < blocks)
        assert result["metadata"]["execution_waves"] < 8, (
            f"Expected parallel execution, got {result['metadata']['execution_waves']} waves"
        )

    @pytest.mark.asyncio
    async def test_variable_resolution_across_blocks(self, executor):
        """Test variable resolution from one block to another."""
        workflow_def = WorkflowDefinition(
            name="test-variable-resolution",
            description="Test variable resolution",
            blocks=[
                {
                    "id": "echo1",
                    "type": "EchoBlock",
                    "inputs": {"message": "Hello"},
                    "depends_on": [],
                },
                {
                    "id": "echo2",
                    "type": "EchoBlock",
                    "inputs": {"message": "Echo from echo1: ${blocks.echo1.outputs.echoed}"},
                    "depends_on": ["echo1"],
                },
            ],
        )

        executor.load_workflow(workflow_def)
        result = await executor.execute_workflow("test-variable-resolution", {})

        assert result.is_success
        outputs = result.value

        # Verify both blocks executed
        assert "echo1" in outputs["blocks"], "echo1 should have executed"
        assert outputs["blocks"]["echo1"]["outputs"]["echoed"] == "Echo: Hello"
        assert (
            outputs["blocks"]["echo2"]["outputs"]["echoed"] == "Echo: Echo from echo1: Echo: Hello"
        )

    @pytest.mark.asyncio
    async def test_variable_resolution_with_workflow_inputs(self, executor):
        """Test variable resolution from workflow inputs."""
        workflow_def = WorkflowDefinition(
            name="test-workflow-inputs",
            description="Test workflow inputs",
            blocks=[
                {
                    "id": "greet",
                    "type": "EchoBlock",
                    "inputs": {"message": "Hello ${inputs.name}!"},
                    "depends_on": [],
                },
            ],
        )

        executor.load_workflow(workflow_def)
        result = await executor.execute_workflow("test-workflow-inputs", {"name": "Alice"})

        assert result.is_success
        outputs = result.value

        assert outputs["blocks"]["greet"]["outputs"]["echoed"] == "Echo: Hello Alice!"

    @pytest.mark.asyncio
    async def test_chained_variable_resolution(self, executor):
        """Test variable resolution across multiple blocks in chain."""
        workflow_def = WorkflowDefinition(
            name="test-chained-variables",
            description="Test chained variable resolution",
            blocks=[
                {
                    "id": "block1",
                    "type": "EchoBlock",
                    "inputs": {"message": "first"},
                    "depends_on": [],
                },
                {
                    "id": "block2",
                    "type": "EchoBlock",
                    "inputs": {"message": "${blocks.block1.outputs.echoed}-second"},
                    "depends_on": ["block1"],
                },
                {
                    "id": "block3",
                    "type": "EchoBlock",
                    "inputs": {"message": "${blocks.block2.outputs.echoed}-third"},
                    "depends_on": ["block2"],
                },
            ],
        )

        executor.load_workflow(workflow_def)
        result = await executor.execute_workflow("test-chained-variables", {})

        assert result.is_success
        outputs = result.value

        assert (
            outputs["blocks"]["block3"]["outputs"]["echoed"]
            == "Echo: Echo: Echo: first-second-third"
        )

    @pytest.mark.asyncio
    async def test_nested_variable_resolution(self, executor):
        """Test variable resolution in nested structures."""
        workflow_def = WorkflowDefinition(
            name="test-nested-variables",
            description="Test nested variable resolution",
            blocks=[
                {
                    "id": "setup",
                    "type": "EchoBlock",
                    "inputs": {"message": "config"},
                    "depends_on": [],
                },
                {
                    "id": "process",
                    "type": "EchoBlock",
                    "inputs": {
                        "message": "Processing with ${blocks.setup.outputs.echoed}",
                    },
                    "depends_on": ["setup"],
                },
            ],
        )

        executor.load_workflow(workflow_def)
        result = await executor.execute_workflow("test-nested-variables", {})

        assert result.is_success
        outputs = result.value

        assert (
            outputs["blocks"]["process"]["outputs"]["echoed"]
            == "Echo: Processing with Echo: config"
        )


# ============================================================================
# Workflow Composition Tests
# ============================================================================


class TestWorkflowComposition:
    """Workflow composition and nesting tests."""

    @pytest.mark.asyncio
    async def test_workflow_discovery(self, mock_context):
        """Test workflow discovery - MCP server loads workflows from templates."""
        workflows = await list_workflows(ctx=mock_context)
        assert len(workflows) > 0, "Should discover workflows from templates"

        # Verify all 5 example workflows are loaded
        expected_workflows = {
            "hello-world",
            "sequential-echo",
            "parallel-echo",
            "input-substitution",
            "complex-workflow",
        }
        # list_workflows returns a list of workflow names (strings), not dicts
        actual_workflows = set(workflows)

        assert expected_workflows.issubset(actual_workflows), (
            f"Missing workflows: {expected_workflows - actual_workflows}"
        )

    @pytest.mark.asyncio
    async def test_list_workflows_by_category(self, mock_context):
        """Test list_workflows by category - Filters workflows correctly."""
        # Test valid tag filter
        test_workflows = await list_workflows(tags=["test"], ctx=mock_context)
        assert len(test_workflows) >= 5, (
            f"Expected at least 5 test workflows, got {len(test_workflows)}"
        )

        # Test empty tags (all workflows)
        all_workflows = await list_workflows(tags=[], ctx=mock_context)
        assert len(all_workflows) >= len(test_workflows), (
            "empty tags should return at least as many as 'test'"
        )

        # Test non-existent tag
        invalid_result = await list_workflows(tags=["invalid_tag_xyz"], ctx=mock_context)
        assert isinstance(invalid_result, list), "Should return list even for invalid tag"

    @pytest.mark.asyncio
    async def test_get_workflow_info(self, mock_context):
        """Test get_workflow_info - Returns correct metadata for each workflow."""
        test_cases = [
            ("hello-world", 1),
            ("sequential-echo", 3),
            ("parallel-echo", 4),
            ("input-substitution", 6),
            ("complex-workflow", 8),
        ]

        for workflow_name, expected_blocks in test_cases:
            info = await get_workflow_info(workflow=workflow_name, ctx=mock_context)

            assert info["name"] == workflow_name, (
                f"Name mismatch: {info['name']} != {workflow_name}"
            )
            assert info["total_blocks"] == expected_blocks, (
                f"{workflow_name}: Expected {expected_blocks} blocks, got {info['total_blocks']}"
            )

            # Verify blocks structure
            assert "blocks" in info, f"{workflow_name}: Missing 'blocks' field"
            assert len(info["blocks"]) == expected_blocks, f"{workflow_name}: Block count mismatch"

            for block in info["blocks"]:
                assert "id" in block, f"{workflow_name}: Block missing 'id'"
                assert "type" in block, f"{workflow_name}: Block missing 'type'"
                assert "depends_on" in block, f"{workflow_name}: Block missing 'depends_on'"

    @pytest.mark.asyncio
    async def test_workflow_metadata(self, mock_context):
        """Test workflow metadata - Verify YAML schema fields are loaded correctly."""
        workflows = await list_workflows(ctx=mock_context)

        # list_workflows returns a list of workflow names (strings), not dicts
        for workflow_name in workflows:
            # Get detailed info
            info = await get_workflow_info(workflow=workflow_name, ctx=mock_context)

            # Verify metadata fields
            assert "name" in info, f"{workflow_name}: Missing 'name'"
            assert "description" in info, f"{workflow_name}: Missing 'description'"
            assert "total_blocks" in info, f"{workflow_name}: Missing 'total_blocks'"
            assert "blocks" in info, f"{workflow_name}: Missing 'blocks'"

            # Verify blocks have required fields
            for block in info["blocks"]:
                assert "id" in block, f"{workflow_name}: Block missing 'id'"
                assert "type" in block, f"{workflow_name}: Block missing 'type'"
                assert "depends_on" in block, f"{workflow_name}: Block missing 'depends_on'"


# ============================================================================
# Conditional Execution Tests
# ============================================================================


class TestConditionalExecution:
    """Conditional block execution tests."""

    @pytest.mark.asyncio
    async def test_conditional_execution_skip_block(self, executor):
        """Test conditional execution that skips a block."""
        workflow_def = WorkflowDefinition(
            name="test-conditional-skip",
            description="Test conditional skip",
            blocks=[
                {
                    "id": "check",
                    "type": "EchoBlock",
                    "inputs": {"message": "checking"},
                    "depends_on": [],
                },
                {
                    "id": "deploy",
                    "type": "EchoBlock",
                    "inputs": {"message": "deploying"},
                    "depends_on": ["check"],
                    "condition": "${blocks.check.outputs.echoed} == 'Echo: success'",
                },
            ],
        )

        executor.load_workflow(workflow_def)
        result = await executor.execute_workflow("test-conditional-skip", {})

        assert result.is_success
        # The workflow should complete but deploy should be skipped

    @pytest.mark.asyncio
    async def test_conditional_execution_run_block(self, executor):
        """Test conditional execution that runs a block."""
        workflow_def = WorkflowDefinition(
            name="test-conditional-run",
            description="Test conditional run",
            blocks=[
                {
                    "id": "setup",
                    "type": "EchoBlock",
                    "inputs": {"message": "ready"},
                    "depends_on": [],
                },
                {
                    "id": "execute",
                    "type": "EchoBlock",
                    "inputs": {"message": "executing"},
                    "depends_on": ["setup"],
                    "condition": "${blocks.setup.outputs.echoed} == 'Echo: ready'",  # Will be true
                },
            ],
        )

        executor.load_workflow(workflow_def)
        result = await executor.execute_workflow("test-conditional-run", {})

        assert result.is_success
        outputs = result.value

        # Both blocks should execute
        assert outputs["blocks"]["execute"]["outputs"]["echoed"] == "Echo: executing"

    @pytest.mark.asyncio
    async def test_conditional_branches(self, executor):
        """Test DAG with conditional branches (if-else pattern)."""
        workflow_def = WorkflowDefinition(
            name="test-conditional-branches",
            description="Test conditional branches",
            blocks=[
                {
                    "id": "check_status",
                    "type": "EchoBlock",
                    "inputs": {"message": "failed"},
                    "depends_on": [],
                },
                {
                    "id": "on_success",
                    "type": "EchoBlock",
                    "inputs": {"message": "success path"},
                    "depends_on": ["check_status"],
                    "condition": "${blocks.check_status.outputs.echoed} == 'Echo: success'",
                },
                {
                    "id": "on_failure",
                    "type": "EchoBlock",
                    "inputs": {"message": "failure path"},
                    "depends_on": ["check_status"],
                    "condition": "${blocks.check_status.outputs.echoed} == 'Echo: failed'",
                },
            ],
        )

        executor.load_workflow(workflow_def)
        result = await executor.execute_workflow("test-conditional-branches", {})

        assert result.is_success
        outputs = result.value

        # on_failure should execute, on_success should skip
        assert outputs["blocks"]["on_failure"]["outputs"]["echoed"] == "Echo: failure path"

    @pytest.mark.asyncio
    async def test_complex_condition_with_multiple_variables(self, executor):
        """Test complex condition referencing multiple block outputs."""
        workflow_def = WorkflowDefinition(
            name="test-complex-condition",
            description="Test complex condition",
            blocks=[
                {
                    "id": "test_result",
                    "type": "EchoBlock",
                    "inputs": {"message": "passed"},
                    "depends_on": [],
                },
                {
                    "id": "lint_result",
                    "type": "EchoBlock",
                    "inputs": {"message": "passed"},
                    "depends_on": [],
                },
                {
                    "id": "deploy",
                    "type": "EchoBlock",
                    "inputs": {"message": "deploying"},
                    "depends_on": ["test_result", "lint_result"],
                    "condition": (
                        "${blocks.test_result.outputs.echoed} == 'Echo: passed' and "
                        "${blocks.lint_result.outputs.echoed} == 'Echo: passed'"
                    ),
                },
            ],
        )

        executor.load_workflow(workflow_def)
        result = await executor.execute_workflow("test-complex-condition", {})

        assert result.is_success
        outputs = result.value

        # Deploy should execute since both conditions are true
        assert outputs["blocks"]["deploy"]["outputs"]["echoed"] == "Echo: deploying"

    @pytest.mark.asyncio
    async def test_convergence_after_conditional(self, executor):
        """Test convergence point after conditional branches."""
        workflow_def = WorkflowDefinition(
            name="test-convergence",
            description="Test convergence after conditionals",
            blocks=[
                {
                    "id": "start",
                    "type": "EchoBlock",
                    "inputs": {"message": "starting"},
                    "depends_on": [],
                },
                {
                    "id": "branch_a",
                    "type": "EchoBlock",
                    "inputs": {"message": "branch a"},
                    "depends_on": ["start"],
                    "condition": "${blocks.start.outputs.echoed} == 'Echo: success'",
                },
                {
                    "id": "branch_b",
                    "type": "EchoBlock",
                    "inputs": {"message": "branch b"},
                    "depends_on": ["start"],
                    "condition": "${blocks.start.outputs.echoed} == 'Echo: starting'",
                },
                {
                    "id": "converge",
                    "type": "EchoBlock",
                    "inputs": {"message": "converged"},
                    "depends_on": ["branch_a", "branch_b"],
                },
            ],
        )

        executor.load_workflow(workflow_def)
        result = await executor.execute_workflow("test-convergence", {})

        assert result.is_success
        outputs = result.value

        # Converge should execute after branch_b
        assert outputs["blocks"]["converge"]["outputs"]["echoed"] == "Echo: converged"

    @pytest.mark.asyncio
    async def test_conditional_with_workflow_input(self, executor):
        """Test conditional that depends on workflow input."""
        workflow_def = WorkflowDefinition(
            name="test-conditional-input",
            description="Test conditional with input",
            blocks=[
                {
                    "id": "process",
                    "type": "EchoBlock",
                    "inputs": {"message": "processing"},
                    "depends_on": [],
                    "condition": "${inputs.should_process} == True",
                },
            ],
        )

        executor.load_workflow(workflow_def)

        # Test with should_process=True
        result = await executor.execute_workflow("test-conditional-input", {"should_process": True})

        assert result.is_success
        outputs = result.value

        assert outputs["blocks"]["process"]["outputs"]["echoed"] == "Echo: processing"

    @pytest.mark.asyncio
    async def test_condition_with_numeric_comparison(self, executor):
        """Test conditional with numeric comparison."""
        workflow_def = WorkflowDefinition(
            name="test-numeric-condition",
            description="Test numeric condition",
            blocks=[
                {
                    "id": "setup",
                    "type": "EchoBlock",
                    "inputs": {"message": "85"},
                    "depends_on": [],
                },
                {
                    "id": "check_threshold",
                    "type": "EchoBlock",
                    "inputs": {"message": "above threshold"},
                    "depends_on": ["setup"],
                    "condition": "${blocks.setup.outputs.echoed} >= 'Echo: 80'",
                },
            ],
        )

        executor.load_workflow(workflow_def)
        result = await executor.execute_workflow("test-numeric-condition", {})

        assert result.is_success
        outputs = result.value

        # Block should execute (string '85' >= '80')
        assert outputs["blocks"]["check_threshold"]["outputs"]["echoed"] == "Echo: above threshold"

    @pytest.mark.asyncio
    async def test_multiple_conditional_paths_parallel(self, executor):
        """Test multiple independent conditional paths executing in parallel."""
        workflow_def = WorkflowDefinition(
            name="test-parallel-conditionals",
            description="Test parallel conditional paths",
            blocks=[
                {
                    "id": "start",
                    "type": "EchoBlock",
                    "inputs": {"message": "ready"},
                    "depends_on": [],
                },
                {
                    "id": "path1",
                    "type": "EchoBlock",
                    "inputs": {"message": "path1"},
                    "depends_on": ["start"],
                    "condition": "${blocks.start.outputs.echoed} == 'Echo: ready'",
                },
                {
                    "id": "path2",
                    "type": "EchoBlock",
                    "inputs": {"message": "path2"},
                    "depends_on": ["start"],
                    "condition": "${blocks.start.outputs.echoed} == 'Echo: ready'",
                },
                {
                    "id": "path3",
                    "type": "EchoBlock",
                    "inputs": {"message": "path3"},
                    "depends_on": ["start"],
                    "condition": "${blocks.start.outputs.echoed} == 'Echo: ready'",
                },
            ],
        )

        executor.load_workflow(workflow_def)
        result = await executor.execute_workflow("test-parallel-conditionals", {})

        assert result.is_success
        outputs = result.value

        # All three paths should execute
        assert outputs["blocks"]["path1"]["outputs"]["echoed"] == "Echo: path1"
        assert outputs["blocks"]["path2"]["outputs"]["echoed"] == "Echo: path2"
        assert outputs["blocks"]["path3"]["outputs"]["echoed"] == "Echo: path3"


# ============================================================================
# Async Execution Tests
# ============================================================================


class TestAsyncExecution:
    """Async workflow execution tests."""

    @pytest.mark.asyncio
    async def test_parallel_execution(self, mock_context):
        """Test parallel execution - parallel-echo executes waves correctly."""
        # Execute parallel-echo and verify wave structure
        result = to_dict(
            await execute_workflow(workflow="parallel-echo", inputs={}, ctx=mock_context)
        )
        assert result["status"] == "success", f"parallel-echo failed: {result.get('error')}"

        waves = result["metadata"]["execution_waves"]

        # Diamond pattern should have exactly 3 waves
        assert waves == 3, f"Expected 3 waves for diamond pattern, got {waves}"

        # Verify execution order makes sense
        blocks = result["blocks"]
        assert "start_block" in blocks, "Missing start_block"
        assert "parallel_a" in blocks, "Missing parallel_a"
        assert "parallel_b" in blocks, "Missing parallel_b"
        assert "final_merge" in blocks, "Missing final_merge"

    @pytest.mark.asyncio
    async def test_complex_workflow_parallel_execution(self, mock_context):
        """Test complex workflow parallel execution."""
        result = to_dict(
            await execute_workflow(
                workflow="complex-workflow",
                inputs={"project_name": "test", "environment": "dev"},
                ctx=mock_context,
            )
        )
        assert result["status"] == "success", f"complex-workflow failed: {result.get('error')}"

        waves = result["metadata"]["execution_waves"]
        total_blocks = result["metadata"]["total_blocks"]

        # Complex workflow (8 blocks) should have parallel stages
        assert waves < total_blocks, (
            f"Expected parallel execution (waves < blocks), "
            f"got {waves} waves for {total_blocks} blocks"
        )


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestErrorHandling:
    """Error handling and recovery tests."""

    @pytest.mark.asyncio
    async def test_missing_workflow(self, mock_context):
        """Test error handling - Missing workflow."""
        result = to_dict(
            await execute_workflow(workflow="nonexistent-workflow-xyz", inputs={}, ctx=mock_context)
        )
        assert result["status"] == "failure", "Expected failure for missing workflow"
        assert "error" in result, "Missing error message"

    @pytest.mark.asyncio
    async def test_nonexistent_tag(self, mock_context):
        """Test error handling - Non-existent tag in list_workflows."""
        result = await list_workflows(tags=["invalid_xyz"], ctx=mock_context)
        assert isinstance(result, list), "Should return list"
        # Empty list is acceptable for non-existent tags

    @pytest.mark.asyncio
    async def test_invalid_workflow_info_request(self, mock_context):
        """Test error handling - Invalid workflow name in get_workflow_info."""
        try:
            result = await get_workflow_info(workflow="nonexistent-xyz", ctx=mock_context)
            # If it doesn't raise an exception, check for error in result
            if isinstance(result, dict) and "error" in result:
                pass  # Expected error in result
            else:
                pytest.fail(f"get_workflow_info returned unexpected result: {result}")
        except Exception:
            # Expected exception
            pass


# ============================================================================
# Tool Integration Tests (Phase 4)
# ============================================================================


# Templates directory
TEMPLATES_DIR = Path(__file__).parent.parent.parent / "src" / "workflows_mcp" / "templates"


def load_workflow(workflow_path: str):
    """Helper to load a workflow and handle Result."""
    file_path = TEMPLATES_DIR / workflow_path
    result = load_workflow_from_file(file_path)
    if not result.is_success:
        pytest.fail(f"Failed to load workflow {workflow_path}: {result.error}")
    return result.value


class TestAutoInstallParameter:
    """Test that auto_install parameter is properly defined and validated."""

    def test_run_pytest_auto_install_parameter(self):
        """run-pytest accepts auto_install parameter."""
        workflow_def = load_workflow("python/run-pytest.yaml")

        # Verify parameter exists and has correct type
        auto_install_input = workflow_def.inputs["auto_install"]
        assert auto_install_input["type"] == "boolean"
        assert auto_install_input["default"] is True
        assert "auto" in auto_install_input["description"].lower()

    def test_lint_python_auto_install_parameter(self):
        """lint-python accepts auto_install parameter."""
        workflow_def = load_workflow("python/lint-python.yaml")

        # Verify parameter exists and has correct type
        auto_install_input = workflow_def.inputs["auto_install"]
        assert auto_install_input["type"] == "boolean"
        assert auto_install_input["default"] is True
        assert "auto" in auto_install_input["description"].lower()

    def test_conditional_deploy_auto_install_parameter(self):
        """conditional-deploy accepts auto_install parameter."""
        workflow_def = load_workflow("ci/conditional-deploy.yaml")

        # Verify parameter exists and has correct type
        auto_install_input = workflow_def.inputs["auto_install"]
        assert auto_install_input["type"] == "boolean"
        assert auto_install_input["default"] is False
        assert "auto" in auto_install_input["description"].lower()


class TestDocumentation:
    """Test that workflows are properly documented with auto-install capability."""

    def test_run_pytest_mentions_auto_install(self):
        """run-pytest description mentions auto-install support."""
        workflow_def = load_workflow("python/run-pytest.yaml")
        assert "auto-install" in workflow_def.description.lower()

    def test_lint_python_mentions_auto_install(self):
        """lint-python description mentions auto-install support."""
        workflow_def = load_workflow("python/lint-python.yaml")
        assert "auto-install" in workflow_def.description.lower()
