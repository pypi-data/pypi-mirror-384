"""Interactive workflow executors with pause/resume."""

import re
from typing import Any, ClassVar

from pydantic import Field

from .block import BlockInput, BlockOutput
from .block_utils import ExecutionTimer
from .checkpoint import PauseData
from .executor_base import (
    EXECUTOR_REGISTRY,
    BlockExecutor,
    ExecutorCapabilities,
    ExecutorSecurityLevel,
)
from .result import Result

# ============================================================================
# ConfirmOperation Executor
# ============================================================================


class ConfirmOperationInput(BlockInput):
    """Input for ConfirmOperation executor."""

    message: str = Field(description="Confirmation message to display")
    operation: str = Field(description="Operation being confirmed")
    details: dict[str, Any] = Field(default_factory=dict, description="Additional context details")


class ConfirmOperationOutput(BlockOutput):
    """Output for ConfirmOperation executor."""

    confirmed: bool = Field(description="Whether user confirmed")
    response: str = Field(description="Raw user response")


class ConfirmOperationExecutor(BlockExecutor):
    """Confirmation executor - pauses workflow for yes/no answer.

    This executor always pauses on first execution, then resumes
    with user's response.

    Example YAML:
        - id: confirm_deploy
          type: ConfirmOperation
          inputs:
            message: "Deploy to production?"
            operation: "production_deploy"
            details:
              environment: "production"
              version: "v1.2.3"
    """

    type_name: ClassVar[str] = "ConfirmOperation"
    input_type: ClassVar[type[BlockInput]] = ConfirmOperationInput
    output_type: ClassVar[type[BlockOutput]] = ConfirmOperationOutput

    security_level: ClassVar[ExecutorSecurityLevel] = ExecutorSecurityLevel.SAFE
    capabilities: ClassVar[ExecutorCapabilities] = ExecutorCapabilities()

    async def execute(self, inputs: BlockInput, context: dict[str, Any]) -> Result[BlockOutput]:
        """Execute confirmation - always pauses for user input.

        Args:
            inputs: Validated ConfirmOperationInput
            context: Workflow context (unused by this executor)

        Returns:
            Result.pause() with prompt for LLM
        """
        assert isinstance(inputs, ConfirmOperationInput)
        # Build prompt for LLM
        prompt = f"Confirm operation: {inputs.message}\n\nRespond with 'yes' or 'no'"

        # Create pause data
        pause_data = PauseData(
            prompt=prompt,
            checkpoint_id="",  # Will be filled by workflow executor
            pause_metadata={
                "type": "confirm",
                "operation": inputs.operation,
                "details": inputs.details,
            },
        )

        return Result.pause(
            prompt=pause_data.prompt,
            checkpoint_id=pause_data.checkpoint_id,
            **pause_data.pause_metadata,
        )

    async def resume(
        self,
        inputs: BlockInput,
        context: dict[str, Any],
        llm_response: str,
        pause_metadata: dict[str, Any],
    ) -> Result[BlockOutput]:
        """Resume with user response.

        Args:
            inputs: Original ConfirmOperationInput
            context: Workflow context
            llm_response: LLM's response to the confirmation prompt
            pause_metadata: Metadata from the pause

        Returns:
            Result with ConfirmOperationOutput
        """
        assert isinstance(inputs, ConfirmOperationInput)
        timer = ExecutionTimer()

        # Parse response - accept various affirmative responses
        response_lower = llm_response.strip().lower()
        confirmed = response_lower in ("yes", "y", "true", "1", "confirm", "approved")

        output = ConfirmOperationOutput(
            confirmed=confirmed,
            response=llm_response,
        )

        return Result.success(output, metadata={"execution_time_ms": timer.elapsed_ms()})


# ============================================================================
# AskChoice Executor
# ============================================================================


class AskChoiceInput(BlockInput):
    """Input for AskChoice executor."""

    question: str = Field(description="Question to ask")
    choices: list[str] = Field(description="Available choices")


class AskChoiceOutput(BlockOutput):
    """Output for AskChoice executor."""

    choice: str = Field(description="Selected choice")
    choice_index: int = Field(description="Index of selected choice (0-based)")


