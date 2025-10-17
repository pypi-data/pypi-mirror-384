"""Shared pytest fixtures for workflows-mcp test suite.

This file contains fixtures used across multiple test categories to reduce
duplication and ensure consistent test setup.

Fixture Scoping Strategy:
- Session: Read-only paths and expensive one-time setup
- Module: Shared state within a test module
- Function: Fresh instances for test isolation (default)
"""

import os
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from workflows_mcp.context import AppContext
from workflows_mcp.engine.block import BLOCK_REGISTRY
from workflows_mcp.engine.blocks_example import EchoBlock
from workflows_mcp.engine.executor import WorkflowExecutor
from workflows_mcp.engine.registry import WorkflowRegistry
from workflows_mcp.engine.schema import WorkflowSchema

# ============================================================================
# Global Test Configuration
# ============================================================================


def pytest_configure(config):
    """Set WORKFLOWS_LOG_LEVEL=DEBUG for all tests.

    Tests typically need to inspect block details and metadata.
    Individual tests can override this by setting their own log level using monkeypatch.
    """
    os.environ["WORKFLOWS_LOG_LEVEL"] = "DEBUG"


# ============================================================================
# Session-level MCP Server Initialization
# ============================================================================

# NOTE: MCP server initialization removed as it's no longer needed.
# The FastMCP server uses lifespan management and doesn't expose global
# executor/registry variables. Tests should create their own instances
# using fixtures like `executor()` and `registry()` below.


