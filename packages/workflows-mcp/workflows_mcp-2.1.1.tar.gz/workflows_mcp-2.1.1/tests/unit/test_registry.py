"""
Consolidated tests for WorkflowRegistry functionality.

Consolidates tests from:
- test_registry.py (1026 lines, 50+ tests)
- test_registry_load.py (77 lines, validation script moved)
- test_registry_integration.py (152 lines, 5 tests)

Organization:
- TestRegistryBasics: Core registry operations
- TestRegistryLoading: Loading workflows from directories
- TestRegistryValidation: Schema validation and error handling
- TestRegistryIntegration: Integration with workflow execution
"""

from pathlib import Path

import pytest

from workflows_mcp.engine.executor import WorkflowDefinition, WorkflowExecutor
from workflows_mcp.engine.registry import WorkflowRegistry
from workflows_mcp.engine.schema import WorkflowSchema

# ============================================================================
# TestRegistryBasics: Core Registry Operations
# ============================================================================


class TestRegistryBasics:
    """Basic registry operations: register, get, list, unregister."""

    def test_register_workflow_success(
        self, registry: WorkflowRegistry, sample_workflow_schema: WorkflowSchema
    ) -> None:
        """Test successful workflow registration."""
        workflow_def = WorkflowDefinition(
            name=sample_workflow_schema.name,
            description=sample_workflow_schema.description,
            blocks=sample_workflow_schema.blocks,
        )
        registry.register(workflow_def)

        assert len(registry) == 1
        assert registry.exists(sample_workflow_schema.name)
        assert sample_workflow_schema.name in registry

    def test_register_workflow_with_schema(
        self, registry: WorkflowRegistry, sample_workflow_schema: WorkflowSchema
    ) -> None:
        """Test registration with schema metadata."""
        workflow_def = WorkflowDefinition(
            name=sample_workflow_schema.name,
            description=sample_workflow_schema.description,
            blocks=sample_workflow_schema.blocks,
        )
        registry.register(workflow_def, sample_workflow_schema)

        assert registry.exists(sample_workflow_schema.name)
        schema = registry.get_schema(sample_workflow_schema.name)
        assert schema is not None
        assert schema.version == sample_workflow_schema.version

    def test_register_duplicate_raises_error(
        self, registry: WorkflowRegistry, sample_workflow_schema: WorkflowSchema
    ) -> None:
        """Test that registering duplicate workflow raises ValueError."""
        workflow_def = WorkflowDefinition(
            name=sample_workflow_schema.name,
            description=sample_workflow_schema.description,
            blocks=sample_workflow_schema.blocks,
        )
        registry.register(workflow_def)

        with pytest.raises(ValueError, match="already registered"):
            registry.register(workflow_def)

    def test_get_workflow_success(
        self, registry: WorkflowRegistry, sample_workflow_schema: WorkflowSchema
    ) -> None:
        """Test successful workflow retrieval."""
        workflow_def = WorkflowDefinition(
            name=sample_workflow_schema.name,
            description=sample_workflow_schema.description,
            blocks=sample_workflow_schema.blocks,
        )
        registry.register(workflow_def)

        workflow = registry.get(sample_workflow_schema.name)
        assert workflow.name == sample_workflow_schema.name
        assert workflow.description == sample_workflow_schema.description

    def test_get_workflow_not_found(self, registry: WorkflowRegistry) -> None:
        """Test that retrieving non-existent workflow raises KeyError."""
        with pytest.raises(KeyError, match="not found"):
            registry.get("nonexistent")

    def test_get_workflow_not_found_lists_available(
        self, registry: WorkflowRegistry, sample_workflow_schema: WorkflowSchema
    ) -> None:
        """Test that KeyError includes list of available workflows."""
        workflow_def = WorkflowDefinition(
            name=sample_workflow_schema.name,
            description=sample_workflow_schema.description,
            blocks=sample_workflow_schema.blocks,
        )
        registry.register(workflow_def)

        with pytest.raises(KeyError, match="Available workflows"):
            registry.get("nonexistent")

    def test_exists(
        self, registry: WorkflowRegistry, sample_workflow_schema: WorkflowSchema
    ) -> None:
        """Test exists() method."""
        workflow_def = WorkflowDefinition(
            name=sample_workflow_schema.name,
            description=sample_workflow_schema.description,
            blocks=sample_workflow_schema.blocks,
        )
        assert not registry.exists(sample_workflow_schema.name)

        registry.register(workflow_def)
        assert registry.exists(sample_workflow_schema.name)

    def test_contains_operator(
        self, registry: WorkflowRegistry, sample_workflow_schema: WorkflowSchema
    ) -> None:
        """Test 'in' operator support."""
        workflow_def = WorkflowDefinition(
            name=sample_workflow_schema.name,
            description=sample_workflow_schema.description,
            blocks=sample_workflow_schema.blocks,
        )
        assert sample_workflow_schema.name not in registry

        registry.register(workflow_def)
        assert sample_workflow_schema.name in registry

    def test_list_all_empty(self, registry: WorkflowRegistry) -> None:
        """Test listing when registry is empty."""
        workflows = registry.list_all()
        assert workflows == []

    def test_list_all_multiple_workflows(self, registry: WorkflowRegistry) -> None:
        """Test listing multiple workflows."""
        wf1 = WorkflowDefinition("workflow-1", "First", [])
        wf2 = WorkflowDefinition("workflow-2", "Second", [])

        registry.register(wf1)
        registry.register(wf2)

        workflows = registry.list_all()
        assert len(workflows) == 2

        names = {w.name for w in workflows}
        assert names == {"workflow-1", "workflow-2"}

    def test_list_names(self, registry: WorkflowRegistry) -> None:
        """Test listing workflow names."""
        wf1 = WorkflowDefinition("workflow-1", "First", [])
        wf2 = WorkflowDefinition("workflow-2", "Second", [])

        registry.register(wf1)
        registry.register(wf2)

        names = registry.list_names()
        assert names == ["workflow-1", "workflow-2"]  # Should be sorted

    def test_unregister_workflow(
        self, registry: WorkflowRegistry, sample_workflow_schema: WorkflowSchema
    ) -> None:
        """Test workflow unregistration."""
        workflow_def = WorkflowDefinition(
            name=sample_workflow_schema.name,
            description=sample_workflow_schema.description,
            blocks=sample_workflow_schema.blocks,
        )
        registry.register(workflow_def)
        assert registry.exists(sample_workflow_schema.name)

        registry.unregister(sample_workflow_schema.name)
        assert not registry.exists(sample_workflow_schema.name)
        assert len(registry) == 0

    def test_unregister_nonexistent_raises_error(self, registry: WorkflowRegistry) -> None:
        """Test that unregistering non-existent workflow raises KeyError."""
        with pytest.raises(KeyError, match="not found"):
            registry.unregister("nonexistent")

    def test_clear_empty_registry(self, registry: WorkflowRegistry) -> None:
        """Test clearing empty registry."""
        registry.clear()
        assert len(registry) == 0

    def test_clear_with_workflows(
        self, registry: WorkflowRegistry, sample_workflow_schema: WorkflowSchema
    ) -> None:
        """Test clearing registry with workflows."""
        workflow_def = WorkflowDefinition(
            name=sample_workflow_schema.name,
            description=sample_workflow_schema.description,
            blocks=sample_workflow_schema.blocks,
        )
        registry.register(workflow_def)
        assert len(registry) == 1

        registry.clear()
        assert len(registry) == 0
        assert not registry.exists(sample_workflow_schema.name)

    def test_clear_with_schemas(
        self, registry: WorkflowRegistry, sample_workflow_schema: WorkflowSchema
    ) -> None:
        """Test that clear removes both workflows and schemas."""
        workflow_def = WorkflowDefinition(
            name=sample_workflow_schema.name,
            description=sample_workflow_schema.description,
            blocks=sample_workflow_schema.blocks,
        )
        registry.register(workflow_def, sample_workflow_schema)
        assert registry.get_schema(sample_workflow_schema.name) is not None

        registry.clear()
        assert registry.get_schema(sample_workflow_schema.name) is None

    def test_len(self, registry: WorkflowRegistry) -> None:
        """Test __len__ method."""
        assert len(registry) == 0

        wf1 = WorkflowDefinition("workflow-1", "First", [])
        registry.register(wf1)
        assert len(registry) == 1

        wf2 = WorkflowDefinition("workflow-2", "Second", [])
        registry.register(wf2)
        assert len(registry) == 2

    def test_repr(self, registry: WorkflowRegistry) -> None:
        """Test __repr__ method."""
        repr_str = repr(registry)
        assert "WorkflowRegistry" in repr_str
        assert "0 workflows" in repr_str

        wf = WorkflowDefinition("test", "Test", [])
        registry.register(wf)

        repr_str = repr(registry)
        assert "1 workflows" in repr_str


