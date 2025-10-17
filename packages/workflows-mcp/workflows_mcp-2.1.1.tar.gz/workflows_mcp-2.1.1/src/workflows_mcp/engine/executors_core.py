"""Core workflow executors - Shell and ExecuteWorkflow."""

import asyncio
import json
import os
import shlex
from pathlib import Path
from typing import Any, ClassVar

from pydantic import Field

from .block import BlockInput, BlockOutput
from .block_utils import ExecutionTimer
from .executor_base import (
    EXECUTOR_REGISTRY,
    BlockExecutor,
    ExecutorCapabilities,
    ExecutorSecurityLevel,
)
from .result import Result

# ============================================================================
# Shell Executor
# ============================================================================


class ShellInput(BlockInput):
    """Input model for Shell executor.

    Note: YAML workflows must use 'continue-on-error' (kebab-case, GitHub Actions standard).
    Python code internally uses 'continue_on_error' (snake_case, PEP 8 standard).
    """

    model_config = {"extra": "forbid", "populate_by_name": True}  # Accept both name and alias

    command: str = Field(description="Shell command to execute")
    working_dir: str = Field(default="", description="Working directory (empty = current dir)")
    timeout: int = Field(default=120, description="Timeout in seconds")
    env: dict[str, str] = Field(default_factory=dict, description="Environment variables")
    capture_output: bool = Field(default=True, description="Capture stdout/stderr")
    shell: bool = Field(default=True, description="Execute via shell")
    continue_on_error: bool = Field(
        default=False,
        description="Continue workflow even if command fails (GitHub Actions semantics)",
        alias="continue-on-error",
    )
    # Custom outputs support (from original Shell block)
    custom_outputs: dict[str, Any] | None = Field(
        default=None,
        description="Custom file-based outputs to read after execution",
        exclude=True,  # Not part of validation, managed separately
    )


class ShellOutput(BlockOutput):
    """Output model for Shell executor.

    Custom outputs declared in YAML are merged directly as fields via extra="allow".
    No separate custom_outputs dict needed.
    """

    exit_code: int = Field(description="Process exit code")
    stdout: str = Field(description="Standard output")
    stderr: str = Field(description="Standard error")
    success: bool = Field(description="Whether command succeeded")
    command_executed: str = Field(description="The command that was executed")
    execution_time_ms: float = Field(description="Execution time in milliseconds")

    model_config = {"extra": "allow"}  # Allow dynamic custom output fields


class OutputSecurityError(Exception):
    """Raised when output path violates security constraints."""

    pass


class OutputNotFoundError(Exception):
    """Raised when output file not found."""

    pass


def validate_output_path(
    output_name: str, path: str, working_dir: Path, unsafe: bool = False
) -> Path:
    """
    Validate output file path with security checks.

    Security rules:
    - Safe mode (default): Relative paths only, within working_dir
    - Unsafe mode (opt-in): Allows absolute paths
    - Always: No symlinks, size limit (10MB), no path traversal

    Args:
        output_name: Name of the output (for error messages)
        path: File path to validate (can contain env vars)
        working_dir: Working directory for relative paths
        unsafe: Allow absolute paths (default: False)

    Returns:
        Validated absolute Path

    Raises:
        OutputSecurityError: If path violates security constraints
        OutputNotFoundError: If file doesn't exist
    """
    # Expand environment variables
    expanded_path = os.path.expandvars(path)

    # Convert to Path object
    file_path = Path(expanded_path)

    # Security check: reject absolute paths in safe mode
    if file_path.is_absolute() and not unsafe:
        raise OutputSecurityError(
            f"Output '{output_name}': Absolute paths not allowed in safe mode. "
            f"Path: {path}. Set 'unsafe: true' to allow absolute paths."
        )

    # Build absolute path (without resolving symlinks yet)
    if file_path.is_absolute():
        absolute_path = file_path
    else:
        absolute_path = working_dir / file_path

    # Security check: no symlinks (check BEFORE resolving)
    # Must check before resolve() because resolve() follows symlinks
    if absolute_path.is_symlink():
        raise OutputSecurityError(
            f"Output '{output_name}': Symlinks not allowed for security. Path: {absolute_path}"
        )

    # Security check: path traversal - check BEFORE file existence
    # This prevents information leakage about files outside working directory
    # Resolve the path to handle .. and any symlinks in parent directories
    resolved_path = absolute_path.resolve()

    if not unsafe:
        try:
            resolved_path.relative_to(working_dir.resolve())
        except ValueError:
            raise OutputSecurityError(
                f"Output '{output_name}': Path escapes working directory. "
                f"Path: {path}, Resolved: {resolved_path}, Working dir: {working_dir}"
            )

    # Check file exists (after security checks)
    if not resolved_path.exists():
        raise OutputNotFoundError(f"Output '{output_name}': File not found at {resolved_path}")

    # Security check: must be a file
    if not resolved_path.is_file():
        raise OutputSecurityError(
            f"Output '{output_name}': Path is not a file. Path: {resolved_path}"
        )

    # Security check: size limit (10MB)
    max_size = 10 * 1024 * 1024  # 10MB
    file_size = resolved_path.stat().st_size
    if file_size > max_size:
        raise OutputSecurityError(
            f"Output '{output_name}': File too large ({file_size} bytes, max {max_size} bytes). "
            f"Path: {resolved_path}"
        )

    return resolved_path


