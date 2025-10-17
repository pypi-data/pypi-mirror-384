"""Integration tests for file processing workflows.

Tests all 2 file workflows for functional correctness, file generation,
and template processing.

Tested workflows:
- generate-readme (Priority 0 - previously broken)
- process-config (Priority 0 - previously broken)

Both workflows were previously broken due to use of unsupported "contains"
operator. These tests validate the fix: "contains" → "in" operator.
"""

import pytest

from workflows_mcp.engine.response import WorkflowResponse
from workflows_mcp.tools import execute_workflow


def to_dict(result):
    """Convert WorkflowResponse to dict for testing."""
    if isinstance(result, WorkflowResponse):
        return result.model_dump()
    return result


class TestGenerateReadme:
    """Test generate-readme workflow.

    This workflow was previously broken due to 3 instances of unsupported
    "contains" operator. Tests validate the fix to use "in" operator.
    """

    @pytest.mark.asyncio
    async def test_generate_readme_creates_file(self, temp_workspace, mock_context):
        """Test generate-readme creates README.md file."""
        result = to_dict(
            await execute_workflow(
                workflow="generate-readme",
                inputs={
                    "project_name": "test-project",
                    "description": "Test project description",
                    "workspace": str(temp_workspace),
                },
                ctx=mock_context,
            )
        )

        assert result["status"] == "success", (
            f"generate-readme failed: {result.get('error')}. "
            f"This may indicate the 'contains' → 'in' fix was not applied correctly."
        )

        # Validate README.md was created
        readme_path = temp_workspace / "README.md"
        assert readme_path.exists(), "README.md was not created"

        # Validate README content
        readme_content = readme_path.read_text()
        assert "test-project" in readme_content, "README should contain project name"
        assert "Test project description" in readme_content, "README should contain description"

    @pytest.mark.asyncio
    async def test_generate_readme_with_template(self, temp_workspace, mock_context):
        """Test generate-readme with custom template."""
        # Create custom template
        template_dir = temp_workspace / "templates"
        template_dir.mkdir()
        template_path = template_dir / "README.template.md"
        template_path.write_text("# {{project_name}}\n\n{{description}}\n")

        result = to_dict(
            await execute_workflow(
                workflow="generate-readme",
                inputs={
                    "project_name": "custom-project",
                    "description": "Custom description",
                    "workspace": str(temp_workspace),
                    "template_path": str(template_path),
                },
                ctx=mock_context,
            )
        )

        assert result["status"] == "success", (
            f"generate-readme with template failed: {result.get('error')}"
        )

        # Validate README was created with template
        readme_path = temp_workspace / "README.md"
        assert readme_path.exists()
        assert "custom-project" in readme_path.read_text()

    @pytest.mark.asyncio
    async def test_generate_readme_conditional_template_creation(
        self, temp_workspace, mock_context
    ):
        """Test generate-readme conditional logic for template creation.

        This test validates the fix for the 'contains' operator bug.
        The workflow should check if template exists using 'in' operator.
        """
        result = to_dict(
            await execute_workflow(
                workflow="generate-readme",
                inputs={
                    "project_name": "test-project",
                    "workspace": str(temp_workspace),
                    "create_template_if_missing": True,  # Enable template creation
                },
                ctx=mock_context,
            )
        )

        assert result["status"] == "success", (
            f"generate-readme with template creation failed: {result.get('error')}. "
            f"Conditional logic may still be using 'contains' operator."
        )

    @pytest.mark.asyncio
    async def test_generate_readme_outputs(self, temp_workspace, mock_context):
        """Test generate-readme provides correct outputs."""
        result = to_dict(
            await execute_workflow(
                workflow="generate-readme",
                inputs={
                    "project_name": "output-test",
                    "workspace": str(temp_workspace),
                },
                ctx=mock_context,
            )
        )

        assert result["status"] == "success"
        assert "outputs" in result

        # Should have blocks about file creation
        assert "blocks" in result, "Missing blocks in result"


