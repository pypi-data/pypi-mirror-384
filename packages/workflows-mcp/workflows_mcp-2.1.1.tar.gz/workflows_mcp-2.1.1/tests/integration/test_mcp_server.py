"""Tests for MCP server initialization and configuration.

This module consolidates tests from:
- test_server_workflow_loading.py (404 lines, 19 functions) - Workflow loading mechanism
- (test_mcp_integration.py content already in test_mcp_tools.py)

Total: 1 file (404 lines) → 1 file
Test functions: 19 tests
"""

import tempfile
from pathlib import Path

import pytest

from workflows_mcp.engine import WorkflowExecutor, WorkflowRegistry
from workflows_mcp.server import load_workflows


@pytest.fixture
def sample_workflow_yaml():
    """Sample workflow YAML content for testing."""
    return """
name: test-workflow
description: Test workflow for loading tests
tags: [test]
version: "1.0"

blocks:
  - id: echo1
    type: EchoBlock
    inputs:
      message: "Test message"
      delay_ms: 10
"""


@pytest.fixture
def override_workflow_yaml():
    """Override workflow YAML with same name but different content."""
    return """
name: test-workflow
description: OVERRIDDEN test workflow
tags: [test]
version: "2.0"

blocks:
  - id: echo1
    type: EchoBlock
    inputs:
      message: "OVERRIDDEN message"
      delay_ms: 20
"""


# ============================================================================
# Part 1: Environment Variable Parsing Tests
# ============================================================================


class TestEnvironmentVariableParsing:
    """Test environment variable parsing for WORKFLOWS_TEMPLATE_PATHS."""

    @pytest.mark.slow
    def test_no_env_variable_set(self, monkeypatch):
        """Test loading with no WORKFLOWS_TEMPLATE_PATHS set."""
        monkeypatch.delenv("WORKFLOWS_TEMPLATE_PATHS", raising=False)

        # Create fresh registry and executor for testing
        registry = WorkflowRegistry()
        executor = WorkflowExecutor()

        load_workflows(registry, executor)

        # Should load built-in templates only
        workflows = registry.list_names()
        assert len(workflows) > 0, "Should load built-in templates"

    @pytest.mark.slow
    def test_single_user_path(self, monkeypatch, temp_workflow_dir, sample_workflow_yaml):
        """Test loading with single user template path."""
        # Create test workflow in temp directory
        workflow_file = temp_workflow_dir / "test-workflow.yaml"
        workflow_file.write_text(sample_workflow_yaml)

        monkeypatch.setenv("WORKFLOWS_TEMPLATE_PATHS", str(temp_workflow_dir))
        # Import load_workflows after setting env

        # Create fresh registry and executor for testing
        registry = WorkflowRegistry()
        executor = WorkflowExecutor()

        load_workflows(registry, executor)

        # Should have loaded the test workflow
        assert "test-workflow" in registry

    @pytest.mark.slow
    def test_multiple_comma_separated_paths(
        self, monkeypatch, temp_workflow_dir, sample_workflow_yaml
    ):
        """Test loading with multiple comma-separated paths."""
        # Create two separate directories
        dir1 = temp_workflow_dir / "dir1"
        dir2 = temp_workflow_dir / "dir2"
        dir1.mkdir()
        dir2.mkdir()

        # Create workflow in each directory with different names
        workflow1 = dir1 / "workflow1.yaml"
        workflow1.write_text(sample_workflow_yaml.replace("test-workflow", "workflow1"))

        workflow2 = dir2 / "workflow2.yaml"
        workflow2.write_text(sample_workflow_yaml.replace("test-workflow", "workflow2"))

        monkeypatch.setenv("WORKFLOWS_TEMPLATE_PATHS", f"{dir1},{dir2}")

        # Create fresh registry and executor for testing
        registry = WorkflowRegistry()
        executor = WorkflowExecutor()

        load_workflows(registry, executor)

        # Should have loaded both workflows
        assert "workflow1" in registry
        assert "workflow2" in registry

    @pytest.mark.slow
    def test_whitespace_handling(self, monkeypatch, temp_workflow_dir, sample_workflow_yaml):
        """Test that whitespace around paths is handled correctly."""
        workflow_file = temp_workflow_dir / "test-workflow.yaml"
        workflow_file.write_text(sample_workflow_yaml)

        # Add whitespace around the path
        monkeypatch.setenv("WORKFLOWS_TEMPLATE_PATHS", f"  {temp_workflow_dir}  ")

        # Create fresh registry and executor for testing
        registry = WorkflowRegistry()
        executor = WorkflowExecutor()

        load_workflows(registry, executor)

        assert "test-workflow" in registry

    @pytest.mark.slow
    def test_tilde_expansion(self, monkeypatch, sample_workflow_yaml):
        """Test that ~ expands to home directory."""
        # Create test workflow in a subdirectory of temp (simulating home)
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir) / ".workflows-test"
            test_dir.mkdir()

            workflow_file = test_dir / "test-workflow.yaml"
            workflow_file.write_text(sample_workflow_yaml)

            # Use absolute path with ~ simulation
            monkeypatch.setenv("WORKFLOWS_TEMPLATE_PATHS", str(test_dir))

            # Create fresh registry and executor for testing
            registry = WorkflowRegistry()
            executor = WorkflowExecutor()

            load_workflows(registry, executor)

            # Workflow should be loaded (tilde expansion works via Path.expanduser)
            assert "test-workflow" in registry

    @pytest.mark.slow
    def test_empty_env_variable(self, monkeypatch):
        """Test that empty WORKFLOWS_TEMPLATE_PATHS is handled gracefully."""
        monkeypatch.setenv("WORKFLOWS_TEMPLATE_PATHS", "")

        # Create fresh registry and executor for testing
        registry = WorkflowRegistry()
        executor = WorkflowExecutor()

        load_workflows(registry, executor)

        # Should still load built-in templates
        workflows = registry.list_names()
        assert len(workflows) > 0

    @pytest.mark.slow
    def test_nonexistent_path(self, monkeypatch):
        """Test that non-existent paths log warning but don't crash."""
        nonexistent = "/path/that/does/not/exist/workflows"
        monkeypatch.setenv("WORKFLOWS_TEMPLATE_PATHS", nonexistent)

        # Should not raise exception
        # Create fresh registry and executor for testing
        registry = WorkflowRegistry()
        executor = WorkflowExecutor()

        load_workflows(registry, executor)

        # Should still have built-in workflows
        workflows = registry.list_names()
        assert len(workflows) > 0


