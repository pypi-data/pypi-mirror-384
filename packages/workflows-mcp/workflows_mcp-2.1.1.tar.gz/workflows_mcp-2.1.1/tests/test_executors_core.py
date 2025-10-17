"""Tests for core executors (Shell, ExecuteWorkflow)."""

import tempfile
from pathlib import Path

import pytest

# Import from engine package to ensure executors are registered
# Import module to trigger executor registration
from workflows_mcp.engine import (
    EXECUTOR_REGISTRY,
    ExecuteWorkflowExecutor,
    ExecuteWorkflowInput,
    ShellExecutor,
    ShellInput,
    executors_core,  # noqa: F401
)
from workflows_mcp.engine.block import Block


@pytest.fixture(autouse=True)
def ensure_executors_registered():
    """Ensure executors are registered before each test."""
    # Re-register if registry was cleared
    if not EXECUTOR_REGISTRY.has_type("Shell"):
        # Need to re-execute registration code
        # Import fresh instances to re-register
        shell_exec = ShellExecutor()
        workflow_exec = ExecuteWorkflowExecutor()
        EXECUTOR_REGISTRY.register(shell_exec)
        EXECUTOR_REGISTRY.register(workflow_exec)
    yield


@pytest.mark.asyncio
async def test_shell_executor_simple_command():
    """Test Shell executor with simple command."""
    executor = ShellExecutor()
    inputs = ShellInput(command="echo 'Hello, World!'")

    result = await executor.execute(inputs, context={})

    assert result.is_success
    assert result.value.success is True
    assert result.value.exit_code == 0
    assert "Hello, World!" in result.value.stdout
    assert result.value.stderr == ""


@pytest.mark.asyncio
async def test_shell_executor_failure():
    """Test Shell executor with failing command."""
    executor = ShellExecutor()
    inputs = ShellInput(command="exit 1")

    result = await executor.execute(inputs, context={})

    assert not result.is_success  # Executor returns failure for non-zero exit
    assert "failed with exit code 1" in result.error.lower()


@pytest.mark.asyncio
async def test_shell_executor_continue_on_error():
    """Test Shell executor with continue_on_error flag."""
    executor = ShellExecutor()
    # Use kebab-case as dict to test alias support
    inputs = ShellInput(**{"command": "exit 1", "continue-on-error": True})

    result = await executor.execute(inputs, context={})

    assert result.is_success  # continue_on_error makes it succeed
    assert result.value.success is True  # success flag is True
    assert result.value.exit_code == 1  # but exit code is still 1


@pytest.mark.asyncio
async def test_shell_executor_with_working_dir():
    """Test Shell executor with working directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test file
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("test content")

        executor = ShellExecutor()
        inputs = ShellInput(command="ls test.txt", working_dir=tmpdir)

        result = await executor.execute(inputs, context={})

        assert result.is_success
        assert result.value.success is True
        assert "test.txt" in result.value.stdout


@pytest.mark.asyncio
async def test_shell_executor_with_env():
    """Test Shell executor with environment variables."""
    executor = ShellExecutor()
    inputs = ShellInput(command="echo $MY_VAR", env={"MY_VAR": "custom_value"})

    result = await executor.execute(inputs, context={})

    assert result.is_success
    assert "custom_value" in result.value.stdout


@pytest.mark.asyncio
async def test_shell_executor_timeout():
    """Test Shell executor with timeout."""
    executor = ShellExecutor()
    inputs = ShellInput(command="sleep 10", timeout=1)  # 1 second timeout

    result = await executor.execute(inputs, context={})

    assert not result.is_success
    assert "timed out" in result.error.lower()


@pytest.mark.asyncio
async def test_shell_executor_scratch_directory():
    """Test Shell executor creates .scratch directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        executor = ShellExecutor()
        inputs = ShellInput(
            command="echo 'test' > $SCRATCH/output.txt",
            working_dir=tmpdir,
        )

        result = await executor.execute(inputs, context={})

        assert result.is_success
        # Check scratch directory was created
        scratch_dir = Path(tmpdir) / ".scratch"
        assert scratch_dir.exists()
        assert scratch_dir.is_dir()
        # Check file was created in scratch
        output_file = scratch_dir / "output.txt"
        assert output_file.exists()
        assert output_file.read_text().strip() == "test"


