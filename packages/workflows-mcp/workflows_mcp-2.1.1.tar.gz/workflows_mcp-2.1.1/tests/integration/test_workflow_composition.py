"""
Comprehensive tests for ExecuteWorkflow block (Phase 2.2 workflow composition).

Test Coverage:
- Unit Tests (≥10): Basic execution, input/output handling, registry verification
- Circular Dependency Tests (≥5): Direct, indirect, and deep circular detection
- Integration Tests (≥5): Complex compositions, parallel execution, multi-level nesting

Success Criteria:
- All new ExecuteWorkflow tests pass (≥20 new tests)
- All existing tests still pass (no regressions)
- Circular dependency detection working correctly
- Clean context isolation verified
"""

import pytest

from workflows_mcp.engine import BLOCK_REGISTRY
from workflows_mcp.engine.blocks_workflow import ExecuteWorkflow
from workflows_mcp.engine.executor import WorkflowDefinition, WorkflowExecutor
from workflows_mcp.engine.response import WorkflowResponse


def to_dict(result):
    """Convert WorkflowResponse to dict for testing."""
    if isinstance(result, WorkflowResponse):
        return result.model_dump()
    return result


@pytest.mark.asyncio
class TestExecuteWorkflowUnit:
    """Unit tests for ExecuteWorkflow block (≥10 tests)."""

    async def test_basic_child_workflow_execution(self):
        """Test basic execution of a child workflow."""
        # Setup: Create simple child workflow
        child_workflow = WorkflowDefinition(
            name="child",
            description="Simple child workflow",
            blocks=[
                {
                    "id": "echo",
                    "type": "EchoBlock",
                    "inputs": {"message": "Hello from child"},
                }
            ],
        )

        # Setup: Create parent workflow that calls child
        parent_workflow = WorkflowDefinition(
            name="parent",
            description="Parent workflow",
            blocks=[
                {
                    "id": "run_child",
                    "type": "ExecuteWorkflow",
                    "inputs": {"workflow": "child", "inputs": {}},
                }
            ],
        )

        # Execute parent workflow
        executor = WorkflowExecutor()
        executor.load_workflow(child_workflow)
        executor.load_workflow(parent_workflow)

        result = await executor.execute_workflow("parent")

        # Verify
        assert result.is_success
        outputs = result.value
        assert outputs is not None
        # New four-namespace structure: blocks are at top level
        assert "run_child" in outputs["blocks"]

        run_child_output = outputs["blocks"]["run_child"]
        assert run_child_output["outputs"]["success"] is True
        assert run_child_output["outputs"]["workflow"] == "child"
        assert "outputs" in run_child_output
        assert run_child_output["outputs"]["total_blocks"] == 1
        assert run_child_output["outputs"]["execution_waves"] == 1

    async def test_input_passing_to_child_workflow(self):
        """Test passing inputs from parent to child workflow."""
        # Child workflow that uses inputs and exposes outputs
        child_workflow = WorkflowDefinition(
            name="greeter",
            description="Greets with name",
            blocks=[
                {
                    "id": "greet",
                    "type": "EchoBlock",
                    "inputs": {"message": "${inputs.name}"},  # Use inputs namespace
                }
            ],
            inputs={"name": {"type": "str", "default": "World"}},
            outputs={"greeting": "${blocks.greet.outputs.echoed}"},  # Expose result through outputs
        )

        # Parent passes input to child
        parent_workflow = WorkflowDefinition(
            name="parent",
            description="Parent workflow",
            blocks=[
                {
                    "id": "greet_alice",
                    "type": "ExecuteWorkflow",
                    "inputs": {"workflow": "greeter", "inputs": {"name": "Alice"}},
                }
            ],
        )

        executor = WorkflowExecutor()
        executor.load_workflow(child_workflow)
        executor.load_workflow(parent_workflow)

        result = await executor.execute_workflow("parent")

        assert result.is_success
        outputs = result.value
        assert outputs is not None

        # Verify child received the input and processed it correctly
        greet_output = outputs["blocks"]["greet_alice"]
        assert greet_output["outputs"]["success"] is True
        # Access child outputs through ExecuteWorkflow's flattened outputs
        assert greet_output["outputs"]["greeting"] == "Echo: Alice"

    async def test_output_receiving_from_child_workflow(self):
        """Test receiving and accessing outputs from child workflow."""
        child_workflow = WorkflowDefinition(
            name="calculator",
            description="Does calculations",
            blocks=[
                {
                    "id": "calc",
                    "type": "EchoBlock",
                    "inputs": {"message": "42"},
                }
            ],
            outputs={"result": "${blocks.calc.outputs.echoed}"},  # Expose calculation result
        )

        parent_workflow = WorkflowDefinition(
            name="parent",
            description="Parent workflow",
            blocks=[
                {
                    "id": "run_calc",
                    "type": "ExecuteWorkflow",
                    "inputs": {"workflow": "calculator", "inputs": {}},
                }
            ],
        )

        executor = WorkflowExecutor()
        executor.load_workflow(child_workflow)
        executor.load_workflow(parent_workflow)

        result = await executor.execute_workflow("parent")

        assert result.is_success
        outputs = result.value
        assert outputs is not None

        # Verify parent can access child outputs (flattened by ExecuteWorkflow)
        calc_output = outputs["blocks"]["run_calc"]
        assert "outputs" in calc_output
        assert calc_output["outputs"]["success"] is True
        # Access child output through ExecuteWorkflow's flattened outputs
        assert calc_output["outputs"]["result"] == "Echo: 42"

    async def test_output_namespacing_under_block_id(self):
        """Test that child outputs are properly namespaced under block_id."""
        child_workflow = WorkflowDefinition(
            name="worker",
            description="Worker workflow",
            blocks=[
                {
                    "id": "work",
                    "type": "EchoBlock",
                    "inputs": {"message": "work done"},
                }
            ],
        )

        parent_workflow = WorkflowDefinition(
            name="parent",
            description="Parent workflow",
            blocks=[
                {
                    "id": "task1",
                    "type": "ExecuteWorkflow",
                    "inputs": {"workflow": "worker", "inputs": {}},
                },
                {
                    "id": "task2",
                    "type": "ExecuteWorkflow",
                    "inputs": {"workflow": "worker", "inputs": {}},
                    "depends_on": ["task1"],
                },
            ],
        )

        executor = WorkflowExecutor()
        executor.load_workflow(child_workflow)
        executor.load_workflow(parent_workflow)

        result = await executor.execute_workflow("parent")

        assert result.is_success
        outputs = result.value
        assert outputs is not None

        # Verify both tasks have separate namespaces
        assert "task1" in outputs["blocks"]
        assert "task2" in outputs["blocks"]
        task1_output = outputs["blocks"]["task1"]
        task2_output = outputs["blocks"]["task2"]

        # Both should have their own outputs
        assert task1_output["outputs"]["workflow"] == "worker"
        assert task2_output["outputs"]["workflow"] == "worker"
        assert "outputs" in task1_output
        assert "outputs" in task2_output

    async def test_variable_resolution_in_workflow_name(self):
        """Test variable resolution in the workflow name parameter."""
        child_workflow = WorkflowDefinition(
            name="dynamic-worker",
            description="Dynamic workflow",
            blocks=[
                {
                    "id": "echo",
                    "type": "EchoBlock",
                    "inputs": {"message": "dynamic"},
                }
            ],
        )

        parent_workflow = WorkflowDefinition(
            name="parent",
            description="Parent with variable workflow name",
            blocks=[
                {
                    "id": "run_dynamic",
                    "type": "ExecuteWorkflow",
                    "inputs": {"workflow": "${inputs.workflow_name}", "inputs": {}},
                }
            ],
            inputs={"workflow_name": {"type": "str", "default": "dynamic-worker"}},
        )

        executor = WorkflowExecutor()
        executor.load_workflow(child_workflow)
        executor.load_workflow(parent_workflow)

        result = await executor.execute_workflow("parent")

        assert result.is_success
        outputs = result.value
        assert outputs is not None
        run_dynamic_output = outputs["blocks"]["run_dynamic"]
        assert run_dynamic_output["outputs"]["workflow"] == "dynamic-worker"

    async def test_variable_resolution_in_inputs(self):
        """Test variable resolution in child workflow inputs."""
        child_workflow = WorkflowDefinition(
            name="processor",
            description="Processes data",
            blocks=[
                {
                    "id": "process",
                    "type": "EchoBlock",
                    "inputs": {"message": "${inputs.data}"},
                }
            ],
            inputs={"data": {"type": "str"}},
            outputs={"processed": "${blocks.process.outputs.echoed}"},  # Expose processed result
        )

        parent_workflow = WorkflowDefinition(
            name="parent",
            description="Parent with variable inputs",
            blocks=[
                {
                    "id": "prepare",
                    "type": "EchoBlock",
                    "inputs": {"message": "prepared data"},
                },
                {
                    "id": "process",
                    "type": "ExecuteWorkflow",
                    "inputs": {
                        "workflow": "processor",
                        "inputs": {"data": "${blocks.prepare.outputs.echoed}"},
                    },
                    "depends_on": ["prepare"],
                },
            ],
        )

        executor = WorkflowExecutor()
        executor.load_workflow(child_workflow)
        executor.load_workflow(parent_workflow)

        result = await executor.execute_workflow("parent")

        assert result.is_success
        outputs = result.value
        assert outputs is not None

        # Verify variable was resolved and passed to child
        process_output = outputs["blocks"]["process"]
        # Access child output through ExecuteWorkflow's flattened outputs
        assert process_output["outputs"]["processed"] == "Echo: Echo: prepared data"

    async def test_workflow_not_found_error(self):
        """Test error handling when child workflow doesn't exist."""
        parent_workflow = WorkflowDefinition(
            name="parent",
            description="Parent workflow",
            blocks=[
                {
                    "id": "run_missing",
                    "type": "ExecuteWorkflow",
                    "inputs": {"workflow": "nonexistent", "inputs": {}},
                }
            ],
        )

        executor = WorkflowExecutor()
        executor.load_workflow(parent_workflow)

        result = await executor.execute_workflow("parent")

        assert not result.is_success
        assert "Workflow 'nonexistent' not found" in result.error
        assert "Available:" in result.error

    async def test_child_workflow_failure_propagation(self):
        """Test that child workflow failures propagate to parent."""
        # Child workflow that will fail (invalid block type)
        child_workflow = WorkflowDefinition(
            name="failer",
            description="Fails on purpose",
            blocks=[
                {
                    "id": "fail",
                    "type": "NonExistentBlock",
                    "inputs": {},
                }
            ],
        )

        parent_workflow = WorkflowDefinition(
            name="parent",
            description="Parent workflow",
            blocks=[
                {
                    "id": "run_failer",
                    "type": "ExecuteWorkflow",
                    "inputs": {"workflow": "failer", "inputs": {}},
                }
            ],
        )

        executor = WorkflowExecutor()
        executor.load_workflow(child_workflow)
        executor.load_workflow(parent_workflow)

        result = await executor.execute_workflow("parent")

        assert not result.is_success
        assert "Child workflow 'failer' failed" in result.error

    async def test_execution_time_tracking(self):
        """Test that execution time is tracked correctly."""
        child_workflow = WorkflowDefinition(
            name="timed",
            description="Timed workflow",
            blocks=[
                {
                    "id": "delay",
                    "type": "EchoBlock",
                    "inputs": {"message": "test", "delay_ms": 100},
                }
            ],
        )

        parent_workflow = WorkflowDefinition(
            name="parent",
            description="Parent workflow",
            blocks=[
                {
                    "id": "run_timed",
                    "type": "ExecuteWorkflow",
                    "inputs": {"workflow": "timed", "inputs": {}},
                }
            ],
        )

        executor = WorkflowExecutor()
        executor.load_workflow(child_workflow)
        executor.load_workflow(parent_workflow)

        result = await executor.execute_workflow("parent")

        assert result.is_success
        outputs = result.value
        assert outputs is not None

        # Verify execution time was tracked
        run_output = outputs["blocks"]["run_timed"]
        assert "outputs" in run_output
        assert "execution_time_ms" in run_output["outputs"]
        assert run_output["outputs"]["execution_time_ms"] >= 100  # At least the delay time

    async def test_registry_verification(self):
        """Test that ExecuteWorkflow is properly registered in BLOCK_REGISTRY."""
        # Verify ExecuteWorkflow is registered
        assert "ExecuteWorkflow" in BLOCK_REGISTRY.list_types()

        # Verify we can get the class
        block_class = BLOCK_REGISTRY.get("ExecuteWorkflow")
        assert block_class == ExecuteWorkflow

        # Verify we can instantiate it
        block = block_class(
            id="test",
            inputs={"workflow": "test-workflow", "inputs": {}},
        )
        assert block.id == "test"
        assert isinstance(block, ExecuteWorkflow)


