"""
YAML workflow schema with Pydantic v2 models for Phase 1.

This module defines the complete schema for YAML workflow definitions, including:
- Workflow metadata (name, description, tags)
- Input declarations with types and defaults
- Block definitions with dependencies
- Output mappings with variable substitution
- Comprehensive validation logic

The schema validates:
- YAML syntax and structure
- Required fields and types
- Block type existence in registry
- Dependency validity (no cycles, valid references)
- Variable substitution syntax (${block_id.field})
"""

import re
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from .block import BLOCK_REGISTRY
from .dag import DAGResolver
from .executor import WorkflowDefinition
from .result import Result


class InputType(str, Enum):
    """
    Supported input types for workflow parameters.

    These map to Python types:
    - string: str
    - integer: int
    - boolean: bool
    - array: list
    - object: dict
    """

    STRING = "string"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


class WorkflowMetadata(BaseModel):
    """
    Workflow metadata for identification and documentation.

    Attributes:
        name: Unique workflow identifier (kebab-case recommended)
        description: Human-readable workflow description
        version: Semantic version string (default: "1.0")
        author: Optional workflow author
        tags: List of searchable tags for organization and discovery
    """

    name: str = Field(
        description="Unique workflow identifier (kebab-case)",
        pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$",
        min_length=1,
        max_length=100,
    )
    description: str = Field(description="Human-readable workflow description", min_length=1)
    version: str = Field(
        default="1.0", description="Semantic version", pattern=r"^\d+\.\d+(\.\d+)?$"
    )
    author: str | None = Field(default=None, description="Workflow author")
    tags: list[str] = Field(default_factory=list, description="Searchable tags")

    model_config = {"extra": "forbid"}


class OutputSchema(BaseModel):
    """
    Schema for block output declaration.

    Defines file-based outputs that blocks can declare. The workflow engine
    validates paths and reads files after block execution.

    Attributes:
        type: Output type (string, int, float, bool, json)
        path: Relative or absolute file path
        description: Optional human-readable output description
        validation: Optional Python expression for validation
        unsafe: Allow absolute paths (default: False for security)
        required: Whether output is required (default: True)

    Example:
        outputs:
          test_results:
            type: json
            path: "$SCRATCH/test-results.json"
            description: "Test execution results"
            required: true
          coverage_percent:
            type: float
            path: ".scratch/coverage.txt"
            description: "Code coverage percentage"
    """

    type: Literal["string", "int", "float", "bool", "json"] = Field(description="Output value type")
    path: str = Field(description="Relative or absolute file path", min_length=1)
    description: str | None = Field(default=None, description="Human-readable description")
    validation: str | None = Field(
        default=None, description="Optional Python expression for validation"
    )
    unsafe: bool = Field(
        default=False, description="Allow absolute paths (security risk if enabled)"
    )
    required: bool = Field(default=True, description="Whether output is required")

    model_config = {"extra": "forbid"}


class WorkflowInputDeclaration(BaseModel):
    """
    Workflow input parameter declaration.

    Defines expected runtime inputs with types, descriptions, and defaults.

    Attributes:
        type: Input type (string, integer, boolean, array, object)
        description: Human-readable input description
        default: Optional default value (must match type)
        required: Whether input is required (default: True if no default)

    Example:
        inputs:
          branch_name:
            type: string
            description: "Git branch name"
            default: "main"
          issue_number:
            type: integer
            description: "GitHub issue number"
            required: true
    """

    type: InputType = Field(description="Input value type")
    description: str = Field(description="Human-readable description", min_length=1)
    default: Any | None = Field(default=None, description="Default value (must match type)")
    required: bool = Field(default=True, description="Whether input is required")

    model_config = {"extra": "forbid"}

    @model_validator(mode="after")
    def validate_default_type(self) -> "WorkflowInputDeclaration":
        """Validate that default value matches declared type."""
        if self.default is None:
            return self

        # Type validation mapping
        type_validators = {
            InputType.STRING: lambda v: isinstance(v, str),
            InputType.INTEGER: lambda v: isinstance(v, int) and not isinstance(v, bool),
            InputType.BOOLEAN: lambda v: isinstance(v, bool),
            InputType.ARRAY: lambda v: isinstance(v, list),
            InputType.OBJECT: lambda v: isinstance(v, dict),
        }

        validator = type_validators.get(self.type)
        if validator and not validator(self.default):
            raise ValueError(
                f"Default value {self.default!r} does not match declared type '{self.type.value}'"
            )

        return self

    @model_validator(mode="after")
    def validate_required_with_default(self) -> "WorkflowInputDeclaration":
        """If default is provided, required should be False."""
        if self.default is not None and self.required:
            # Auto-correct: if default exists, input is not required
            self.required = False

        return self


