"""Tests for interactive workflow executors with pause/resume."""

import pytest

from workflows_mcp.engine.executors_interactive import (
    AskChoiceExecutor,
    AskChoiceInput,
    ConfirmOperationExecutor,
    ConfirmOperationInput,
    GetInputExecutor,
    GetInputInput,
)

# ============================================================================
# ConfirmOperation Tests
# ============================================================================


@pytest.mark.asyncio
async def test_confirm_operation_pauses() -> None:
    """Test ConfirmOperation pauses on first execution."""
    executor = ConfirmOperationExecutor()
    inputs = ConfirmOperationInput(
        message="Deploy to production?",
        operation="production_deploy",
        details={"env": "prod"},
    )

    result = await executor.execute(inputs, {})

    # Verify pause
    assert not result.is_success
    assert result.is_paused
    assert result.pause_data is not None
    assert "Deploy to production?" in result.pause_data.prompt
    assert result.pause_data.pause_metadata["type"] == "confirm"


@pytest.mark.asyncio
async def test_confirm_operation_resume_yes() -> None:
    """Test ConfirmOperation resume with affirmative responses."""
    executor = ConfirmOperationExecutor()
    inputs = ConfirmOperationInput(message="Continue?", operation="test_op", details={})

    # Test various affirmative responses
    for response in ["yes", "YES", "y", "Y", "true", "confirm", "approved"]:
        result = await executor.resume(inputs, {}, response, {})

        assert result.is_success
        assert result.value.confirmed is True
        assert result.value.response == response


@pytest.mark.asyncio
async def test_confirm_operation_resume_no() -> None:
    """Test ConfirmOperation resume with negative responses."""
    executor = ConfirmOperationExecutor()
    inputs = ConfirmOperationInput(message="Continue?", operation="test_op", details={})

    # Test various negative responses
    for response in ["no", "NO", "n", "N", "false", "cancel", "denied"]:
        result = await executor.resume(inputs, {}, response, {})

        assert result.is_success
        assert result.value.confirmed is False
        assert result.value.response == response


@pytest.mark.asyncio
async def test_confirm_operation_resume_timing() -> None:
    """Test ConfirmOperation resume includes timing metadata."""
    executor = ConfirmOperationExecutor()
    inputs = ConfirmOperationInput(message="Continue?", operation="test_op", details={})

    result = await executor.resume(inputs, {}, "yes", {})

    assert result.is_success
    assert "execution_time_ms" in result.metadata
    assert result.metadata["execution_time_ms"] >= 0


# ============================================================================
# AskChoice Tests
# ============================================================================


@pytest.mark.asyncio
async def test_ask_choice_pauses() -> None:
    """Test AskChoice pauses on first execution."""
    executor = AskChoiceExecutor()
    inputs = AskChoiceInput(
        question="Select environment:",
        choices=["development", "staging", "production"],
    )

    result = await executor.execute(inputs, {})

    # Verify pause
    assert not result.is_success
    assert result.is_paused
    assert result.pause_data is not None
    assert "Select environment:" in result.pause_data.prompt
    assert "1. development" in result.pause_data.prompt
    assert "2. staging" in result.pause_data.prompt
    assert "3. production" in result.pause_data.prompt


@pytest.mark.asyncio
async def test_ask_choice_resume_by_number() -> None:
    """Test AskChoice resume with numeric selection (1-indexed)."""
    executor = AskChoiceExecutor()
    inputs = AskChoiceInput(question="Select:", choices=["option1", "option2", "option3"])
    pause_metadata = {"choices": inputs.choices}

    # Test selecting by number
    result = await executor.resume(inputs, {}, "2", pause_metadata)

    assert result.is_success
    assert result.value.choice == "option2"
    assert result.value.choice_index == 1  # 0-based index


@pytest.mark.asyncio
async def test_ask_choice_resume_by_text() -> None:
    """Test AskChoice resume with text matching."""
    executor = AskChoiceExecutor()
    inputs = AskChoiceInput(question="Select:", choices=["development", "staging", "production"])
    pause_metadata = {"choices": inputs.choices}

    # Test selecting by text (case-insensitive substring)
    result = await executor.resume(inputs, {}, "production", pause_metadata)

    assert result.is_success
    assert result.value.choice == "production"
    assert result.value.choice_index == 2


@pytest.mark.asyncio
async def test_ask_choice_resume_partial_match() -> None:
    """Test AskChoice resume with partial text match."""
    executor = AskChoiceExecutor()
    inputs = AskChoiceInput(question="Select:", choices=["development", "staging", "production"])
    pause_metadata = {"choices": inputs.choices}

    # Test partial match
    result = await executor.resume(inputs, {}, "prod", pause_metadata)

    assert result.is_success
    assert result.value.choice == "production"
    assert result.value.choice_index == 2


@pytest.mark.asyncio
async def test_ask_choice_resume_invalid() -> None:
    """Test AskChoice resume with invalid selection."""
    executor = AskChoiceExecutor()
    inputs = AskChoiceInput(question="Select:", choices=["option1", "option2"])
    pause_metadata = {"choices": inputs.choices}

    # Test invalid number
    result = await executor.resume(inputs, {}, "99", pause_metadata)
    assert not result.is_success
    assert "invalid choice" in result.error.lower()

    # Test invalid text
    result = await executor.resume(inputs, {}, "nonexistent", pause_metadata)
    assert not result.is_success
    assert "invalid choice" in result.error.lower()


