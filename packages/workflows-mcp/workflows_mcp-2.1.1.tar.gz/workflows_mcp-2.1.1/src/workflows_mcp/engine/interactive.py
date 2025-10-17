"""Interactive blocks that can pause workflow execution for LLM input.

This module provides the InteractiveBlock base class, which extends WorkflowBlock
with the ability to pause execution and resume with LLM responses.
"""

from abc import abstractmethod
from typing import Any

from .block import BlockOutput, WorkflowBlock
from .result import Result


class InteractiveBlock(WorkflowBlock):
    """Base class for blocks that can pause workflow execution.

    Interactive blocks extend WorkflowBlock with the ability to:
    1. Pause workflow execution mid-block
    2. Request input from the LLM with a prompt
    3. Resume execution with the LLM's response

    Subclasses must implement both execute() and resume() methods.

    Example use cases:
    - User confirmation dialogs
    - Parameter selection from options
    - Human-in-the-loop decision points
    - External approval workflows

    Example:
        class ConfirmOperation(InteractiveBlock):
            async def execute(self, context):
                return Result.pause(
                    prompt="Confirm operation: Deploy to production?",
                    checkpoint_id="",  # Filled by executor
                    operation="deploy"
                )

            async def resume(self, context, llm_response, pause_metadata):
                confirmed = llm_response.lower() in ["yes", "y"]
                return Result.success(ConfirmOperationOutput(confirmed=confirmed))
    """

    @abstractmethod
    async def execute(self, context: dict[str, Any]) -> Result[BlockOutput]:
        """Initial execution - may return Result.pause().

        If this block needs LLM input, return Result.pause(prompt="...").
        Otherwise, return Result.success() or Result.failure() as normal.

        Args:
            context: Shared workflow context

        Returns:
            Result.success(), Result.failure(), or Result.pause()
        """
        pass

    @abstractmethod
    async def resume(
        self,
        context: dict[str, Any],
        llm_response: str,
        pause_metadata: dict[str, Any],
    ) -> Result[BlockOutput]:
        """Resume execution with LLM response.

        Called when workflow is resumed after a pause. The block should
        process the LLM's response and either:
        - Complete successfully (Result.success())
        - Fail (Result.failure())
        - Pause again (Result.pause()) for multi-step interactions

        Args:
            context: Restored workflow context
            llm_response: The LLM's response to the pause prompt
            pause_metadata: Metadata stored when block paused

        Returns:
            Result.success(), Result.failure(), or Result.pause()
        """
        pass