# ============================================================================
# TestRegistryMetadata: Metadata Extraction for MCP Tools
# ============================================================================


class TestRegistryMetadata:
    """Test metadata extraction for MCP tools."""

    def test_get_workflow_metadata_basic(
        self, registry: WorkflowRegistry, sample_workflow_schema: WorkflowSchema
    ) -> None:
        """Test metadata extraction without schema."""
        workflow_def = WorkflowDefinition(
            name=sample_workflow_schema.name,
            description=sample_workflow_schema.description,
            blocks=sample_workflow_schema.blocks,
        )
        registry.register(workflow_def)

        metadata = registry.get_workflow_metadata(sample_workflow_schema.name)
        assert metadata["name"] == sample_workflow_schema.name
        assert metadata["description"] == sample_workflow_schema.description
        assert metadata["tags"] == []  # Empty tags when no schema
        assert metadata["inputs"] == {}  # Empty inputs when no schema

    def test_get_workflow_metadata_with_schema(
        self, registry: WorkflowRegistry, sample_workflow_schema: WorkflowSchema
    ) -> None:
        """Test metadata extraction with schema (default mode)."""
        workflow_def = WorkflowDefinition(
            name=sample_workflow_schema.name,
            description=sample_workflow_schema.description,
            blocks=sample_workflow_schema.blocks,
        )
        registry.register(workflow_def, sample_workflow_schema)

        # Default mode: name, description, tags, inputs
        metadata = registry.get_workflow_metadata(sample_workflow_schema.name)
        assert metadata["name"] == sample_workflow_schema.name
        assert metadata["description"] == sample_workflow_schema.description
        assert metadata["tags"] == sample_workflow_schema.tags
        assert "inputs" in metadata
        # Version and author should NOT be in default mode
        assert "version" not in metadata
        assert "author" not in metadata
        assert "outputs" not in metadata

    def test_get_workflow_metadata_with_schema_detailed(
        self, registry: WorkflowRegistry, sample_workflow_schema: WorkflowSchema
    ) -> None:
        """Test metadata extraction with schema (detailed mode)."""
        workflow_def = WorkflowDefinition(
            name=sample_workflow_schema.name,
            description=sample_workflow_schema.description,
            blocks=sample_workflow_schema.blocks,
        )
        registry.register(workflow_def, sample_workflow_schema)

        # Detailed mode: includes version, author, outputs
        metadata = registry.get_workflow_metadata(sample_workflow_schema.name, detailed=True)
        assert metadata["name"] == sample_workflow_schema.name
        assert metadata["description"] == sample_workflow_schema.description
        assert metadata["tags"] == sample_workflow_schema.tags
        assert "inputs" in metadata
        # Detailed mode includes version, author, outputs
        assert metadata["version"] == sample_workflow_schema.version
        if sample_workflow_schema.author:
            assert metadata["author"] == sample_workflow_schema.author

    def test_list_all_metadata(self, registry: WorkflowRegistry) -> None:
        """Test listing metadata for all workflows."""
        wf1 = WorkflowDefinition("workflow-1", "First", [])
        wf2 = WorkflowDefinition("workflow-2", "Second", [])

        registry.register(wf1)
        registry.register(wf2)

        metadata_list = registry.list_all_metadata()
        assert len(metadata_list) == 2

        assert metadata_list[0]["name"] == "workflow-1"  # Sorted
        assert metadata_list[1]["name"] == "workflow-2"


