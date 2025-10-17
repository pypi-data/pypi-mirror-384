"""Integration tests for execute_inline_workflow MCP tool.

This module tests the execute_inline_workflow() MCP tool which allows
executing workflows provided as YAML strings without pre-registration.
"""

import pytest

from workflows_mcp.engine.response import WorkflowResponse
from workflows_mcp.tools import execute_inline_workflow


def to_dict(result):
    """Convert WorkflowResponse to dict for testing."""
    if isinstance(result, WorkflowResponse):
        return result.model_dump()
    return result


@pytest.mark.asyncio
async def test_execute_inline_workflow_simple_success(mock_context):
    """Test executing a simple inline workflow with EchoBlock."""
    workflow_yaml = """
name: test-inline-echo
description: Simple inline test workflow
tags: [test, inline]

blocks:
  - id: echo
    type: EchoBlock
    inputs:
      message: Hello from inline workflow
"""

    result = to_dict(await execute_inline_workflow(workflow_yaml, ctx=mock_context))

    assert result["status"] == "success"
    assert "outputs" in result
    # EchoBlock prepends "Echo: " to the message
    echo_output = result["blocks"]["echo"]["outputs"]["echoed"]
    assert echo_output == "Echo: Hello from inline workflow"


@pytest.mark.asyncio
async def test_execute_inline_workflow_with_inputs(mock_context):
    """Test inline workflow with runtime input substitution."""
    workflow_yaml = """
name: test-inline-with-inputs
description: Inline workflow with variable substitution
tags: [test, inline]

inputs:
  user_message:
    type: string
    description: Custom user message
    default: "Default message"

blocks:
  - id: echo
    type: EchoBlock
    inputs:
      message: "${inputs.user_message}"
"""

    result = to_dict(
        await execute_inline_workflow(
            workflow_yaml, inputs={"user_message": "Custom message"}, ctx=mock_context
        )
    )

    assert result["status"] == "success"
    # EchoBlock prepends "Echo: " to the message
    echo_output = result["blocks"]["echo"]["outputs"]["echoed"]
    assert echo_output == "Echo: Custom message"


@pytest.mark.asyncio
async def test_execute_inline_workflow_multi_block(mock_context):
    """Test inline workflow with multiple dependent blocks."""
    workflow_yaml = """
name: test-inline-multi-block
description: Multi-block inline workflow
tags: [test, inline]

blocks:
  - id: block1
    type: EchoBlock
    inputs:
      message: First block

  - id: block2
    type: EchoBlock
    inputs:
      message: "Got: ${blocks.block1.outputs.echoed}"
    depends_on:
      - block1

  - id: block3
    type: EchoBlock
    inputs:
      message: "Final: ${blocks.block2.outputs.echoed}"
    depends_on:
      - block2
"""

    result = to_dict(await execute_inline_workflow(workflow_yaml, ctx=mock_context))

    assert result["status"] == "success"
    # EchoBlock prepends "Echo: " to messages
    block1_output = result["blocks"]["block1"]["outputs"]["echoed"]
    assert block1_output == "Echo: First block"
    block2_output = result["blocks"]["block2"]["outputs"]["echoed"]
    assert block2_output == "Echo: Got: Echo: First block"
    block3_output = result["blocks"]["block3"]["outputs"]["echoed"]
    expected = "Echo: Final: Echo: Got: Echo: First block"
    assert block3_output == expected


@pytest.mark.asyncio
async def test_execute_inline_workflow_invalid_yaml(mock_context):
    """Test inline workflow with invalid YAML syntax."""
    invalid_yaml = """
name: test-invalid
description: Invalid YAML
blocks:
  - id: echo
    type: EchoBlock
    inputs:
      message: "Unclosed quote
"""

    result = to_dict(await execute_inline_workflow(invalid_yaml, ctx=mock_context))

    assert result["status"] == "failure"
    assert "error" in result
    assert "YAML" in result["error"]


@pytest.mark.asyncio
async def test_execute_inline_workflow_missing_required_field(mock_context):
    """Test inline workflow missing required fields."""
    incomplete_yaml = """
description: Missing name field
blocks:
  - id: echo
    type: EchoBlock
    inputs:
      message: Test
"""

    result = to_dict(await execute_inline_workflow(incomplete_yaml, ctx=mock_context))

    assert result["status"] == "failure"
    assert "error" in result


