"""
Comprehensive test suite for library workflows.

Tests all 10 library workflows to ensure they:
- Load and validate successfully
- Demonstrate Phase 2 features (variables, conditionals, composition, file ops)
"""

from pathlib import Path

import pytest

from workflows_mcp.engine.loader import load_workflow_from_file

# Library workflow paths
LIBRARY_DIR = Path(__file__).parent.parent.parent / "src" / "workflows_mcp" / "templates"

PYTHON_WORKFLOWS = [
    "python/setup-python-env.yaml",
    "python/run-pytest.yaml",
    "python/lint-python.yaml",
]

GIT_WORKFLOWS = [
    "git/create-feature-branch.yaml",
    "git/commit-and-push.yaml",
]

CI_WORKFLOWS = [
    "ci/python-ci-pipeline.yaml",
    "ci/conditional-deploy.yaml",
]

FILE_WORKFLOWS = [
    "files/generate-readme.yaml",
    "files/process-config.yaml",
]

EXAMPLE_WORKFLOWS = [
    "examples/multi-level-composition.yaml",
    "examples/parallel-processing.yaml",
]

ALL_LIBRARY_WORKFLOWS = (
    PYTHON_WORKFLOWS + GIT_WORKFLOWS + CI_WORKFLOWS + FILE_WORKFLOWS + EXAMPLE_WORKFLOWS
)


def load_library_workflow(workflow_path: str):
    """Helper to load a library workflow and handle Result."""
    result = load_workflow_from_file(str(LIBRARY_DIR / workflow_path))
    assert result.is_success, f"Failed to load {workflow_path}: {result.error}"
    return result.value


class TestLibraryWorkflowLoading:
    """Test that all library workflows load and validate successfully."""

    @pytest.mark.parametrize("workflow_path", ALL_LIBRARY_WORKFLOWS)
    def test_load_library_workflow(self, workflow_path):
        """Test loading individual library workflow."""
        full_path = LIBRARY_DIR / workflow_path
        assert full_path.exists(), f"Workflow file not found: {full_path}"

        # Load workflow
        result = load_workflow_from_file(str(full_path))
        assert result.is_success, f"Failed to load workflow: {result.error}"
        workflow = result.value

        # Validate structure
        assert workflow.name is not None
        assert workflow.description is not None
        assert len(workflow.blocks) > 0

    def test_all_library_workflows_exist(self):
        """Verify all 10 library workflow files exist."""
        for workflow_path in ALL_LIBRARY_WORKFLOWS:
            full_path = LIBRARY_DIR / workflow_path
            assert full_path.exists(), f"Workflow file not found: {full_path}"


class TestPythonWorkflows:
    """Test Python category workflows."""

    def test_setup_python_env_workflow(self):
        """Test setup-python-env workflow loads correctly."""
        workflow = load_library_workflow("python/setup-python-env.yaml")
        assert workflow.name == "setup-python-env"
        assert "python_version" in workflow.inputs
        assert "project_path" in workflow.inputs

    def test_run_pytest_workflow(self):
        """Test run-pytest workflow loads correctly."""
        workflow = load_library_workflow("python/run-pytest.yaml")
        assert workflow.name == "run-pytest"
        assert "test_path" in workflow.inputs
        assert "coverage_threshold" in workflow.inputs

    def test_lint_python_workflow(self):
        """Test lint-python workflow loads correctly."""
        workflow = load_library_workflow("python/lint-python.yaml")
        assert workflow.name == "lint-python"
        assert "src_path" in workflow.inputs


class TestGitWorkflows:
    """Test Git category workflows."""

    def test_create_feature_branch_workflow(self):
        """Test create-feature-branch workflow loads correctly."""
        workflow = load_library_workflow("git/create-feature-branch.yaml")
        assert workflow.name == "create-feature-branch"
        assert "branch_name" in workflow.inputs
        assert "base_branch" in workflow.inputs

    def test_commit_and_push_workflow(self):
        """Test commit-and-push workflow loads correctly."""
        workflow = load_library_workflow("git/commit-and-push.yaml")
        assert workflow.name == "commit-and-push"
        assert "commit_message" in workflow.inputs
        assert "add_files" in workflow.inputs


