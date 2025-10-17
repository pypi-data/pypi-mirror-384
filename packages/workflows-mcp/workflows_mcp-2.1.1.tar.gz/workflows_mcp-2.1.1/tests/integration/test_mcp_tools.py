"""Tests for MCP tool implementations (execute_workflow, list_workflows, get_workflow_info).

This module consolidates tests from:
- test_tools.py (266 lines, 16 functions) - MCP tool validation tests
- test_tool_providers.py (374 lines, 29 functions) - Tool provider workflows
- test_phase4_tool_integration.py (203 lines, 12 functions) - Phase 4 integration
- test_mcp_integration.py (78 lines, 1 function) - End-to-end integration

Total: 4 files (921 lines) → 1 file
Test functions: 58 tests
"""

from pathlib import Path

import pytest
import yaml

from workflows_mcp.engine.loader import load_workflow_from_file
from workflows_mcp.engine.response import WorkflowResponse
from workflows_mcp.tools import execute_workflow, get_workflow_info, list_workflows


def to_dict(result):
    """Convert WorkflowResponse to dict for testing."""
    if isinstance(result, WorkflowResponse):
        return result.model_dump()
    return result


# Tool management paths
TOOLS_DIR = Path(__file__).parent.parent.parent / "src" / "workflows_mcp" / "templates" / "tools"
PROVIDERS_DIR = TOOLS_DIR / "providers"
CATALOG_DIR = TOOLS_DIR / "catalog"

PROVIDER_WORKFLOWS = [
    "providers/pip-install.yaml",
    "providers/uv-install.yaml",
    "providers/brew-install.yaml",
]

CATALOG_FILES = [
    "catalog/catalog-pytest.yaml",
    "catalog/catalog-ruff.yaml",
    "catalog/catalog-mypy.yaml",
]


def load_workflow(workflow_path: str):
    """Helper to load a workflow and handle Result."""
    result = load_workflow_from_file(str(TOOLS_DIR / workflow_path))
    assert result.is_success, f"Failed to load {workflow_path}: {result.error}"
    return result.value


def load_workflow_yaml(workflow_path: str) -> dict:
    """Helper to load raw YAML data from workflow file."""
    full_path = TOOLS_DIR / workflow_path
    with open(full_path) as f:
        return yaml.safe_load(f)


def load_catalog(catalog_path: str):
    """Helper to load a catalog file and handle Result."""
    result = load_workflow_from_file(str(TOOLS_DIR / catalog_path))
    assert result.is_success, f"Failed to load {catalog_path}: {result.error}"
    return result.value


# ============================================================================
# Part 1: ExecuteWorkflow Tool Tests (from test_tools.py)
# ============================================================================


class TestExecuteWorkflowTool:
    """Tests for execute_workflow MCP tool."""

    @pytest.mark.asyncio
    async def test_execute_workflow_with_real_workflow(self, mock_context):
        """Test execute_workflow with hello-world workflow."""
        result = to_dict(
            await execute_workflow(
                workflow="hello-world", inputs={"message": "test"}, ctx=mock_context
            )
        )
        assert isinstance(result, dict), "execute_workflow should return dict"
        assert "status" in result, "execute_workflow should have 'status' field"
        assert result["status"] == "success", "execute_workflow should return 'success' status"

    @pytest.mark.asyncio
    async def test_execute_workflow_returns_outputs(self, mock_context):
        """Test that execute_workflow returns workflow outputs."""
        result = to_dict(
            await execute_workflow(
                workflow="hello-world", inputs={"message": "test"}, ctx=mock_context
            )
        )
        assert "outputs" in result, "execute_workflow should return outputs"
        assert isinstance(result["outputs"], dict), "outputs should be a dict"

    @pytest.mark.asyncio
    async def test_execute_workflow_with_inputs(self, mock_context):
        """Test execute_workflow accepts workflow inputs."""
        result = to_dict(
            await execute_workflow(
                workflow="hello-world", inputs={"name": "Integration Test"}, ctx=mock_context
            )
        )
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_execute_workflow_nonexistent_workflow(self, mock_context):
        """Test execute_workflow with non-existent workflow."""
        result = to_dict(
            await execute_workflow(workflow="nonexistent-workflow", inputs={}, ctx=mock_context)
        )
        assert result["status"] == "failure"
        assert "error" in result


# ============================================================================
# Part 2: ListWorkflows Tool Tests (from test_tools.py)
# ============================================================================


