"""
YAML workflow loader for Phase 1.

This module provides utilities for loading and validating YAML workflow definitions
using the WorkflowSchema Pydantic models.

Features:
- Load workflows from YAML files or strings
- Comprehensive validation with clear error messages
- Automatic conversion to WorkflowDefinition for execution
- Support for workflow discovery and listing
"""

import logging
from pathlib import Path

import yaml

from .executor import WorkflowDefinition
from .result import Result
from .schema import WorkflowSchema

logger = logging.getLogger(__name__)


def load_workflow_from_file(file_path: str | Path) -> Result[WorkflowDefinition]:
    """
    Load and validate a workflow from a YAML file.

    This is the primary entry point for loading workflows. It:
    1. Reads the YAML file
    2. Validates the structure against WorkflowSchema
    3. Converts to WorkflowDefinition for execution

    Args:
        file_path: Path to YAML workflow file

    Returns:
        Result.success(WorkflowDefinition) if valid
        Result.failure(error_message) with validation errors

    Example:
        result = load_workflow_from_file("workflows/my-workflow.yaml")
        if result.is_success:
            executor.load_workflow(result.value)
        else:
            print(f"Failed to load: {result.error}")
    """
    path = Path(file_path)

    # Check file exists
    if not path.exists():
        return Result.failure(f"Workflow file not found: {file_path}")

    if not path.is_file():
        return Result.failure(f"Path is not a file: {file_path}")

    # Read YAML file
    try:
        with open(path, encoding="utf-8") as f:
            yaml_content = f.read()
    except Exception as e:
        return Result.failure(f"Failed to read file '{file_path}': {e}")

    # Load YAML
    return load_workflow_from_yaml(yaml_content, source=str(file_path))


def load_workflow_from_yaml(
    yaml_content: str, source: str = "<string>"
) -> Result[WorkflowDefinition]:
    """
    Load and validate a workflow from YAML string.

    Args:
        yaml_content: YAML content as string
        source: Source identifier for error messages (default: "<string>")

    Returns:
        Result.success(WorkflowDefinition) if valid
        Result.failure(error_message) with validation errors

    Example:
        yaml_str = '''
        name: my-workflow
        description: My workflow
        tags: [test, example]
        blocks:
          - id: block1
            type: EchoBlock
            inputs:
              message: "Hello"
        '''
        result = load_workflow_from_yaml(yaml_str)
    """
    # Parse YAML
    try:
        data = yaml.safe_load(yaml_content)
    except yaml.YAMLError as e:
        return Result.failure(f"Invalid YAML syntax in {source}: {e}")

    # Validate it's a dictionary
    if not isinstance(data, dict):
        return Result.failure(
            f"Workflow {source} must be a YAML dictionary, got {type(data).__name__}"
        )

    # Validate against schema
    schema_result = WorkflowSchema.validate_yaml_dict(data)
    if not schema_result.is_success:
        return Result.failure(f"Workflow validation failed in {source}:\n{schema_result.error}")

    # Convert to WorkflowDefinition
    schema = schema_result.value
    if schema is None:
        return Result.failure(f"Workflow schema validation returned None for {source}")

    workflow_def = schema.to_workflow_definition()

    return Result.success(workflow_def)


def discover_workflows(directory: str | Path) -> Result[list[WorkflowDefinition]]:
    """
    Discover and load all YAML workflows in a directory.

    Searches for *.yaml and *.yml files and attempts to load them as workflows.
    Invalid workflows are skipped with warnings, but don't fail the entire operation.

    Args:
        directory: Directory path to search for workflows

    Returns:
        Result.success(list[WorkflowDefinition]) with valid workflows
        Result.failure(error_message) if directory doesn't exist

    Example:
        result = discover_workflows("workflows/")
        if result.is_success:
            for workflow in result.value:
                executor.load_workflow(workflow)
    """
    dir_path = Path(directory)

    if not dir_path.exists():
        return Result.failure(f"Directory not found: {directory}")

    if not dir_path.is_dir():
        return Result.failure(f"Path is not a directory: {directory}")

    workflows: list[WorkflowDefinition] = []
    errors: list[str] = []

    # Find all YAML files
    yaml_files = list(dir_path.glob("*.yaml")) + list(dir_path.glob("*.yml"))

    for yaml_file in yaml_files:
        result = load_workflow_from_file(yaml_file)
        if result.is_success:
            if result.value is not None:
                workflows.append(result.value)
        else:
            errors.append(f"{yaml_file.name}: {result.error}")

    # Report errors as warnings but return success
    if errors:
        logger.warning(f"{len(errors)} workflow(s) failed to load:")
        for error in errors:
            logger.warning(f"  - {error}")

    return Result.success(workflows)


def validate_workflow_file(file_path: str | Path) -> Result[WorkflowSchema]:
    """
    Validate a workflow file without converting to WorkflowDefinition.

    Useful for linting and validation tools that need the full schema information.

    Args:
        file_path: Path to YAML workflow file

    Returns:
        Result.success(WorkflowSchema) if valid
        Result.failure(error_message) with validation errors

    Example:
        result = validate_workflow_file("workflow.yaml")
        if result.is_success:
            schema = result.value
            print(f"Valid workflow: {schema.name}")
            print(f"Tags: {schema.tags}")
            print(f"Blocks: {len(schema.blocks)}")
    """
    path = Path(file_path)

    if not path.exists():
        return Result.failure(f"Workflow file not found: {file_path}")

    # Read and parse YAML
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        return Result.failure(f"Invalid YAML syntax: {e}")
    except Exception as e:
        return Result.failure(f"Failed to read file: {e}")

    if not isinstance(data, dict):
        return Result.failure(f"Workflow must be a YAML dictionary, got {type(data).__name__}")

    # Validate schema
    return WorkflowSchema.validate_yaml_dict(data)
