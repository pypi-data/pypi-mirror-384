"""
Workflow composition block for Phase 2.2 - ExecuteWorkflow.

This module implements the ExecuteWorkflow block, enabling workflows to call
other workflows as reusable components. This is a critical feature for building
complex workflows from simpler, composable pieces.

Key Features:
- Execute child workflows by name (from registry)
- Pass inputs to child workflow with variable resolution
- Receive outputs from child workflow (namespaced under block_id)
- Circular dependency detection (prevent infinite recursion)
- Clean context isolation (child only sees passed inputs)
- Error propagation from child to parent
- Execution time tracking
"""

import time
from typing import Any, cast

from pydantic import Field

from .block import BLOCK_REGISTRY, BlockInput, BlockOutput, WorkflowBlock
from .result import Result


class ExecuteWorkflowInput(BlockInput):
    """Input for ExecuteWorkflow block.

    Supports variable references from the four-namespace context structure:
    - ${inputs.field}: Parent workflow inputs
    - ${blocks.block_id.outputs.field}: Parent block outputs
    - ${metadata.field}: Parent workflow metadata

    Variable resolution happens in the parent context before passing to child,
    so the child receives fully resolved values.
    """

    workflow: str = Field(description="Workflow name to execute (supports ${variables})")
    inputs: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Inputs to pass to child workflow. Supports variable references like "
            "${blocks.setup.outputs.path} which are resolved in parent context."
        ),
    )
    timeout_ms: int | None = Field(
        default=None, description="Optional timeout for child execution in milliseconds"
    )


class ExecuteWorkflowOutput(BlockOutput):
    """Output for ExecuteWorkflow block.

    Child workflow outputs are flattened into this model as dynamic fields via extra="allow".
    This allows referencing child outputs as ${blocks.block_id.outputs.field_name}.

    The model includes standard execution metadata plus any workflow-level outputs
    defined in the child workflow's outputs: section. These outputs become top-level
    fields in this model thanks to Pydantic's extra="allow" configuration.

    Standard Fields:
        success: Whether child workflow executed successfully
        workflow: Child workflow name executed
        execution_time_ms: Child workflow execution time in milliseconds
        total_blocks: Number of blocks executed in child workflow
        execution_waves: Number of execution waves in child workflow

    Dynamic Fields (from child workflow outputs):
        Any fields defined in child workflow's outputs: section become
        top-level fields in this model automatically.
    """

    success: bool = Field(description="Whether child workflow executed successfully")
    workflow: str = Field(description="Child workflow name executed")
    execution_time_ms: float = Field(description="Child workflow execution time in milliseconds")
    total_blocks: int = Field(description="Number of blocks executed in child workflow")
    execution_waves: int = Field(description="Number of execution waves in child workflow")
    # Child workflow outputs become dynamic fields via extra="allow"

    model_config = {"extra": "allow"}  # Allow dynamic fields from child workflow outputs