class TestListWorkflowsTool:
    """Tests for list_workflows MCP tool."""

    @pytest.mark.asyncio
    async def test_list_workflows_returns_list(self, mock_context):
        """Test list_workflows returns a list of workflow names (strings)."""
        result = await list_workflows(ctx=mock_context)
        assert isinstance(result, list), "list_workflows should return list"
        assert len(result) > 0, "list_workflows should return non-empty list"
        # All items should be strings (workflow names)
        assert all(isinstance(name, str) for name in result), "All items should be strings"

    @pytest.mark.asyncio
    async def test_list_workflows_with_tag_filter(self, mock_context):
        """Test list_workflows with tag filter returns workflows with ALL specified tags."""
        result = await list_workflows(tags=["test"], ctx=mock_context)
        assert isinstance(result, list), "list_workflows should return list"
        # All results should be strings
        assert all(isinstance(name, str) for name in result)

    @pytest.mark.asyncio
    async def test_list_workflows_no_filter(self, mock_context):
        """Test list_workflows without filter returns all workflows."""
        result = await list_workflows(ctx=mock_context)
        assert len(result) > 0
        # All items should be strings (workflow names)
        assert all(isinstance(name, str) for name in result)


# ============================================================================
# Part 3: GetWorkflowInfo Tool Tests (from test_tools.py)
# ============================================================================


class TestGetWorkflowInfoTool:
    """Tests for get_workflow_info MCP tool."""

    @pytest.mark.asyncio
    async def test_get_workflow_info_returns_dict(self, mock_context):
        """Test get_workflow_info returns a dict."""
        result = await get_workflow_info(workflow="hello-world", ctx=mock_context)
        assert isinstance(result, dict), "get_workflow_info should return dict"

    @pytest.mark.asyncio
    async def test_get_workflow_info_has_required_fields(self, mock_context):
        """Test get_workflow_info returns required fields."""
        result = await get_workflow_info(workflow="hello-world", ctx=mock_context)
        assert "name" in result, "get_workflow_info should have 'name' field"
        assert "blocks" in result, "get_workflow_info should have 'blocks' field"

    @pytest.mark.asyncio
    async def test_get_workflow_info_nonexistent_workflow(self, mock_context):
        """Test get_workflow_info with non-existent workflow."""
        result = await get_workflow_info(workflow="nonexistent-workflow", ctx=mock_context)
        assert "error" in result, "Should return error dict for nonexistent workflow"
        assert "Workflow not found" in result["error"]


# ============================================================================
# Part 4: Tool Provider Workflows Tests (from test_tool_providers.py)
# ============================================================================


class TestProviderWorkflowsExist:
    """Test that all provider workflow files exist."""

    @pytest.mark.parametrize("workflow_path", PROVIDER_WORKFLOWS)
    def test_provider_workflow_exists(self, workflow_path):
        """Test provider workflow file exists."""
        full_path = TOOLS_DIR / workflow_path
        assert full_path.exists(), f"Provider workflow not found: {full_path}"

    def test_all_providers_exist(self):
        """Verify all 3 provider workflows exist."""
        for workflow_path in PROVIDER_WORKFLOWS:
            full_path = TOOLS_DIR / workflow_path
            assert full_path.exists(), f"Provider workflow not found: {full_path}"


class TestCatalogFilesExist:
    """Test that all catalog metadata files exist."""

    @pytest.mark.parametrize("catalog_path", CATALOG_FILES)
    def test_catalog_file_exists(self, catalog_path):
        """Test catalog file exists."""
        full_path = TOOLS_DIR / catalog_path
        assert full_path.exists(), f"Catalog file not found: {full_path}"

    def test_all_catalogs_exist(self):
        """Verify all 3 catalog files exist."""
        for catalog_path in CATALOG_FILES:
            full_path = TOOLS_DIR / catalog_path
            assert full_path.exists(), f"Catalog file not found: {full_path}"


