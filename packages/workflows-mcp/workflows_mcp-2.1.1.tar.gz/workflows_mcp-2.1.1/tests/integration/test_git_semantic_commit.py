"""Integration tests for git-semantic-commit workflow."""

import subprocess
from pathlib import Path

import pytest

from workflows_mcp.engine.response import WorkflowResponse
from workflows_mcp.tools import execute_inline_workflow


def to_dict(result):
    """Convert WorkflowResponse to dict for testing."""
    if isinstance(result, WorkflowResponse):
        return result.model_dump()
    return result


@pytest.fixture
def temp_git_repo(tmp_path):
    """Create a temporary git repository for testing."""
    repo_path = tmp_path / "test_repo"
    repo_path.mkdir()

    # Initialize git repo
    subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )

    # Create initial commit
    (repo_path / "README.md").write_text("# Test Repo\n")
    subprocess.run(["git", "add", "."], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "initial commit"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )

    return repo_path


def test_semantic_commit_workflow_loads():
    """Test that the git-semantic-commit workflow loads correctly."""
    from workflows_mcp.engine.loader import load_workflow_from_file

    workflow_path = (
        Path(__file__).parent.parent.parent
        / "src/workflows_mcp/templates/git/git-semantic-commit.yaml"
    )

    result = load_workflow_from_file(workflow_path)
    assert result.is_success, f"Failed to load workflow: {result.error}"

    workflow = result.value
    assert workflow.name == "git-semantic-commit"
    assert len(workflow.blocks) == 13
    assert "stage_all" in workflow.inputs
    assert "repository_path" in workflow.inputs
    assert "auto_commit" in workflow.inputs
    assert "override_message" in workflow.inputs


@pytest.mark.asyncio
async def test_semantic_commit_no_changes(temp_git_repo, mock_context):
    """Test workflow behavior when there are no staged changes."""
    # Don't stage anything
    workflow_path = (
        Path(__file__).parent.parent.parent
        / "src/workflows_mcp/templates/git/git-semantic-commit.yaml"
    )
    workflow_yaml = workflow_path.read_text()

    result = await execute_inline_workflow(
        workflow_yaml, inputs={"repository_path": str(temp_git_repo)}, ctx=mock_context
    )
    result = to_dict(result)

    assert result["status"] == "success"

    outputs = result.get("outputs", {})
    assert outputs.get("has_changes") == "no_changes"
    assert outputs.get("commit_created") != "True" and outputs.get("commit_created") is not True


@pytest.mark.asyncio
async def test_semantic_commit_override_message(temp_git_repo, mock_context):
    """Test manual commit message override."""

    # Create and stage a file
    (temp_git_repo / "test.py").write_text("# Test\n")
    subprocess.run(["git", "add", "test.py"], cwd=temp_git_repo, check=True, capture_output=True)

    custom_message = "feat(custom): my custom commit message"

    workflow_path = (
        Path(__file__).parent.parent.parent
        / "src/workflows_mcp/templates/git/git-semantic-commit.yaml"
    )
    workflow_yaml = workflow_path.read_text()

    result = await execute_inline_workflow(
        workflow_yaml,
        inputs={
            "repository_path": str(temp_git_repo),
            "override_message": custom_message,
            "auto_commit": True,
        },
        ctx=mock_context,
    )
    result = to_dict(result)

    assert result["status"] == "success"

    outputs = result.get("outputs", {})
    assert outputs.get("commit_created") == "True" or outputs.get("commit_created") is True
    assert outputs.get("generated_message") == custom_message

    # Verify commit message
    commit_result = subprocess.run(
        ["git", "log", "-1", "--pretty=%s"], cwd=temp_git_repo, capture_output=True, text=True
    )
    assert commit_result.stdout.strip() == custom_message