class ExecuteWorkflow(WorkflowBlock):
    """
    Execute another workflow as a block within a parent workflow.

    This block enables workflow composition by allowing one workflow to call
    another workflow. Child workflow outputs become parent block outputs through
    Pydantic's extra="allow" configuration, creating a clean composition pattern.

    Composition Pattern:
        Child workflow outputs become parent block outputs!

        Example:
            # Child workflow (run-tests.yaml):
            outputs:
              test_passed: "${blocks.pytest.outputs.success}"
              coverage: "${blocks.coverage.outputs.percent}"

            # Parent workflow:
            blocks:
              - id: run_tests
                type: ExecuteWorkflow
                inputs:
                  workflow: "run-tests"
                  inputs:
                    project_path: "${inputs.project_path}"

              - id: deploy
                type: Shell
                inputs:
                  command: "deploy.sh"
                condition: "${blocks.run_tests.outputs.test_passed}"
                depends_on: [run_tests]

            # Parent can reference child outputs:
            ${blocks.run_tests.outputs.test_passed}  # ← Child's workflow output
            ${blocks.run_tests.outputs.coverage}     # ← Another child output

    Context Structure:
        Parent context uses four-namespace structure:
        {
            "inputs": {...},          # Parent workflow inputs
            "blocks": {
                "run_tests": {        # ExecuteWorkflow block
                    "inputs": {...},  # What parent passed to child
                    "outputs": {      # Child's workflow outputs (flattened)
                        "test_passed": True,
                        "coverage": 87,
                        "success": True,      # Standard field
                        "workflow": "run-tests"  # Standard field
                    },
                    "metadata": {...}
                }
            },
            "metadata": {...},
            "__internal__": {...}
        }

    Features:
    - Output composition: Child outputs become block outputs via extra="allow"
    - Context isolation: Child sees only passed inputs, not parent context
    - Circular dependency detection: Prevents A -> B -> A recursion
    - Error propagation: Child workflow failures become parent block failures
    - Execution tracking: Time and statistics from child execution

    Circular Dependency Detection:
        - Direct: A calls A (detected immediately)
        - Indirect: A -> B -> A (detected via workflow stack)
        - Deep: A -> B -> C -> A (detected via workflow stack)
        - Diamond (allowed): A calls B and C, both call D (not circular)
    """

    def input_model(self) -> type[BlockInput]:
        return ExecuteWorkflowInput

    def output_model(self) -> type[BlockOutput]:
        return ExecuteWorkflowOutput

    async def execute(self, context: dict[str, Any]) -> Result[BlockOutput]:
        """
        Execute a child workflow with clean context isolation.

        This method handles the four-namespace context structure where child workflow
        outputs become parent block outputs through Pydantic's extra="allow" configuration.

        Process:
        1. Retrieve executor from __internal__ namespace
        2. Check for circular dependencies via workflow_stack
        3. Resolve child workflow inputs from parent context
        4. Execute child workflow (returns four-namespace structure)
        5. Extract child's workflow outputs and flatten into block outputs
        6. Return ExecuteWorkflowOutput with both standard and dynamic fields

        Args:
            context: Parent workflow context (four-namespace structure):
                {
                    "inputs": {...},
                    "blocks": {...},
                    "metadata": {...},
                    "__internal__": {
                        "executor": WorkflowExecutor,
                        "workflow_stack": [...]
                    }
                }

        Returns:
            Result.success(ExecuteWorkflowOutput) with:
                - Standard fields: success, workflow, execution_time_ms, total_blocks,
                  execution_waves
                - Dynamic fields: child workflow outputs (via extra="allow")
            Result.failure(error_message) if:
                - Executor not found
                - Workflow not found in registry
                - Circular dependency detected
                - Child workflow execution failed
                - Child workflow paused (pause propagation)
        """
        inputs = cast(ExecuteWorkflowInput, self._validated_inputs)
        if inputs is None:
            return Result.failure("Inputs not validated")

        start_time = time.time()

        # 1. Get executor from __internal__ namespace (new four-namespace structure)
        executor = context.get("__internal__", {}).get("executor")
        if executor is None:
            return Result.failure(
                "Executor not found in context - workflow composition not supported in this context"
            )

        # 2. Circular dependency detection via workflow_stack in __internal__
        workflow_stack = context.get("__internal__", {}).get("workflow_stack", [])
        workflow_name = inputs.workflow

        if workflow_name in workflow_stack:
            # Circular dependency detected
            cycle_path = " → ".join(workflow_stack) + f" → {workflow_name}"
            return Result.failure(f"Circular dependency detected: {cycle_path}")

        # 3. Check if workflow exists in registry
        if workflow_name not in executor.workflows:
            available = ", ".join(executor.workflows.keys())
            return Result.failure(
                f"Workflow '{workflow_name}' not found in registry. Available: {available}"
            )

        # 4. Resolve child workflow inputs from parent context
        #    Variable resolution happens in parent context, so child receives resolved values
        child_inputs = inputs.inputs.copy() if inputs.inputs else {}

        # 5. Execute child workflow with parent workflow stack for circular dependency detection
        try:
            # Use internal method to get Result object for internal block processing
            child_result = await executor._execute_workflow_internal(
                workflow_name, child_inputs, parent_workflow_stack=workflow_stack
            )

            # Handle pause (propagate to parent)
            if child_result.is_paused:
                # Propagate pause to parent by returning the paused result directly
                # The pause_data contains checkpoint information for resumption
                return Result[BlockOutput](
                    is_success=False,
                    is_paused=True,
                    pause_data=child_result.pause_data,
                    metadata={"child_workflow": workflow_name, "paused": True},
                )

            # Handle failure
            if not child_result.is_success:
                return Result.failure(
                    f"Child workflow '{workflow_name}' failed: {child_result.error}"
                )

            # Validate result value
            if child_result.value is None:
                return Result.failure(f"Child workflow '{workflow_name}' returned None value")

            # Child result has four-namespace structure:
            # {
            #   "inputs": {...},      # What was passed in
            #   "outputs": {...},     # Workflow-level outputs ← These become our block outputs!
            #   "blocks": {...},      # Child's internal block results
            #   "metadata": {...}     # Child's workflow metadata
            # }
            child_result_dict = child_result.value

        except Exception as e:
            return Result.failure(f"Child workflow '{workflow_name}' raised exception: {e}")

        # 6. Extract child's workflow outputs and create block output
        execution_time_ms = (time.time() - start_time) * 1000

        # Extract child workflow outputs (from outputs namespace)
        child_workflow_outputs = child_result_dict.get("outputs", {})
        child_metadata = child_result_dict.get("metadata", {})

        # Build output dict with standard fields
        output_dict: dict[str, Any] = {
            "success": True,
            "workflow": workflow_name,
            "execution_time_ms": execution_time_ms,
            "total_blocks": child_metadata.get("total_blocks", 0),
            "execution_waves": child_metadata.get("execution_waves", 0),
        }

        # Add child workflow outputs as dynamic fields
        # Pydantic extra="allow" lets us add arbitrary fields from child outputs
        if child_workflow_outputs:
            output_dict.update(child_workflow_outputs)

        # Create output with both standard and dynamic fields
        # extra="allow" configuration enables dynamic fields from child workflow outputs
        output = ExecuteWorkflowOutput(**output_dict)

        # Create metadata for debugging
        metadata = {
            "child_workflow": workflow_name,
            "child_execution_time": child_metadata.get("execution_time_seconds", 0),
            "child_blocks_count": child_metadata.get("total_blocks", 0),
            "child_outputs_count": len(child_workflow_outputs),
        }

        return Result.success(output, metadata=metadata)


# Register block
BLOCK_REGISTRY.register("ExecuteWorkflow", ExecuteWorkflow)
