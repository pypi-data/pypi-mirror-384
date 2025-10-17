"""
Integration test for YAML workflow schema.

Tests that WorkflowSchema:
1. Validates YAML workflow definitions correctly
2. Converts to WorkflowDefinition format
3. Integrates with existing DAGResolver and WorkflowExecutor
4. Catches common validation errors with clear messages
"""

import asyncio

from workflows_mcp.engine.block import BLOCK_REGISTRY
from workflows_mcp.engine.blocks_example import EchoBlock
from workflows_mcp.engine.executor import WorkflowExecutor
from workflows_mcp.engine.schema import WorkflowSchema


def test_valid_workflow_schema():
    """Test that a valid workflow schema validates and converts correctly."""
    yaml_data = {
        "name": "test-workflow",
        "description": "Test workflow for validation",
        "tags": ["test"],
        "version": "1.0",
        "inputs": {
            "input_name": {
                "type": "string",
                "description": "Test input parameter",
                "default": "default_value",
            }
        },
        "blocks": [
            {
                "id": "block1",
                "type": "EchoBlock",
                "inputs": {"message": "Hello ${inputs.input_name}", "delay_ms": 0},
            },
            {
                "id": "block2",
                "type": "EchoBlock",
                "inputs": {
                    "message": "Output from block1: ${blocks.block1.outputs.echoed}",
                    "delay_ms": 0,
                },
                "depends_on": ["block1"],
            },
        ],
        "outputs": {"final_message": "${blocks.block2.outputs.echoed}"},
    }

    # Validate schema
    result = WorkflowSchema.validate_yaml_dict(yaml_data)
    assert result.is_success, f"Validation failed: {result.error}"

    schema = result.value
    assert schema is not None
    assert schema.name == "test-workflow"
    assert "test" in schema.tags
    assert len(schema.blocks) == 2
    assert "input_name" in schema.inputs

    # Convert to WorkflowDefinition
    workflow_def = schema.to_workflow_definition()
    assert workflow_def.name == "test-workflow"
    assert len(workflow_def.blocks) == 2

    print("✓ Valid workflow schema test passed")


def test_schema_with_executor():
    """Test that schema integrates with WorkflowExecutor."""

    async def run_test():
        # Ensure EchoBlock is registered
        if "EchoBlock" not in BLOCK_REGISTRY.list_types():
            BLOCK_REGISTRY.register("EchoBlock", EchoBlock)

        yaml_data = {
            "name": "executor-test",
            "description": "Executor integration test",
            "tags": ["test"],
            "blocks": [
                {
                    "id": "echo1",
                    "type": "EchoBlock",
                    "inputs": {"message": "First block", "delay_ms": 0},
                },
                {
                    "id": "echo2",
                    "type": "EchoBlock",
                    "inputs": {"message": "Second block depends on first", "delay_ms": 0},
                    "depends_on": ["echo1"],
                },
            ],
        }

        # Validate and convert
        result = WorkflowSchema.validate_yaml_dict(yaml_data)
        assert result.is_success, f"Schema validation failed: {result.error}"

        schema = result.value
        assert schema is not None
        workflow_def = schema.to_workflow_definition()

        # Execute with WorkflowExecutor
        executor = WorkflowExecutor()
        executor.load_workflow(workflow_def)

        exec_result = await executor.execute_workflow("executor-test", {})
        assert exec_result.is_success, f"Execution failed: {exec_result.error}"

        result_data = exec_result.value
        assert result_data is not None
        assert "echo1" in result_data["blocks"]
        assert "echo2" in result_data["blocks"]
        echo1_output = result_data["blocks"]["echo1"]["outputs"]["echoed"]
        assert echo1_output == "Echo: First block"

        print("✓ Executor integration test passed")

    asyncio.run(run_test())