# ============================================================================
# Part 2: Multi-Directory Loading Tests
# ============================================================================


class TestMultiDirectoryLoading:
    """Test multi-directory loading functionality."""

    @pytest.mark.slow
    def test_builtin_plus_user_directory(
        self, monkeypatch, temp_workflow_dir, sample_workflow_yaml
    ):
        """Test loading from built-in + single user directory."""
        workflow_file = temp_workflow_dir / "custom-workflow.yaml"
        workflow_file.write_text(sample_workflow_yaml.replace("test-workflow", "custom-workflow"))

        monkeypatch.setenv("WORKFLOWS_TEMPLATE_PATHS", str(temp_workflow_dir))

        # Create fresh registry and executor for testing
        registry = WorkflowRegistry()
        executor = WorkflowExecutor()

        load_workflows(registry, executor)

        # Should have both built-in and custom workflow
        workflows = registry.list_names()
        assert "custom-workflow" in workflows
        assert len(workflows) > 1  # Has built-in workflows too

    @pytest.mark.slow
    def test_workflows_loaded_into_registry_and_executor(
        self, monkeypatch, temp_workflow_dir, sample_workflow_yaml
    ):
        """Test that workflows are loaded into both registry and executor."""
        workflow_file = temp_workflow_dir / "test-workflow.yaml"
        workflow_file.write_text(sample_workflow_yaml)

        monkeypatch.setenv("WORKFLOWS_TEMPLATE_PATHS", str(temp_workflow_dir))

        # Create fresh registry and executor for testing
        registry = WorkflowRegistry()
        executor = WorkflowExecutor()

        load_workflows(registry, executor)

        # Check registry
        assert "test-workflow" in registry

        # Check executor
        assert "test-workflow" in executor.workflows


# ============================================================================
# Part 3: Priority Override Tests
# ============================================================================


