"""Test YAML workflow loader."""

import asyncio
from pathlib import Path

from workflows_mcp.engine.block import BLOCK_REGISTRY
from workflows_mcp.engine.blocks_example import EchoBlock
from workflows_mcp.engine.executor import WorkflowExecutor
from workflows_mcp.engine.loader import (
    load_workflow_from_file,
    validate_workflow_file,
)

# Get project root directory (parent of tests/)
PROJECT_ROOT = Path(__file__).parent.parent.parent
EXAMPLES_DIR = PROJECT_ROOT / "src" / "workflows_mcp" / "templates" / "examples"


def test_load_yaml_workflow():
    """Test loading workflow from YAML file."""
    # Ensure EchoBlock is registered
    if "EchoBlock" not in BLOCK_REGISTRY.list_types():
        BLOCK_REGISTRY.register("EchoBlock", EchoBlock)

    # Load and validate - using hello-world.yaml from examples
    result = load_workflow_from_file(str(EXAMPLES_DIR / "hello-world.yaml"))
    assert result.is_success, f"Failed to load workflow: {result.error}"

    workflow_def = result.value
    assert workflow_def is not None
    assert workflow_def.name == "hello-world"
    assert len(workflow_def.blocks) >= 1

    print("✓ Successfully loaded YAML workflow")
    print(f"  Name: {workflow_def.name}")
    print(f"  Description: {workflow_def.description}")
    print(f"  Blocks: {len(workflow_def.blocks)}")


def test_validate_yaml_workflow():
    """Test validation without conversion."""
    result = validate_workflow_file(str(EXAMPLES_DIR / "hello-world.yaml"))
    assert result.is_success, f"Validation failed: {result.error}"

    schema = result.value
    assert schema is not None
    assert schema.name == "hello-world"
    assert len(schema.tags) >= 1

    print("✓ Workflow validation passed")
    print(f"  Tags: {', '.join(schema.tags)}")
    print(f"  Version: {schema.version}")


def test_execute_yaml_workflow():
    """Test executing workflow loaded from YAML."""

    async def run_test():
        # Ensure EchoBlock is registered
        if "EchoBlock" not in BLOCK_REGISTRY.list_types():
            BLOCK_REGISTRY.register("EchoBlock", EchoBlock)

        # Load workflow - using sequential-echo.yaml which has simple structure
        result = load_workflow_from_file(str(EXAMPLES_DIR / "sequential-echo.yaml"))
        assert result.is_success, f"Failed to load: {result.error}"

        workflow_def = result.value
        assert workflow_def is not None

        # Execute with custom inputs
        executor = WorkflowExecutor()
        executor.load_workflow(workflow_def)

        exec_result = await executor.execute_workflow("sequential-echo", {})

        assert exec_result.is_success, f"Execution failed: {exec_result.error}"

        result_data = exec_result.value
        assert result_data is not None
        assert "metadata" in result_data
        assert len(result_data["blocks"]) > 0

        print("✓ Workflow execution successful")
        metadata = result_data["metadata"]
        print(f"  Execution time: {metadata['execution_time_seconds']:.3f}s")
        print(f"  Total blocks: {metadata['total_blocks']}")
        print(f"  Execution waves: {metadata['execution_waves']}")

    asyncio.run(run_test())


if __name__ == "__main__":
    print("Testing YAML workflow loader...\n")

    test_load_yaml_workflow()
    print()
    test_validate_yaml_workflow()
    print()
    test_execute_yaml_workflow()

    print("\n✅ All loader tests passed!")