@pytest.mark.asyncio
class TestCircularDependencyDetection:
    """Circular dependency detection tests (≥5 tests)."""

    async def test_direct_circular_a_calls_a(self):
        """Test detection of direct circular dependency (A calls A)."""
        # Self-referential workflow
        workflow = WorkflowDefinition(
            name="self-caller",
            description="Calls itself",
            blocks=[
                {
                    "id": "recurse",
                    "type": "ExecuteWorkflow",
                    "inputs": {"workflow": "self-caller", "inputs": {}},
                }
            ],
        )

        executor = WorkflowExecutor()
        executor.load_workflow(workflow)

        result = await executor.execute_workflow("self-caller")

        assert not result.is_success
        assert "Circular dependency detected" in result.error
        assert "self-caller → self-caller" in result.error

    async def test_indirect_circular_a_calls_b_calls_a(self):
        """Test detection of indirect circular dependency (A -> B -> A)."""
        # Workflow A calls B
        workflow_a = WorkflowDefinition(
            name="workflow-a",
            description="Calls B",
            blocks=[
                {
                    "id": "call_b",
                    "type": "ExecuteWorkflow",
                    "inputs": {"workflow": "workflow-b", "inputs": {}},
                }
            ],
        )

        # Workflow B calls A (creates cycle)
        workflow_b = WorkflowDefinition(
            name="workflow-b",
            description="Calls A",
            blocks=[
                {
                    "id": "call_a",
                    "type": "ExecuteWorkflow",
                    "inputs": {"workflow": "workflow-a", "inputs": {}},
                }
            ],
        )

        executor = WorkflowExecutor()
        executor.load_workflow(workflow_a)
        executor.load_workflow(workflow_b)

        result = await executor.execute_workflow("workflow-a")

        assert not result.is_success
        assert "Circular dependency detected" in result.error
        assert "workflow-a → workflow-b → workflow-a" in result.error

    async def test_deep_circular_a_b_c_a(self):
        """Test detection of deep circular dependency (A -> B -> C -> A)."""
        workflow_a = WorkflowDefinition(
            name="workflow-a",
            description="Calls B",
            blocks=[
                {
                    "id": "call_b",
                    "type": "ExecuteWorkflow",
                    "inputs": {"workflow": "workflow-b", "inputs": {}},
                }
            ],
        )

        workflow_b = WorkflowDefinition(
            name="workflow-b",
            description="Calls C",
            blocks=[
                {
                    "id": "call_c",
                    "type": "ExecuteWorkflow",
                    "inputs": {"workflow": "workflow-c", "inputs": {}},
                }
            ],
        )

        workflow_c = WorkflowDefinition(
            name="workflow-c",
            description="Calls A (creates cycle)",
            blocks=[
                {
                    "id": "call_a",
                    "type": "ExecuteWorkflow",
                    "inputs": {"workflow": "workflow-a", "inputs": {}},
                }
            ],
        )

        executor = WorkflowExecutor()
        executor.load_workflow(workflow_a)
        executor.load_workflow(workflow_b)
        executor.load_workflow(workflow_c)

        result = await executor.execute_workflow("workflow-a")

        assert not result.is_success
        assert "Circular dependency detected" in result.error
        assert "workflow-a → workflow-b → workflow-c → workflow-a" in result.error

    async def test_diamond_pattern_allowed(self):
        """Test that diamond pattern (A calls B and C, both call D) is allowed (not circular)."""
        # Workflow D (leaf)
        workflow_d = WorkflowDefinition(
            name="workflow-d",
            description="Leaf workflow",
            blocks=[
                {
                    "id": "leaf",
                    "type": "EchoBlock",
                    "inputs": {"message": "leaf"},
                }
            ],
        )

        # Workflow B calls D
        workflow_b = WorkflowDefinition(
            name="workflow-b",
            description="Calls D",
            blocks=[
                {
                    "id": "call_d",
                    "type": "ExecuteWorkflow",
                    "inputs": {"workflow": "workflow-d", "inputs": {}},
                }
            ],
        )

        # Workflow C calls D
        workflow_c = WorkflowDefinition(
            name="workflow-c",
            description="Calls D",
            blocks=[
                {
                    "id": "call_d",
                    "type": "ExecuteWorkflow",
                    "inputs": {"workflow": "workflow-d", "inputs": {}},
                }
            ],
        )

        # Workflow A calls B and C (diamond pattern)
        workflow_a = WorkflowDefinition(
            name="workflow-a",
            description="Calls B and C",
            blocks=[
                {
                    "id": "call_b",
                    "type": "ExecuteWorkflow",
                    "inputs": {"workflow": "workflow-b", "inputs": {}},
                },
                {
                    "id": "call_c",
                    "type": "ExecuteWorkflow",
                    "inputs": {"workflow": "workflow-c", "inputs": {}},
                    "depends_on": ["call_b"],
                },
            ],
        )

        executor = WorkflowExecutor()
        executor.load_workflow(workflow_a)
        executor.load_workflow(workflow_b)
        executor.load_workflow(workflow_c)
        executor.load_workflow(workflow_d)

        result = await executor.execute_workflow("workflow-a")

        # Diamond pattern should succeed (not circular)
        assert result.is_success

    async def test_circular_detection_error_message_format(self):
        """Test that circular dependency error messages are clear and helpful."""
        workflow_a = WorkflowDefinition(
            name="alpha",
            description="Calls beta",
            blocks=[
                {
                    "id": "call_beta",
                    "type": "ExecuteWorkflow",
                    "inputs": {"workflow": "beta", "inputs": {}},
                }
            ],
        )

        workflow_b = WorkflowDefinition(
            name="beta",
            description="Calls alpha",
            blocks=[
                {
                    "id": "call_alpha",
                    "type": "ExecuteWorkflow",
                    "inputs": {"workflow": "alpha", "inputs": {}},
                }
            ],
        )

        executor = WorkflowExecutor()
        executor.load_workflow(workflow_a)
        executor.load_workflow(workflow_b)

        result = await executor.execute_workflow("alpha")

        assert not result.is_success
        # Error should contain:
        # 1. "Circular dependency detected" message
        # 2. Full cycle path with arrows
        assert "Circular dependency detected" in result.error
        assert "alpha → beta → alpha" in result.error