class AskChoiceExecutor(BlockExecutor):
    """Choice selection executor - pauses workflow for multiple choice selection.

    Example YAML:
        - id: select_env
          type: AskChoice
          inputs:
            question: "Select deployment environment:"
            choices: ["development", "staging", "production"]

    Accepts responses:
        - By number: "2" selects second choice (1-indexed)
        - By text: "production" selects matching choice
    """

    type_name: ClassVar[str] = "AskChoice"
    input_type: ClassVar[type[BlockInput]] = AskChoiceInput
    output_type: ClassVar[type[BlockOutput]] = AskChoiceOutput

    security_level: ClassVar[ExecutorSecurityLevel] = ExecutorSecurityLevel.SAFE
    capabilities: ClassVar[ExecutorCapabilities] = ExecutorCapabilities()

    async def execute(self, inputs: BlockInput, context: dict[str, Any]) -> Result[BlockOutput]:
        """Execute choice selection - always pauses for user input.

        Args:
            inputs: Validated AskChoiceInput
            context: Workflow context (unused by this executor)

        Returns:
            Result.pause() with formatted choices prompt
        """
        assert isinstance(inputs, AskChoiceInput)
        # Format choices for display
        choices_str = "\n".join(f"{i + 1}. {c}" for i, c in enumerate(inputs.choices))
        prompt = (
            f"{inputs.question}\n\nChoices:\n{choices_str}\n\n"
            f"Respond with the number of your choice."
        )

        # Create pause data
        pause_data = PauseData(
            prompt=prompt,
            checkpoint_id="",  # Will be filled by workflow executor
            pause_metadata={
                "type": "choice",
                "choices": inputs.choices,
            },
        )

        return Result.pause(
            prompt=pause_data.prompt,
            checkpoint_id=pause_data.checkpoint_id,
            **pause_data.pause_metadata,
        )

    async def resume(
        self,
        inputs: BlockInput,
        context: dict[str, Any],
        llm_response: str,
        pause_metadata: dict[str, Any],
    ) -> Result[BlockOutput]:
        """Resume with user choice.

        Args:
            inputs: Original AskChoiceInput
            context: Workflow context
            llm_response: LLM's response with selected choice
            pause_metadata: Metadata from the pause (contains choices list)

        Returns:
            Result with AskChoiceOutput
        """
        assert isinstance(inputs, AskChoiceInput)
        timer = ExecutionTimer()
        choices = pause_metadata.get("choices", inputs.choices)

        # Try parsing as number first (1-indexed)
        try:
            choice_num = int(llm_response.strip())
            if 1 <= choice_num <= len(choices):
                choice = choices[choice_num - 1]
                output = AskChoiceOutput(choice=choice, choice_index=choice_num - 1)
                return Result.success(output, metadata={"execution_time_ms": timer.elapsed_ms()})
        except ValueError:
            pass

        # Try text match (case-insensitive substring match)
        response_lower = llm_response.strip().lower()
        for i, choice in enumerate(choices):
            if choice.lower() in response_lower or response_lower in choice.lower():
                output = AskChoiceOutput(choice=choice, choice_index=i)
                return Result.success(output, metadata={"execution_time_ms": timer.elapsed_ms()})

        # No match found
        return Result.failure(f"Invalid choice: {llm_response}")


# ============================================================================
# GetInput Executor
# ============================================================================


class GetInputInput(BlockInput):
    """Input for GetInput executor."""

    prompt: str = Field(description="Prompt for LLM")
    validation_pattern: str | None = Field(
        default=None, description="Optional regex pattern for validation"
    )


class GetInputOutput(BlockOutput):
    """Output for GetInput executor."""

    input_value: str = Field(description="Input provided by LLM")


class GetInputExecutor(BlockExecutor):
    """Free-form input executor - pauses workflow for text input.

    Example YAML:
        - id: get_email
          type: GetInput
          inputs:
            prompt: "Enter your email address:"
            validation_pattern: "^[\\w\\.-]+@[\\w\\.-]+\\.\\w+$"

    Optional validation_pattern validates input against regex.
    """

    type_name: ClassVar[str] = "GetInput"
    input_type: ClassVar[type[BlockInput]] = GetInputInput
    output_type: ClassVar[type[BlockOutput]] = GetInputOutput

    security_level: ClassVar[ExecutorSecurityLevel] = ExecutorSecurityLevel.SAFE
    capabilities: ClassVar[ExecutorCapabilities] = ExecutorCapabilities()

    async def execute(self, inputs: BlockInput, context: dict[str, Any]) -> Result[BlockOutput]:
        """Execute input request - always pauses for user input.

        Args:
            inputs: Validated GetInputInput
            context: Workflow context (unused by this executor)

        Returns:
            Result.pause() with input prompt
        """
        assert isinstance(inputs, GetInputInput)
        # Create pause data
        pause_data = PauseData(
            prompt=inputs.prompt,
            checkpoint_id="",  # Will be filled by workflow executor
            pause_metadata={
                "type": "input",
                "validation_pattern": inputs.validation_pattern,
            },
        )

        return Result.pause(
            prompt=pause_data.prompt,
            checkpoint_id=pause_data.checkpoint_id,
            **pause_data.pause_metadata,
        )

    async def resume(
        self,
        inputs: BlockInput,
        context: dict[str, Any],
        llm_response: str,
        pause_metadata: dict[str, Any],
    ) -> Result[BlockOutput]:
        """Resume with user input.

        Args:
            inputs: Original GetInputInput
            context: Workflow context
            llm_response: LLM's response with input value
            pause_metadata: Metadata from the pause (contains validation pattern)

        Returns:
            Result with GetInputOutput
        """
        assert isinstance(inputs, GetInputInput)
        timer = ExecutionTimer()

        # Validate against pattern if provided
        validation_pattern = pause_metadata.get("validation_pattern", inputs.validation_pattern)

        if validation_pattern:
            try:
                if not re.match(validation_pattern, llm_response):
                    return Result.failure(
                        f"Input doesn't match pattern {validation_pattern}: {llm_response}"
                    )
            except re.error as e:
                return Result.failure(f"Invalid regex pattern {validation_pattern}: {e}")

        output = GetInputOutput(input_value=llm_response)

        return Result.success(output, metadata={"execution_time_ms": timer.elapsed_ms()})


# ============================================================================
# Registration
# ============================================================================

EXECUTOR_REGISTRY.register(ConfirmOperationExecutor())
EXECUTOR_REGISTRY.register(AskChoiceExecutor())
EXECUTOR_REGISTRY.register(GetInputExecutor())
