"""Tests for Result.pause() functionality.

Following TDD: Write tests FIRST, then implement.
"""


def test_result_pause_factory():
    """Result.pause() must create paused result."""
    from workflows_mcp.engine.result import Result

    result = Result.pause(prompt="Confirm deployment?", checkpoint_id="pause_123")

    assert result.is_paused is True
    assert result.is_success is False
    assert result.pause_data is not None
    assert result.pause_data.prompt == "Confirm deployment?"
    assert result.pause_data.checkpoint_id == "pause_123"


def test_result_pause_with_metadata():
    """Result.pause() must accept custom metadata."""
    from workflows_mcp.engine.result import Result

    result = Result.pause(
        prompt="Select option",
        checkpoint_id="pause_456",
        operation="deploy",
        environment="production",
    )

    assert result.pause_data.pause_metadata["operation"] == "deploy"
    assert result.pause_data.pause_metadata["environment"] == "production"