# ============================================================================
# Directory Fixtures (Session Scope - Read-Only)
# ============================================================================


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Project root directory.

    Returns:
        Path to the project root directory (parent of tests/)
    """
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def src_dir(project_root: Path) -> Path:
    """Source code directory.

    Returns:
        Path to src/workflows_mcp directory
    """
    return project_root / "src" / "workflows_mcp"


@pytest.fixture(scope="session")
def templates_dir(src_dir: Path) -> Path:
    """Path to templates directory.

    Returns:
        Path to templates directory containing workflow templates
    """
    return src_dir / "templates"


@pytest.fixture(scope="session")
def examples_dir(templates_dir: Path) -> Path:
    """Path to example workflows directory.

    Returns:
        Path to templates/examples directory
    """
    return templates_dir / "examples"


# ============================================================================
# MCP Context Fixtures (Function Scope - For Integration Tests)
# ============================================================================


@pytest.fixture
def mock_context(templates_dir: Path):
    """Create mock MCP context with registry and executor loaded with all workflows.

    This fixture mimics the FastMCP context injection pattern used in production.
    All MCP tools require this context parameter.

    The context includes:
    - WorkflowRegistry loaded with all built-in templates
    - WorkflowExecutor with all workflows pre-loaded

    Use this fixture in integration tests that call MCP tools directly.

    Args:
        templates_dir: Path to built-in templates directory

    Returns:
        Mock context object matching FastMCP's Context[ServerSession, AppContext]

    Example:
        async def test_workflow_execution(mock_context):
            result = await execute_workflow("hello-world", ctx=mock_context)
            assert result["status"] == "success"
    """
    # Ensure EchoBlock is registered for testing
    if "EchoBlock" not in BLOCK_REGISTRY.list_types():
        BLOCK_REGISTRY.register("EchoBlock", EchoBlock)

    # Create registry and load all built-in workflows
    registry = WorkflowRegistry()
    result = registry.load_from_directory(str(templates_dir))

    if not result.is_success:
        pytest.fail(f"Failed to load workflows for mock_context: {result.error}")

    # Create executor and load all workflows from registry
    executor = WorkflowExecutor()
    for workflow in registry.list_all():
        executor.load_workflow(workflow)

    # Create mock context structure matching FastMCP's Context[ServerSession, AppContext]
    mock_ctx = MagicMock()
    mock_ctx.request_context.lifespan_context = AppContext(registry=registry, executor=executor)

    return mock_ctx


# ============================================================================
# Registry Fixtures (Function Scope - Fresh Instances)
# ============================================================================


@pytest.fixture
def registry() -> WorkflowRegistry:
    """Fresh registry for each test.

    Provides a clean WorkflowRegistry instance with no pre-loaded workflows.
    Use this for unit tests that need full control over registry state.

    Returns:
        Empty WorkflowRegistry instance
    """
    return WorkflowRegistry()


@pytest.fixture
def registry_with_examples(examples_dir: Path) -> WorkflowRegistry:
    """Registry pre-loaded with example workflows.

    Loads all workflows from templates/examples/ directory.
    Use this for integration tests that need a realistic workflow library.

    Args:
        examples_dir: Path to examples directory

    Returns:
        WorkflowRegistry loaded with example workflows

    Raises:
        pytest.skip: If example workflows cannot be loaded
    """
    registry = WorkflowRegistry()
    result = registry.load_from_directory(str(examples_dir))
    if not result.is_success:
        pytest.skip(f"Could not load examples: {result.error}")
    return registry


# ============================================================================
# Executor Fixtures (Function Scope - Fresh Instances)
# ============================================================================


@pytest.fixture
def executor() -> WorkflowExecutor:
    """Fresh executor for each test.

    Provides a clean WorkflowExecutor instance with empty context.
    Use this for unit and integration tests requiring isolated execution.

    Returns:
        WorkflowExecutor with empty context
    """
    # Ensure EchoBlock is registered for testing
    if "EchoBlock" not in BLOCK_REGISTRY.list_types():
        BLOCK_REGISTRY.register("EchoBlock", EchoBlock)

    return WorkflowExecutor()


@pytest.fixture
def executor_with_registry(registry_with_examples: WorkflowRegistry) -> WorkflowExecutor:
    """Executor pre-configured with example workflow registry.

    Use this for end-to-end tests that need to execute real workflows.

    Args:
        registry_with_examples: Registry with example workflows loaded

    Returns:
        WorkflowExecutor with registry attached
    """
    # Ensure EchoBlock is registered for testing
    if "EchoBlock" not in BLOCK_REGISTRY.list_types():
        BLOCK_REGISTRY.register("EchoBlock", EchoBlock)

    executor = WorkflowExecutor()
    # Load all workflows from registry
    for name in registry_with_examples.list_workflows():
        workflow = registry_with_examples.get_workflow(name)
        if workflow:
            executor.load_workflow(workflow)
    return executor


# ============================================================================
# Workflow Definition Fixtures (Function Scope)
# ============================================================================


@pytest.fixture
def simple_workflow_def() -> dict[str, Any]:
    """Minimal test workflow with single echo block.

    Use this for basic execution and validation tests.

    Returns:
        Dictionary representing a simple workflow definition
    """
    return {
        "name": "test-simple",
        "description": "Simple test workflow",
        "version": "1.0",
        "blocks": [
            {
                "id": "echo",
                "type": "EchoBlock",
                "inputs": {"message": "Hello World"},
                "depends_on": [],
            }
        ],
    }


@pytest.fixture
def multi_block_workflow_def() -> dict[str, Any]:
    """Test workflow with multiple dependent blocks.

    Use this for testing DAG resolution and variable substitution.

    Returns:
        Dictionary representing a multi-block workflow with dependencies
    """
    return {
        "name": "test-multi",
        "description": "Multi-block test workflow",
        "version": "1.0",
        "blocks": [
            {
                "id": "block1",
                "type": "EchoBlock",
                "inputs": {"message": "First"},
                "depends_on": [],
            },
            {
                "id": "block2",
                "type": "EchoBlock",
                "inputs": {"message": "${block1.echoed}"},
                "depends_on": ["block1"],
            },
            {
                "id": "block3",
                "type": "EchoBlock",
                "inputs": {"message": "${block2.echoed}"},
                "depends_on": ["block2"],
            },
        ],
    }


@pytest.fixture
def sample_workflow_schema() -> WorkflowSchema:
    """Standard test workflow schema for YAML validation.

    Use this for loader and schema validation tests.

    Returns:
        WorkflowSchema instance for testing
    """
    return WorkflowSchema(
        name="test-workflow",
        description="Test workflow description",
        version="1.0",
        tags=["test", "example"],
        blocks=[
            {
                "id": "block1",
                "type": "EchoBlock",
                "inputs": {"message": "Hello"},
            }
        ],
    )


# ============================================================================
# Temporary File Fixtures (Function Scope - Auto Cleanup)
# ============================================================================


@pytest.fixture
def temp_workflow_file(tmp_path: Path) -> Path:
    """Temporary YAML workflow file for testing loaders.

    Creates a simple workflow YAML file in pytest's tmp_path.
    File is automatically cleaned up after test.

    Args:
        tmp_path: pytest's temporary directory fixture

    Returns:
        Path to temporary workflow YAML file
    """
    workflow_file = tmp_path / "test-workflow.yaml"
    workflow_content = """name: test-workflow