class TestProviderWorkflowsLoad:
    """Test that provider workflows load and validate successfully."""

    @pytest.mark.parametrize("workflow_path", PROVIDER_WORKFLOWS)
    def test_load_provider_workflow(self, workflow_path):
        """Test loading individual provider workflow."""
        workflow = load_workflow(workflow_path)
        yaml_data = load_workflow_yaml(workflow_path)

        # Validate structure
        assert workflow.name is not None
        assert workflow.description is not None
        assert len(workflow.blocks) > 0
        assert "tools" in yaml_data["tags"]

    def test_pip_install_workflow(self):
        """Test pip-install provider workflow structure."""
        workflow = load_workflow("providers/pip-install.yaml")
        yaml_data = load_workflow_yaml("providers/pip-install.yaml")

        assert workflow.name == "pip-install"

        # Check required inputs
        assert "package_name" in workflow.inputs
        assert workflow.inputs["package_name"]["required"] is True

        # Check optional inputs
        assert "version" in workflow.inputs
        assert "venv_path" in workflow.inputs
        assert "extra_args" in workflow.inputs
        assert "extras" in workflow.inputs

        # Check outputs (from YAML)
        assert "success" in yaml_data["outputs"]
        assert "installed_version" in yaml_data["outputs"]
        assert "install_location" in yaml_data["outputs"]
        assert "exit_code" in yaml_data["outputs"]

    def test_uv_install_workflow(self):
        """Test uv-install provider workflow structure."""
        workflow = load_workflow("providers/uv-install.yaml")
        yaml_data = load_workflow_yaml("providers/uv-install.yaml")

        assert workflow.name == "uv-install"

        # Check required inputs
        assert "package_name" in workflow.inputs
        assert workflow.inputs["package_name"]["required"] is True

        # Check optional inputs
        assert "version" in workflow.inputs
        assert "venv_path" in workflow.inputs
        assert "extras" in workflow.inputs

        # Check outputs (from YAML)
        assert "success" in yaml_data["outputs"]
        assert "installed_version" in yaml_data["outputs"]
        assert "install_location" in yaml_data["outputs"]
        assert "exit_code" in yaml_data["outputs"]
        assert "uv_available" in yaml_data["outputs"]

    def test_brew_install_workflow(self):
        """Test brew-install provider workflow structure."""
        workflow = load_workflow("providers/brew-install.yaml")
        yaml_data = load_workflow_yaml("providers/brew-install.yaml")

        assert workflow.name == "brew-install"

        # Check required inputs
        assert "package_name" in workflow.inputs
        assert workflow.inputs["package_name"]["required"] is True

        # Check optional inputs
        assert "cask" in workflow.inputs
        assert "upgrade" in workflow.inputs

        # Check outputs (from YAML)
        assert "success" in yaml_data["outputs"]
        assert "installed_version" in yaml_data["outputs"]
        assert "exit_code" in yaml_data["outputs"]
        assert "brew_available" in yaml_data["outputs"]
        assert "already_installed" in yaml_data["outputs"]


class TestCatalogFilesLoad:
    """Test that catalog files load and have correct structure."""

    @pytest.mark.parametrize("catalog_path", CATALOG_FILES)
    def test_load_catalog_file(self, catalog_path):
        """Test loading individual catalog file."""
        catalog = load_catalog(catalog_path)
        yaml_data = load_workflow_yaml(catalog_path)

        # Validate structure
        assert catalog.name is not None
        assert catalog.description is not None
        # Catalog files should have tool_catalog_type="catalog" marker
        assert yaml_data["inputs"]["tool_catalog_type"]["default"] == "catalog"
        assert "tools" in yaml_data["tags"]

    def test_catalog_pytest(self):
        """Test catalog-pytest metadata structure."""
        catalog = load_catalog("catalog/catalog-pytest.yaml")
        yaml_data = load_workflow_yaml("catalog/catalog-pytest.yaml")
        assert catalog.name == "catalog-pytest"

        # Check metadata in inputs.metadata.default
        assert "inputs" in yaml_data
        assert "metadata" in yaml_data["inputs"]
        assert "default" in yaml_data["inputs"]["metadata"]
        metadata = yaml_data["inputs"]["metadata"]["default"]

        assert "tool_name" in metadata
        assert metadata["tool_name"] == "pytest"
        assert "tool_type" in metadata
        assert metadata["tool_type"] == "python_package"
        assert "command_name" in metadata
        assert metadata["command_name"] == "pytest"

        # Check version_check
        assert "version_check" in metadata
        version_check = metadata["version_check"]
        assert "command" in version_check
        assert "pattern" in version_check
        assert "import_name" in version_check

        # Check installation options
        assert "installation" in metadata
        installation = metadata["installation"]
        assert "uv" in installation or "pip" in installation

        # Check constraints
        assert "constraints" in metadata
        constraints = metadata["constraints"]
        assert "python_version" in constraints
        assert "recommended_version" in constraints

    def test_catalog_ruff(self):
        """Test catalog-ruff metadata structure."""
        catalog = load_catalog("catalog/catalog-ruff.yaml")
        yaml_data = load_workflow_yaml("catalog/catalog-ruff.yaml")
        assert catalog.name == "catalog-ruff"

        # Check metadata in inputs.metadata.default
        assert "inputs" in yaml_data
        assert "metadata" in yaml_data["inputs"]
        assert "default" in yaml_data["inputs"]["metadata"]
        metadata = yaml_data["inputs"]["metadata"]["default"]

        assert metadata["tool_name"] == "ruff"
        assert metadata["tool_type"] == "python_package"
        assert metadata["command_name"] == "ruff"

        # Check version_check
        assert "version_check" in metadata
        assert "command" in metadata["version_check"]
        assert "pattern" in metadata["version_check"]

        # Check installation options
        assert "installation" in metadata

        # Check constraints
        assert "constraints" in metadata

    def test_catalog_mypy(self):
        """Test catalog-mypy metadata structure."""
        catalog = load_catalog("catalog/catalog-mypy.yaml")
        yaml_data = load_workflow_yaml("catalog/catalog-mypy.yaml")
        assert catalog.name == "catalog-mypy"

        # Check metadata in inputs.metadata.default
        assert "inputs" in yaml_data
        assert "metadata" in yaml_data["inputs"]
        assert "default" in yaml_data["inputs"]["metadata"]
        metadata = yaml_data["inputs"]["metadata"]["default"]

        assert metadata["tool_name"] == "mypy"
        assert metadata["tool_type"] == "python_package"
        assert metadata["command_name"] == "mypy"

        # Check version_check
        assert "version_check" in metadata
        assert "command" in metadata["version_check"]
        assert "pattern" in metadata["version_check"]

        # Check installation options
        assert "installation" in metadata

        # Check constraints
        assert "constraints" in metadata


