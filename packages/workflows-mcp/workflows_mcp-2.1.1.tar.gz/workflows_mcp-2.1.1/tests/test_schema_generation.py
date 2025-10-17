"""Tests for schema generation and validation."""

import json

import pytest


@pytest.fixture(autouse=True)
def ensure_executors_registered():
    """Ensure all executors are registered before each test.

    This fixture re-registers executors in case other tests have cleared the registry.
    Module-level registration only happens once, so we need to manually re-register.
    """
    from workflows_mcp.engine.executor_base import EXECUTOR_REGISTRY

    # If registry is empty or missing core executors, re-register them
    if len(EXECUTOR_REGISTRY.list_types()) < 11:  # Expecting 11 core executors
        # Import and manually register all executors
        from workflows_mcp.engine.executors_core import ExecuteWorkflowExecutor, ShellExecutor
        from workflows_mcp.engine.executors_file import (
            CreateFileExecutor,
            PopulateTemplateExecutor,
            ReadFileExecutor,
        )
        from workflows_mcp.engine.executors_interactive import (
            AskChoiceExecutor,
            ConfirmOperationExecutor,
            GetInputExecutor,
        )
        from workflows_mcp.engine.executors_state import (
            MergeJSONStateExecutor,
            ReadJSONStateExecutor,
            WriteJSONStateExecutor,
        )

        # Re-register if not present
        executors_to_register = [
            ShellExecutor(),
            ExecuteWorkflowExecutor(),
            CreateFileExecutor(),
            ReadFileExecutor(),
            PopulateTemplateExecutor(),
            ConfirmOperationExecutor(),
            AskChoiceExecutor(),
            GetInputExecutor(),
            ReadJSONStateExecutor(),
            WriteJSONStateExecutor(),
            MergeJSONStateExecutor(),
        ]

        for executor in executors_to_register:
            if not EXECUTOR_REGISTRY.has_type(executor.type_name):
                EXECUTOR_REGISTRY.register(executor)

    yield


from workflows_mcp.engine.executor_base import EXECUTOR_REGISTRY  # noqa: E402


def test_schema_generation():
    """Test schema generation from registry."""
    schema = EXECUTOR_REGISTRY.generate_workflow_schema()

    # Verify schema structure
    assert schema["$schema"] == "http://json-schema.org/draft-07/schema#"
    assert "properties" in schema
    assert "blocks" in schema["properties"]
    assert "definitions" in schema

    # Verify core executors are included
    # Note: Other tests may clear the registry, so we only check what's currently registered
    block_types = schema["properties"]["blocks"]["items"]["properties"]["type"]["enum"]
    registered_types = EXECUTOR_REGISTRY.list_types()

    # Schema should include all registered executor types
    assert len(block_types) > 0, "Schema should include at least one block type"
    assert set(block_types) == set(registered_types), (
        "Schema block types should match registered executors"
    )

    # Core executors that should be present when all modules are loaded
    expected_core_executors = {
        "Shell",
        "CreateFile",
        "ReadFile",
        "PopulateTemplate",
        "ExecuteWorkflow",
        "ReadJSONState",
        "WriteJSONState",
        "MergeJSONState",
        "ConfirmOperation",
        "AskChoice",
        "GetInput",
    }

    # Check if we have the expected core executors
    # (They should all be there since we explicitly imported the executor modules)
    missing_core = expected_core_executors - set(block_types)
    assert not missing_core, f"Missing core executors in schema: {missing_core}"


def test_schema_has_all_executor_definitions():
    """Test that schema includes input definitions for all executors."""
    schema = EXECUTOR_REGISTRY.generate_workflow_schema()

    # All executor types should have input definitions
    block_types = schema["properties"]["blocks"]["items"]["properties"]["type"]["enum"]

    for block_type in block_types:
        definition_key = f"{block_type}Input"
        assert definition_key in schema["definitions"], f"Missing definition for {block_type}"


def test_schema_json_serializable():
    """Test that schema is JSON serializable."""
    schema = EXECUTOR_REGISTRY.generate_workflow_schema()

    # Should serialize to JSON without errors
    json_str = json.dumps(schema, indent=2)
    assert len(json_str) > 0

    # Should deserialize back
    parsed = json.loads(json_str)
    assert parsed == schema


def test_validate_valid_workflow():
    """Test validation of valid workflow."""
    from jsonschema import validate

    schema = EXECUTOR_REGISTRY.generate_workflow_schema()

    workflow = {
        "name": "test-workflow",
        "blocks": [{"id": "test", "type": "Shell", "inputs": {"command": "echo test"}}],
    }

    # Should not raise
    validate(instance=workflow, schema=schema)


def test_validate_invalid_workflow_missing_name():
    """Test validation catches missing required field."""
    from jsonschema import ValidationError, validate

    schema = EXECUTOR_REGISTRY.generate_workflow_schema()

    workflow = {
        # Missing "name" (required)
        "blocks": []
    }

    with pytest.raises(ValidationError):
        validate(instance=workflow, schema=schema)


def test_validate_invalid_workflow_unknown_type():
    """Test validation catches unknown block type."""
    from jsonschema import ValidationError, validate

    schema = EXECUTOR_REGISTRY.generate_workflow_schema()

    workflow = {
        "name": "test",
        "blocks": [
            {
                "id": "test",
                "type": "NonExistentBlock",  # Unknown type
                "inputs": {},
            }
        ],
    }

    with pytest.raises(ValidationError):
        validate(instance=workflow, schema=schema)