description: Test workflow
version: 1.0
tags:
  - test
blocks:
  - id: echo
    type: EchoBlock
    inputs:
      message: Hello from YAML
"""
    workflow_file.write_text(workflow_content)
    return workflow_file


@pytest.fixture
def temp_workflow_dir(tmp_path: Path) -> Path:
    """Temporary directory with multiple workflow YAML files.

    Creates a directory with 3 test workflows for directory loading tests.
    Directory is automatically cleaned up after test.

    Args:
        tmp_path: pytest's temporary directory fixture

    Returns:
        Path to temporary directory containing workflow YAML files
    """
    workflow_dir = tmp_path / "workflows"
    workflow_dir.mkdir()

    # Create workflow 1
    (workflow_dir / "workflow1.yaml").write_text("""name: workflow-one
description: First test workflow
version: "1.0"
blocks:
  - id: echo
    type: EchoBlock
    inputs:
      message: Workflow 1
""")

    # Create workflow 2
    (workflow_dir / "workflow2.yaml").write_text("""name: workflow-two
description: Second test workflow
version: "1.0"
tags:
  - python
blocks:
  - id: echo
    type: EchoBlock
    inputs:
      message: Workflow 2
""")

    # Create workflow 3 with tags
    (workflow_dir / "workflow3.yaml").write_text("""name: workflow-three
description: Third test workflow
version: "1.0"
tags:
  - python
  - test
blocks:
  - id: echo
    type: EchoBlock
    inputs:
      message: Workflow 3
""")

    return workflow_dir


# ============================================================================
# Test Data Fixtures
# ============================================================================


@pytest.fixture
def create_checkpoint():
    """Factory fixture to create test checkpoints.

    Returns:
        Callable that creates CheckpointState with sensible defaults
    """
    import time

    from workflows_mcp.engine.checkpoint import CheckpointState

    def _create(
        checkpoint_id: str = "test_checkpoint",
        workflow_name: str = "test_workflow",
        context: dict[str, Any] | None = None,
        completed_blocks: list[str] | None = None,
    ) -> CheckpointState:
        """Create a test checkpoint with sensible defaults.

        Args:
            checkpoint_id: Unique checkpoint identifier
            workflow_name: Name of the workflow
            context: Execution context (defaults to empty dict)
            completed_blocks: List of completed block IDs (defaults to empty list)

        Returns:
            CheckpointState for testing
        """
        return CheckpointState(
            checkpoint_id=checkpoint_id,
            workflow_name=workflow_name,
            created_at=time.time(),
            runtime_inputs={},
            context=context or {},
            completed_blocks=completed_blocks or [],
            current_wave_index=0,
            execution_waves=[],
            block_definitions={},
            workflow_stack=[],
        )

    return _create


@pytest.fixture
def sample_block_inputs() -> dict[str, Any]:
    """Sample block inputs for testing variable resolution.

    Returns:
        Dictionary of sample block input values
    """
    return {
        "message": "Test message",
        "path": "/tmp/test.txt",
        "count": 42,
        "enabled": True,
    }


@pytest.fixture
def sample_context() -> dict[str, Any]:
    """Sample workflow execution context.

    Returns:
        Dictionary representing a workflow execution context with block outputs
    """
    return {
        "workspace": "/tmp/workspace",
        "project_name": "test-project",
        "version": "1.0.0",
        "block1": {
            "echoed": "Block 1 output",
            "status": "success",
        },
        "block2": {
            "echoed": "Block 2 output",
            "exit_code": 0,
        },
    }