@pytest.mark.asyncio
class TestWorkflowCompositionIntegration:
    """Integration tests for complex workflow composition (≥5 tests)."""

    async def test_simple_composition_parent_child(self):
        """Test simple two-level composition (Parent -> Child)."""
        child = WorkflowDefinition(
            name="child",
            description="Child workflow",
            blocks=[
                {
                    "id": "step1",
                    "type": "EchoBlock",
                    "inputs": {"message": "child step 1"},
                },
                {
                    "id": "step2",
                    "type": "EchoBlock",
                    "inputs": {"message": "${blocks.step1.outputs.echoed}"},
                    "depends_on": ["step1"],
                },
            ],
        )

        parent = WorkflowDefinition(
            name="parent",
            description="Parent workflow",
            blocks=[
                {
                    "id": "run_child",
                    "type": "ExecuteWorkflow",
                    "inputs": {"workflow": "child", "inputs": {}},
                }
            ],
        )

        executor = WorkflowExecutor()
        executor.load_workflow(child)
        executor.load_workflow(parent)

        result = await executor.execute_workflow("parent")

        assert result.is_success
        outputs = result.value
        assert outputs is not None
        assert outputs["metadata"]["total_blocks"] == 1
        assert outputs["blocks"]["run_child"]["outputs"]["total_blocks"] == 2

    async def test_complex_composition_three_levels(self):
        """Test complex three-level composition (Grandparent -> Parent -> Child)."""
        # Leaf child - exposes work result
        child = WorkflowDefinition(
            name="child",
            description="Child workflow",
            blocks=[
                {
                    "id": "work",
                    "type": "EchoBlock",
                    "inputs": {"message": "child work"},
                }
            ],
            outputs={"result": "${blocks.work.outputs.echoed}"},  # Expose child work result
        )

        # Middle parent - calls child and exposes child result
        parent = WorkflowDefinition(
            name="parent",
            description="Parent workflow",
            blocks=[
                {
                    "id": "call_child",
                    "type": "ExecuteWorkflow",
                    "inputs": {"workflow": "child", "inputs": {}},
                }
            ],
            outputs={"child_result": "${blocks.call_child.outputs.result}"},  # Forward child result
        )

        # Top grandparent - calls parent
        grandparent = WorkflowDefinition(
            name="grandparent",
            description="Grandparent workflow",
            blocks=[
                {
                    "id": "call_parent",
                    "type": "ExecuteWorkflow",
                    "inputs": {"workflow": "parent", "inputs": {}},
                }
            ],
        )

        executor = WorkflowExecutor()
        executor.load_workflow(child)
        executor.load_workflow(parent)
        executor.load_workflow(grandparent)

        result = await executor.execute_workflow("grandparent")

        assert result.is_success
        outputs = result.value
        assert outputs is not None

        # Verify three-level composition works through flattened outputs
        gp_output = outputs["blocks"]["call_parent"]
        assert gp_output["outputs"]["workflow"] == "parent"
        # Verify we can access parent's forwarded output (which came from child)
        assert gp_output["outputs"]["child_result"] == "Echo: child work"

    async def test_parallel_child_workflows(self):
        """Test parallel execution of multiple child workflows."""
        worker1 = WorkflowDefinition(
            name="worker1",
            description="Worker 1",
            blocks=[
                {
                    "id": "work",
                    "type": "EchoBlock",
                    "inputs": {"message": "worker 1"},
                }
            ],
        )

        worker2 = WorkflowDefinition(
            name="worker2",
            description="Worker 2",
            blocks=[
                {
                    "id": "work",
                    "type": "EchoBlock",
                    "inputs": {"message": "worker 2"},
                }
            ],
        )

        coordinator = WorkflowDefinition(
            name="coordinator",
            description="Coordinates parallel workers",
            blocks=[
                {
                    "id": "run_worker1",
                    "type": "ExecuteWorkflow",
                    "inputs": {"workflow": "worker1", "inputs": {}},
                },
                {
                    "id": "run_worker2",
                    "type": "ExecuteWorkflow",
                    "inputs": {"workflow": "worker2", "inputs": {}},
                },
            ],
        )

        executor = WorkflowExecutor()
        executor.load_workflow(worker1)
        executor.load_workflow(worker2)
        executor.load_workflow(coordinator)

        result = await executor.execute_workflow("coordinator")

        assert result.is_success
        outputs = result.value
        assert outputs is not None

        # Verify both workers executed
        assert "run_worker1" in outputs["blocks"]
        assert "run_worker2" in outputs["blocks"]
        assert outputs["blocks"]["run_worker1"]["outputs"]["workflow"] == "worker1"
        assert outputs["blocks"]["run_worker2"]["outputs"]["workflow"] == "worker2"

    async def test_conditional_child_execution(self):
        """Test conditional execution of child workflow based on parent condition."""
        child = WorkflowDefinition(
            name="child",
            description="Child workflow",
            blocks=[
                {
                    "id": "work",
                    "type": "EchoBlock",
                    "inputs": {"message": "conditional work"},
                }
            ],
        )

        parent_success = WorkflowDefinition(
            name="parent-success",
            description="Parent with condition that passes",
            blocks=[
                {
                    "id": "check",
                    "type": "EchoBlock",
                    "inputs": {"message": "check passed"},
                },
                {
                    "id": "run_child",
                    "type": "ExecuteWorkflow",
                    "inputs": {"workflow": "child", "inputs": {}},
                    "condition": "True",  # Explicit True condition (Python boolean)
                    "depends_on": ["check"],
                },
            ],
        )

        parent_skip = WorkflowDefinition(
            name="parent-skip",
            description="Parent with condition that fails",
            blocks=[
                {
                    "id": "check",
                    "type": "EchoBlock",
                    "inputs": {"message": "check failed"},
                },
                {
                    "id": "run_child",
                    "type": "ExecuteWorkflow",
                    "inputs": {"workflow": "child", "inputs": {}},
                    "condition": "False",  # Explicit False condition (Python boolean)
                    "depends_on": ["check"],
                },
            ],
        )

        executor = WorkflowExecutor()
        executor.load_workflow(child)
        executor.load_workflow(parent_success)
        executor.load_workflow(parent_skip)

        # Test success case
        result_success = await executor.execute_workflow("parent-success")
        assert result_success.is_success
        outputs_success = result_success.value
        assert "run_child" in outputs_success["blocks"]
        run_child_output = outputs_success["blocks"]["run_child"]
        assert run_child_output["outputs"]["success"] is True

        # Test skip case
        result_skip = await executor.execute_workflow("parent-skip")
        assert result_skip.is_success
        outputs_skip = result_skip.value
        # run_child should be skipped (present in blocks but marked as skipped)
        assert "run_child" in outputs_skip["blocks"]
        run_child_skip = outputs_skip["blocks"]["run_child"]
        assert run_child_skip["outputs"]["skipped"] is True
        assert run_child_skip["outputs"]["success"] is False

    async def test_variable_passing_through_composition(self):
        """Test complex variable passing through multiple composition levels."""
        # Child workflow that uses input and exposes result
        child = WorkflowDefinition(
            name="processor",
            description="Processes input data",
            blocks=[
                {
                    "id": "process",
                    "type": "EchoBlock",
                    "inputs": {"message": "Processed: ${inputs.input_data}"},
                }
            ],
            inputs={"input_data": {"type": "str"}},
            outputs={"processed_result": "${blocks.process.outputs.echoed}"},  # Expose result
        )

        # Parent workflow that prepares data and passes to child
        parent = WorkflowDefinition(
            name="coordinator",
            description="Prepares and processes data",
            blocks=[
                {
                    "id": "prepare",
                    "type": "EchoBlock",
                    "inputs": {"message": "raw data"},
                },
                {
                    "id": "process",
                    "type": "ExecuteWorkflow",
                    "inputs": {
                        "workflow": "processor",
                        "inputs": {"input_data": "${blocks.prepare.outputs.echoed}"},
                    },
                    "depends_on": ["prepare"],
                },
            ],
        )

        executor = WorkflowExecutor()
        executor.load_workflow(child)
        executor.load_workflow(parent)

        result = await executor.execute_workflow("coordinator")

        assert result.is_success
        outputs = result.value
        assert outputs is not None

        # Verify data flowed through correctly (via flattened child outputs)
        process_output = outputs["blocks"]["process"]
        assert "Processed: Echo: raw data" in process_output["outputs"]["processed_result"]

    async def test_multi_level_with_file_operations(self):
        """Test multi-level composition with actual file operations."""
        import tempfile
        from pathlib import Path

        # Create temp directory for testing
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"

            # Child workflow creates and reads file, exposes results
            child = WorkflowDefinition(
                name="file-worker",
                description="File operations",
                blocks=[
                    {
                        "id": "create",
                        "type": "CreateFile",
                        "inputs": {
                            "path": str(test_file),
                            "content": "Hello from child",
                        },
                    },
                    {
                        "id": "read",
                        "type": "ReadFile",
                        "inputs": {"path": str(test_file)},
                        "depends_on": ["create"],
                    },
                ],
                outputs={
                    "file_created": "${blocks.create.outputs.success}",
                    "file_content": "${blocks.read.outputs.content}",
                },
            )

            # Parent calls child
            parent = WorkflowDefinition(
                name="orchestrator",
                description="Orchestrates file operations",
                blocks=[
                    {
                        "id": "run_file_ops",
                        "type": "ExecuteWorkflow",
                        "inputs": {"workflow": "file-worker", "inputs": {}},
                    }
                ],
            )

            executor = WorkflowExecutor()
            executor.load_workflow(child)
            executor.load_workflow(parent)

            result = await executor.execute_workflow("orchestrator")

            assert result.is_success
            outputs = result.value
            assert outputs is not None

            # Verify file was created and read (via flattened child outputs)
            file_ops_output = outputs["blocks"]["run_file_ops"]
            # Note: Variable resolution produces string values, not typed values
            assert file_ops_output["outputs"]["file_created"] == "True"
            assert file_ops_output["outputs"]["file_content"] == "Hello from child"

            # Verify file exists
            assert test_file.exists()
            assert test_file.read_text() == "Hello from child"