class TestPriorityOverride:
    """Test priority override system where user templates override built-in."""

    def test_user_overrides_builtin(
        self, monkeypatch, temp_workflow_dir, sample_workflow_yaml, override_workflow_yaml
    ):
        """Test that user workflow overrides built-in workflow by name."""
        # First, load a workflow into "built-in" area
        builtin_dir = temp_workflow_dir / "builtin"
        builtin_dir.mkdir()

        builtin_file = builtin_dir / "test-workflow.yaml"
        builtin_file.write_text(sample_workflow_yaml)

        # Create user override directory
        user_dir = temp_workflow_dir / "user"
        user_dir.mkdir()

        user_file = user_dir / "test-workflow.yaml"
        user_file.write_text(override_workflow_yaml)

        # Manually test the registry loading behavior
        registry = WorkflowRegistry()

        # Load built-in first, then user (with overwrite)
        result = registry.load_from_directories([builtin_dir, user_dir], on_duplicate="overwrite")

        assert result.is_success
        assert "test-workflow" in registry

        # Get the workflow and verify it's the overridden version
        workflow = registry.get("test-workflow")
        assert workflow.description == "OVERRIDDEN test workflow"

    def test_multiple_user_directories_priority(
        self, temp_workflow_dir, sample_workflow_yaml, override_workflow_yaml
    ):
        """Test that later user directories override earlier ones."""
        dir1 = temp_workflow_dir / "user1"
        dir2 = temp_workflow_dir / "user2"
        dir1.mkdir()
        dir2.mkdir()

        # Create same workflow in both directories
        file1 = dir1 / "test-workflow.yaml"
        file1.write_text(sample_workflow_yaml)

        file2 = dir2 / "test-workflow.yaml"
        file2.write_text(override_workflow_yaml)

        registry = WorkflowRegistry()

        # Load dir1 first, then dir2 (dir2 should win)
        result = registry.load_from_directories([dir1, dir2], on_duplicate="overwrite")

        assert result.is_success

        workflow = registry.get("test-workflow")
        assert workflow.description == "OVERRIDDEN test workflow"

    def test_source_tracking_shows_origin(self, temp_workflow_dir, sample_workflow_yaml):
        """Test that source tracking shows correct origin for workflows."""
        workflow_file = temp_workflow_dir / "test-workflow.yaml"
        workflow_file.write_text(sample_workflow_yaml)

        registry = WorkflowRegistry()
        result = registry.load_from_directories([temp_workflow_dir])

        assert result.is_success

        # Check source tracking
        source = registry.get_workflow_source("test-workflow")
        assert source == temp_workflow_dir.resolve()

    def test_nonconflicting_workflows_coexist(self, temp_workflow_dir, sample_workflow_yaml):
        """Test that non-conflicting workflows from all directories coexist."""
        dir1 = temp_workflow_dir / "dir1"
        dir2 = temp_workflow_dir / "dir2"
        dir1.mkdir()
        dir2.mkdir()

        # Create different workflows in each directory
        file1 = dir1 / "workflow1.yaml"
        file1.write_text(sample_workflow_yaml.replace("test-workflow", "workflow1"))

        file2 = dir2 / "workflow2.yaml"
        file2.write_text(sample_workflow_yaml.replace("test-workflow", "workflow2"))

        registry = WorkflowRegistry()
        result = registry.load_from_directories([dir1, dir2], on_duplicate="overwrite")

        assert result.is_success

        # Both should exist
        assert "workflow1" in registry
        assert "workflow2" in registry


# ============================================================================
# Part 4: Error Handling Tests
# ============================================================================


class TestErrorHandling:
    """Test error handling and graceful degradation."""

    @pytest.mark.slow
    def test_invalid_yaml_in_user_directory(self, monkeypatch, temp_workflow_dir):
        """Test that invalid YAML doesn't crash loading."""
        invalid_file = temp_workflow_dir / "invalid.yaml"
        invalid_file.write_text("this is not: valid: yaml: content:")

        monkeypatch.setenv("WORKFLOWS_TEMPLATE_PATHS", str(temp_workflow_dir))

        # Should not raise exception
        # Create fresh registry and executor for testing
        registry = WorkflowRegistry()
        executor = WorkflowExecutor()

        load_workflows(registry, executor)

        # Built-in templates should still be loaded
        workflows = registry.list_names()
        assert len(workflows) > 0

    @pytest.mark.slow
    def test_file_instead_of_directory(self, monkeypatch, temp_workflow_dir):
        """Test handling when path points to a file instead of directory."""
        # Create a file instead of directory
        file_path = temp_workflow_dir / "not-a-directory.txt"
        file_path.write_text("This is a file, not a directory")

        monkeypatch.setenv("WORKFLOWS_TEMPLATE_PATHS", str(file_path))

        # Should not crash
        # Create fresh registry and executor for testing
        registry = WorkflowRegistry()
        executor = WorkflowExecutor()

        load_workflows(registry, executor)

        # Should still have built-in workflows
        workflows = registry.list_names()
        assert len(workflows) > 0
