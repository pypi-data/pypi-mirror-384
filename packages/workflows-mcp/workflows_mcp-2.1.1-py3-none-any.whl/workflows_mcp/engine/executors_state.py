"""JSON state management executors."""

from typing import Any, ClassVar

from pydantic import Field

from .block import BlockInput, BlockOutput
from .block_utils import ExecutionTimer, JSONOperations, PathResolver
from .executor_base import (
    EXECUTOR_REGISTRY,
    BlockExecutor,
    ExecutorCapabilities,
    ExecutorSecurityLevel,
)
from .result import Result

# ============================================================================
# ReadJSONState Executor
# ============================================================================


class ReadJSONStateInput(BlockInput):
    """Input for ReadJSONState executor."""

    path: str = Field(description="Path to JSON file")
    required: bool = Field(
        default=False, description="Whether file must exist (False returns empty dict)"
    )


class ReadJSONStateOutput(BlockOutput):
    """Output for ReadJSONState executor."""

    data: dict[str, Any] = Field(description="JSON data from file")
    found: bool = Field(description="Whether file was found")
    path: str = Field(description="Absolute path to file")


class ReadJSONStateExecutor(BlockExecutor):
    """Read JSON state file executor."""

    type_name: ClassVar[str] = "ReadJSONState"
    input_type: ClassVar[type[BlockInput]] = ReadJSONStateInput
    output_type: ClassVar[type[BlockOutput]] = ReadJSONStateOutput

    security_level: ClassVar[ExecutorSecurityLevel] = ExecutorSecurityLevel.SAFE
    capabilities: ClassVar[ExecutorCapabilities] = ExecutorCapabilities(can_read_files=True)

    async def execute(self, inputs: BlockInput, context: dict[str, Any]) -> Result[BlockOutput]:
        """Read JSON state file.

        Args:
            inputs: Validated ReadJSONStateInput
            context: Workflow context (unused by this executor)

        Returns:
            Result with ReadJSONStateOutput containing data and metadata
        """
        assert isinstance(inputs, ReadJSONStateInput)
        timer = ExecutionTimer()

        # Resolve path with security validation
        path_result = PathResolver.resolve_and_validate(inputs.path, allow_traversal=True)
        if not path_result.is_success:
            return Result.failure(f"Invalid path: {path_result.error}")

        file_path = path_result.value
        assert file_path is not None

        # Read JSON using utility (handles missing files gracefully)
        read_result = JSONOperations.read_json(file_path, required=inputs.required)

        if not read_result.is_success:
            assert read_result.error is not None
            return Result.failure(read_result.error)

        # Build output
        assert read_result.value is not None
        output = ReadJSONStateOutput(
            data=read_result.value,
            found=file_path.exists(),
            path=str(file_path),
        )

        return Result.success(output, metadata={"execution_time_ms": timer.elapsed_ms()})


# ============================================================================
# WriteJSONState Executor
# ============================================================================


class WriteJSONStateInput(BlockInput):
    """Input for WriteJSONState executor."""

    path: str = Field(description="Path to JSON file")
    data: dict[str, Any] = Field(description="JSON data to write")
    create_parents: bool = Field(default=True, description="Create parent directories if missing")


class WriteJSONStateOutput(BlockOutput):
    """Output for WriteJSONState executor."""

    success: bool = Field(description="Whether write succeeded")
    path: str = Field(description="Absolute path to file")
    size_bytes: int = Field(description="Size of written file in bytes")


class WriteJSONStateExecutor(BlockExecutor):
    """Write JSON state file executor."""

    type_name: ClassVar[str] = "WriteJSONState"
    input_type: ClassVar[type[BlockInput]] = WriteJSONStateInput
    output_type: ClassVar[type[BlockOutput]] = WriteJSONStateOutput

    security_level: ClassVar[ExecutorSecurityLevel] = ExecutorSecurityLevel.TRUSTED
    capabilities: ClassVar[ExecutorCapabilities] = ExecutorCapabilities(can_write_files=True)

    async def execute(self, inputs: BlockInput, context: dict[str, Any]) -> Result[BlockOutput]:
        """Write JSON state file.

        Args:
            inputs: Validated WriteJSONStateInput
            context: Workflow context (unused by this executor)

        Returns:
            Result with WriteJSONStateOutput containing success status
        """
        assert isinstance(inputs, WriteJSONStateInput)
        timer = ExecutionTimer()

        # Resolve path with security validation
        path_result = PathResolver.resolve_and_validate(inputs.path, allow_traversal=True)
        if not path_result.is_success:
            return Result.failure(f"Invalid path: {path_result.error}")

        file_path = path_result.value
        assert file_path is not None

        # Create parents if needed
        if inputs.create_parents:
            try:
                file_path.parent.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                return Result.failure(f"Failed to create parent directories: {e}")
        elif not file_path.parent.exists():
            return Result.failure(f"Parent directory missing: {file_path.parent}")

        # Write JSON using utility
        write_result = JSONOperations.write_json(file_path, inputs.data)

        if not write_result.is_success:
            assert write_result.error is not None
            return Result.failure(write_result.error)

        # Get file size
        try:
            size_bytes = file_path.stat().st_size
        except OSError as e:
            return Result.failure(f"Failed to get file size: {e}")

        # Build output
        output = WriteJSONStateOutput(
            success=True,
            path=str(file_path),
            size_bytes=size_bytes,
        )

        return Result.success(output, metadata={"execution_time_ms": timer.elapsed_ms()})


