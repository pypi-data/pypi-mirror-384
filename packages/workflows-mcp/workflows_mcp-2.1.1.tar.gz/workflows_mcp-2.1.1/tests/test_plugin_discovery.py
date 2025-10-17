"""Tests for executor plugin discovery system."""

from pathlib import Path
from typing import Any, ClassVar

import pytest
from pydantic import Field

from workflows_mcp.engine.block import BlockInput, BlockOutput
from workflows_mcp.engine.executor_base import (
    BlockExecutor,
    ExecutorRegistry,
    ExecutorSecurityLevel,
)
from workflows_mcp.engine.result import Result


# Test executor classes
class PluginInputModel(BlockInput):
    """Input for test plugin executor."""

    value: str = Field(description="Test value")


class PluginOutputModel(BlockOutput):
    """Output for test plugin executor."""

    result: str = Field(description="Test result")


class TestPluginExecutor(BlockExecutor):
    """Test executor for plugin discovery tests."""

    type_name: ClassVar[str] = "TestPlugin"
    input_type: ClassVar[type[BlockInput]] = PluginInputModel
    output_type: ClassVar[type[BlockOutput]] = PluginOutputModel
    security_level: ClassVar[ExecutorSecurityLevel] = ExecutorSecurityLevel.SAFE

    async def execute(
        self, inputs: PluginInputModel, context: dict[str, Any]
    ) -> Result[PluginOutputModel]:
        return Result.success(PluginOutputModel(result=f"Processed: {inputs.value}"))


class AnotherTestExecutor(BlockExecutor):
    """Another test executor for multi-plugin discovery."""

    type_name: ClassVar[str] = "AnotherTest"
    input_type: ClassVar[type[BlockInput]] = PluginInputModel
    output_type: ClassVar[type[BlockOutput]] = PluginOutputModel

    async def execute(
        self, inputs: PluginInputModel, context: dict[str, Any]
    ) -> Result[PluginOutputModel]:
        return Result.success(PluginOutputModel(result=f"Another: {inputs.value}"))


# Invalid executor classes for error testing
class InvalidExecutor:
    """Not a BlockExecutor subclass."""

    pass


class MissingTypeNameExecutor(BlockExecutor):
    """Executor missing type_name attribute."""

    input_type: ClassVar[type[BlockInput]] = PluginInputModel
    output_type: ClassVar[type[BlockOutput]] = PluginOutputModel

    async def execute(self, inputs, context) -> Result:
        return Result.success(PluginOutputModel(result="test"))


@pytest.fixture
def registry():
    """Create fresh executor registry for each test."""
    return ExecutorRegistry()


@pytest.fixture
def plugin_directory(tmp_path):
    """Create temporary directory with plugin files."""
    plugin_dir = tmp_path / "executors"
    plugin_dir.mkdir()

    # Create valid plugin file
    valid_plugin = plugin_dir / "test_executor.py"
    valid_plugin.write_text(
        """
from typing import Any, ClassVar
from pydantic import Field
from workflows_mcp.engine.block import BlockInput, BlockOutput
from workflows_mcp.engine.executor_base import BlockExecutor
from workflows_mcp.engine.result import Result

class PluginInput(BlockInput):
    value: str = Field(description="Test")

class PluginOutput(BlockOutput):
    result: str = Field(description="Result")

class DiscoveredExecutor(BlockExecutor):
    type_name: ClassVar[str] = "Discovered"
    input_type: ClassVar[type[BlockInput]] = PluginInput
    output_type: ClassVar[type[BlockOutput]] = PluginOutput

    async def execute(self, inputs, context) -> Result:
        return Result.success(PluginOutput(result="discovered"))
"""
    )

    # Create another valid plugin
    another_plugin = plugin_dir / "another_executor.py"
    another_plugin.write_text(
        """
from typing import Any, ClassVar
from pydantic import Field
from workflows_mcp.engine.block import BlockInput, BlockOutput
from workflows_mcp.engine.executor_base import BlockExecutor
from workflows_mcp.engine.result import Result

class AnotherInput(BlockInput):
    value: str = Field(description="Test")

class AnotherOutput(BlockOutput):
    result: str = Field(description="Result")

class AnotherDiscoveredExecutor(BlockExecutor):
    type_name: ClassVar[str] = "AnotherDiscovered"
    input_type: ClassVar[type[BlockInput]] = AnotherInput
    output_type: ClassVar[type[BlockOutput]] = AnotherOutput

    async def execute(self, inputs, context) -> Result:
        return Result.success(AnotherOutput(result="another"))
"""
    )

    # Create invalid plugin (not a BlockExecutor)
    invalid_plugin = plugin_dir / "invalid_executor.py"
    invalid_plugin.write_text(
        """
class NotAnExecutor:
    pass
"""
    )

    # Create plugin with syntax error
    syntax_error_plugin = plugin_dir / "syntax_error_executor.py"
    syntax_error_plugin.write_text("this is not valid python {{{")

    return plugin_dir