# ============================================================================
# TestRegistryLoading: Loading Workflows from Directories
# ============================================================================


class TestRegistryLoading:
    """Test loading workflows from directories."""

    def test_load_from_directory_success(
        self, registry: WorkflowRegistry, temp_workflow_dir: Path
    ) -> None:
        """Test successful directory loading."""
        result = registry.load_from_directory(temp_workflow_dir)

        assert result.is_success
        assert result.value == 3  # 3 workflows in temp_workflow_dir

        assert registry.exists("workflow-one")
        assert registry.exists("workflow-two")
        assert registry.exists("workflow-three")

    def test_load_from_directory_nonexistent(self, registry: WorkflowRegistry) -> None:
        """Test loading from non-existent directory."""
        result = registry.load_from_directory("/nonexistent/path")

        assert not result.is_success
        assert "not found" in result.error.lower()

    def test_load_from_directory_recursive(
        self, registry: WorkflowRegistry, tmp_path: Path
    ) -> None:
        """Test that directory loading is recursive."""
        # Create subdirectory with workflow
        subdir = tmp_path / "subdir"
        subdir.mkdir()

        workflow = """
name: workflow-in-subdir
description: Test workflow in subdirectory
version: "1.0"

blocks:
  - id: block1
    type: EchoBlock
    inputs:
      message: "Test"
"""
        (subdir / "workflow.yaml").write_text(workflow)

        result = registry.load_from_directory(tmp_path)

        assert result.is_success
        assert registry.exists("workflow-in-subdir")

    def test_load_from_directory_duplicate_handling(
        self, registry: WorkflowRegistry, temp_workflow_dir: Path
    ) -> None:
        """Test that duplicate workflows are skipped with warning."""
        # Load once
        result1 = registry.load_from_directory(temp_workflow_dir)
        assert result1.is_success
        assert result1.value == 3

        # Load again - duplicates should be skipped
        result2 = registry.load_from_directory(temp_workflow_dir)
        assert result2.is_success
        assert result2.value == 0  # No new workflows loaded

        # Still only 3 workflows
        assert len(registry) == 3

    def test_load_from_directories_success(
        self, registry: WorkflowRegistry, tmp_path: Path
    ) -> None:
        """Test successful multi-directory loading."""
        # Create two directories with workflows
        dir1 = tmp_path / "dir1"
        dir1.mkdir()
        (dir1 / "wf1.yaml").write_text("""
name: workflow-1
description: First workflow
version: "1.0"
blocks:
  - id: echo
    type: EchoBlock
    inputs:
      message: "Test 1"
""")

        dir2 = tmp_path / "dir2"
        dir2.mkdir()
        (dir2 / "wf2.yaml").write_text("""
name: workflow-2
description: Second workflow
version: "1.0"
blocks:
  - id: echo
    type: EchoBlock
    inputs:
      message: "Test 2"
""")

        result = registry.load_from_directories([dir1, dir2])

        assert result.is_success
        assert isinstance(result.value, dict)
        assert result.value[str(dir1.resolve())] == 1
        assert result.value[str(dir2.resolve())] == 1
        assert len(registry) == 2

    def test_load_from_directories_empty_list(self, registry: WorkflowRegistry) -> None:
        """Test loading with empty directory list."""
        result = registry.load_from_directories([])

        assert not result.is_success
        assert "No directories provided" in result.error

    def test_load_from_directories_priority_ordering(
        self, registry: WorkflowRegistry, tmp_path: Path
    ) -> None:
        """Test that first directory takes precedence (skip mode)."""
        # Create two directories with same workflow name
        dir1 = tmp_path / "dir1"
        dir1.mkdir()
        (dir1 / "wf.yaml").write_text("""
name: test-workflow
description: From dir1
version: "1.0"
blocks:
  - id: echo
    type: EchoBlock
    inputs:
      message: "Dir1"
""")

        dir2 = tmp_path / "dir2"
        dir2.mkdir()
        (dir2 / "wf.yaml").write_text("""
name: test-workflow
description: From dir2
version: "2.0"
blocks:
  - id: echo
    type: EchoBlock
    inputs:
      message: "Dir2"
""")

        result = registry.load_from_directories([dir1, dir2], on_duplicate="skip")

        assert result.is_success
        workflow = registry.get("test-workflow")
        assert "dir1" in workflow.description.lower()
        assert registry.get_workflow_source("test-workflow") == dir1.resolve()

    def test_load_from_directories_overwrite_mode(
        self, registry: WorkflowRegistry, tmp_path: Path
    ) -> None:
        """Test duplicate handling with overwrite mode."""
        # Create two directories with same workflow name
        dir1 = tmp_path / "dir1"
        dir1.mkdir()
        (dir1 / "wf.yaml").write_text("""
name: test-workflow
description: From dir1
version: "1.0"
blocks:
  - id: echo
    type: EchoBlock
    inputs:
      message: "Dir1"
""")

        dir2 = tmp_path / "dir2"
        dir2.mkdir()
        (dir2 / "wf.yaml").write_text("""
name: test-workflow
description: From dir2
version: "2.0"
blocks:
  - id: echo
    type: EchoBlock
    inputs:
      message: "Dir2"
""")

        result = registry.load_from_directories([dir1, dir2], on_duplicate="overwrite")

        assert result.is_success
        workflow = registry.get("test-workflow")
        assert "dir2" in workflow.description.lower()
        assert registry.get_workflow_source("test-workflow") == dir2.resolve()

    def test_load_from_directories_error_mode(
        self, registry: WorkflowRegistry, tmp_path: Path
    ) -> None:
        """Test duplicate handling with error mode."""
        # Create two directories with same workflow name
        dir1 = tmp_path / "dir1"
        dir1.mkdir()
        (dir1 / "wf.yaml").write_text("""
name: test-workflow
description: From dir1
version: "1.0"
blocks:
  - id: echo
    type: EchoBlock
    inputs:
      message: "Dir1"
""")

        dir2 = tmp_path / "dir2"
        dir2.mkdir()
        (dir2 / "wf.yaml").write_text("""
name: test-workflow
description: From dir2
version: "2.0"
blocks:
  - id: echo
    type: EchoBlock
    inputs:
      message: "Dir2"
""")

        result = registry.load_from_directories([dir1, dir2], on_duplicate="error")

        assert not result.is_success
        assert "Duplicate workflow" in result.error
        assert "test-workflow" in result.error


