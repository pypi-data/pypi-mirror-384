"""Tests for executor base architecture."""

import pytest
from pydantic import Field

from workflows_mcp.engine.block import Block, BlockInput, BlockOutput
from workflows_mcp.engine.executor_base import (
    EXECUTOR_REGISTRY,
    BlockExecutor,
    ExecutorCapabilities,
    ExecutorRegistry,
    ExecutorSecurityLevel,
)
from workflows_mcp.engine.result import Result


@pytest.fixture
def clear_global_registry():
    """Clear global registry before each test to prevent test pollution.

    This fixture must be explicitly requested by tests that need a clean registry.
    It's not autouse to avoid clearing the registry for tests in other modules
    that depend on executors being registered.
    """
    EXECUTOR_REGISTRY._executors.clear()
    yield
    # Re-register the standard executors after clearing
    from workflows_mcp.engine import executors_core, executors_file  # noqa: F401


# Test executor implementation
class DemoInput(BlockInput):
    """Demo input model for testing."""

    message: str = Field(description="Test message")


class DemoOutput(BlockOutput):
    """Demo output model for testing."""

    result: str = Field(description="Test result")


class DemoExecutor(BlockExecutor):
    """Demo executor for testing purposes."""

    type_name = "Demo"
    input_type = DemoInput
    output_type = DemoOutput
    security_level = ExecutorSecurityLevel.SAFE

    async def execute(self, inputs: BlockInput, context: dict) -> Result[BlockOutput]:
        """Execute demo logic."""
        demo_inputs = inputs  # Already validated as DemoInput
        output = DemoOutput(result=f"Processed: {demo_inputs.message}")
        return Result.success(output)


def test_executor_registration(clear_global_registry):
    """Test executor registration."""
    registry = ExecutorRegistry()
    executor = DemoExecutor()

    registry.register(executor)

    assert registry.has_type("Demo")
    assert registry.get("Demo") == executor
    assert "Demo" in registry.list_types()


def test_executor_duplicate_registration(clear_global_registry):
    """Test that duplicate registration fails."""
    registry = ExecutorRegistry()
    executor = DemoExecutor()

    registry.register(executor)

    with pytest.raises(ValueError, match="already registered"):
        registry.register(executor)


def test_executor_unknown_type(clear_global_registry):
    """Test that unknown type raises error."""
    registry = ExecutorRegistry()

    with pytest.raises(ValueError, match="Unknown block type"):
        registry.get("NonExistent")


@pytest.mark.asyncio
async def test_block_execution(clear_global_registry):
    """Test block execution via executor."""
    # Create fresh registry
    from workflows_mcp.engine.executor_base import EXECUTOR_REGISTRY

    executor = DemoExecutor()
    EXECUTOR_REGISTRY.register(executor)

    # Create block using new architecture
    block = Block(id="test1", type="Demo", inputs={"message": "hello"})

    # Execute
    result = await block.execute(context={})

    assert result.is_success
    assert result.value.result == "Processed: hello"


def test_schema_generation(clear_global_registry):
    """Test JSON Schema generation."""
    registry = ExecutorRegistry()
    executor = DemoExecutor()
    registry.register(executor)

    schema = registry.generate_workflow_schema()

    assert schema["$schema"] == "http://json-schema.org/draft-07/schema#"
    assert "Demo" in schema["properties"]["blocks"]["items"]["properties"]["type"]["enum"]
    assert "DemoInput" in schema["definitions"]


def test_executor_input_schema(clear_global_registry):
    """Test executor input schema generation."""
    executor = DemoExecutor()

    schema = executor.get_input_schema()

    assert "properties" in schema
    assert "message" in schema["properties"]
    assert schema["properties"]["message"]["description"] == "Test message"


def test_executor_output_schema(clear_global_registry):
    """Test executor output schema generation."""
    executor = DemoExecutor()

    schema = executor.get_output_schema()

    assert "properties" in schema
    assert "result" in schema["properties"]


def test_executor_capabilities(clear_global_registry):
    """Test executor capabilities retrieval."""
    executor = DemoExecutor()

    capabilities = executor.get_capabilities()

    assert capabilities["type"] == "Demo"
    assert capabilities["security_level"] == "safe"
    assert "capabilities" in capabilities


