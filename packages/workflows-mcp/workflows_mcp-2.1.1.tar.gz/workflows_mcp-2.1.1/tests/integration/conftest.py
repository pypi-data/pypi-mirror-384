"""Integration test-specific fixtures.

Fixtures for tests that span multiple components or require complex setup.
"""

import subprocess
from pathlib import Path
from typing import Any

import pytest

from workflows_mcp.engine.block import BLOCK_REGISTRY
from workflows_mcp.engine.blocks_example import EchoBlock
from workflows_mcp.engine.executor import WorkflowExecutor
from workflows_mcp.engine.registry import WorkflowRegistry


@pytest.fixture
def populated_registry(temp_workflow_dir: Path) -> WorkflowRegistry:
    """Registry loaded with temporary test workflows.

    Args:
        temp_workflow_dir: Path to directory containing test workflow YAML files

    Returns:
        WorkflowRegistry loaded with workflows from temp directory

    Raises:
        AssertionError: If workflows fail to load
    """
    registry = WorkflowRegistry()
    result = registry.load_from_directory(str(temp_workflow_dir))
    assert result.is_success, f"Failed to load workflows: {result.error}"
    return registry


@pytest.fixture
def executor_with_context() -> WorkflowExecutor:
    """Executor with pre-populated context for integration tests.

    Returns:
        WorkflowExecutor with context pre-populated with test values
    """
    # Ensure EchoBlock is registered
    if "EchoBlock" not in BLOCK_REGISTRY.list_types():
        BLOCK_REGISTRY.register("EchoBlock", EchoBlock)

    executor = WorkflowExecutor()
    executor.context = {
        "workspace": "/tmp/test-workspace",
        "project_name": "integration-test",
        "version": "1.0.0",
    }
    return executor


@pytest.fixture
def mock_workflow_dir(tmp_path: Path) -> Path:
    """Create a temporary directory with mock workflow files.

    Args:
        tmp_path: pytest's temporary directory fixture

    Returns:
        Path to directory containing mock workflow YAML files
    """
    workflow_dir = tmp_path / "mock_workflows"
    workflow_dir.mkdir()

    # Create a simple workflow
    (workflow_dir / "simple.yaml").write_text("""name: simple-workflow
description: Simple mock workflow
version: 1.0
tags:
  - test
  - mock
blocks:
  - id: greet
    type: EchoBlock
    inputs:
      message: Hello from mock workflow
""")

    # Create a workflow with dependencies
    (workflow_dir / "dependencies.yaml").write_text("""name: dependency-workflow
description: Workflow with dependencies
version: 1.0
tags:
  - test
  - dependencies
blocks:
  - id: step1
    type: EchoBlock
    inputs:
      message: Step 1

  - id: step2
    type: EchoBlock
    inputs:
      message: Step 2 depends on step1
    depends_on:
      - step1

  - id: step3
    type: EchoBlock
    inputs:
      message: Step 3 depends on step2
    depends_on:
      - step2
""")

    return workflow_dir


@pytest.fixture
def temp_template_dir(tmp_path: Path) -> Path:
    """Create a temporary directory for template testing.

    Args:
        tmp_path: pytest's temporary directory fixture

    Returns:
        Path to directory for template operations
    """
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    return template_dir


@pytest.fixture
def integration_context() -> dict[str, Any]:
    """Pre-populated context for integration testing.

    Returns:
        Dictionary with common context values for integration tests
    """
    return {
        "workspace": "/tmp/integration-workspace",
        "project_name": "integration-project",
        "version": "2.0.0",
        "environment": "test",
        "debug": True,
    }


@pytest.fixture
def temp_workspace(tmp_path: Path) -> Path:
    """Provide temporary workspace for workflow execution.

    Args:
        tmp_path: pytest's temporary directory fixture

    Returns:
        Path to temporary workspace directory
    """
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    return workspace


@pytest.fixture
def mock_git_repo(tmp_path: Path) -> Path:
    """Create mock git repository for testing git workflows.

    Args:
        tmp_path: pytest's temporary directory fixture

    Returns:
        Path to initialized git repository with initial commit

    Note:
        Repository is configured with test user credentials
    """
    repo = tmp_path / "repo"
    repo.mkdir()

    # Initialize git repository
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo,
        check=True,
        capture_output=True,
    )

    # Create initial commit
    readme = repo / "README.md"
    readme.write_text("# Test Repository\n")
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo,
        check=True,
        capture_output=True,
    )

    return repo