# ============================================================================
# TestRegistrySourceTracking: Workflow Source Tracking
# ============================================================================


class TestRegistrySourceTracking:
    """Test workflow source tracking functionality."""

    def test_register_with_source_dir(self, registry: WorkflowRegistry) -> None:
        """Test registering workflow with source directory."""
        wf = WorkflowDefinition("test-wf", "Test", [])
        source = Path("/tmp/templates")

        registry.register(wf, source_dir=source)

        assert registry.exists("test-wf")
        assert registry.get_workflow_source("test-wf") == source

    def test_register_without_source_dir(self, registry: WorkflowRegistry) -> None:
        """Test registering workflow without source directory."""
        wf = WorkflowDefinition("test-wf", "Test", [])

        registry.register(wf)

        assert registry.exists("test-wf")
        assert registry.get_workflow_source("test-wf") is None

    def test_get_workflow_source_nonexistent(self, registry: WorkflowRegistry) -> None:
        """Test getting source for non-existent workflow."""
        assert registry.get_workflow_source("nonexistent") is None

    def test_list_by_source_empty(self, registry: WorkflowRegistry) -> None:
        """Test listing workflows by source with empty registry."""
        workflows = registry.list_by_source(Path("/tmp/templates"))
        assert workflows == []

    def test_list_by_source_with_workflows(self, registry: WorkflowRegistry) -> None:
        """Test listing workflows filtered by source directory."""
        source1 = Path("/tmp/templates")
        source2 = Path("/tmp/library")

        wf1 = WorkflowDefinition("wf-1", "First", [])
        wf2 = WorkflowDefinition("wf-2", "Second", [])
        wf3 = WorkflowDefinition("wf-3", "Third", [])

        registry.register(wf1, source_dir=source1)
        registry.register(wf2, source_dir=source1)
        registry.register(wf3, source_dir=source2)

        # List workflows from source1
        source1_workflows = registry.list_by_source(source1)
        assert len(source1_workflows) == 2
        assert set(source1_workflows) == {"wf-1", "wf-2"}

        # List workflows from source2
        source2_workflows = registry.list_by_source(source2)
        assert len(source2_workflows) == 1
        assert source2_workflows == ["wf-3"]

        # List workflows from unused source
        unused_workflows = registry.list_by_source(Path("/tmp/unused"))
        assert unused_workflows == []

    def test_unregister_removes_source(self, registry: WorkflowRegistry) -> None:
        """Test that unregister removes source tracking."""
        wf = WorkflowDefinition("test-wf", "Test", [])
        source = Path("/tmp/templates")

        registry.register(wf, source_dir=source)
        assert registry.get_workflow_source("test-wf") == source

        registry.unregister("test-wf")
        assert registry.get_workflow_source("test-wf") is None

    def test_clear_removes_all_sources(self, registry: WorkflowRegistry) -> None:
        """Test that clear removes all source tracking."""
        wf1 = WorkflowDefinition("wf-1", "First", [])
        wf2 = WorkflowDefinition("wf-2", "Second", [])
        source = Path("/tmp/templates")

        registry.register(wf1, source_dir=source)
        registry.register(wf2, source_dir=source)

        assert len(registry.list_by_source(source)) == 2

        registry.clear()

        assert len(registry.list_by_source(source)) == 0