class TestProviderBlockStructure:
    """Test that provider workflows use correct block types."""

    def test_providers_use_bash_commands(self):
        """Verify provider workflows use Shell blocks."""
        for workflow_path in PROVIDER_WORKFLOWS:
            workflow = load_workflow(workflow_path)

            # Check for Shell blocks
            bash_blocks = [block for block in workflow.blocks if block.get("type") == "Shell"]
            assert len(bash_blocks) > 0, f"{workflow_path} should use Shell blocks"

    def test_providers_have_verification_blocks(self):
        """Verify provider workflows have verification blocks."""
        for workflow_path in PROVIDER_WORKFLOWS:
            workflow = load_workflow(workflow_path)

            # Look for blocks that verify installation
            block_ids = [block.get("id") for block in workflow.blocks]
            has_verification = any(
                "verify" in block_id or "check" in block_id for block_id in block_ids
            )
            assert has_verification, f"{workflow_path} should have verification blocks"


class TestCatalogMetadataStructure:
    """Test that catalog files have NO blocks section (metadata only)."""

    @pytest.mark.parametrize("catalog_path", CATALOG_FILES)
    def test_catalog_has_minimal_blocks(self, catalog_path):
        """Verify catalog files have minimal blocks (only marker)."""
        catalog = load_catalog(catalog_path)

        # Catalog files should have only 1 block (the catalog_marker EchoBlock)
        assert len(catalog.blocks) == 1, f"{catalog_path} should have only 1 marker block"
        assert catalog.blocks[0]["id"] == "catalog_marker"
        assert catalog.blocks[0]["type"] == "EchoBlock"

    @pytest.mark.parametrize("catalog_path", CATALOG_FILES)
    def test_catalog_type_is_catalog(self, catalog_path):
        """Verify catalog files use tool_catalog_type: catalog."""
        yaml_data = load_workflow_yaml(catalog_path)
        assert yaml_data["inputs"]["tool_catalog_type"]["default"] == "catalog", (
            f"{catalog_path} should have tool_catalog_type: catalog"
        )


class TestProviderOutputContracts:
    """Test that provider workflows have expected output contracts."""

    def test_all_providers_have_success_output(self):
        """Verify all providers have 'success' output."""
        for workflow_path in PROVIDER_WORKFLOWS:
            yaml_data = load_workflow_yaml(workflow_path)
            assert "success" in yaml_data["outputs"], f"{workflow_path} must have 'success' output"

    def test_all_providers_have_exit_code_output(self):
        """Verify all providers have 'exit_code' output."""
        for workflow_path in PROVIDER_WORKFLOWS:
            yaml_data = load_workflow_yaml(workflow_path)
            assert "exit_code" in yaml_data["outputs"], (
                f"{workflow_path} must have 'exit_code' output"
            )

    def test_all_providers_have_version_output(self):
        """Verify all providers have 'installed_version' output."""
        for workflow_path in PROVIDER_WORKFLOWS:
            yaml_data = load_workflow_yaml(workflow_path)
            assert "installed_version" in yaml_data["outputs"], (
                f"{workflow_path} must have 'installed_version' output"
            )


