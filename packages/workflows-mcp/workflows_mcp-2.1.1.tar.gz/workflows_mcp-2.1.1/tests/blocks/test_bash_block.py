"""Test Shell block implementation.

Validates:
- Command execution (shell and direct modes)
- Timeout handling
- Working directory support
- Environment variable injection
- Exit code validation
- Output capture (stdout/stderr)
- Error handling
"""

import asyncio
import tempfile
from pathlib import Path

import pytest

from workflows_mcp.engine.block import BLOCK_REGISTRY
from workflows_mcp.engine.blocks_bash import Shell, ShellOutput


@pytest.mark.asyncio
async def test_basic_command_execution():
    """Test basic command execution."""
    print("\nTest 1: Basic command execution")

    block = Shell(id="echo_test", inputs={"command": "echo 'Hello World'"})

    result = await block.execute(context={})

    assert result.is_success, f"Block execution should succeed: {result.error}"
    assert result.value is not None
    assert isinstance(result.value, ShellOutput)
    assert "Hello World" in result.value.stdout
    assert result.value.exit_code == 0
    assert result.value.success is True
    print(f"  ✓ Command executed: {result.value.command_executed}")
    print(f"  ✓ Output: {result.value.stdout.strip()}")
    print(f"  ✓ Execution time: {result.value.execution_time_ms:.1f}ms")


@pytest.mark.asyncio
async def test_command_with_exit_code():
    """Test command with non-zero exit code."""
    print("\nTest 2: Command with non-zero exit code")

    # Command that fails (exit code 1)
    block = Shell(id="fail_test", inputs={"command": "exit 1"})

    result = await block.execute(context={})

    assert not result.is_success, "Block execution should fail for non-zero exit code"
    assert "exit code 1" in result.error
    print(f"  ✓ Failed as expected: {result.error[:80]}")

    # Test with continue-on-error=true (GitHub Actions semantics: continue even on error)
    block2 = Shell(id="ignore_exit", inputs={"command": "exit 1", "continue-on-error": True})

    result2 = await block2.execute(context={})

    assert result2.is_success, "Block should succeed when continue_on_error=True"
    assert result2.value is not None
    assert result2.value.exit_code == 1
    assert result2.value.success is True  # Success despite exit code
    print(f"  ✓ Exit code ignored: exit_code={result2.value.exit_code}, success=True")


@pytest.mark.asyncio
async def test_working_directory():
    """Test working directory support."""
    print("\nTest 3: Working directory support")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a test file in temp directory
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("test content")

        # Execute command in temp directory
        block = Shell(
            id="pwd_test",
            inputs={"command": "pwd && ls test.txt", "working_dir": tmpdir},
        )

        result = await block.execute(context={})

        assert result.is_success, f"Block execution should succeed: {result.error}"
        assert result.value is not None
        assert tmpdir in result.value.stdout
        assert "test.txt" in result.value.stdout
        print(f"  ✓ Working directory: {tmpdir}")
        print(f"  ✓ Output: {result.value.stdout.strip()}")


@pytest.mark.asyncio
async def test_invalid_working_directory():
    """Test handling of invalid working directory."""
    print("\nTest 4: Invalid working directory")

    block = Shell(
        id="bad_dir",
        inputs={"command": "echo test", "working_dir": "/nonexistent/directory"},
    )

    result = await block.execute(context={})

    assert not result.is_success, "Block should fail for non-existent working directory"
    assert "does not exist" in result.error
    print(f"  ✓ Failed as expected: {result.error[:80]}")


@pytest.mark.asyncio
async def test_environment_variables():
    """Test environment variable injection."""
    print("\nTest 5: Environment variables")

    block = Shell(
        id="env_test",
        inputs={
            "command": "echo $TEST_VAR $ANOTHER_VAR",
            "env": {"TEST_VAR": "hello", "ANOTHER_VAR": "world"},
        },
    )

    result = await block.execute(context={})

    assert result.is_success, f"Block execution should succeed: {result.error}"
    assert result.value is not None
    assert "hello" in result.value.stdout
    assert "world" in result.value.stdout
    print("  ✓ Environment variables: TEST_VAR=hello, ANOTHER_VAR=world")
    print(f"  ✓ Output: {result.value.stdout.strip()}")


@pytest.mark.asyncio
async def test_timeout_handling():
    """Test timeout handling."""
    print("\nTest 6: Timeout handling")

    # Command that sleeps for 5 seconds with 1 second timeout
    block = Shell(id="timeout_test", inputs={"command": "sleep 5", "timeout": 1})

    result = await block.execute(context={})

    assert not result.is_success, "Block should fail on timeout"
    assert "timed out" in result.error
    print(f"  ✓ Timeout detected: {result.error[:80]}")