# ============================================================================
# TestRegistryTagFiltering: Tag-Based Filtering
# ============================================================================


class TestRegistryTagFiltering:
    """Test tag-based workflow filtering functionality."""

    def test_list_metadata_by_tags_empty_registry(self, registry: WorkflowRegistry) -> None:
        """Test tag filtering with empty registry."""
        result = registry.list_metadata_by_tags(["python"])
        assert result == []

    def test_list_metadata_by_tags_empty_tag_list(self, registry: WorkflowRegistry) -> None:
        """Test that empty tag list returns empty result."""
        wf = WorkflowDefinition("test-wf", "Test", [])
        schema = WorkflowSchema(
            name="test-wf",
            description="Test",
            tags=["python", "linting"],
            blocks=[{"id": "b1", "type": "EchoBlock", "inputs": {}}],
        )
        registry.register(wf, schema)

        result = registry.list_metadata_by_tags([])
        assert result == []

    def test_list_metadata_by_tags_single_tag_match(self, registry: WorkflowRegistry) -> None:
        """Test filtering with single tag."""
        # Create workflow with tags
        wf1 = WorkflowDefinition("python-wf", "Python workflow", [])
        schema1 = WorkflowSchema(
            name="python-wf",
            description="Python workflow",
            tags=["python", "linting", "ruff"],
            blocks=[{"id": "b1", "type": "EchoBlock", "inputs": {}}],
        )

        # Create workflow without matching tag
        wf2 = WorkflowDefinition("git-wf", "Git workflow", [])
        schema2 = WorkflowSchema(
            name="git-wf",
            description="Git workflow",
            tags=["git", "version-control"],
            blocks=[{"id": "b1", "type": "EchoBlock", "inputs": {}}],
        )

        registry.register(wf1, schema1)
        registry.register(wf2, schema2)

        # Filter by "python" tag
        result = registry.list_metadata_by_tags(["python"])
        assert len(result) == 1
        assert result[0]["name"] == "python-wf"
        assert "python" in result[0]["tags"]

    def test_list_metadata_by_tags_multiple_tags_and_semantics(
        self, registry: WorkflowRegistry
    ) -> None:
        """Test filtering with multiple tags using AND semantics."""
        # Workflow with both tags
        wf1 = WorkflowDefinition("lint-python", "Python linting", [])
        schema1 = WorkflowSchema(
            name="lint-python",
            description="Python linting",
            tags=["python", "linting", "ruff", "mypy"],
            blocks=[{"id": "b1", "type": "EchoBlock", "inputs": {}}],
        )

        # Workflow with only one tag
        wf2 = WorkflowDefinition("run-pytest", "Run Python tests", [])
        schema2 = WorkflowSchema(
            name="run-pytest",
            description="Run Python tests",
            tags=["python", "testing", "pytest"],
            blocks=[{"id": "b1", "type": "EchoBlock", "inputs": {}}],
        )

        # Workflow with different tags
        wf3 = WorkflowDefinition("lint-node", "Node linting", [])
        schema3 = WorkflowSchema(
            name="lint-node",
            description="Node linting",
            tags=["node", "linting", "eslint"],
            blocks=[{"id": "b1", "type": "EchoBlock", "inputs": {}}],
        )

        registry.register(wf1, schema1)
        registry.register(wf2, schema2)
        registry.register(wf3, schema3)

        # Filter by both "python" AND "linting"
        result = registry.list_metadata_by_tags(["python", "linting"])
        assert len(result) == 1
        assert result[0]["name"] == "lint-python"

    def test_list_metadata_by_tags_match_all_false(self, registry: WorkflowRegistry) -> None:
        """Test filtering with OR semantics (match_all=False)."""
        wf1 = WorkflowDefinition("python-ci", "Python CI", [])
        schema1 = WorkflowSchema(
            name="python-ci",
            description="Python CI",
            tags=["python", "ci", "testing"],
            blocks=[{"id": "b1", "type": "EchoBlock", "inputs": {}}],
        )

        wf2 = WorkflowDefinition("node-ci", "Node CI", [])
        schema2 = WorkflowSchema(
            name="node-ci",
            description="Node CI",
            tags=["node", "ci", "testing"],
            blocks=[{"id": "b1", "type": "EchoBlock", "inputs": {}}],
        )

        wf3 = WorkflowDefinition("deploy", "Deploy", [])
        schema3 = WorkflowSchema(
            name="deploy",
            description="Deploy",
            tags=["deployment", "production"],
            blocks=[{"id": "b1", "type": "EchoBlock", "inputs": {}}],
        )

        registry.register(wf1, schema1)
        registry.register(wf2, schema2)
        registry.register(wf3, schema3)

        # Filter with OR semantics: workflows with "python" OR "node"
        result = registry.list_metadata_by_tags(["python", "node"], match_all=False)
        assert len(result) == 2
        names = {wf["name"] for wf in result}
        assert names == {"python-ci", "node-ci"}

    def test_list_metadata_by_tags_no_schema(self, registry: WorkflowRegistry) -> None:
        """Test that workflows without schemas are not included."""
        # Workflow without schema
        wf1 = WorkflowDefinition("no-schema-wf", "No schema", [])
        registry.register(wf1)

        # Workflow with schema and tags
        wf2 = WorkflowDefinition("with-schema-wf", "With schema", [])
        schema2 = WorkflowSchema(
            name="with-schema-wf",
            description="With schema",
            tags=["python", "testing"],
            blocks=[{"id": "b1", "type": "EchoBlock", "inputs": {}}],
        )
        registry.register(wf2, schema2)

        result = registry.list_metadata_by_tags(["python"])
        assert len(result) == 1
        assert result[0]["name"] == "with-schema-wf"

    def test_list_metadata_by_tags_workflow_with_empty_tags(
        self, registry: WorkflowRegistry
    ) -> None:
        """Test that workflows with empty tag list are not included."""
        wf = WorkflowDefinition("empty-tags-wf", "Empty tags", [])
        schema = WorkflowSchema(
            name="empty-tags-wf",
            description="Empty tags",
            tags=[],  # Empty tags list
            blocks=[{"id": "b1", "type": "EchoBlock", "inputs": {}}],
        )
        registry.register(wf, schema)

        result = registry.list_metadata_by_tags(["python"])
        assert result == []

    def test_list_metadata_by_tags_case_sensitive(self, registry: WorkflowRegistry) -> None:
        """Test that tag matching is case-sensitive."""
        wf = WorkflowDefinition("test-wf", "Test", [])
        schema = WorkflowSchema(
            name="test-wf",
            description="Test",
            tags=["Python", "Testing"],  # Capitalized tags
            blocks=[{"id": "b1", "type": "EchoBlock", "inputs": {}}],
        )
        registry.register(wf, schema)

        # Lowercase search should not match
        result = registry.list_metadata_by_tags(["python"])
        assert result == []

        # Exact case should match
        result = registry.list_metadata_by_tags(["Python"])
        assert len(result) == 1
        assert result[0]["name"] == "test-wf"