def test_validation_errors():
    """Test that schema catches common validation errors."""

    # Test 1: Duplicate block IDs
    yaml_data_dup = {
        "name": "dup-test",
        "description": "Test duplicate IDs",
        "tags": ["test"],
        "blocks": [
            {"id": "block1", "type": "EchoBlock", "inputs": {"message": "msg1"}},
            {"id": "block1", "type": "EchoBlock", "inputs": {"message": "msg2"}},
        ],
    }

    result = WorkflowSchema.validate_yaml_dict(yaml_data_dup)
    assert not result.is_success, "Should fail with duplicate IDs"
    assert "Duplicate block IDs" in result.error
    print(f"✓ Caught duplicate block IDs: {result.error}")

    # Test 2: Unknown block type
    yaml_data_unknown = {
        "name": "unknown-test",
        "description": "Test unknown block type",
        "tags": ["test"],
        "blocks": [{"id": "block1", "type": "UnknownBlock", "inputs": {}}],
    }

    result = WorkflowSchema.validate_yaml_dict(yaml_data_unknown)
    assert not result.is_success, "Should fail with unknown block type"
    assert "Unknown block type" in result.error
    print(f"✓ Caught unknown block type: {result.error}")

    # Test 3: Invalid dependency reference
    yaml_data_dep = {
        "name": "dep-test",
        "description": "Test invalid dependency",
        "tags": ["test"],
        "blocks": [
            {
                "id": "block1",
                "type": "EchoBlock",
                "inputs": {"message": "msg"},
                "depends_on": ["nonexistent"],
            }
        ],
    }

    result = WorkflowSchema.validate_yaml_dict(yaml_data_dep)
    assert not result.is_success, "Should fail with invalid dependency"
    assert "depends on non-existent block" in result.error
    print(f"✓ Caught invalid dependency: {result.error}")

    # Test 4: Cyclic dependency
    yaml_data_cycle = {
        "name": "cycle-test",
        "description": "Test cyclic dependency",
        "tags": ["test"],
        "blocks": [
            {
                "id": "block1",
                "type": "EchoBlock",
                "inputs": {"message": "msg1"},
                "depends_on": ["block2"],
            },
            {
                "id": "block2",
                "type": "EchoBlock",
                "inputs": {"message": "msg2"},
                "depends_on": ["block1"],
            },
        ],
    }

    result = WorkflowSchema.validate_yaml_dict(yaml_data_cycle)
    assert not result.is_success, "Should fail with cyclic dependency"
    assert "Cyclic dependency" in result.error or "Invalid workflow dependencies" in result.error
    print(f"✓ Caught cyclic dependency: {result.error}")

    # Test 5: Invalid variable reference
    yaml_data_var = {
        "name": "var-test",
        "description": "Test invalid variable",
        "tags": ["test"],
        "blocks": [
            {
                "id": "block1",
                "type": "EchoBlock",
                "inputs": {"message": "${nonexistent_block.field}"},
            }
        ],
    }

    result = WorkflowSchema.validate_yaml_dict(yaml_data_var)
    assert not result.is_success, "Should fail with invalid variable reference"
    assert "Invalid variable reference" in result.error
    print(f"✓ Caught invalid variable reference: {result.error}")

    # Test 6: Invalid input type with default
    yaml_data_type = {
        "name": "type-test",
        "description": "Test type validation",
        "tags": ["test"],
        "inputs": {
            "bad_input": {
                "type": "integer",
                "description": "Should be integer",
                "default": "not_an_integer",
            }
        },
        "blocks": [{"id": "block1", "type": "EchoBlock", "inputs": {"message": "test"}}],
    }

    result = WorkflowSchema.validate_yaml_dict(yaml_data_type)
    assert not result.is_success, "Should fail with type mismatch"
    assert "does not match declared type" in result.error
    print(f"✓ Caught type mismatch: {result.error}")

    print("✓ All validation error tests passed")


def test_metadata_extraction():
    """Test metadata property extraction."""
    yaml_data = {
        "name": "metadata-test",
        "description": "Test metadata",
        "tags": ["test", "example"],
        "version": "2.1",
        "author": "Test Author",
        "blocks": [{"id": "block1", "type": "EchoBlock", "inputs": {"message": "test"}}],
    }

    result = WorkflowSchema.validate_yaml_dict(yaml_data)
    assert result.is_success

    schema = result.value
    assert schema is not None
    metadata = schema.metadata

    assert metadata.name == "metadata-test"
    assert metadata.description == "Test metadata"
    assert metadata.version == "2.1"
    assert metadata.author == "Test Author"
    assert "test" in metadata.tags
    assert "example" in metadata.tags

    print("✓ Metadata extraction test passed")


if __name__ == "__main__":
    print("Running YAML workflow schema integration tests...\n")

    # Ensure EchoBlock is registered
    if "EchoBlock" not in BLOCK_REGISTRY.list_types():
        BLOCK_REGISTRY.register("EchoBlock", EchoBlock)

    test_valid_workflow_schema()
    test_schema_with_executor()
    test_validation_errors()
    test_metadata_extraction()

    print("\n✅ All integration tests passed!")