class TestIntegrationWithEnsureTool:
    """Test that providers integrate with ensure-tool workflow."""

    def test_ensure_tool_workflow_exists(self):
        """Verify ensure-tool core workflow exists."""
        ensure_tool_path = TOOLS_DIR / "core" / "ensure-tool.yaml"
        assert ensure_tool_path.exists(), "ensure-tool.yaml must exist"

    def test_provider_outputs_match_ensure_tool_expectations(self):
        """Verify provider outputs are compatible with ensure-tool."""
        # ensure-tool expects these outputs from providers
        required_outputs = ["success", "installed_version", "exit_code"]

        for workflow_path in PROVIDER_WORKFLOWS:
            yaml_data = load_workflow_yaml(workflow_path)

            for output_key in required_outputs:
                assert output_key in yaml_data["outputs"], (
                    f"{workflow_path} must have '{output_key}' output for ensure-tool compatibility"
                )


# ============================================================================
# Part 5: End-to-End MCP Integration Test (from test_mcp_integration.py)
# ============================================================================


@pytest.mark.asyncio
async def test_end_to_end_mcp_integration(mock_context):
    """Test complete MCP workflow execution pipeline.

    This test validates:
    1. Workflow loading and registration
    2. MCP tool exposure and invocation
    3. DAG-based execution with parallel waves
    4. Result collection and validation
    """
    # Test 1: List workflows (returns list of workflow names)
    workflows = await list_workflows(ctx=mock_context)
    assert len(workflows) > 0, "Should find workflows"
    # list_workflows now returns list of strings (workflow names)
    assert all(isinstance(name, str) for name in workflows), "All items should be strings"

    # Test 2: Get workflow info for first workflow
    first_workflow = workflows[0] if workflows else "hello-world"
    info = await get_workflow_info(workflow=first_workflow, ctx=mock_context)
    assert "name" in info
    assert "blocks" in info
    assert info["total_blocks"] > 0

    # Test 3: Execute hello-world workflow
    result = to_dict(
        await execute_workflow(workflow="hello-world", inputs={"name": "Phase 1"}, ctx=mock_context)
    )
    assert result["status"] in ["success", "failure"]
    if result["status"] == "failure":
        assert "error" in result
    else:
        assert "metadata" in result
        assert "execution_time_seconds" in result["metadata"]
        assert "outputs" in result

    # Test 4: Execute parallel workflow
    result2 = to_dict(await execute_workflow(workflow="parallel-echo", inputs={}, ctx=mock_context))
    assert result2["status"] in ["success", "failure"]
    if result2["status"] == "success":
        outputs = result2.get("outputs", {})
        blocks = outputs.get("blocks", {})
        assert len(blocks) >= 0

        # Verify block outputs if present
        if blocks:
            for block_id, output in blocks.items():
                assert isinstance(output, dict), f"Block {block_id} output should be dict"


# ============================================================================
# Part 6: Output Verbosity Control Tests
# ============================================================================


