"""Tests for InteractiveBlock base class and interactive block implementations.

This test module follows TDD principles:
1. RED: Write failing tests first
2. GREEN: Implement minimal code to pass tests
3. REFACTOR: Improve code while keeping tests passing
"""

import pytest


@pytest.mark.asyncio
async def test_interactive_block_has_resume_method():
    """InteractiveBlock must have resume() method."""
    from workflows_mcp.engine.interactive import InteractiveBlock

    # Check that InteractiveBlock has resume as abstract method
    assert hasattr(InteractiveBlock, "resume")


@pytest.mark.asyncio
async def test_confirm_operation_pauses():
    """ConfirmOperation must pause execution with prompt."""
    from workflows_mcp.engine.blocks_interactive import ConfirmOperation

    block = ConfirmOperation(
        id="confirm1",
        inputs={"message": "Deploy to production?", "operation": "deploy"},
        depends_on=[],
    )

    result = await block.execute({})

    assert result.is_paused is True
    assert result.is_success is False
    assert result.pause_data is not None
    assert "Deploy to production?" in result.pause_data.prompt
    assert "operation" in result.pause_data.pause_metadata
    assert result.pause_data.pause_metadata["operation"] == "deploy"


@pytest.mark.asyncio
async def test_confirm_operation_resume_yes():
    """Resume with 'yes' must set confirmed=True."""
    from workflows_mcp.engine.blocks_interactive import ConfirmOperation

    block = ConfirmOperation(
        id="confirm1",
        inputs={"message": "Deploy?", "operation": "deploy"},
        depends_on=[],
    )

    # First execution pauses
    pause_result = await block.execute({})
    assert pause_result.is_paused

    # Resume with "yes"
    result = await block.resume(
        context={},
        llm_response="yes",
        pause_metadata=pause_result.pause_data.pause_metadata,
    )

    assert result.is_success is True
    assert result.value is not None
    assert result.value.confirmed is True
    assert result.value.response == "yes"


@pytest.mark.asyncio
async def test_confirm_operation_resume_no():
    """Resume with 'no' must set confirmed=False."""
    from workflows_mcp.engine.blocks_interactive import ConfirmOperation

    block = ConfirmOperation(
        id="confirm1",
        inputs={"message": "Deploy?", "operation": "deploy"},
        depends_on=[],
    )

    result = await block.resume(context={}, llm_response="no", pause_metadata={})

    assert result.is_success is True
    assert result.value.confirmed is False


@pytest.mark.asyncio
async def test_confirm_operation_resume_variations():
    """Resume must handle various yes/no variations."""
    from workflows_mcp.engine.blocks_interactive import ConfirmOperation

    block = ConfirmOperation(
        id="confirm1",
        inputs={"message": "Deploy?", "operation": "deploy"},
        depends_on=[],
    )

    # Test "yes" variations
    for response in ["yes", "y", "YES", "Yes", "Y", "confirm", "approved"]:
        result = await block.resume({}, response, {})
        assert result.value.confirmed is True, f"Failed for response: {response}"

    # Test "no" variations
    for response in ["no", "n", "NO", "No", "N", "cancel", "denied"]:
        result = await block.resume({}, response, {})
        assert result.value.confirmed is False, f"Failed for response: {response}"


@pytest.mark.asyncio
async def test_ask_choice_pauses():
    """AskChoice must pause with question and choices."""
    from workflows_mcp.engine.blocks_interactive import AskChoice

    block = AskChoice(
        id="choice1",
        inputs={
            "question": "Select deployment environment:",
            "choices": ["development", "staging", "production"],
        },
        depends_on=[],
    )

    result = await block.execute({})

    assert result.is_paused is True
    assert "Select deployment environment" in result.pause_data.prompt
    assert "development" in result.pause_data.prompt
    assert "staging" in result.pause_data.prompt
    assert "production" in result.pause_data.prompt
    assert result.pause_data.pause_metadata["choices"] == [
        "development",
        "staging",
        "production",
    ]


