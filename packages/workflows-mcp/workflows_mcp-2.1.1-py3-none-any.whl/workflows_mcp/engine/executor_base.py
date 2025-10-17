"""Base executor architecture for workflow blocks.

This module provides the foundation for the executor pattern redesign.
Executors are pure functions that implement block logic as stateless,
reusable components. This architecture enables:

- Plugin-based extensibility (third-party executors)
- Schema-first development (auto-generated JSON Schema)
- Enhanced security (per-executor permissions)
- Better testing (pure functions, no mocking)
- Performance optimization (singleton pattern, caching)
"""

import importlib.util
import inspect
import sys
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Any, ClassVar

from pydantic import BaseModel

from .block import BlockInput, BlockOutput
from .result import Result


class ExecutorSecurityLevel(Enum):
    """Security level classification for executors.

    Used for security policy enforcement and audit purposes.
    """

    SAFE = "safe"  # Read-only operations, no system access
    TRUSTED = "trusted"  # File I/O, safe commands
    PRIVILEGED = "privileged"  # Full system access (shell, git, network)


class ExecutorCapabilities(BaseModel):
    """Executor capability flags for security audit.

    Declares what system resources an executor can access.
    Used by security policies to restrict execution.
    """

    can_read_files: bool = False
    can_write_files: bool = False
    can_execute_commands: bool = False
    can_network: bool = False
    can_modify_state: bool = False


class BlockExecutor(ABC):
    """Base class for workflow block executors.

    Executors are pure functions that implement block logic. They are:
    - Stateless: No mutable state between executions
    - Reusable: Single instance serves all blocks of this type
    - Type-safe: Pydantic models for inputs and outputs
    - Testable: Pure functions with no side effects in tests

    Subclasses must:
    1. Set class attributes (type_name, input_type, output_type)
    2. Implement execute() method
    3. Optionally override security attributes

    Example:
        class ShellExecutor(BlockExecutor):
            type_name = "Shell"
            input_type = ShellInput
            output_type = ShellOutput
            security_level = ExecutorSecurityLevel.PRIVILEGED
            capabilities = ExecutorCapabilities(can_execute_commands=True)

            async def execute(self, inputs: ShellInput, context: dict) -> Result[ShellOutput]:
                # Implementation
                pass
    """

    # Class attributes (must be set by subclasses)
    type_name: ClassVar[str]  # Block type identifier (e.g., "Shell")
    input_type: ClassVar[type[BlockInput]]  # Pydantic input model
    output_type: ClassVar[type[BlockOutput]]  # Pydantic output model

    # Security attributes (can be overridden by subclasses)
    security_level: ClassVar[ExecutorSecurityLevel] = ExecutorSecurityLevel.SAFE
    capabilities: ClassVar[ExecutorCapabilities] = ExecutorCapabilities()

    @abstractmethod
    async def execute(self, inputs: BlockInput, context: dict[str, Any]) -> Result[BlockOutput]:
        """Execute block logic with validated inputs.

        This is the core method that implements block behavior. It receives:
        - Validated inputs (already parsed via Pydantic)
        - Workflow context (four namespaces: inputs, blocks, metadata, __internal__)

        Args:
            inputs: Validated input model instance (type matches input_type)
            context: Workflow execution context with access to:
                - context["inputs"]: Workflow input parameters
                - context["blocks"][block_id]["outputs"]: Outputs from previous blocks
                - context["metadata"]: Workflow metadata (name, timestamps, etc.)

        Returns:
            Result.success(output) with BlockOutput on success
            Result.failure(error) with error message on failure

        Example:
            async def execute(self, inputs: ShellInput, context: dict) -> Result[ShellOutput]:
                # Run shell command
                process = await asyncio.create_subprocess_shell(
                    inputs.command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()

                # Return typed output
                return Result.success(ShellOutput(
                    stdout=stdout.decode(),
                    stderr=stderr.decode(),
                    exit_code=process.returncode,
                    success=process.returncode == 0
                ))
        """
        pass

    async def resume(
        self,
        _inputs: BlockInput,
        _context: dict[str, Any],
        _llm_response: str,
        _pause_metadata: dict[str, Any],
    ) -> Result[BlockOutput]:
        """Resume execution after a pause (optional, for interactive blocks).

        This method is called when a workflow is resumed after a pause.
        Most executors don't need to implement this - it's only required
        for interactive executors that can pause workflow execution.

        Args:
            _inputs: Validated input model instance
            _context: Workflow execution context
            _llm_response: Response from LLM to the pause prompt
            _pause_metadata: Metadata stored when the block paused

        Returns:
            Result.success(output), Result.failure(error), or Result.pause() again

        Raises:
            NotImplementedError: By default (non-interactive executors)
        """
        raise NotImplementedError(
            f"{self.type_name} executor does not support resume (not an interactive executor)"
        )

    def get_input_schema(self) -> dict[str, Any]:
        """Generate JSON Schema for input validation.

        Uses Pydantic's model_json_schema() to auto-generate schema from input_type.
        This schema is used for:
        - VS Code autocomplete
        - Pre-execution validation
        - MCP schema tools
        - Documentation generation

        Returns:
            JSON Schema dictionary for input model
        """
        return self.input_type.model_json_schema()

    def get_output_schema(self) -> dict[str, Any]:
        """Generate JSON Schema for output structure.

        Returns:
            JSON Schema dictionary for output model
        """
        return self.output_type.model_json_schema()

    def get_capabilities(self) -> dict[str, Any]:
        """Get executor capabilities for security audit.

        Returns:
            Dictionary with type, security_level, and capabilities
        """
        return {
            "type": self.type_name,
            "security_level": self.security_level.value,
            "capabilities": self.capabilities.model_dump(),
        }