@pytest.mark.asyncio
async def test_shell_vs_direct_execution():
    """Test shell vs direct execution modes."""
    print("\nTest 7: Shell vs direct execution")

    # Shell mode: supports pipes and redirects
    block_shell = Shell(
        id="shell_test",
        inputs={"command": "echo 'hello' | tr 'a-z' 'A-Z'", "shell": True},
    )

    result_shell = await block_shell.execute(context={})

    assert result_shell.is_success, f"Shell mode execution should succeed: {result_shell.error}"
    assert result_shell.value is not None
    assert "HELLO" in result_shell.value.stdout
    print(f"  ✓ Shell mode: {result_shell.value.stdout.strip()}")

    # Direct mode: doesn't support shell features but is safer
    block_direct = Shell(id="direct_test", inputs={"command": "echo hello", "shell": False})

    result_direct = await block_direct.execute(context={})

    assert result_direct.is_success, f"Direct mode execution should succeed: {result_direct.error}"
    assert result_direct.value is not None
    assert "hello" in result_direct.value.stdout
    print(f"  ✓ Direct mode: {result_direct.value.stdout.strip()}")


@pytest.mark.asyncio
async def test_output_capture():
    """Test stdout and stderr capture."""
    print("\nTest 8: Output capture (stdout/stderr)")

    # Command that writes to both stdout and stderr
    block = Shell(
        id="output_test",
        inputs={"command": "echo 'to stdout' && echo 'to stderr' >&2"},
    )

    result = await block.execute(context={})

    assert result.is_success, f"Block execution should succeed: {result.error}"
    assert result.value is not None
    assert "to stdout" in result.value.stdout
    assert "to stderr" in result.value.stderr
    print(f"  ✓ stdout: {result.value.stdout.strip()}")
    print(f"  ✓ stderr: {result.value.stderr.strip()}")


@pytest.mark.asyncio
async def test_block_registry():
    """Test Shell is registered in BLOCK_REGISTRY."""
    print("\nTest 9: Block registry")

    block_class = BLOCK_REGISTRY.get("Shell")
    assert block_class is Shell

    # Instantiate via registry
    block = block_class(id="registry_test", inputs={"command": "echo 'from registry'"})

    result = await block.execute(context={})

    assert result.is_success, f"Block execution should succeed: {result.error}"
    assert result.value is not None
    assert "from registry" in result.value.stdout
    print("  ✓ Block registered as 'Shell'")
    print(f"  ✓ Output: {result.value.stdout.strip()}")


@pytest.mark.asyncio
async def test_input_validation():
    """Test input validation."""
    print("\nTest 10: Input validation")

    # Missing required field
    try:
        _ = Shell(id="bad_input", inputs={})
        assert False, "Should have raised validation error for missing 'command'"
    except ValueError as e:
        assert "command" in str(e).lower()
        print(f"  ✓ Validation error for missing field: {str(e)[:80]}")

    # Invalid type
    try:
        _ = Shell(id="bad_type", inputs={"command": "echo test", "timeout": "not_an_int"})
        assert False, "Should have raised validation error for invalid type"
    except ValueError as e:
        print(f"  ✓ Validation error for invalid type: {str(e)[:80]}")


@pytest.mark.asyncio
async def test_parallel_execution():
    """Test parallel execution of multiple Shell blocks."""
    print("\nTest 11: Parallel execution")

    import time

    # Create multiple blocks with small delays
    blocks = [
        Shell(
            id=f"parallel_{i}",
            inputs={"command": f"sleep 0.1 && echo 'Block {i}'"},
        )
        for i in range(5)
    ]

    start = time.time()
    results = await asyncio.gather(*[block.execute({}) for block in blocks])
    elapsed = (time.time() - start) * 1000

    assert all(r.is_success for r in results)
    # Should be faster than sequential (5 * 100ms = 500ms)
    # Parallel should be ~100-200ms
    assert elapsed < 400, f"Parallel execution should be faster: {elapsed:.1f}ms"
    print(f"  ✓ {len(blocks)} blocks executed in {elapsed:.1f}ms (parallel)")


@pytest.mark.asyncio
async def test_complex_command():
    """Test complex multi-line command."""
    print("\nTest 12: Complex multi-line command")

    command = """
    for i in 1 2 3; do
        echo "Number: $i"
    done
    """

    block = Shell(id="complex_test", inputs={"command": command})

    result = await block.execute(context={})

    assert result.is_success, f"Block execution should succeed: {result.error}"
    assert result.value is not None
    assert "Number: 1" in result.value.stdout
    assert "Number: 2" in result.value.stdout
    assert "Number: 3" in result.value.stdout
    print("  ✓ Complex command executed")
    print(f"  ✓ Output lines: {len(result.value.stdout.strip().split())}")


if __name__ == "__main__":
    # Run tests manually
    print("=" * 80)
    print("Shell Block Tests")
    print("=" * 80)

    async def run_tests():
        await test_basic_command_execution()
        await test_command_with_exit_code()
        await test_working_directory()
        await test_invalid_working_directory()
        await test_environment_variables()
        await test_timeout_handling()
        await test_shell_vs_direct_execution()
        await test_output_capture()
        await test_block_registry()
        await test_input_validation()
        await test_parallel_execution()
        await test_complex_command()

    asyncio.run(run_tests())

    print("\n" + "=" * 80)
    print("All tests passed! ✅")
    print("=" * 80)