class BlockDefinition(BaseModel):
    """
    Workflow block definition.

    Defines a single block in the workflow with its inputs and dependencies.

    Attributes:
        id: Unique block identifier within workflow
        type: Block type name (must exist in BLOCK_REGISTRY)
        inputs: Block input parameters (dict with variable substitution support)
        depends_on: List of block IDs this block depends on
        condition: Optional boolean expression for conditional execution
        outputs: Optional custom file-based outputs (for Shell blocks)

    Example:
        blocks:
          - id: create_worktree
            type: CreateWorktree
            inputs:
              branch: "feature/${issue_number}"
              base_branch: "main"

          - id: create_file
            type: CreateFile
            inputs:
              path: "${create_worktree.worktree_path}/README.md"
              content: "# Feature"
            depends_on:
              - create_worktree

          - id: run_tests
            type: Shell
            inputs:
              command: "pytest --json-report --json-report-file=$SCRATCH/results.json"
            outputs:
              test_results:
                type: json
                path: "$SCRATCH/results.json"
                description: "Test execution results"

          - id: deploy
            type: Shell
            inputs:
              command: "echo 'Deploying...'"
            condition: "${run_tests.exit_code} == 0"
            depends_on:
              - run_tests
    """

    id: str = Field(
        description="Unique block identifier",
        pattern=r"^[a-z_][a-z0-9_]*$",
        min_length=1,
        max_length=100,
    )
    type: str = Field(description="Block type name from BLOCK_REGISTRY", min_length=1)
    inputs: dict[str, Any] = Field(default_factory=dict, description="Block input parameters")
    depends_on: list[str] = Field(default_factory=list, description="Dependency block IDs")
    condition: str | None = Field(
        default=None,
        description="Optional condition expression for conditional execution",
    )
    outputs: dict[str, OutputSchema] | None = Field(
        default=None, description="Custom file-based outputs"
    )

    model_config = {"extra": "forbid"}

    @field_validator("depends_on")
    @classmethod
    def validate_depends_on_unique(cls, v: list[str]) -> list[str]:
        """Ensure dependency list has no duplicates."""
        if len(v) != len(set(v)):
            duplicates = [dep for dep in v if v.count(dep) > 1]
            raise ValueError(f"Duplicate dependencies found: {duplicates}")
        return v


class WorkflowOutputSchema(BaseModel):
    """
    Schema for workflow-level output.

    Defines outputs that the workflow exposes to callers. These are typically
    expressions that reference block outputs.

    Attributes:
        value: Expression (e.g., "${block.outputs.field}" or "${block.exit_code}")
        type: Output type (string, int, float, bool, json)
        description: Optional human-readable output description

    Example:
        outputs:
          test_results:
            value: "${run_tests.outputs.test_results}"
            type: json
            description: "Test execution results"
          success:
            value: "${run_tests.exit_code}"
            type: int
            description: "Test exit code"
    """

    value: str = Field(description="Expression referencing block outputs", min_length=1)
    type: Literal["string", "int", "float", "bool", "json"] = Field(description="Output value type")
    description: str | None = Field(default=None, description="Human-readable description")

    model_config = {"extra": "forbid"}