def parse_output_value(content: str, output_type: str) -> Any:
    """
    Parse file content according to declared type.

    Args:
        content: Raw file content
        output_type: One of: string, int, float, bool, json

    Returns:
        Parsed value with correct Python type

    Raises:
        ValueError: If content doesn't match declared type
    """
    content = content.strip()

    if output_type == "string":
        return content
    elif output_type == "int":
        try:
            return int(content)
        except ValueError:
            raise ValueError(f"Cannot parse as int: {content}")
    elif output_type == "float":
        try:
            return float(content)
        except ValueError:
            raise ValueError(f"Cannot parse as float: {content}")
    elif output_type == "bool":
        # Accept: true/false, 1/0, yes/no (case-insensitive)
        lower = content.lower()
        if lower in ["true", "1", "yes"]:
            return True
        elif lower in ["false", "0", "no"]:
            return False
        else:
            raise ValueError(
                f"Cannot parse as bool: {content}. "
                f"Accepted values: true/false, 1/0, yes/no (case-insensitive)"
            )
    elif output_type == "json":
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Cannot parse as JSON: {e}")
    else:
        raise ValueError(f"Unknown output type: {output_type}")


class ShellExecutor(BlockExecutor):
    """
    Shell command executor.

    Executes shell commands with comprehensive error handling.
    Supports working directory, environment variables, timeouts, and custom file-based outputs.

    Features:
    - Async subprocess execution
    - Timeout support
    - Environment variable injection
    - Working directory control
    - Output capture (stdout/stderr)
    - Shell/direct execution modes
    - Exit code validation
    - Custom file-based outputs
    - Scratch directory management
    """

    type_name: ClassVar[str] = "Shell"
    input_type: ClassVar[type[BlockInput]] = ShellInput
    output_type: ClassVar[type[BlockOutput]] = ShellOutput

    security_level: ClassVar[ExecutorSecurityLevel] = ExecutorSecurityLevel.PRIVILEGED
    capabilities: ClassVar[ExecutorCapabilities] = ExecutorCapabilities(
        can_execute_commands=True,
        can_read_files=True,
        can_write_files=True,
        can_network=True,
    )

    async def execute(  # type: ignore[override]
        self, inputs: ShellInput, context: dict[str, Any]
    ) -> Result[ShellOutput]:
        """Execute shell command."""
        timer = ExecutionTimer()

        try:
            # Prepare working directory
            cwd = Path(inputs.working_dir) if inputs.working_dir else Path.cwd()
            if not cwd.exists():
                return Result.failure(f"Working directory does not exist: {cwd}")

            # Setup scratch directory
            scratch_dir = cwd / ".scratch"
            scratch_dir.mkdir(exist_ok=True, mode=0o700)

            # Update .gitignore if it exists
            gitignore = cwd / ".gitignore"
            if gitignore.exists():
                content = gitignore.read_text()
                if ".scratch/" not in content:
                    with gitignore.open("a") as f:
                        f.write("\n.scratch/\n")

            # Prepare environment with SCRATCH
            env = dict(os.environ)
            if inputs.env:
                env.update(inputs.env)
            env["SCRATCH"] = ".scratch"

            # Execute command
            if inputs.shell:
                # Execute via shell (supports pipes, redirects, etc.)
                process = await asyncio.create_subprocess_shell(
                    inputs.command,
                    stdout=asyncio.subprocess.PIPE if inputs.capture_output else None,
                    stderr=asyncio.subprocess.PIPE if inputs.capture_output else None,
                    cwd=cwd,
                    env=env,
                )
            else:
                # Execute directly (safer, but no shell features)
                args = shlex.split(inputs.command)
                process = await asyncio.create_subprocess_exec(
                    *args,
                    stdout=asyncio.subprocess.PIPE if inputs.capture_output else None,
                    stderr=asyncio.subprocess.PIPE if inputs.capture_output else None,
                    cwd=cwd,
                    env=env,
                )

            # Wait for completion with timeout
            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(), timeout=inputs.timeout
                )
            except TimeoutError:
                process.kill()
                await process.wait()
                return Result.failure(
                    f"Command timed out after {inputs.timeout} seconds: {inputs.command}"
                )

            # Decode output
            stdout = stdout_bytes.decode("utf-8") if stdout_bytes else ""
            stderr = stderr_bytes.decode("utf-8") if stderr_bytes else ""
            exit_code = process.returncode or 0

            # Determine success (GitHub Actions semantics)
            # continue_on_error=false (default): fail on non-zero exit code
            # continue_on_error=true: always succeed, even on non-zero exit code
            success = True if inputs.continue_on_error else (exit_code == 0)

            # Build output dict with default fields
            output_dict = {
                "exit_code": exit_code,
                "stdout": stdout,
                "stderr": stderr,
                "success": success,
                "command_executed": inputs.command,
                "execution_time_ms": timer.elapsed_ms(),
            }

            # Read and merge custom outputs (if declared)
            # Note: custom_outputs come from the Block's outputs attribute, not inputs
            # This is handled by the Block class which injects it into context
            custom_outputs = context.get("__block_custom_outputs__")
            if custom_outputs:
                # Set SCRATCH for path expansion
                original_env = os.environ.get("SCRATCH")
                os.environ["SCRATCH"] = ".scratch"

                try:
                    for output_name, output_schema in custom_outputs.items():
                        try:
                            # Validate path
                            file_path = validate_output_path(
                                output_name,
                                output_schema["path"],
                                cwd,
                                output_schema.get("unsafe", False),
                            )

                            # Read file
                            content = file_path.read_text()

                            # Parse type
                            value = parse_output_value(content, output_schema["type"])

                            # TODO: Validate with expression if provided
                            # if output_schema.get("validation"):
                            #     # Use ConditionEvaluator to validate
                            #     pass

                            # Merge directly into output dict
                            output_dict[output_name] = value

                        except (OutputSecurityError, OutputNotFoundError, ValueError) as e:
                            if output_schema.get("required", True):
                                return Result.failure(f"Output '{output_name}' error: {e}")
                            # Optional output, continue without it
                finally:
                    # Restore original environment
                    if original_env is not None:
                        os.environ["SCRATCH"] = original_env
                    elif "SCRATCH" in os.environ:
                        del os.environ["SCRATCH"]

            # Create output with merged fields (extra="allow" handles custom fields)
            output = ShellOutput(**output_dict)  # type: ignore[arg-type]

            # Return failure if exit code is non-zero and continue_on_error is False (default)
            if not success:
                return Result.failure(
                    f"Command failed with exit code {exit_code}: {inputs.command}\n"
                    f"stderr: {stderr[:500]}"
                )

            return Result.success(output, metadata={"execution_time_ms": timer.elapsed_ms()})

        except Exception as e:
            return Result.failure(f"Failed to execute command: {inputs.command}\nError: {str(e)}")