def test_executor_security_level(clear_global_registry):
    """Test executor security level attributes."""
    executor = DemoExecutor()

    assert executor.security_level == ExecutorSecurityLevel.SAFE


def test_executor_capabilities_model(clear_global_registry):
    """Test ExecutorCapabilities model."""
    caps = ExecutorCapabilities(can_read_files=True, can_write_files=True)

    assert caps.can_read_files is True
    assert caps.can_write_files is True
    assert caps.can_execute_commands is False
    assert caps.can_network is False


def test_registry_list_types(clear_global_registry):
    """Test listing registered types."""
    registry = ExecutorRegistry()

    # Should be empty initially
    assert registry.list_types() == []

    # Register executor
    executor = DemoExecutor()
    registry.register(executor)

    # Should contain Demo
    assert registry.list_types() == ["Demo"]


def test_registry_has_type(clear_global_registry):
    """Test checking if type exists."""
    registry = ExecutorRegistry()
    executor = DemoExecutor()
    registry.register(executor)

    assert registry.has_type("Demo") is True
    assert registry.has_type("NonExistent") is False


@pytest.mark.asyncio
async def test_block_invalid_inputs(clear_global_registry):
    """Test block creation with invalid inputs."""
    from workflows_mcp.engine.executor_base import EXECUTOR_REGISTRY

    executor = DemoExecutor()
    EXECUTOR_REGISTRY.register(executor)

    # Missing required field 'message'
    with pytest.raises(ValueError, match="input validation failed"):
        Block(id="test1", type="Demo", inputs={})


@pytest.mark.asyncio
async def test_block_unknown_type(clear_global_registry):
    """Test block creation with unknown type."""
    # Type not registered
    with pytest.raises(ValueError, match="Unknown block type"):
        Block(id="test1", type="NonExistent", inputs={"message": "hello"})


def test_executor_missing_type_name(clear_global_registry):
    """Test executor registration without type_name."""

    class BadExecutor(BlockExecutor):
        # Missing type_name
        input_type = DemoInput
        output_type = DemoOutput

        async def execute(self, inputs, context):
            pass

    registry = ExecutorRegistry()
    executor = BadExecutor()

    with pytest.raises(ValueError, match="missing type_name"):
        registry.register(executor)


def test_workflow_schema_structure(clear_global_registry):
    """Test complete workflow schema structure."""
    registry = ExecutorRegistry()
    executor = DemoExecutor()
    registry.register(executor)

    schema = registry.generate_workflow_schema()

    # Check top-level structure
    assert "properties" in schema
    assert "name" in schema["properties"]
    assert "blocks" in schema["properties"]
    assert "inputs" in schema["properties"]
    assert "outputs" in schema["properties"]

    # Check required fields
    assert "name" in schema["required"]
    assert "blocks" in schema["required"]

    # Check blocks schema
    blocks_schema = schema["properties"]["blocks"]
    assert blocks_schema["type"] == "array"
    assert "items" in blocks_schema

    # Check block item schema
    block_item = blocks_schema["items"]
    assert block_item["type"] == "object"
    assert "id" in block_item["required"]
    assert "type" in block_item["required"]
    assert "inputs" in block_item["required"]


@pytest.mark.asyncio
async def test_block_with_dependencies(clear_global_registry):
    """Test block creation with dependencies."""
    from workflows_mcp.engine.executor_base import EXECUTOR_REGISTRY

    executor = DemoExecutor()
    EXECUTOR_REGISTRY.register(executor)

    block = Block(
        id="test1",
        type="Demo",
        inputs={"message": "hello"},
        depends_on=["setup", "config"],
    )

    assert block.depends_on == ["setup", "config"]


@pytest.mark.asyncio
async def test_block_capabilities(clear_global_registry):
    """Test block capabilities retrieval."""
    from workflows_mcp.engine.executor_base import EXECUTOR_REGISTRY

    executor = DemoExecutor()
    EXECUTOR_REGISTRY.register(executor)

    block = Block(id="test1", type="Demo", inputs={"message": "hello"})

    capabilities = block.get_capabilities()

    assert capabilities["type"] == "Demo"
    assert capabilities["security_level"] == "safe"