class WorkflowSchema(BaseModel):
    """
    Complete YAML workflow schema.

    This is the root model for workflow definitions loaded from YAML files.
    It validates the entire workflow structure and provides conversion to
    the executor's WorkflowDefinition format.

    Attributes:
        name: Workflow name (from metadata)
        description: Workflow description (from metadata)
        version: Workflow version (from metadata)
        author: Optional workflow author (from metadata)
        tags: Searchable tags for organization and discovery
        inputs: Input parameter declarations
        blocks: Block definitions
        outputs: Output mappings with variable substitution

    Example YAML:
        name: example-workflow
        description: Example workflow with validation
        version: "1.0"
        tags: [test, example]

        inputs:
          input_name:
            type: string
            description: Input parameter
            default: "default_value"

        blocks:
          - id: block1
            type: EchoBlock
            inputs:
              message: "Hello ${input_name}"

          - id: block2
            type: EchoBlock
            inputs:
              message: "Output: ${block1.echoed}"
            depends_on:
              - block1

        outputs:
          final_message: "${block2.echoed}"
    """

    # Metadata fields (flattened for YAML convenience)
    name: str = Field(
        description="Unique workflow identifier",
        pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$",
        min_length=1,
        max_length=100,
    )
    description: str = Field(description="Workflow description", min_length=1)
    version: str = Field(default="1.0", pattern=r"^\d+\.\d+(\.\d+)?$")
    author: str | None = Field(default=None)
    tags: list[str] = Field(default_factory=list)

    # Workflow structure
    inputs: dict[str, WorkflowInputDeclaration] = Field(
        default_factory=dict, description="Input parameter declarations"
    )
    blocks: list[BlockDefinition] = Field(description="Workflow block definitions", min_length=1)
    outputs: dict[str, str | WorkflowOutputSchema] = Field(
        default_factory=dict, description="Output mappings with variable substitution"
    )

    model_config = {"extra": "forbid"}

    @property
    def metadata(self) -> WorkflowMetadata:
        """Extract metadata as separate model."""
        return WorkflowMetadata(
            name=self.name,
            description=self.description,
            version=self.version,
            author=self.author,
            tags=self.tags,
        )

    @field_validator("blocks")
    @classmethod
    def validate_unique_block_ids(cls, v: list[BlockDefinition]) -> list[BlockDefinition]:
        """Ensure all block IDs are unique."""
        block_ids = [block.id for block in v]
        if len(block_ids) != len(set(block_ids)):
            duplicates = [bid for bid in block_ids if block_ids.count(bid) > 1]
            raise ValueError(f"Duplicate block IDs found: {duplicates}")
        return v

    @model_validator(mode="after")
    def validate_block_types_exist(self) -> "WorkflowSchema":
        """Validate that all block types exist in BLOCK_REGISTRY."""
        available_types = set(BLOCK_REGISTRY.list_types())

        for block in self.blocks:
            if block.type not in available_types:
                raise ValueError(
                    f"Unknown block type '{block.type}' in block '{block.id}'. "
                    f"Available types: {sorted(available_types)}"
                )

        return self

    @model_validator(mode="after")
    def validate_dependencies_exist(self) -> "WorkflowSchema":
        """Validate that all dependencies reference existing blocks."""
        block_ids = {block.id for block in self.blocks}

        for block in self.blocks:
            for dep in block.depends_on:
                if dep not in block_ids:
                    raise ValueError(
                        f"Block '{block.id}' depends on non-existent block '{dep}'. "
                        f"Available blocks: {sorted(block_ids)}"
                    )

        return self

    @model_validator(mode="after")
    def validate_no_cyclic_dependencies(self) -> "WorkflowSchema":
        """Validate that dependencies form a valid DAG (no cycles)."""
        block_ids = [block.id for block in self.blocks]
        dependencies = {block.id: block.depends_on for block in self.blocks}

        resolver = DAGResolver(block_ids, dependencies)
        result = resolver.topological_sort()

        if not result.is_success:
            raise ValueError(f"Invalid workflow dependencies: {result.error}")

        return self

    @model_validator(mode="after")
    def validate_variable_substitution_syntax(self) -> "WorkflowSchema":
        """Validate variable substitution syntax in all string values."""
        # Pattern: ${namespace.path.to.field} - captures full dotted path
        var_pattern = re.compile(r"\$\{([a-z_][a-z0-9_.]*)\}")

        block_ids = {block.id for block in self.blocks}
        input_names = set(self.inputs.keys())

        def validate_string_value(value: str, context: str) -> None:
            """Validate variable references in a string value."""
            matches = var_pattern.findall(value)
            for var_path in matches:
                parts = var_path.split(".")

                # ${inputs.field} - workflow input
                if parts[0] == "inputs":
                    if len(parts) < 2:
                        raise ValueError(
                            f"{context}: Invalid variable reference '${{{var_path}}}'. "
                            f"Input reference must include field name: ${{inputs.field_name}}"
                        )
                    field_name = parts[1]
                    if field_name not in input_names:
                        raise ValueError(
                            f"{context}: Invalid variable reference '${{{var_path}}}'. "
                            f"Input '{field_name}' does not exist. "
                            f"Available inputs: {sorted(input_names)}"
                        )

                # ${blocks.block_id.namespace.field} - block outputs/metadata
                # Also supports shortcut: ${blocks.block_id.field} -> outputs.field
                elif parts[0] == "blocks":
                    if len(parts) < 3:
                        raise ValueError(
                            f"{context}: Invalid variable reference '${{{var_path}}}'. "
                            f"Block reference must be: "
                            f"${{blocks.block_id.outputs.field}}, "
                            f"${{blocks.block_id.metadata.field}}, or "
                            f"${{blocks.block_id.field}} (shortcut for outputs)"
                        )
                    block_id = parts[1]

                    # Check if block exists
                    if block_id not in block_ids:
                        raise ValueError(
                            f"{context}: Invalid variable reference '${{{var_path}}}'. "
                            f"Block '{block_id}' does not exist. "
                            f"Available blocks: {sorted(block_ids)}"
                        )

                    # If 4+ parts, second level can be:
                    # - Standard namespaces: outputs, metadata, inputs
                    # - Custom output fields: any valid identifier
                    # Both are valid, so no validation needed beyond block existence
                    # If 3 parts, it's shortcut form ${blocks.block_id.field}
                    # This is valid and will be auto-expanded to outputs.field

                # ${metadata.field} - workflow metadata
                elif parts[0] == "metadata":
                    # Metadata references are valid (read-only workflow metadata)
                    pass

                # Unknown namespace
                else:
                    raise ValueError(
                        f"{context}: Invalid variable reference '${{{var_path}}}'. "
                        f"Unknown namespace '{parts[0]}'. "
                        f"Valid namespaces: 'inputs', 'blocks', 'metadata'"
                    )

        def check_dict_values(obj: Any, path: str) -> None:
            """Recursively check all string values in nested structures."""
            if isinstance(obj, str):
                validate_string_value(obj, path)
            elif isinstance(obj, dict):
                for key, value in obj.items():
                    check_dict_values(value, f"{path}.{key}")
            elif isinstance(obj, list):
                for idx, item in enumerate(obj):
                    check_dict_values(item, f"{path}[{idx}]")

        # Validate block inputs
        for block in self.blocks:
            check_dict_values(block.inputs, f"Block '{block.id}' inputs")

        # Validate outputs
        for output_name, output_value in self.outputs.items():
            if isinstance(output_value, str):
                validate_string_value(output_value, f"Output '{output_name}'")

        return self

    def to_workflow_definition(self) -> WorkflowDefinition:
        """
        Convert WorkflowSchema to WorkflowDefinition for executor.

        This creates the executor-compatible format from the validated YAML schema.
        Input declarations are converted to a simplified format for the executor.

        Returns:
            WorkflowDefinition instance ready for execution
        """
        blocks_data = [
            {
                "id": block.id,
                "type": block.type,
                "inputs": block.inputs,
                "depends_on": block.depends_on,
                "condition": block.condition,
            }
            for block in self.blocks
        ]

        # Convert WorkflowInputDeclaration to simple dict format for executor
        inputs_data = {
            name: {
                "type": decl.type.value,
                "description": decl.description,
                "default": decl.default,
                "required": decl.required,
            }
            for name, decl in self.inputs.items()
        }

        # Convert outputs to simple string mapping
        outputs_data = {}
        for name, output_value in self.outputs.items():
            if isinstance(output_value, str):
                outputs_data[name] = output_value
            elif isinstance(output_value, WorkflowOutputSchema):
                outputs_data[name] = output_value.value
            else:
                outputs_data[name] = str(output_value)

        return WorkflowDefinition(
            name=self.name,
            description=self.description,
            blocks=blocks_data,
            inputs=inputs_data,
            outputs=outputs_data,
        )

    @staticmethod
    def validate_yaml_dict(data: dict[str, Any]) -> Result["WorkflowSchema"]:
        """
        Validate YAML dictionary against schema with detailed error messages.

        This is the primary validation entry point for loaded YAML data.

        Args:
            data: Dictionary loaded from YAML file

        Returns:
            Result.success(WorkflowSchema) if valid
            Result.failure(error_message) with clear validation errors

        Example:
            import yaml

            with open("workflow.yaml") as f:
                data = yaml.safe_load(f)

            result = WorkflowSchema.validate_yaml_dict(data)
            if result.is_success:
                schema = result.value
                workflow_def = schema.to_workflow_definition()
            else:
                print(f"Validation failed: {result.error}")
        """
        try:
            schema = WorkflowSchema(**data)
            return Result.success(schema)
        except Exception as e:
            # Extract meaningful error from Pydantic ValidationError
            error_msg = str(e)
            if "validation error" in error_msg.lower():
                # Pydantic v2 provides detailed error messages
                return Result.failure(f"Workflow validation failed:\n{error_msg}")
            else:
                return Result.failure(f"Workflow validation failed: {error_msg}")