class TestExecutorRegistry:
    """Test basic executor registry functionality."""

    def test_register_executor(self, registry):
        """Test registering an executor."""
        executor = TestPluginExecutor()
        registry.register(executor)

        assert registry.has_type("TestPlugin")
        assert "TestPlugin" in registry.list_types()

    def test_get_registered_executor(self, registry):
        """Test retrieving registered executor."""
        executor = TestPluginExecutor()
        registry.register(executor)

        retrieved = registry.get("TestPlugin")
        assert retrieved is executor
        assert retrieved.type_name == "TestPlugin"

    def test_register_duplicate_type_fails(self, registry):
        """Test that registering duplicate type raises error."""
        registry.register(TestPluginExecutor())

        with pytest.raises(ValueError, match="already registered"):
            registry.register(TestPluginExecutor())

    def test_get_unknown_type_fails(self, registry):
        """Test that getting unknown type raises error."""
        with pytest.raises(ValueError, match="Unknown block type"):
            registry.get("NonExistent")

    def test_register_executor_without_type_name_fails(self, registry):
        """Test that executor without type_name raises error."""
        executor = MissingTypeNameExecutor()

        with pytest.raises(ValueError, match="missing type_name"):
            registry.register(executor)

    def test_list_types(self, registry):
        """Test listing all registered types."""
        registry.register(TestPluginExecutor())
        registry.register(AnotherTestExecutor())

        types = registry.list_types()
        assert "TestPlugin" in types
        assert "AnotherTest" in types
        assert types == sorted(types)  # Should be sorted

    def test_has_type(self, registry):
        """Test checking if type is registered."""
        assert not registry.has_type("TestPlugin")

        registry.register(TestPluginExecutor())

        assert registry.has_type("TestPlugin")
        assert not registry.has_type("NonExistent")


