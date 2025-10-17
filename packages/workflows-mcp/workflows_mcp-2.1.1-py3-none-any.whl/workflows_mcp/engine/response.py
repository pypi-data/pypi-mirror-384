"""Workflow response models.

This module contains the WorkflowResponse model used across the MCP server
for consistent workflow execution result handling.
"""

import os
from typing import Any, Literal

from pydantic import BaseModel, Field


class WorkflowResponse(BaseModel):
    """Unified response model for all workflow execution states.

    This model is the single source of truth for:
    - Output structure across all workflow states
    - Verbosity filtering based on WORKFLOWS_LOG_LEVEL environment variable
    - Serialization logic for MCP tool responses

    Provides a consistent API contract where all fields are always present.
    Fields contain None when not applicable for the current state.

    Verbosity Levels (controlled by WORKFLOWS_LOG_LEVEL):
    - DEBUG: Full details including blocks and metadata
    - INFO/WARNING/ERROR: Minimal output (outputs, error, checkpoint_id only)

    The model handles verbosity filtering during serialization via custom
    model_dump() override, ensuring clean separation of concerns.
    """

    status: Literal["success", "failure", "paused"] = Field(
        description="Workflow execution status indicating outcome"
    )
    outputs: dict[str, Any] | None = Field(
        default=None, description="Workflow outputs on success, None otherwise"
    )
    blocks: dict[str, Any] | None = Field(
        default=None, description="Block execution details (DEBUG mode only), None otherwise"
    )
    metadata: dict[str, Any] | None = Field(
        default=None, description="Execution metadata (DEBUG mode only), None otherwise"
    )
    error: str | None = Field(default=None, description="Error message on failure, None otherwise")
    checkpoint_id: str | None = Field(
        default=None, description="Checkpoint ID when paused, None otherwise"
    )
    prompt: str | None = Field(default=None, description="LLM prompt when paused, None otherwise")
    message: str | None = Field(
        default=None, description="Additional status message, None if not needed"
    )

    @property
    def is_debug(self) -> bool:
        """Check if debug mode is enabled based on WORKFLOWS_LOG_LEVEL.

        Returns:
            True if WORKFLOWS_LOG_LEVEL is set to DEBUG, False otherwise.
        """
        return os.getenv("WORKFLOWS_LOG_LEVEL", "INFO").upper() == "DEBUG"

    @property
    def is_success(self) -> bool:
        """Check if workflow executed successfully.

        Convenience property for backward compatibility with Result interface.

        Returns:
            True if status is "success", False otherwise.
        """
        return self.status == "success"

    @property
    def is_failure(self) -> bool:
        """Check if workflow failed.

        Convenience property for backward compatibility with Result interface.

        Returns:
            True if status is "failure", False otherwise.
        """
        return self.status == "failure"

    @property
    def is_paused(self) -> bool:
        """Check if workflow is paused.

        Convenience property for backward compatibility with Result interface.

        Returns:
            True if status is "paused", False otherwise.
        """
        return self.status == "paused"

    @property
    def value(self) -> dict[str, Any] | None:
        """Get workflow execution result data.

        Convenience property for backward compatibility with Result interface.
        Returns a dict with outputs, blocks, metadata for success cases.

        Returns:
            Dictionary with workflow data for success, None otherwise.
        """
        if self.status == "success":
            return {
                "outputs": self.outputs,
                "blocks": self.blocks,
                "metadata": self.metadata,
            }
        return None

    @property
    def pause_data(self) -> Any:
        """Get pause data for paused workflows.

        Convenience property for backward compatibility with Result interface.
        Returns a simple object with checkpoint_id and prompt attributes.

        Returns:
            Pause data object for paused status, None otherwise.
        """
        if self.status == "paused":
            # Create a simple namespace object with pause data attributes
            from types import SimpleNamespace

            return SimpleNamespace(
                checkpoint_id=self.checkpoint_id,
                prompt=self.prompt,
                pause_metadata=None,  # Not stored in WorkflowResponse
            )
        return None

    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        """Override model_dump to apply verbosity filtering.

        This method is the single source of truth for serialization behavior.
        It filters blocks/metadata based on debug mode and workflow status.

        Verbosity Rules:
        - DEBUG mode: Include all data
        - Non-DEBUG mode:
          - Success: blocks={}, metadata={} (consistent structure)
          - Failure/Paused: blocks=None, metadata=None (fields remain None)

        Args:
            **kwargs: All standard Pydantic model_dump() arguments

        Returns:
            Dictionary with verbosity filtering applied
        """
        # Get base serialization from parent
        data = super().model_dump(**kwargs)

        # Apply verbosity filtering if not in DEBUG mode
        if not self.is_debug:
            # For success status: clear to empty dicts (maintain consistent structure)
            # For failure/paused: keep as None (fields not applicable)
            if data.get("status") == "success":
                if "blocks" in data and data["blocks"] is not None:
                    data["blocks"] = {}
                if "metadata" in data and data["metadata"] is not None:
                    data["metadata"] = {}
            # For failure/paused: blocks and metadata remain None (no change needed)

        return data


__all__ = ["WorkflowResponse"]