# ============================================================================
# TestRegistryIntegration: Integration with Workflow Execution
# ============================================================================


class TestRegistryIntegration:
    """Test registry integration with workflow execution."""

    def test_load_example_workflow(self, registry_with_examples: WorkflowRegistry) -> None:
        """Test loading example workflows."""
        if len(registry_with_examples) == 0:
            pytest.skip("No example workflows found")

        # Check that hello-world workflow was loaded (it's in every example set)
        assert registry_with_examples.exists("hello-world")

        # Get workflow definition
        workflow = registry_with_examples.get("hello-world")
        assert workflow.name == "hello-world"
        assert "Hello" in workflow.description or "hello" in workflow.description.lower()

    def test_example_workflow_metadata(self, registry_with_examples: WorkflowRegistry) -> None:
        """Test metadata extraction for example workflow."""
        if not registry_with_examples.exists("hello-world"):
            pytest.skip("hello-world workflow not found")

        metadata = registry_with_examples.get_workflow_metadata("hello-world")

        assert metadata["name"] == "hello-world"
        # Metadata may include tags, version, author (check if present)
        assert "description" in metadata

    def test_registry_to_executor_integration(
        self, registry_with_examples: WorkflowRegistry
    ) -> None:
        """Test loading workflow from registry into executor."""
        if not registry_with_examples.exists("hello-world"):
            pytest.skip("hello-world workflow not found")

        # Get workflow from registry
        workflow = registry_with_examples.get("hello-world")

        # Load into executor
        executor = WorkflowExecutor()
        executor.load_workflow(workflow)

        # Verify executor has the workflow
        assert "hello-world" in executor.workflows

    @pytest.mark.asyncio
    async def test_end_to_end_workflow_execution(
        self, registry_with_examples: WorkflowRegistry
    ) -> None:
        """Test complete workflow execution from registry to results."""
        if not registry_with_examples.exists("hello-world"):
            pytest.skip("hello-world workflow not found")

        # Get workflow from registry
        workflow = registry_with_examples.get("hello-world")

        # Load into executor
        executor = WorkflowExecutor()
        executor.load_workflow(workflow)

        # Execute workflow with inputs (hello-world might not need specific inputs)
        result = await executor.execute_workflow(
            "hello-world",
            runtime_inputs={},
        )

        # Verify execution succeeded
        assert result.is_success, f"Workflow execution failed: {result.error}"

        # Verify output structure
        output = result.value
        assert output is not None
        assert "metadata" in output
        assert "blocks" in output
        assert "execution_time_seconds" in output["metadata"]
        assert output["metadata"]["total_blocks"] > 0

    def test_list_all_metadata_for_mcp(self, registry_with_examples: WorkflowRegistry) -> None:
        """Test MCP-friendly metadata listing."""
        if len(registry_with_examples) == 0:
            pytest.skip("No example workflows found")

        metadata_list = registry_with_examples.list_all_metadata()

        # Should be a list of dicts
        assert isinstance(metadata_list, list)
        assert len(metadata_list) > 0

        # Each metadata entry should have required fields
        for metadata in metadata_list:
            assert "name" in metadata
            assert "description" in metadata
            assert isinstance(metadata["name"], str)
            assert isinstance(metadata["description"], str)

    def test_workflow_discovery_pattern(self, registry_with_examples: WorkflowRegistry) -> None:
        """Test typical MCP tool workflow discovery pattern."""
        if len(registry_with_examples) == 0:
            pytest.skip("No example workflows found")

        # 1. List all available workflows
        all_workflows = registry_with_examples.list_names()
        assert len(all_workflows) > 0

        # 2. Get metadata for first workflow
        first_workflow_name = all_workflows[0]
        metadata = registry_with_examples.get_workflow_metadata(first_workflow_name)

        # 3. Verify metadata structure suitable for MCP tool response
        assert "name" in metadata
        assert "description" in metadata

        # Optional fields may or may not be present
        if "tags" in metadata:
            assert isinstance(metadata["tags"], list)