class TestDirectoryDiscovery:
    """Test directory-based plugin discovery."""

    def test_discover_from_directory(self, registry, plugin_directory):
        """Test discovering executors from directory."""
        count = registry.discover_from_directories([plugin_directory])

        assert count == 2  # Two valid executors
        assert registry.has_type("Discovered")
        assert registry.has_type("AnotherDiscovered")

    def test_discover_from_multiple_directories(self, registry, tmp_path):
        """Test discovering from multiple directories."""
        dir1 = tmp_path / "dir1"
        dir1.mkdir()
        (dir1 / "exec1_executor.py").write_text(
            """
from typing import ClassVar
from pydantic import Field
from workflows_mcp.engine.block import BlockInput, BlockOutput
from workflows_mcp.engine.executor_base import BlockExecutor
from workflows_mcp.engine.result import Result

class Input1(BlockInput):
    value: str = Field(description="Test")

class Output1(BlockOutput):
    result: str = Field(description="Result")

class Executor1(BlockExecutor):
    type_name: ClassVar[str] = "Exec1"
    input_type: ClassVar[type[BlockInput]] = Input1
    output_type: ClassVar[type[BlockOutput]] = Output1

    async def execute(self, inputs, context) -> Result:
        return Result.success(Output1(result="exec1"))
"""
        )

        dir2 = tmp_path / "dir2"
        dir2.mkdir()
        (dir2 / "exec2_executor.py").write_text(
            """
from typing import ClassVar
from pydantic import Field
from workflows_mcp.engine.block import BlockInput, BlockOutput
from workflows_mcp.engine.executor_base import BlockExecutor
from workflows_mcp.engine.result import Result

class Input2(BlockInput):
    value: str = Field(description="Test")

class Output2(BlockOutput):
    result: str = Field(description="Result")

class Executor2(BlockExecutor):
    type_name: ClassVar[str] = "Exec2"
    input_type: ClassVar[type[BlockInput]] = Input2
    output_type: ClassVar[type[BlockOutput]] = Output2

    async def execute(self, inputs, context) -> Result:
        return Result.success(Output2(result="exec2"))
"""
        )

        count = registry.discover_from_directories([dir1, dir2])

        assert count == 2
        assert registry.has_type("Exec1")
        assert registry.has_type("Exec2")

    def test_discover_nonexistent_directory(self, registry, tmp_path):
        """Test discovering from nonexistent directory doesn't fail."""
        nonexistent = tmp_path / "does_not_exist"
        count = registry.discover_from_directories([nonexistent])

        assert count == 0

    def test_discover_ignores_invalid_files(self, registry, plugin_directory):
        """Test that invalid files are silently skipped."""
        # Directory contains both valid and invalid files
        count = registry.discover_from_directories([plugin_directory])

        # Only valid executors are registered
        assert count == 2
        assert registry.has_type("Discovered")
        assert registry.has_type("AnotherDiscovered")

    def test_discover_with_custom_pattern(self, registry, tmp_path):
        """Test discovering with custom file pattern."""
        plugin_dir = tmp_path / "plugins"
        plugin_dir.mkdir()

        # Create file matching custom pattern
        (plugin_dir / "my_plugin.py").write_text(
            """
from typing import ClassVar
from pydantic import Field
from workflows_mcp.engine.block import BlockInput, BlockOutput
from workflows_mcp.engine.executor_base import BlockExecutor
from workflows_mcp.engine.result import Result

class CustomInput(BlockInput):
    value: str = Field(description="Test")

class CustomOutput(BlockOutput):
    result: str = Field(description="Result")

class CustomExecutor(BlockExecutor):
    type_name: ClassVar[str] = "Custom"
    input_type: ClassVar[type[BlockInput]] = CustomInput
    output_type: ClassVar[type[BlockOutput]] = CustomOutput

    async def execute(self, inputs, context) -> Result:
        return Result.success(CustomOutput(result="custom"))
"""
        )

        # Default pattern won't match
        count = registry.discover_from_directories([plugin_dir], pattern="*_executor.py")
        assert count == 0

        # Custom pattern matches
        registry2 = ExecutorRegistry()
        count = registry2.discover_from_directories([plugin_dir], pattern="*.py")
        assert count == 1
        assert registry2.has_type("Custom")


class TestEntryPointDiscovery:
    """Test entry point-based plugin discovery."""

    def test_discover_entry_points_no_entry_points(self, registry):
        """Test discovering when no entry points exist."""
        # Should return 0 without error
        count = registry.discover_entry_points(group="nonexistent.group")
        assert count == 0