class TestCIWorkflows:
    """Test CI/CD category workflows."""

    def test_python_ci_pipeline_workflow(self):
        """Test python-ci-pipeline workflow loads correctly."""
        workflow = load_library_workflow("ci/python-ci-pipeline.yaml")
        assert workflow.name == "python-ci-pipeline"
        assert "project_path" in workflow.inputs

    def test_conditional_deploy_workflow(self):
        """Test conditional-deploy workflow loads correctly."""
        workflow = load_library_workflow("ci/conditional-deploy.yaml")
        assert workflow.name == "conditional-deploy"
        assert "environment" in workflow.inputs


class TestFileWorkflows:
    """Test file processing workflows."""

    def test_generate_readme_workflow(self):
        """Test generate-readme workflow loads correctly."""
        workflow = load_library_workflow("files/generate-readme.yaml")
        assert workflow.name == "generate-readme"
        assert "project_name" in workflow.inputs
        assert "template_path" in workflow.inputs

    def test_process_config_workflow(self):
        """Test process-config workflow loads correctly."""
        workflow = load_library_workflow("files/process-config.yaml")
        assert workflow.name == "process-config"
        assert "config_path" in workflow.inputs
        assert "environment" in workflow.inputs


class TestExampleWorkflows:
    """Test advanced example workflows."""

    def test_multi_level_composition_workflow(self):
        """Test multi-level-composition workflow loads correctly."""
        # May have some blocks that reference other workflows
        workflow = load_library_workflow("examples/multi-level-composition.yaml")
        assert workflow.name == "multi-level-composition"
        assert "project_name" in workflow.inputs

    def test_parallel_processing_workflow(self):
        """Test parallel-processing workflow loads correctly."""
        workflow = load_library_workflow("examples/parallel-processing.yaml")
        assert workflow.name == "parallel-processing"
        assert "project_path" in workflow.inputs


class TestPhase2Features:
    """Test that library workflows demonstrate all Phase 2 features."""

    def test_workflows_use_variables(self):
        """Verify workflows use variable substitution (${})."""
        workflow = load_library_workflow("python/setup-python-env.yaml")

        # Check blocks use ${var} syntax in inputs
        has_variable_refs = False
        for block in workflow.blocks:
            if block.get("inputs"):
                for value in block["inputs"].values():
                    if isinstance(value, str) and "${" in value:
                        has_variable_refs = True
                        break
                if has_variable_refs:
                    break

        assert has_variable_refs, "Workflows should use variable references"

    def test_workflows_use_conditionals(self):
        """Verify workflows use conditional execution."""
        workflow = load_library_workflow("ci/conditional-deploy.yaml")

        # Check blocks have conditions
        conditional_blocks = [block for block in workflow.blocks if block.get("condition")]
        assert len(conditional_blocks) > 0, "Workflows should have conditional blocks"

    def test_workflows_use_composition(self):
        """Verify workflows use ExecuteWorkflow for composition."""
        workflow = load_library_workflow("ci/python-ci-pipeline.yaml")

        # Check for ExecuteWorkflow blocks
        execute_workflow_blocks = [
            block for block in workflow.blocks if block.get("type") == "ExecuteWorkflow"
        ]
        assert len(execute_workflow_blocks) >= 2, "Pipeline should compose multiple workflows"

    def test_workflows_use_file_operations(self):
        """Verify workflows use file operation blocks."""
        workflow = load_library_workflow("files/generate-readme.yaml")

        # Check for file operation blocks
        block_types = [block.get("type") for block in workflow.blocks]
        has_file_ops = "ReadFile" in block_types or "CreateFile" in block_types
        assert has_file_ops, "Workflows should use file operations"

    def test_workflows_use_bash_commands(self):
        """Verify workflows use Shell blocks."""
        workflow = load_library_workflow("python/run-pytest.yaml")

        # Check for Shell blocks
        bash_blocks = [block for block in workflow.blocks if block.get("type") == "Shell"]
        assert len(bash_blocks) > 0, "Workflows should use Shell blocks"


class TestLibraryDocumentation:
    """Test library documentation."""

    def test_readme_exists(self):
        """Verify library README exists."""
        readme_path = LIBRARY_DIR / "README.md"
        assert readme_path.exists()

    def test_all_workflows_documented(self):
        """Verify README documents workflow categories and structure."""
        readme_path = LIBRARY_DIR / "README.md"
        readme_content = readme_path.read_text()

        # Check that key categories are documented
        required_categories = [
            "python/",
            "git/",
            "examples/",
            "Directory Structure",
            "YAML Workflow Format",
            "Category Organization",
        ]

        for category in required_categories:
            assert category in readme_content, f"Category {category} not documented in README"


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