@pytest.mark.asyncio
async def test_execute_inline_workflow_unknown_block_type(mock_context):
    """Test inline workflow with unknown block type."""
    workflow_yaml = """
name: test-unknown-block
description: Workflow with unknown block type
blocks:
  - id: unknown
    type: NonExistentBlock
    inputs:
      foo: bar
"""

    result = to_dict(await execute_inline_workflow(workflow_yaml, ctx=mock_context))

    assert result["status"] == "failure"
    assert "error" in result


@pytest.mark.asyncio
async def test_execute_inline_workflow_with_outputs(mock_context):
    """Test inline workflow with output mappings.

    Note: Currently output mappings are defined in the YAML schema but block
    outputs are returned in the 'blocks' key. This test verifies the actual
    behavior rather than the ideal behavior.
    """
    workflow_yaml = """
name: test-inline-outputs
description: Inline workflow with output mappings
tags: [test, inline]

blocks:
  - id: echo
    type: EchoBlock
    inputs:
      message: Test output

outputs:
  result: "${blocks.echo.outputs.echoed}"
  execution_time: "${blocks.echo.outputs.execution_time_ms}"
"""

    result = to_dict(await execute_inline_workflow(workflow_yaml, ctx=mock_context))

    assert result["status"] == "success"
    # Test workflow-level outputs
    assert result["outputs"]["result"] == "Echo: Test output"
    assert "execution_time" in result["outputs"]
    # Also verify block outputs are in metadata
    echo_output = result["blocks"]["echo"]["outputs"]["echoed"]
    assert echo_output == "Echo: Test output"


@pytest.mark.asyncio
async def test_execute_inline_workflow_bash_command(mock_context):
    """Test inline workflow with Shell block."""
    workflow_yaml = """
name: test-inline-bash
description: Inline workflow with bash command
tags: [test, inline, bash]

blocks:
  - id: run_echo
    type: Shell
    inputs:
      command: echo "Hello from bash"
"""

    result = to_dict(await execute_inline_workflow(workflow_yaml, ctx=mock_context))

    assert result["status"] == "success"
    assert "run_echo" in result["blocks"]
    # Shell returns stdout in output
    stdout = result["blocks"]["run_echo"]["outputs"]["stdout"]
    assert "Hello from bash" in stdout


@pytest.mark.asyncio
async def test_execute_inline_workflow_use_case(mock_context):
    """Test the motivating use case: adapting existing workflow for new language.

    This simulates the scenario where an LLM:
    1. Examines python-quality-check via get_workflow_info()
    2. Creates a rust-quality-check YAML
    3. Executes it via execute_inline_workflow()
    """
    # Simulated Rust quality check workflow adapted from Python version
    rust_quality_workflow = """
name: rust-quality-check
description: Quality checks for Rust projects
tags: [rust, quality, linting]

inputs:
  source_path:
    type: string
    description: Path to Rust project source
    default: "."

blocks:
  - id: lint
    type: Shell
    inputs:
      command: echo "Running cargo clippy..."
      working_dir: "${inputs.source_path}"

  - id: format_check
    type: Shell
    inputs:
      command: echo "Running cargo fmt check..."
      working_dir: "${inputs.source_path}"
    depends_on:
      - lint

  - id: tests
    type: Shell
    inputs:
      command: echo "Running cargo test..."
      working_dir: "${inputs.source_path}"
    depends_on:
      - format_check

outputs:
  linting_passed: "${blocks.lint.outputs.success}"
  formatting_passed: "${blocks.format_check.outputs.success}"
  tests_passed: "${blocks.tests.outputs.success}"
"""

    result = to_dict(
        await execute_inline_workflow(
            rust_quality_workflow, inputs={"source_path": "."}, ctx=mock_context
        )
    )

    assert result["status"] == "success"
    # Verify all blocks executed successfully
    lint_success = result["blocks"]["lint"]["outputs"]["success"]
    assert lint_success is True
    format_success = result["blocks"]["format_check"]["outputs"]["success"]
    assert format_success is True
    tests_success = result["blocks"]["tests"]["outputs"]["success"]
    assert tests_success is True