@pytest.mark.asyncio
async def test_ask_choice_resume_by_number():
    """Resume AskChoice with choice number (1, 2, 3)."""
    from workflows_mcp.engine.blocks_interactive import AskChoice

    block = AskChoice(
        id="choice1",
        inputs={"question": "Select environment:", "choices": ["dev", "staging", "prod"]},
        depends_on=[],
    )

    # Pause to get metadata
    pause_result = await block.execute({})

    # Resume with number "2"
    result = await block.resume(
        context={},
        llm_response="2",
        pause_metadata=pause_result.pause_data.pause_metadata,
    )

    assert result.is_success is True
    assert result.value.choice == "staging"
    assert result.value.choice_index == 1


@pytest.mark.asyncio
async def test_ask_choice_resume_by_text():
    """Resume AskChoice with choice text."""
    from workflows_mcp.engine.blocks_interactive import AskChoice

    block = AskChoice(
        id="choice1",
        inputs={
            "question": "Select:",
            "choices": ["development", "staging", "production"],
        },
        depends_on=[],
    )

    pause_result = await block.execute({})

    # Resume with text "production"
    result = await block.resume(
        context={},
        llm_response="production",
        pause_metadata=pause_result.pause_data.pause_metadata,
    )

    assert result.is_success is True
    assert result.value.choice == "production"
    assert result.value.choice_index == 2


@pytest.mark.asyncio
async def test_ask_choice_invalid_response():
    """Invalid choice must return failure."""
    from workflows_mcp.engine.blocks_interactive import AskChoice

    block = AskChoice(
        id="choice1",
        inputs={"question": "Select:", "choices": ["a", "b", "c"]},
        depends_on=[],
    )

    pause_result = await block.execute({})

    # Invalid number
    result = await block.resume({}, "999", pause_result.pause_data.pause_metadata)
    assert not result.is_success
    assert "invalid" in result.error.lower()

    # Invalid text (using "xyz" which doesn't match any choice)
    result = await block.resume({}, "xyz", pause_result.pause_data.pause_metadata)
    assert not result.is_success


@pytest.mark.asyncio
async def test_get_input_pauses():
    """GetInput must pause with prompt."""
    from workflows_mcp.engine.blocks_interactive import GetInput

    block = GetInput(
        id="input1",
        inputs={"prompt": "Enter your name:"},
        depends_on=[],
    )

    result = await block.execute({})

    assert result.is_paused is True
    assert "Enter your name" in result.pause_data.prompt


@pytest.mark.asyncio
async def test_get_input_resume():
    """GetInput resume must return input value."""
    from workflows_mcp.engine.blocks_interactive import GetInput

    block = GetInput(
        id="input1",
        inputs={"prompt": "Enter name:"},
        depends_on=[],
    )

    pause_result = await block.execute({})

    result = await block.resume(
        context={},
        llm_response="John Doe",
        pause_metadata=pause_result.pause_data.pause_metadata,
    )

    assert result.is_success is True
    assert result.value.input_value == "John Doe"


@pytest.mark.asyncio
async def test_get_input_with_validation():
    """GetInput with regex validation must validate input."""
    from workflows_mcp.engine.blocks_interactive import GetInput

    block = GetInput(
        id="input1",
        inputs={
            "prompt": "Enter email:",
            "validation_pattern": r"^[\w\.-]+@[\w\.-]+\.\w+$",
        },
        depends_on=[],
    )

    pause_result = await block.execute({})

    # Valid email
    result = await block.resume({}, "test@example.com", pause_result.pause_data.pause_metadata)
    assert result.is_success is True

    # Invalid email
    result = await block.resume({}, "not-an-email", pause_result.pause_data.pause_metadata)
    assert not result.is_success
    assert "pattern" in result.error.lower() or "match" in result.error.lower()


@pytest.mark.asyncio
async def test_interactive_blocks_registered():
    """Interactive blocks must be registered in BLOCK_REGISTRY."""
    from workflows_mcp.engine.block import BLOCK_REGISTRY

    registered_types = BLOCK_REGISTRY.list_types()
    assert "ConfirmOperation" in registered_types
    assert "AskChoice" in registered_types
    assert "GetInput" in registered_types