# ============================================================================
# MergeJSONState Executor
# ============================================================================


class MergeJSONStateInput(BlockInput):
    """Input for MergeJSONState executor."""

    path: str = Field(description="Path to JSON file")
    updates: dict[str, Any] = Field(description="Updates to merge")
    create_if_missing: bool = Field(default=True, description="Create file if it doesn't exist")
    create_parents: bool = Field(default=True, description="Create parent directories if missing")


class MergeJSONStateOutput(BlockOutput):
    """Output for MergeJSONState executor."""

    success: bool = Field(description="Whether merge succeeded")
    path: str = Field(description="Absolute path to file")
    created: bool = Field(description="Whether file was created (vs updated)")
    merged_data: dict[str, Any] = Field(description="Result after merge")


class MergeJSONStateExecutor(BlockExecutor):
    """Merge JSON state file executor."""

    type_name: ClassVar[str] = "MergeJSONState"
    input_type: ClassVar[type[BlockInput]] = MergeJSONStateInput
    output_type: ClassVar[type[BlockOutput]] = MergeJSONStateOutput

    security_level: ClassVar[ExecutorSecurityLevel] = ExecutorSecurityLevel.TRUSTED
    capabilities: ClassVar[ExecutorCapabilities] = ExecutorCapabilities(
        can_read_files=True,
        can_write_files=True,
    )

    async def execute(self, inputs: BlockInput, context: dict[str, Any]) -> Result[BlockOutput]:
        """Merge updates into JSON state file.

        This performs a deep merge of updates into existing JSON state.
        Nested dictionaries are merged recursively, while other values
        (lists, primitives) are replaced.

        Args:
            inputs: Validated MergeJSONStateInput
            context: Workflow context (unused by this executor)

        Returns:
            Result with MergeJSONStateOutput containing merged data
        """
        assert isinstance(inputs, MergeJSONStateInput)
        timer = ExecutionTimer()

        # Resolve path with security validation
        path_result = PathResolver.resolve_and_validate(inputs.path, allow_traversal=True)
        if not path_result.is_success:
            return Result.failure(f"Invalid path: {path_result.error}")

        file_path = path_result.value
        assert file_path is not None
        file_existed = file_path.exists()

        # Read existing data
        if file_existed:
            read_result = JSONOperations.read_json(file_path, required=False)
            if not read_result.is_success:
                assert read_result.error is not None
                return Result.failure(read_result.error)
            assert read_result.value is not None
            existing_data = read_result.value
        else:
            if not inputs.create_if_missing:
                return Result.failure(f"File not found: {file_path}")
            existing_data = {}

        # Deep merge using utility
        merged_data = JSONOperations.deep_merge(existing_data, inputs.updates)

        # Create parents if needed
        if inputs.create_parents:
            try:
                file_path.parent.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                return Result.failure(f"Failed to create parent directories: {e}")
        elif not file_path.parent.exists():
            return Result.failure(f"Parent directory missing: {file_path.parent}")

        # Write merged data
        write_result = JSONOperations.write_json(file_path, merged_data)
        if not write_result.is_success:
            assert write_result.error is not None
            return Result.failure(write_result.error)

        # Build output
        output = MergeJSONStateOutput(
            success=True,
            path=str(file_path),
            created=(not file_existed),
            merged_data=merged_data,
        )

        return Result.success(output, metadata={"execution_time_ms": timer.elapsed_ms()})


# ============================================================================
# Registration
# ============================================================================

EXECUTOR_REGISTRY.register(ReadJSONStateExecutor())
EXECUTOR_REGISTRY.register(WriteJSONStateExecutor())
EXECUTOR_REGISTRY.register(MergeJSONStateExecutor())
