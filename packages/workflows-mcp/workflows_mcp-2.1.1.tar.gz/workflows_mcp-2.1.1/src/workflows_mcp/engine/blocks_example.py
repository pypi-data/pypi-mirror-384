"""Example workflow blocks for testing and demonstrations.

This module provides EchoBlock, a simple async workflow block used for:
- Testing the workflow engine without external dependencies
- Demonstrating workflow patterns in example workflows
- Validating async block execution in test suites
- Learning basic workflow block implementation

The EchoBlock is intentionally simple to serve as a reference implementation
and testing fixture rather than production functionality.
"""

import asyncio
from typing import Any

from pydantic import Field

# Get the global registry instance
from .block import BLOCK_REGISTRY, BlockInput, BlockOutput, WorkflowBlock
from .result import Result


class EchoBlockInput(BlockInput):
    """Input for EchoBlock."""

    message: str = Field(description="Message to echo")
    delay_ms: int = Field(default=0, description="Delay in milliseconds")


class EchoBlockOutput(BlockOutput):
    """Output for EchoBlock."""

    echoed: str = Field(description="Echoed message")
    execution_time_ms: float = Field(description="Execution time")


class EchoBlock(WorkflowBlock):
    """
    Example async block that echoes a message with optional delay.

    Demonstrates:
    - Async execution (via asyncio.sleep)
    - Pydantic validation
    - Result monad usage
    - Context access
    """

    def input_model(self) -> type[BlockInput]:
        return EchoBlockInput

    def output_model(self) -> type[BlockOutput]:
        return EchoBlockOutput

    async def execute(self, context: dict[str, Any]) -> Result[BlockOutput]:
        """Echo the message after optional delay."""
        import time
        from typing import cast

        inputs = cast(EchoBlockInput, self._validated_inputs)
        if inputs is None:
            return Result.failure("Inputs not validated")

        start = time.time()

        # Simulate async I/O with delay
        if inputs.delay_ms > 0:
            await asyncio.sleep(inputs.delay_ms / 1000.0)

        execution_time = (time.time() - start) * 1000  # Convert to ms

        output = EchoBlockOutput(echoed=f"Echo: {inputs.message}", execution_time_ms=execution_time)

        return Result.success(output)


# Register example block
BLOCK_REGISTRY.register("EchoBlock", EchoBlock)
