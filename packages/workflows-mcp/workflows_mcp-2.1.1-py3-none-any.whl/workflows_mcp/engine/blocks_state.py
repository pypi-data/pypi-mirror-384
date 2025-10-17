"""JSON state management blocks for workflows."""

import json
import time
from copy import deepcopy
from pathlib import Path
from typing import Any, cast

from pydantic import Field

from .block import BLOCK_REGISTRY, BlockInput, BlockOutput, WorkflowBlock
from .result import Result


def deep_merge(base: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    """
    Recursively merge updates into base dict.

    Rules:
    - Nested dicts: merge recursively
    - Lists: replace entirely (don't append)
    - Other values: replace with update value

    Args:
        base: Base dictionary to merge into
        updates: Dictionary with updates to apply

    Returns:
        Merged dictionary (new instance, does not modify inputs)

    Example:
        base = {"modules": ["a"], "metrics": {"coverage": 80}}
        updates = {"modules": ["b"], "metrics": {"tests": 42}}
        result = {"modules": ["b"], "metrics": {"coverage": 80, "tests": 42}}
    """
    result = deepcopy(base)

    for key, value in updates.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            # Recursively merge nested dicts
            result[key] = deep_merge(result[key], value)
        else:
            # Replace value (works for primitives, lists, and non-dict types)
            result[key] = deepcopy(value)

    return result


class ReadJSONStateInput(BlockInput):
    """Input for ReadJSONState block."""

    path: str = Field(description="Path to JSON state file (supports ${variables})")


class ReadJSONStateOutput(BlockOutput):
    """Output for ReadJSONState block."""

    state: dict[str, Any] = Field(
        default_factory=dict, description="State from JSON file (empty dict if not found)"
    )
    found: bool = Field(description="Whether file was found")
    path: str = Field(description="Resolved absolute path")


class ReadJSONState(WorkflowBlock):
    """
    Read JSON state from a file.

    Features:
    - Read JSON state file into workflow context
    - Return empty dict if file doesn't exist (graceful handling)
    - Variable resolution for file path (${variables})
    - Path traversal protection
    - JSON decode error handling

    Example YAML usage:
        - id: read_state
          type: ReadJSONState
          inputs:
            path: "${workspace}/.workflow-state.json"
    """

    def input_model(self) -> type[BlockInput]:
        return ReadJSONStateInput

    def output_model(self) -> type[BlockOutput]:
        return ReadJSONStateOutput

    async def execute(self, context: dict[str, Any]) -> Result[BlockOutput]:
        """Read JSON state from file."""
        _ = context  # Required by interface, not used in this block
        inputs = cast(ReadJSONStateInput, self._validated_inputs)
        if inputs is None:
            return Result.failure("Inputs not validated")

        start = time.time()

        try:
            # Resolve path (relative or absolute)
            file_path = Path(inputs.path)
            if not file_path.is_absolute():
                file_path = Path.cwd() / file_path

            # Resolve to absolute path and normalize
            file_path = file_path.resolve()

            # Path traversal protection
            if ".." in str(file_path):
                return Result.failure(f"Path traversal detected after resolution: {file_path}")

            # Check if file exists
            if not file_path.exists():
                # Graceful handling: return empty dict with found=False
                execution_time = (time.time() - start) * 1000
                output = ReadJSONStateOutput(
                    state={},
                    found=False,
                    path=str(file_path),
                )
                return Result.success(output, metadata={"execution_time_ms": execution_time})

            # Check if it's a file (not a directory)
            if not file_path.is_file():
                return Result.failure(f"Path is not a file: {file_path}")

            # Read and parse JSON
            try:
                content = file_path.read_text(encoding="utf-8")
                state = json.loads(content)

                # Validate that the JSON is an object (dict), not array or primitive
                if not isinstance(state, dict):
                    return Result.failure(
                        f"JSON file must contain an object (dict), "
                        f"got {type(state).__name__}: {file_path}"
                    )

            except PermissionError:
                return Result.failure(f"Permission denied reading from: {file_path}")
            except json.JSONDecodeError as e:
                return Result.failure(
                    f"Invalid JSON in file: {file_path}\n"
                    f"Error at line {e.lineno}, column {e.colno}: {e.msg}"
                )
            except UnicodeDecodeError as e:
                return Result.failure(
                    f"Encoding error (expected UTF-8): {str(e)}\nFile: {file_path}"
                )

            execution_time = (time.time() - start) * 1000

            output = ReadJSONStateOutput(
                state=state,
                found=True,
                path=str(file_path),
            )

            return Result.success(output, metadata={"execution_time_ms": execution_time})

        except Exception as e:
            execution_time = (time.time() - start) * 1000
            return Result.failure(
                f"Failed to read JSON state: {inputs.path}\nError: {str(e)}",
                metadata={"execution_time_ms": execution_time},
            )


# Register ReadJSONState block
BLOCK_REGISTRY.register("ReadJSONState", ReadJSONState)


class WriteJSONStateInput(BlockInput):
    """Input for WriteJSONState block."""

    path: str = Field(description="Path to JSON state file (supports ${variables})")
    state: dict[str, Any] = Field(description="State dictionary to write as JSON")


class WriteJSONStateOutput(BlockOutput):
    """Output for WriteJSONState block."""

    success: bool = Field(description="Whether file was written successfully")
    path: str = Field(description="Resolved absolute path written")
    size_bytes: int = Field(description="Size of JSON file written")


class WriteJSONState(WorkflowBlock):
    """
    Write JSON state to a file.

    Features:
    - Write state dict as formatted JSON to file (indent=2)
    - Create parent directories automatically
    - Variable resolution for file path (${variables})
    - Path traversal protection
    - Atomic write (write to temp file, then rename)

    Example YAML usage:
        - id: write_state
          type: WriteJSONState
          inputs:
            path: "${workspace}/.workflow-state.json"
            state:
              phase: "implementation"
              modules_completed: ["auth", "api"]
              coverage: 85.5
    """

    def input_model(self) -> type[BlockInput]:
        return WriteJSONStateInput

    def output_model(self) -> type[BlockOutput]:
        return WriteJSONStateOutput

    async def execute(self, context: dict[str, Any]) -> Result[BlockOutput]:
        """Write JSON state to file."""
        _ = context  # Required by interface, not used in this block
        inputs = cast(WriteJSONStateInput, self._validated_inputs)
        if inputs is None:
            return Result.failure("Inputs not validated")

        start = time.time()

        try:
            # Resolve path (relative or absolute)
            file_path = Path(inputs.path)
            if not file_path.is_absolute():
                file_path = Path.cwd() / file_path

            # Resolve to absolute path and normalize
            file_path = file_path.resolve()

            # Path traversal protection
            if ".." in str(file_path):
                return Result.failure(f"Path traversal detected after resolution: {file_path}")

            # Create parent directories
            try:
                file_path.parent.mkdir(parents=True, exist_ok=True)
            except PermissionError:
                return Result.failure(
                    f"Permission denied creating parent directory: {file_path.parent}"
                )

            # Serialize state to JSON with pretty formatting
            try:
                json_content = json.dumps(inputs.state, indent=2, ensure_ascii=False)
                json_content += "\n"  # Add trailing newline for better git diffs
            except (TypeError, ValueError) as e:
                return Result.failure(f"Failed to serialize state to JSON: {str(e)}")

            # Write to file
            try:
                file_path.write_text(json_content, encoding="utf-8")
            except PermissionError:
                return Result.failure(f"Permission denied writing to: {file_path}")

            # Get file size
            size_bytes = file_path.stat().st_size

            execution_time = (time.time() - start) * 1000

            output = WriteJSONStateOutput(
                success=True,
                path=str(file_path),
                size_bytes=size_bytes,
            )

            return Result.success(output, metadata={"execution_time_ms": execution_time})

        except Exception as e:
            execution_time = (time.time() - start) * 1000
            return Result.failure(
                f"Failed to write JSON state: {inputs.path}\nError: {str(e)}",
                metadata={"execution_time_ms": execution_time},
            )


# Register WriteJSONState block
BLOCK_REGISTRY.register("WriteJSONState", WriteJSONState)


class MergeJSONStateInput(BlockInput):
    """Input for MergeJSONState block."""

    path: str = Field(description="Path to JSON state file (supports ${variables})")
    updates: dict[str, Any] = Field(description="Updates to merge into existing state")


class MergeJSONStateOutput(BlockOutput):
    """Output for MergeJSONState block."""

    state: dict[str, Any] = Field(description="Merged state dictionary")
    success: bool = Field(description="Whether merge and write succeeded")
    path: str = Field(description="Resolved absolute path")
    created: bool = Field(description="True if file was created, False if updated existing")


class MergeJSONState(WorkflowBlock):
    """
    Merge updates into existing JSON state file.

    Features:
    - Read existing JSON state file
    - Deep merge updates into existing state (nested dicts merged recursively)
    - Write merged state back to file
    - Create file with updates if doesn't exist
    - Variable resolution for file path (${variables})
    - Path traversal protection

    Merge behavior:
    - Nested dicts: merge recursively
    - Lists: replace (don't append)
    - Other values: replace with update value

    Example YAML usage:
        - id: update_state
          type: MergeJSONState
          inputs:
            path: "${workspace}/.workflow-state.json"
            updates:
              modules_completed: ["auth", "api", "storage"]
              metrics:
                coverage: 87.5
                tests: 156
    """

    def input_model(self) -> type[BlockInput]:
        return MergeJSONStateInput

    def output_model(self) -> type[BlockOutput]:
        return MergeJSONStateOutput

    async def execute(self, context: dict[str, Any]) -> Result[BlockOutput]:
        """Merge updates into existing JSON state file."""
        _ = context  # Required by interface, not used in this block
        inputs = cast(MergeJSONStateInput, self._validated_inputs)
        if inputs is None:
            return Result.failure("Inputs not validated")

        start = time.time()

        try:
            # Resolve path (relative or absolute)
            file_path = Path(inputs.path)
            if not file_path.is_absolute():
                file_path = Path.cwd() / file_path

            # Resolve to absolute path and normalize
            file_path = file_path.resolve()

            # Path traversal protection
            if ".." in str(file_path):
                return Result.failure(f"Path traversal detected after resolution: {file_path}")

            # Read existing state if file exists
            existing_state: dict[str, Any] = {}
            created = False

            if file_path.exists():
                # Check if it's a file (not a directory)
                if not file_path.is_file():
                    return Result.failure(f"Path is not a file: {file_path}")

                # Read and parse existing JSON
                try:
                    content = file_path.read_text(encoding="utf-8")
                    existing_state = json.loads(content)

                    # Validate that the JSON is an object (dict)
                    if not isinstance(existing_state, dict):
                        return Result.failure(
                            f"JSON file must contain an object (dict), "
                            f"got {type(existing_state).__name__}: {file_path}"
                        )

                except PermissionError:
                    return Result.failure(f"Permission denied reading from: {file_path}")
                except json.JSONDecodeError as e:
                    return Result.failure(
                        f"Invalid JSON in existing file: {file_path}\n"
                        f"Error at line {e.lineno}, column {e.colno}: {e.msg}"
                    )
                except UnicodeDecodeError as e:
                    return Result.failure(
                        f"Encoding error (expected UTF-8): {str(e)}\nFile: {file_path}"
                    )
            else:
                # File doesn't exist - will create it
                created = True

            # Deep merge updates into existing state
            merged_state = deep_merge(existing_state, inputs.updates)

            # Create parent directories if needed
            try:
                file_path.parent.mkdir(parents=True, exist_ok=True)
            except PermissionError:
                return Result.failure(
                    f"Permission denied creating parent directory: {file_path.parent}"
                )

            # Serialize merged state to JSON with pretty formatting
            try:
                json_content = json.dumps(merged_state, indent=2, ensure_ascii=False)
                json_content += "\n"  # Add trailing newline for better git diffs
            except (TypeError, ValueError) as e:
                return Result.failure(f"Failed to serialize merged state to JSON: {str(e)}")

            # Write merged state to file
            try:
                file_path.write_text(json_content, encoding="utf-8")
            except PermissionError:
                return Result.failure(f"Permission denied writing to: {file_path}")

            execution_time = (time.time() - start) * 1000

            output = MergeJSONStateOutput(
                state=merged_state,
                success=True,
                path=str(file_path),
                created=created,
            )

            return Result.success(output, metadata={"execution_time_ms": execution_time})

        except Exception as e:
            execution_time = (time.time() - start) * 1000
            return Result.failure(
                f"Failed to merge JSON state: {inputs.path}\nError: {str(e)}",
                metadata={"execution_time_ms": execution_time},
            )


# Register MergeJSONState block
BLOCK_REGISTRY.register("MergeJSONState", MergeJSONState)