class ExecutorRegistry:
    """Central registry for workflow block executors.

    Manages executor lifecycle and provides plugin discovery.
    Implements singleton pattern to share executors across all blocks.

    Features:
    - Type-based registration and lookup
    - Plugin discovery (entry points + directories)
    - Schema generation for all registered executors
    - Security policy enforcement (future)
    """

    def __init__(self) -> None:
        """Initialize empty registry."""
        self._executors: dict[str, BlockExecutor] = {}

    def register(self, executor: BlockExecutor) -> None:
        """Register an executor instance.

        Args:
            executor: BlockExecutor instance to register

        Raises:
            ValueError: If executor missing type_name or type already registered

        Example:
            registry = ExecutorRegistry()
            registry.register(ShellExecutor())
            registry.register(CreateFileExecutor())
        """
        # Validate executor has type_name
        if not hasattr(executor, "type_name"):
            raise ValueError(
                f"Executor {executor.__class__.__name__} missing type_name class attribute"
            )

        type_name = executor.type_name

        # Prevent duplicate registration
        if type_name in self._executors:
            raise ValueError(f"Executor already registered: {type_name}")

        self._executors[type_name] = executor

    def get(self, type_name: str) -> BlockExecutor:
        """Get executor by type name.

        Args:
            type_name: Block type identifier (e.g., "Shell", "CreateFile")

        Returns:
            BlockExecutor instance for this type

        Raises:
            ValueError: If type not registered

        Example:
            executor = registry.get("Shell")
            result = await executor.execute(inputs, context)
        """
        if type_name not in self._executors:
            raise ValueError(f"Unknown block type: '{type_name}'")
        return self._executors[type_name]

    def list_types(self) -> list[str]:
        """List all registered block types.

        Returns:
            Sorted list of block type names

        Example:
            types = registry.list_types()
            # ["CreateFile", "ReadFile", "Shell", ...]
        """
        return sorted(self._executors.keys())

    def has_type(self, type_name: str) -> bool:
        """Check if block type is registered.

        Args:
            type_name: Block type to check

        Returns:
            True if type is registered, False otherwise
        """
        return type_name in self._executors

    def generate_workflow_schema(self) -> dict[str, Any]:
        """Generate complete JSON Schema for workflow validation.

        This creates a comprehensive schema that includes:
        - All registered executor input schemas
        - Workflow structure validation
        - Conditional schemas per block type

        The schema can be used for:
        - VS Code YAML autocomplete
        - Pre-execution workflow validation
        - MCP schema tools for Claude
        - Automatic documentation generation

        Returns:
            Complete JSON Schema for workflow definitions

        Example:
            schema = registry.generate_workflow_schema()

            # Use with jsonschema library
            from jsonschema import validate
            validate(instance=workflow_dict, schema=schema)

            # Save for VS Code autocomplete
            with open("workflow-schema.json", "w") as f:
                json.dump(schema, f, indent=2)
        """
        # Collect all executor input schemas
        definitions = {}
        block_types = []

        for type_name, executor in self._executors.items():
            definitions[f"{type_name}Input"] = executor.get_input_schema()
            block_types.append(type_name)

        # Build complete workflow schema
        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "MCP Workflow Definition",
            "type": "object",
            "required": ["name", "blocks"],
            "properties": {
                "name": {"type": "string", "description": "Workflow name"},
                "description": {
                    "type": "string",
                    "description": "Workflow description",
                },
                "inputs": {
                    "type": "object",
                    "description": "Workflow input parameters",
                    "patternProperties": {
                        ".*": {
                            "type": "object",
                            "properties": {
                                "type": {"enum": ["string", "int", "float", "bool", "json"]},
                                "default": {},
                                "description": {"type": "string"},
                            },
                            "required": ["type"],
                        }
                    },
                },
                "outputs": {
                    "type": "object",
                    "description": "Workflow output expressions",
                    "patternProperties": {".*": {"type": "string"}},
                },
                "blocks": {
                    "type": "array",
                    "description": "Workflow execution blocks",
                    "items": {
                        "type": "object",
                        "required": ["id", "type", "inputs"],
                        "properties": {
                            "id": {
                                "type": "string",
                                "description": "Unique block identifier",
                            },
                            "type": {
                                "enum": block_types,
                                "description": "Block type",
                            },
                            "inputs": {
                                "type": "object",
                                "description": "Block inputs (schema depends on type)",
                            },
                            "depends_on": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Dependencies (block IDs)",
                            },
                            "condition": {
                                "type": "string",
                                "description": "Conditional execution expression",
                            },
                        },
                    },
                },
            },
            "definitions": definitions,
        }

    def discover_entry_points(self, group: str = "mcp_workflows.executors") -> int:
        """Discover and register executors from entry points.

        This enables third-party packages to provide custom executors by declaring
        entry points in their pyproject.toml:

            [project.entry-points."mcp_workflows.executors"]
            custom_executor = "my_package.executors:CustomExecutor"

        Args:
            group: Entry point group name (default: "mcp_workflows.executors")

        Returns:
            Number of executors discovered and registered

        Example:
            # In third-party package pyproject.toml
            [project.entry-points."mcp_workflows.executors"]
            database = "my_pkg.executors:DatabaseExecutor"
            api_call = "my_pkg.executors:APICallExecutor"

            # In application startup
            registry.discover_entry_points()
        """
        try:
            from importlib.metadata import entry_points
        except ImportError:
            return 0

        discovered = 0
        eps = entry_points()

        # Handle both new and old entry_points() API
        if hasattr(eps, "select"):
            group_eps = eps.select(group=group)
        else:
            # Fallback for older API
            group_eps = eps.get(group, []) if hasattr(eps, "get") else []

        for entry_point in group_eps:
            try:
                executor_class = entry_point.load()

                # Validate it's a BlockExecutor subclass
                if not (
                    inspect.isclass(executor_class) and issubclass(executor_class, BlockExecutor)
                ):
                    continue

                # Instantiate and register
                executor = executor_class()
                self.register(executor)
                discovered += 1

            except Exception:
                # Skip invalid entry points
                continue

        return discovered

    def discover_from_directories(
        self, directories: list[Path | str], pattern: str = "*_executor.py"
    ) -> int:
        """Discover and register executors from Python files in directories.

        This enables local executor plugins similar to pytest's conftest.py pattern.
        The registry will scan directories for Python files matching the pattern,
        import them, and register any BlockExecutor subclasses found.

        Args:
            directories: List of directories to scan for executor files
            pattern: Glob pattern for executor files (default: "*_executor.py")

        Returns:
            Number of executors discovered and registered

        Example:
            # Directory structure:
            # ~/.mcp-workflows/executors/
            # ├── database_executor.py  (contains DatabaseExecutor)
            # └── api_executor.py       (contains APICallExecutor)

            # Discover from user and project directories
            registry.discover_from_directories([
                Path.home() / ".mcp-workflows/executors",
                Path.cwd() / ".workflows/executors"
            ])
        """
        discovered = 0

        for directory in directories:
            dir_path = Path(directory)
            if not dir_path.exists() or not dir_path.is_dir():
                continue

            # Find all matching Python files
            for file_path in dir_path.glob(pattern):
                if not file_path.is_file():
                    continue

                try:
                    # Import module from file
                    module_name = f"_executor_plugin_{file_path.stem}"
                    spec = importlib.util.spec_from_file_location(module_name, file_path)
                    if spec is None or spec.loader is None:
                        continue

                    module = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = module
                    spec.loader.exec_module(module)

                    # Find all BlockExecutor subclasses in module
                    for _name, obj in inspect.getmembers(module):
                        if (
                            inspect.isclass(obj)
                            and issubclass(obj, BlockExecutor)
                            and obj is not BlockExecutor
                            and obj.__module__ == module_name
                        ):
                            # Instantiate and register
                            executor = obj()
                            self.register(executor)
                            discovered += 1

                except Exception:
                    # Skip invalid files
                    continue

        return discovered

    def discover_plugins(
        self,
        entry_point_group: str = "mcp_workflows.executors",
        plugin_directories: list[Path | str] | None = None,
    ) -> dict[str, int]:
        """Discover and register executors from all plugin sources.

        This is a convenience method that combines entry point and directory-based
        plugin discovery. It's the recommended way to load plugins at application startup.

        Args:
            entry_point_group: Entry point group name
            plugin_directories: Optional list of directories to scan for plugins.
                If None, uses default locations:
                - ~/.mcp-workflows/executors
                - ./.workflows/executors

        Returns:
            Dictionary with counts: {"entry_points": N, "directories": M}

        Example:
            # Load all plugins at startup
            counts = EXECUTOR_REGISTRY.discover_plugins()
            print(f"Loaded {counts['entry_points']} entry point executors")
            print(f"Loaded {counts['directories']} directory executors")
        """
        # Default plugin directories
        if plugin_directories is None:
            plugin_directories = [
                Path.home() / ".mcp-workflows/executors",
                Path.cwd() / ".workflows/executors",
            ]

        return {
            "entry_points": self.discover_entry_points(entry_point_group),
            "directories": self.discover_from_directories(plugin_directories),
        }


# Global registry instance
EXECUTOR_REGISTRY = ExecutorRegistry()