class TestCombinedDiscovery:
    """Test combined plugin discovery."""

    def test_discover_plugins_default_directories(self, registry, monkeypatch, tmp_path):
        """Test discover_plugins with default directories."""
        # Mock Path.home() and Path.cwd()
        monkeypatch.setattr(Path, "home", lambda: tmp_path / "home")
        monkeypatch.setattr(Path, "cwd", lambda: tmp_path / "cwd")

        # Create default directories with plugins
        home_executors = tmp_path / "home" / ".mcp-workflows" / "executors"
        home_executors.mkdir(parents=True)
        (home_executors / "home_executor.py").write_text(
            """
from typing import ClassVar
from pydantic import Field
from workflows_mcp.engine.block import BlockInput, BlockOutput
from workflows_mcp.engine.executor_base import BlockExecutor
from workflows_mcp.engine.result import Result

class HomeInput(BlockInput):
    value: str = Field(description="Test")

class HomeOutput(BlockOutput):
    result: str = Field(description="Result")

class HomeExecutor(BlockExecutor):
    type_name: ClassVar[str] = "Home"
    input_type: ClassVar[type[BlockInput]] = HomeInput
    output_type: ClassVar[type[BlockOutput]] = HomeOutput

    async def execute(self, inputs, context) -> Result:
        return Result.success(HomeOutput(result="home"))
"""
        )

        cwd_executors = tmp_path / "cwd" / ".workflows" / "executors"
        cwd_executors.mkdir(parents=True)
        (cwd_executors / "cwd_executor.py").write_text(
            """
from typing import ClassVar
from pydantic import Field
from workflows_mcp.engine.block import BlockInput, BlockOutput
from workflows_mcp.engine.executor_base import BlockExecutor
from workflows_mcp.engine.result import Result

class CwdInput(BlockInput):
    value: str = Field(description="Test")

class CwdOutput(BlockOutput):
    result: str = Field(description="Result")

class CwdExecutor(BlockExecutor):
    type_name: ClassVar[str] = "Cwd"
    input_type: ClassVar[type[BlockInput]] = CwdInput
    output_type: ClassVar[type[BlockOutput]] = CwdOutput

    async def execute(self, inputs, context) -> Result:
        return Result.success(CwdOutput(result="cwd"))
"""
        )

        counts = registry.discover_plugins()

        assert counts["directories"] == 2
        assert registry.has_type("Home")
        assert registry.has_type("Cwd")

    def test_discover_plugins_custom_directories(self, registry, plugin_directory):
        """Test discover_plugins with custom directories."""
        counts = registry.discover_plugins(plugin_directories=[plugin_directory])

        assert counts["directories"] == 2
        assert counts["entry_points"] == 0
        assert registry.has_type("Discovered")
        assert registry.has_type("AnotherDiscovered")


class TestSchemaGeneration:
    """Test schema generation with plugins."""

    def test_schema_includes_plugin_types(self, registry):
        """Test that generated schema includes plugin types."""
        registry.register(TestPluginExecutor())
        registry.register(AnotherTestExecutor())

        schema = registry.generate_workflow_schema()

        # Check block types enum includes plugins
        block_types = schema["properties"]["blocks"]["items"]["properties"]["type"]["enum"]
        assert "TestPlugin" in block_types
        assert "AnotherTest" in block_types

        # Check input schemas are included
        assert "TestPluginInput" in schema["definitions"]
        assert "AnotherTestInput" in schema["definitions"]

    def test_schema_updates_after_plugin_discovery(self, registry, plugin_directory):
        """Test that schema updates after discovering plugins."""
        # Generate initial schema
        schema1 = registry.generate_workflow_schema()
        initial_types = schema1["properties"]["blocks"]["items"]["properties"]["type"]["enum"]

        # Discover plugins
        registry.discover_from_directories([plugin_directory])

        # Generate updated schema
        schema2 = registry.generate_workflow_schema()
        updated_types = schema2["properties"]["blocks"]["items"]["properties"]["type"]["enum"]

        # New types should be included
        assert len(updated_types) > len(initial_types)
        assert "Discovered" in updated_types
        assert "AnotherDiscovered" in updated_types


@pytest.mark.asyncio
class TestPluginExecution:
    """Test executing discovered plugins."""

    async def test_execute_discovered_plugin(self, registry, plugin_directory):
        """Test that discovered plugins can be executed."""
        registry.discover_from_directories([plugin_directory])

        executor = registry.get("Discovered")
        inputs = executor.input_type(value="test")
        context = {"inputs": {}, "blocks": {}, "metadata": {}}

        result = await executor.execute(inputs, context)

        assert result.is_success
        assert result.value.result == "discovered"

    async def test_execute_multiple_discovered_plugins(self, registry, plugin_directory):
        """Test executing multiple discovered plugins."""
        registry.discover_from_directories([plugin_directory])

        # Execute first plugin
        executor1 = registry.get("Discovered")
        result1 = await executor1.execute(
            executor1.input_type(value="test1"),
            {"inputs": {}, "blocks": {}, "metadata": {}},
        )

        # Execute second plugin
        executor2 = registry.get("AnotherDiscovered")
        result2 = await executor2.execute(
            executor2.input_type(value="test2"),
            {"inputs": {}, "blocks": {}, "metadata": {}},
        )

        assert result1.is_success
        assert result1.value.result == "discovered"
        assert result2.is_success
        assert result2.value.result == "another"