@pytest.mark.asyncio
async def test_ask_choice_resume_timing() -> None:
    """Test AskChoice resume includes timing metadata."""
    executor = AskChoiceExecutor()
    inputs = AskChoiceInput(question="Select:", choices=["option1", "option2"])
    pause_metadata = {"choices": inputs.choices}

    result = await executor.resume(inputs, {}, "1", pause_metadata)

    assert result.is_success
    assert "execution_time_ms" in result.metadata
    assert result.metadata["execution_time_ms"] >= 0


# ============================================================================
# GetInput Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_input_pauses() -> None:
    """Test GetInput pauses on first execution."""
    executor = GetInputExecutor()
    inputs = GetInputInput(prompt="Enter your name:")

    result = await executor.execute(inputs, {})

    # Verify pause
    assert not result.is_success
    assert result.is_paused
    assert result.pause_data is not None
    assert result.pause_data.prompt == "Enter your name:"


@pytest.mark.asyncio
async def test_get_input_resume_success() -> None:
    """Test GetInput resume with valid input."""
    executor = GetInputExecutor()
    inputs = GetInputInput(prompt="Enter your name:")
    pause_metadata = {"validation_pattern": None}

    result = await executor.resume(inputs, {}, "John Doe", pause_metadata)

    assert result.is_success
    assert result.value.input_value == "John Doe"


@pytest.mark.asyncio
async def test_get_input_resume_with_validation_success() -> None:
    """Test GetInput resume with valid pattern match."""
    executor = GetInputExecutor()
    inputs = GetInputInput(prompt="Enter email:", validation_pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")
    pause_metadata = {"validation_pattern": inputs.validation_pattern}

    result = await executor.resume(inputs, {}, "user@example.com", pause_metadata)

    assert result.is_success
    assert result.value.input_value == "user@example.com"


@pytest.mark.asyncio
async def test_get_input_resume_with_validation_failure() -> None:
    """Test GetInput resume with invalid pattern match."""
    executor = GetInputExecutor()
    inputs = GetInputInput(prompt="Enter email:", validation_pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")
    pause_metadata = {"validation_pattern": inputs.validation_pattern}

    result = await executor.resume(inputs, {}, "not-an-email", pause_metadata)

    assert not result.is_success
    assert "doesn't match pattern" in result.error.lower()


@pytest.mark.asyncio
async def test_get_input_resume_invalid_pattern() -> None:
    """Test GetInput resume with invalid regex pattern."""
    executor = GetInputExecutor()
    inputs = GetInputInput(prompt="Enter:", validation_pattern="[invalid(")
    pause_metadata = {"validation_pattern": inputs.validation_pattern}

    result = await executor.resume(inputs, {}, "test", pause_metadata)

    assert not result.is_success
    assert "invalid regex pattern" in result.error.lower()


@pytest.mark.asyncio
async def test_get_input_resume_timing() -> None:
    """Test GetInput resume includes timing metadata."""
    executor = GetInputExecutor()
    inputs = GetInputInput(prompt="Enter:")
    pause_metadata = {"validation_pattern": None}

    result = await executor.resume(inputs, {}, "test input", pause_metadata)

    assert result.is_success
    assert "execution_time_ms" in result.metadata
    assert result.metadata["execution_time_ms"] >= 0


# ============================================================================
# Security and Edge Cases
# ============================================================================


@pytest.mark.asyncio
async def test_interactive_executors_security_level() -> None:
    """Test interactive executors have SAFE security level."""
    executors = [
        ConfirmOperationExecutor(),
        AskChoiceExecutor(),
        GetInputExecutor(),
    ]

    for executor in executors:
        from workflows_mcp.engine.executor_base import ExecutorSecurityLevel

        assert executor.security_level == ExecutorSecurityLevel.SAFE


@pytest.mark.asyncio
async def test_interactive_executors_no_capabilities() -> None:
    """Test interactive executors have no special capabilities."""
    executors = [
        ConfirmOperationExecutor(),
        AskChoiceExecutor(),
        GetInputExecutor(),
    ]

    for executor in executors:
        caps = executor.capabilities
        assert caps.can_read_files is False
        assert caps.can_write_files is False
        assert caps.can_execute_commands is False
        assert caps.can_network is False
        assert caps.can_modify_state is False


@pytest.mark.asyncio
async def test_get_input_unicode_handling() -> None:
    """Test GetInput handles Unicode input correctly."""
    executor = GetInputExecutor()
    inputs = GetInputInput(prompt="Enter:")
    pause_metadata = {"validation_pattern": None}

    # Test various Unicode inputs
    unicode_inputs = ["你好", "مرحبا", "🚀", "Привет"]

    for unicode_input in unicode_inputs:
        result = await executor.resume(inputs, {}, unicode_input, pause_metadata)
        assert result.is_success
        assert result.value.input_value == unicode_input


@pytest.mark.asyncio
async def test_ask_choice_case_insensitive_matching() -> None:
    """Test AskChoice text matching is case-insensitive."""
    executor = AskChoiceExecutor()
    inputs = AskChoiceInput(question="Select:", choices=["Development", "Staging"])
    pause_metadata = {"choices": inputs.choices}

    # Test various case combinations
    for response in ["development", "DEVELOPMENT", "DevELopMent"]:
        result = await executor.resume(inputs, {}, response, pause_metadata)
        assert result.is_success
        assert result.value.choice == "Development"


@pytest.mark.asyncio
async def test_confirm_operation_whitespace_handling() -> None:
    """Test ConfirmOperation handles whitespace correctly."""
    executor = ConfirmOperationExecutor()
    inputs = ConfirmOperationInput(message="Continue?", operation="test", details={})

    # Test responses with whitespace
    result = await executor.resume(inputs, {}, "  yes  ", {})
    assert result.is_success
    assert result.value.confirmed is True

    result = await executor.resume(inputs, {}, "\tno\n", {})
    assert result.is_success
    assert result.value.confirmed is False
