"""Interactive workflow blocks for user input and confirmations.

This module provides concrete implementations of InteractiveBlock for common
interactive scenarios:
- ConfirmOperation: Yes/no confirmation dialogs
- AskChoice: Multiple choice selection
- GetInput: Free-form text input with optional validation
"""

import re
from typing import Any, cast

from pydantic import Field

from .block import BlockInput, BlockOutput
from .interactive import InteractiveBlock
from .result import Result


# ===== ConfirmOperation Block =====
class ConfirmOperationInput(BlockInput):
    """Input for confirmation block."""

    message: str = Field(description="Confirmation message to display")
    operation: str = Field(description="Operation being confirmed")
    details: dict[str, Any] = Field(default_factory=dict, description="Additional context")


class ConfirmOperationOutput(BlockOutput):
    """Output from confirmation block."""

    confirmed: bool = Field(description="Whether user confirmed")
    response: str = Field(description="Full LLM response")


class ConfirmOperation(InteractiveBlock):
    """Pause workflow and ask LLM to confirm an operation.

    Example:
        blocks:
          - id: confirm_deploy
            type: ConfirmOperation
            inputs:
              message: "Deploy to production?"
              operation: "production_deploy"

    Returns:
        confirmed: True if LLM responds with yes/y/confirm/approved
        confirmed: False if LLM responds with no/n/cancel/denied
    """

    def input_model(self) -> type[BlockInput]:
        return ConfirmOperationInput

    def output_model(self) -> type[BlockOutput]:
        return ConfirmOperationOutput

    async def execute(self, context: dict[str, Any]) -> Result[BlockOutput]:
        """Pause and request confirmation."""
        inputs = cast(ConfirmOperationInput, self._validated_inputs)

        # Pause and ask for confirmation
        return Result.pause(
            prompt=f"Confirm operation: {inputs.message}\n\nRespond with 'yes' or 'no'",
            checkpoint_id="",  # Filled by executor
            operation=inputs.operation,
            details=inputs.details,
        )

    async def resume(
        self,
        context: dict[str, Any],
        llm_response: str,
        pause_metadata: dict[str, Any],
    ) -> Result[BlockOutput]:
        """Process confirmation response."""
        # Parse LLM response
        response_lower = llm_response.strip().lower()
        confirmed = response_lower in ["yes", "y", "true", "confirm", "approved"]

        return Result.success(ConfirmOperationOutput(confirmed=confirmed, response=llm_response))


# ===== AskChoice Block =====
class AskChoiceInput(BlockInput):
    """Input for choice selection block."""

    question: str = Field(description="Question to ask")
    choices: list[str] = Field(description="Available choices")


class AskChoiceOutput(BlockOutput):
    """Output from choice selection block."""

    choice: str = Field(description="Selected choice")
    choice_index: int = Field(description="Index of selected choice")


class AskChoice(InteractiveBlock):
    """Pause workflow and ask LLM to select from options.

    Example:
        blocks:
          - id: select_env
            type: AskChoice
            inputs:
              question: "Select deployment environment:"
              choices: ["development", "staging", "production"]

    Accepts responses:
        - By number: "2" selects second choice (1-indexed)
        - By text: "production" selects matching choice
    """

    def input_model(self) -> type[BlockInput]:
        return AskChoiceInput

    def output_model(self) -> type[BlockOutput]:
        return AskChoiceOutput

    async def execute(self, context: dict[str, Any]) -> Result[BlockOutput]:
        """Pause and display choices."""
        inputs = cast(AskChoiceInput, self._validated_inputs)

        choices_str = "\n".join(f"{i + 1}. {c}" for i, c in enumerate(inputs.choices))
        prompt = (
            f"{inputs.question}\n\nChoices:\n{choices_str}\n\n"
            f"Respond with the number of your choice."
        )

        return Result.pause(
            prompt=prompt,
            checkpoint_id="",
            choices=inputs.choices,  # Filled by executor
        )

    async def resume(
        self,
        context: dict[str, Any],
        llm_response: str,
        pause_metadata: dict[str, Any],
    ) -> Result[BlockOutput]:
        """Process choice selection."""
        choices = pause_metadata["choices"]

        # Parse response (try as number first, then text match)
        try:
            choice_num = int(llm_response.strip())
            if 1 <= choice_num <= len(choices):
                choice = choices[choice_num - 1]
                return Result.success(AskChoiceOutput(choice=choice, choice_index=choice_num - 1))
        except ValueError:
            pass

        # Try text match
        response_lower = llm_response.strip().lower()
        for i, choice in enumerate(choices):
            if choice.lower() in response_lower:
                return Result.success(AskChoiceOutput(choice=choice, choice_index=i))

        return Result.failure(f"Invalid choice: {llm_response}")


# ===== GetInput Block =====
class GetInputInput(BlockInput):
    """Input for free-form input block."""

    prompt: str = Field(description="Prompt for LLM")
    validation_pattern: str | None = Field(default=None, description="Regex pattern for validation")


class GetInputOutput(BlockOutput):
    """Output from free-form input block."""

    input_value: str = Field(description="Input provided by LLM")


class GetInput(InteractiveBlock):
    """Pause workflow and get free-form input from LLM.

    Example:
        blocks:
          - id: get_email
            type: GetInput
            inputs:
              prompt: "Enter your email address:"
              validation_pattern: "^[\\w\\.-]+@[\\w\\.-]+\\.\\w+$"

    Optional validation_pattern validates input against regex.
    """

    def input_model(self) -> type[BlockInput]:
        return GetInputInput

    def output_model(self) -> type[BlockOutput]:
        return GetInputOutput

    async def execute(self, context: dict[str, Any]) -> Result[BlockOutput]:
        """Pause and request input."""
        inputs = cast(GetInputInput, self._validated_inputs)

        return Result.pause(
            prompt=inputs.prompt,
            checkpoint_id="",  # Filled by executor
            validation_pattern=inputs.validation_pattern,
        )

    async def resume(
        self,
        context: dict[str, Any],
        llm_response: str,
        pause_metadata: dict[str, Any],
    ) -> Result[BlockOutput]:
        """Process input response."""
        validation_pattern = pause_metadata.get("validation_pattern")

        if validation_pattern:
            if not re.match(validation_pattern, llm_response):
                return Result.failure(
                    f"Input doesn't match pattern {validation_pattern}: {llm_response}"
                )

        return Result.success(GetInputOutput(input_value=llm_response))


# Register interactive blocks
from .block import BLOCK_REGISTRY  # noqa: E402

BLOCK_REGISTRY.register("ConfirmOperation", ConfirmOperation)
BLOCK_REGISTRY.register("AskChoice", AskChoice)
BLOCK_REGISTRY.register("GetInput", GetInput)