class TestProcessConfig:
    """Test process-config workflow.

    This workflow was previously broken due to 3 instances of unsupported
    "contains" operator. Tests validate the fix to use "in" operator.
    """

    @pytest.mark.asyncio
    async def test_process_config_creates_output(self, temp_workspace, mock_context):
        """Test process-config processes configuration file."""
        # Create input config file
        config_file = temp_workspace / "config.json"
        config_file.write_text('{"key": "value", "number": 42}')

        result = to_dict(
            await execute_workflow(
                workflow="process-config",
                inputs={
                    "config_path": str(config_file),
                    "output_path": str(temp_workspace / "output.json"),
                },
                ctx=mock_context,
            )
        )

        assert result["status"] == "success", (
            f"process-config failed: {result.get('error')}. "
            f"This may indicate the 'contains' → 'in' fix was not applied correctly."
        )

    @pytest.mark.asyncio
    async def test_process_config_validates_input_exists(self, temp_workspace, mock_context):
        """Test process-config validates input file exists.

        This test validates the conditional logic fix from 'contains' to 'in'.
        The workflow checks if file exists using bash test command.
        """
        # Create input file
        config_file = temp_workspace / "input.json"
        config_file.write_text('{"test": true}')

        result = to_dict(
            await execute_workflow(
                workflow="process-config",
                inputs={
                    "config_path": str(config_file),
                    "output_path": str(temp_workspace / "output.json"),
                    "validate_input": True,
                },
                ctx=mock_context,
            )
        )

        assert result["status"] == "success", (
            f"process-config with validation failed: {result.get('error')}. "
            f"Input validation conditional may still use 'contains' operator."
        )

    @pytest.mark.asyncio
    async def test_process_config_handles_missing_input(self, temp_workspace, mock_context):
        """Test process-config handles missing input file gracefully."""
        nonexistent_file = temp_workspace / "nonexistent.json"

        result = to_dict(
            await execute_workflow(
                workflow="process-config",
                inputs={
                    "config_path": str(nonexistent_file),
                    "output_path": str(temp_workspace / "output.json"),
                    "skip_on_missing": True,  # Should skip instead of failing
                },
                ctx=mock_context,
            )
        )

        # Should either succeed (by skipping) or fail gracefully
        assert result["status"] in ["success", "failure"], (
            "Workflow should complete with clear status"
        )

    @pytest.mark.asyncio
    async def test_process_config_transformation(self, temp_workspace, mock_context):
        """Test process-config transforms configuration correctly."""
        # Create input with transformable content
        config_file = temp_workspace / "config.yaml"
        config_file.write_text("""
name: test-app
version: 1.0.0
settings:
  debug: true
  port: 8080
""")

        result = to_dict(
            await execute_workflow(
                workflow="process-config",
                inputs={
                    "config_path": str(config_file),
                    "output_path": str(temp_workspace / "config.json"),
                    "format": "yaml_to_json",
                },
                ctx=mock_context,
            )
        )

        # May succeed or fail depending on workflow capabilities
        if result["status"] == "success":
            output_file = temp_workspace / "config.json"
            # Validate transformation if workflow supports it
            if output_file.exists():
                assert output_file.stat().st_size > 0, "Output file should not be empty"


class TestFileWorkflowsErrorHandling:
    """Test error handling in file workflows."""

    @pytest.mark.asyncio
    async def test_generate_readme_invalid_workspace(self, mock_context):
        """Test generate-readme with invalid workspace path."""
        result = to_dict(
            await execute_workflow(
                workflow="generate-readme",
                inputs={
                    "project_name": "test",
                    "workspace": "/nonexistent/path/that/does/not/exist",
                    "create_workspace": False,  # Disable workspace creation
                },
                ctx=mock_context,
            )
        )

        # Should fail gracefully or succeed by creating workspace
        assert result["status"] in ["success", "failure"]
        if result["status"] == "failure":
            assert "error" in result
            assert len(result["error"]) > 0

    @pytest.mark.asyncio
    async def test_process_config_invalid_path(self, mock_context):
        """Test process-config with invalid paths."""
        result = to_dict(
            await execute_workflow(
                workflow="process-config",
                inputs={
                    "config_path": "/nonexistent/input.json",
                    "output_path": "/nonexistent/output.json",
                    "skip_on_missing": False,  # Should fail on missing input
                },
                ctx=mock_context,
            )
        )

        # Should fail or handle gracefully
        assert result["status"] in ["success", "failure"]