# ============================================================================
# ExecuteWorkflow Executor
# ============================================================================


class ExecuteWorkflowInput(BlockInput):
    """Input model for ExecuteWorkflow executor.

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
    """Output model for ExecuteWorkflow executor.

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


class ExecuteWorkflowExecutor(BlockExecutor):
    """
    Workflow composition executor.

    Executes child workflows, enabling workflow composition patterns.
    Handles circular dependency detection and context isolation.

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

    Features:
    - Output composition: Child outputs become block outputs via extra="allow"
    - Context isolation: Child sees only passed inputs, not parent context
    - Circular dependency detection: Prevents A -> B -> A recursion
    - Error propagation: Child workflow failures become parent block failures
    - Execution tracking: Time and statistics from child execution
    """

    type_name: ClassVar[str] = "ExecuteWorkflow"
    input_type: ClassVar[type[BlockInput]] = ExecuteWorkflowInput
    output_type: ClassVar[type[BlockOutput]] = ExecuteWorkflowOutput

    security_level: ClassVar[ExecutorSecurityLevel] = ExecutorSecurityLevel.TRUSTED
    capabilities: ClassVar[ExecutorCapabilities] = ExecutorCapabilities(
        can_modify_state=True  # Can execute other workflows
    )

    async def execute(  # type: ignore[override]
        self, inputs: ExecuteWorkflowInput, context: dict[str, Any]
    ) -> Result[ExecuteWorkflowOutput]:
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
        timer = ExecutionTimer()

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
                return Result[ExecuteWorkflowOutput](
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
        # Extract child workflow outputs (from outputs namespace)
        child_workflow_outputs = child_result_dict.get("outputs", {})
        child_metadata = child_result_dict.get("metadata", {})

        # Build output dict with standard fields
        output_dict: dict[str, Any] = {
            "success": True,
            "workflow": workflow_name,
            "execution_time_ms": timer.elapsed_ms(),
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


# ============================================================================
# Registration
# ============================================================================

# Register executors with global registry
EXECUTOR_REGISTRY.register(ShellExecutor())
EXECUTOR_REGISTRY.register(ExecuteWorkflowExecutor())