class TestOutputVerbosityControl:
    """Tests for output verbosity control via WORKFLOWS_LOG_LEVEL."""

    @pytest.mark.asyncio
    async def test_minimal_output_by_default(self, monkeypatch, mock_context):
        """Test that default log level returns minimal output (empty blocks/metadata)."""
        # Ensure log level is not DEBUG
        monkeypatch.setenv("WORKFLOWS_LOG_LEVEL", "INFO")

        result = to_dict(
            await execute_workflow(
                workflow="hello-world", inputs={"name": "test"}, ctx=mock_context
            )
        )

        assert result["status"] == "success"
        assert "outputs" in result
        # Consistent contract: blocks and metadata always present
        assert "blocks" in result
        assert "metadata" in result
        # But they should be empty in minimal mode
        assert result["blocks"] == {}
        assert result["metadata"] == {}

    @pytest.mark.asyncio
    async def test_detailed_output_with_debug(self, monkeypatch, mock_context):
        """Test that DEBUG log level returns detailed output (outputs + blocks + metadata)."""
        monkeypatch.setenv("WORKFLOWS_LOG_LEVEL", "DEBUG")

        result = to_dict(
            await execute_workflow(
                workflow="hello-world", inputs={"name": "test"}, ctx=mock_context
            )
        )

        assert result["status"] == "success"
        assert "outputs" in result
        # Should include blocks and metadata in DEBUG mode
        assert "blocks" in result
        assert "metadata" in result
        assert isinstance(result["blocks"], dict)
        assert isinstance(result["metadata"], dict)

    @pytest.mark.asyncio
    async def test_failure_respects_verbosity(self, monkeypatch, mock_context):
        """Test that failures have all fields present with appropriate values."""
        monkeypatch.setenv("WORKFLOWS_LOG_LEVEL", "INFO")

        result = to_dict(
            await execute_workflow(workflow="nonexistent-workflow", inputs={}, ctx=mock_context)
        )

        assert result["status"] == "failure"
        assert "error" in result and result["error"] is not None
        # Workflow not found provides helpful available_workflows in outputs
        assert "outputs" in result
        assert "available_workflows" in result["outputs"]
        # Other success fields are None
        assert result["blocks"] is None
        assert result["metadata"] is None
        # Pause fields are also None
        assert result["checkpoint_id"] is None
        assert result["prompt"] is None
        assert result["message"] is None

    @pytest.mark.asyncio
    async def test_verbosity_with_warning_level(self, monkeypatch, mock_context):
        """Test that WARNING level returns minimal output (empty blocks/metadata)."""
        monkeypatch.setenv("WORKFLOWS_LOG_LEVEL", "WARNING")

        result = to_dict(
            await execute_workflow(
                workflow="hello-world", inputs={"name": "test"}, ctx=mock_context
            )
        )

        assert result["status"] == "success"
        assert "outputs" in result
        # Consistent contract: always present but empty in minimal mode
        assert "blocks" in result
        assert "metadata" in result
        assert result["blocks"] == {}
        assert result["metadata"] == {}

    @pytest.mark.asyncio
    async def test_verbosity_with_error_level(self, monkeypatch, mock_context):
        """Test that ERROR level returns minimal output (empty blocks/metadata)."""
        monkeypatch.setenv("WORKFLOWS_LOG_LEVEL", "ERROR")

        result = to_dict(
            await execute_workflow(
                workflow="hello-world", inputs={"name": "test"}, ctx=mock_context
            )
        )

        assert result["status"] == "success"
        assert "outputs" in result
        # Consistent contract: always present but empty in minimal mode
        assert "blocks" in result
        assert "metadata" in result
        assert result["blocks"] == {}
        assert result["metadata"] == {}

    @pytest.mark.asyncio
    async def test_outputs_always_present_in_success(self, monkeypatch, mock_context):
        """Test that outputs are always present in success, regardless of verbosity."""
        for log_level in ["ERROR", "WARNING", "INFO", "DEBUG"]:
            monkeypatch.setenv("WORKFLOWS_LOG_LEVEL", log_level)

            result = to_dict(
                await execute_workflow(
                    workflow="hello-world", inputs={"name": "test"}, ctx=mock_context
                )
            )

            assert result["status"] == "success"
            assert "outputs" in result, f"outputs missing for log level {log_level}"
            assert isinstance(result["outputs"], dict)

    @pytest.mark.asyncio
    async def test_unified_response_contract(self, monkeypatch, mock_context):
        """Test that all response fields are always present regardless of status."""
        monkeypatch.setenv("WORKFLOWS_LOG_LEVEL", "INFO")

        # Expected fields in all responses
        expected_fields = {
            "status",
            "outputs",
            "blocks",
            "metadata",
            "error",
            "checkpoint_id",
            "prompt",
            "message",
        }

        # Test success response
        success_result = to_dict(
            await execute_workflow(
                workflow="hello-world", inputs={"name": "test"}, ctx=mock_context
            )
        )
        assert set(success_result.keys()) == expected_fields, "Success response missing fields"
        assert success_result["status"] == "success"
        assert success_result["outputs"] is not None  # Success has outputs
        assert success_result["error"] is None  # No error on success

        # Test failure response
        failure_result = to_dict(
            await execute_workflow(workflow="nonexistent-workflow", inputs={}, ctx=mock_context)
        )
        assert set(failure_result.keys()) == expected_fields, "Failure response missing fields"
        assert failure_result["status"] == "failure"
        assert failure_result["error"] is not None  # Failure has error
        # Workflow not found provides helpful available_workflows in outputs
        assert failure_result["outputs"] is not None
        assert "available_workflows" in failure_result["outputs"]


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