@pytest.mark.asyncio
async def test_shell_executor_custom_outputs():
    """Test Shell executor with custom file-based outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create output file
        output_file = Path(tmpdir) / ".scratch" / "result.json"
        output_file.parent.mkdir(exist_ok=True)

        executor = ShellExecutor()
        inputs = ShellInput(
            command='echo \'{"status": "success"}\' > $SCRATCH/result.json',
            working_dir=tmpdir,
        )

        # Custom outputs are passed via context (normally set by Block class)
        context = {
            "__block_custom_outputs__": {
                "test_result": {
                    "type": "json",
                    "path": "$SCRATCH/result.json",
                    "required": True,
                }
            }
        }

        result = await executor.execute(inputs, context)

        assert result.is_success
        # Check custom output was read
        assert hasattr(result.value, "test_result")
        assert result.value.test_result == {"status": "success"}


@pytest.mark.asyncio
async def test_shell_executor_via_block():
    """Test Shell executor via Block class."""
    # Ensure executor is registered
    assert EXECUTOR_REGISTRY.has_type("Shell")

    # Create block
    block = Block(id="test_shell", type="Shell", inputs={"command": "echo 'test'"})

    # Execute
    result = await block.execute(context={})

    assert result.is_success
    assert "test" in result.value.stdout


@pytest.mark.asyncio
async def test_shell_executor_without_shell():
    """Test Shell executor in direct execution mode (no shell)."""
    executor = ShellExecutor()
    inputs = ShellInput(command="echo test", shell=False)

    result = await executor.execute(inputs, context={})

    assert result.is_success
    assert "test" in result.value.stdout


@pytest.mark.asyncio
async def test_execute_workflow_executor_circular_detection():
    """Test ExecuteWorkflow circular dependency detection."""
    executor = ExecuteWorkflowExecutor()
    inputs = ExecuteWorkflowInput(workflow="child-workflow")

    # Simulate circular dependency with a mock executor
    # Need to provide a real executor object (even though it won't be used)
    # to get past the "executor not found" check
    from workflows_mcp.engine.executor import WorkflowExecutor

    mock_executor = WorkflowExecutor({})
    context = {
        "__internal__": {
            "workflow_stack": ["parent", "child-workflow"],
            "executor": mock_executor,
        }
    }

    result = await executor.execute(inputs, context)

    assert not result.is_success
    assert "circular" in result.error.lower()


@pytest.mark.asyncio
async def test_execute_workflow_executor_missing_executor():
    """Test ExecuteWorkflow with missing executor in context."""
    executor = ExecuteWorkflowExecutor()
    inputs = ExecuteWorkflowInput(workflow="test-workflow")

    # Context without executor
    context = {"__internal__": {}}

    result = await executor.execute(inputs, context)

    assert not result.is_success
    assert "executor not found" in result.error.lower()


@pytest.mark.asyncio
async def test_execute_workflow_executor_registry():
    """Test ExecuteWorkflow executor is registered."""
    assert EXECUTOR_REGISTRY.has_type("ExecuteWorkflow")

    # Get executor from registry (method is 'get', not 'get_executor')
    executor_instance = EXECUTOR_REGISTRY.get("ExecuteWorkflow")
    assert executor_instance is not None
    assert isinstance(executor_instance, ExecuteWorkflowExecutor)


def test_shell_executor_capabilities():
    """Test Shell executor security capabilities."""
    executor = ShellExecutor()
    caps = executor.get_capabilities()

    assert caps["type"] == "Shell"
    assert caps["security_level"] == "privileged"
    assert caps["capabilities"]["can_execute_commands"] is True
    assert caps["capabilities"]["can_read_files"] is True
    assert caps["capabilities"]["can_write_files"] is True
    assert caps["capabilities"]["can_network"] is True


def test_execute_workflow_executor_capabilities():
    """Test ExecuteWorkflow executor security capabilities."""
    executor = ExecuteWorkflowExecutor()
    caps = executor.get_capabilities()

    assert caps["type"] == "ExecuteWorkflow"
    assert caps["security_level"] == "trusted"
    assert caps["capabilities"]["can_modify_state"] is True


def test_shell_input_validation():
    """Test Shell input validation."""
    # Valid input
    valid = ShellInput(command="echo test")
    assert valid.command == "echo test"
    assert valid.timeout == 120  # default
    assert valid.shell is True  # default
    assert valid.continue_on_error is False  # default

    # Invalid - missing command
    with pytest.raises(Exception):
        ShellInput()


def test_shell_input_alias():
    """Test Shell input with continue-on-error alias."""
    # Using kebab-case alias (YAML style)
    inputs = ShellInput(**{"command": "test", "continue-on-error": True})
    assert inputs.continue_on_error is True


def test_execute_workflow_input_validation():
    """Test ExecuteWorkflow input validation."""
    # Valid input
    valid = ExecuteWorkflowInput(workflow="test-workflow")
    assert valid.workflow == "test-workflow"
    assert valid.inputs == {}  # default

    # Valid with inputs
    with_inputs = ExecuteWorkflowInput(workflow="test", inputs={"key": "value"})
    assert with_inputs.inputs == {"key": "value"}

    # Invalid - missing workflow
    with pytest.raises(Exception):
        ExecuteWorkflowInput()


@pytest.mark.asyncio
async def test_shell_executor_output_metadata():
    """Test Shell executor includes execution metadata."""
    executor = ShellExecutor()
    inputs = ShellInput(command="echo test")

    result = await executor.execute(inputs, context={})

    assert result.is_success
    # Check metadata includes execution time
    assert "execution_time_ms" in result.metadata
    assert result.metadata["execution_time_ms"] > 0


@pytest.mark.asyncio
async def test_shell_executor_nonexistent_working_dir():
    """Test Shell executor with nonexistent working directory."""
    executor = ShellExecutor()
    inputs = ShellInput(
        command="echo test",
        working_dir="/nonexistent/directory/path",
    )

    result = await executor.execute(inputs, context={})

    assert not result.is_success
    assert "does not exist" in result.error.lower()


@pytest.mark.asyncio
async def test_shell_executor_command_with_pipes():
    """Test Shell executor with shell features (pipes)."""
    executor = ShellExecutor()
    inputs = ShellInput(command="echo 'hello world' | wc -w", shell=True)

    result = await executor.execute(inputs, context={})

    assert result.is_success
    assert "2" in result.value.stdout.strip()  # 2 words


@pytest.mark.asyncio
async def test_shell_executor_stderr_capture():
    """Test Shell executor captures stderr."""
    executor = ShellExecutor()
    # Use kebab-case as dict to test alias support
    inputs = ShellInput(
        **{
            "command": "echo 'error message' >&2",  # Write to stderr
            "continue-on-error": True,  # Don't fail on non-zero exit
        }
    )

    result = await executor.execute(inputs, context={})

    assert result.is_success
    assert "error message" in result.value.stderr
