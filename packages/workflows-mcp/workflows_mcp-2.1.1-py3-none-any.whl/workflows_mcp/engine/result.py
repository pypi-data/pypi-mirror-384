"""Result type for workflow error handling."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Generic, TypeVar

if TYPE_CHECKING:
    from workflows_mcp.engine.checkpoint import PauseData

T = TypeVar("T")


@dataclass
class Result(Generic[T]):  # noqa: UP046
    """
    Result type for success/failure handling without exceptions.

    Usage:
        result = some_operation()
        if result.is_success:
            print(result.value)
        else:
            print(result.error)
    """

    is_success: bool
    value: T | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    is_paused: bool = False
    pause_data: "PauseData | None" = None

    @staticmethod
    def success(value: T, metadata: dict[str, Any] | None = None) -> "Result[T]":
        """Create a successful result."""
        return Result(
            is_success=True,
            value=value,
            metadata=metadata if metadata is not None else {},
        )

    @staticmethod
    def failure(error: str, metadata: dict[str, Any] | None = None) -> "Result[T]":
        """Create a failed result."""
        return Result(
            is_success=False,
            error=error,
            metadata=metadata if metadata is not None else {},
        )

    @staticmethod
    def pause(prompt: str, checkpoint_id: str, **pause_metadata: Any) -> "Result[T]":
        """Create a paused result with checkpoint information.

        Args:
            prompt: Human-readable message explaining why workflow is paused
            checkpoint_id: Reference to checkpoint for resumption
            **pause_metadata: Additional metadata about the pause

        Returns:
            Result marked as paused with associated pause data
        """
        from workflows_mcp.engine.checkpoint import PauseData

        pause_data = PauseData(
            prompt=prompt, checkpoint_id=checkpoint_id, pause_metadata=pause_metadata
        )

        return Result(is_success=False, is_paused=True, pause_data=pause_data, metadata={})

    def __bool__(self) -> bool:
        """Allow using result in if statements."""
        return self.is_success

    def unwrap(self) -> T:
        """Get value or raise exception if failed."""
        if not self.is_success:
            raise ValueError(f"Cannot unwrap failed result: {self.error}")
        if self.value is None:
            raise ValueError("Cannot unwrap result: value is None")
        return self.value

    def unwrap_or(self, default: T) -> T:
        """Get value or return default if failed."""
        if self.is_success and self.value is not None:
            return self.value
        return default
