"""MCP tool implementations for workflow execution.

This module contains all MCP tool function implementations that expose
workflow execution functionality to Claude Code via the MCP protocol.

Following official Anthropic MCP Python SDK patterns:
- Tool functions decorated with @mcp.tool()
- Type hints for automatic schema generation
- Async functions for all tools
- Clear docstrings (become tool descriptions)
"""

from datetime import datetime
from typing import Any

from .context import AppContextType
from .engine import WorkflowResponse, load_workflow_from_yaml
from .server import mcp

# =============================================================================
# MCP Tools (following official SDK decorator pattern)
# =============================================================================


@mcp.tool()
async def execute_workflow(
    workflow: str,
    inputs: dict[str, Any] | None = None,
    *,
    ctx: AppContextType,
) -> WorkflowResponse:
    """Execute a DAG-based workflow with inputs.

    Supports git operations, bash commands, templates, and workflow composition.

    Output verbosity is controlled by WORKFLOWS_LOG_LEVEL environment variable:
    - Non-DEBUG (default): Returns empty blocks/metadata (minimal)
    - DEBUG: Returns full blocks/metadata (detailed)

    Args:
        workflow: Workflow name (e.g., 'sequential-echo', 'parallel-echo')
        inputs: Runtime inputs as key-value pairs for block variable substitution
        ctx: Server context for accessing shared resources

    Returns:
        WorkflowResponse with consistent structure:
        {"status": "success", "outputs": {...}, "blocks": {...}, "metadata": {...}}
        - blocks/metadata are empty dicts when WORKFLOWS_LOG_LEVEL != DEBUG
        - blocks/metadata are fully populated when WORKFLOWS_LOG_LEVEL = DEBUG
    """
    # Validate context availability
    if ctx is None:
        return WorkflowResponse(
            status="failure",
            error="Server context not available. Tool requires server context to access resources.",
        )

    # Access shared resources from lifespan context
    app_ctx = ctx.request_context.lifespan_context
    executor = app_ctx.executor
    registry = app_ctx.registry

    # Validate workflow exists
    if workflow not in registry:
        return WorkflowResponse(
            status="failure",
            error=(
                f"Workflow '{workflow}' not found. "
                "Use list_workflows() to see all available workflows"
            ),
            outputs={"available_workflows": registry.list_names()},
        )

    # Execute workflow - executor returns WorkflowResponse directly
    response = await executor.execute_workflow(workflow, inputs)
    return response


@mcp.tool()
async def execute_inline_workflow(
    workflow_yaml: str,
    inputs: dict[str, Any] | None = None,
    *,
    ctx: AppContextType,
) -> WorkflowResponse:
    """Execute a workflow provided as YAML string without registering it.

    Enables dynamic workflow execution without file system modifications.
    Useful for ad-hoc workflows or tests.

    Output verbosity is controlled by WORKFLOWS_LOG_LEVEL environment variable:
    - Non-DEBUG (default): Returns empty blocks/metadata (minimal)
    - DEBUG: Returns full blocks/metadata (detailed)

    Args:
        workflow_yaml: Complete workflow definition as YAML string including
                      name, description, blocks, etc.
        inputs: Runtime inputs as key-value pairs for block variable substitution
        ctx: Server context for accessing shared resources

    Returns:
        WorkflowResponse with consistent structure on success:
        {"status": "success", "outputs": {...}, "blocks": {...}, "metadata": {...}}
        - blocks/metadata are empty dicts when WORKFLOWS_LOG_LEVEL != DEBUG
        - blocks/metadata are fully populated when WORKFLOWS_LOG_LEVEL = DEBUG

        On failure: {"status": "failure", "error": "..."}
        On pause: {"status": "paused", "checkpoint_id": "...", "prompt": "...", "message": "..."}

    Example:
        execute_inline_workflow(
            workflow_yaml='''
            name: rust-quality-check
            description: Quality checks for Rust projects
            tags: [rust, quality, linting]

            inputs:
              source_path:
                type: string
                default: "src/"

            blocks:
              - id: lint
                type: Shell
                inputs:
                  command: cargo clippy -- -D warnings
                  working_dir: "${source_path}"

              - id: format_check
                type: Shell
                inputs:
                  command: cargo fmt -- --check
                depends_on: [lint]

            outputs:
              linting_passed: "${lint.success}"
              formatting_passed: "${format_check.success}"
            ''',
            inputs={"source_path": "/path/to/rust/project"}
        )
    """
    # Validate context availability
    if ctx is None:
        return WorkflowResponse(
            status="failure",
            error="Server context not available. Tool requires server context to access resources.",
        )

    # Access shared resources from lifespan context
    app_ctx = ctx.request_context.lifespan_context
    executor = app_ctx.executor

    # Parse YAML string to WorkflowDefinition
    load_result = load_workflow_from_yaml(workflow_yaml, source="<inline-workflow>")

    if not load_result.is_success:
        return WorkflowResponse(
            status="failure",
            error=f"Failed to parse workflow YAML: {load_result.error}",
        )

    workflow_def = load_result.value
    if workflow_def is None:
        return WorkflowResponse(
            status="failure",
            error="Workflow definition parsing returned None",
        )

    # Temporarily load workflow into executor
    executor.load_workflow(workflow_def)

    # Execute workflow - executor returns WorkflowResponse directly
    response = await executor.execute_workflow(workflow_def.name, inputs)
    return response


@mcp.tool()
async def list_workflows(
    tags: list[str] = [],
    *,
    ctx: AppContextType,
) -> list[str]:
    """List all available workflows, optionally filtered by tags.

    Args:
        tags: Optional list of tags to filter workflows.
              Workflows matching ALL tags are returned (AND logic).
        ctx: Server context for accessing shared resources

    Returns:
        List of workflow names (strings).
        Use get_workflow_info(name) to get details about a specific workflow.
    """
    # Access shared resources from lifespan context
    app_ctx = ctx.request_context.lifespan_context
    registry = app_ctx.registry

    return registry.list_names(tags=tags)


@mcp.tool()
async def get_workflow_info(
    workflow: str,
    *,
    ctx: AppContextType,
) -> dict[str, Any]:
    """Get detailed information about a specific workflow.

    Retrieve comprehensive metadata about a workflow including block structure and dependencies.

    Args:
        workflow: Workflow name/identifier to retrieve information about
        ctx: Server context for accessing shared resources

    Returns:
        Dictionary with workflow metadata: name, description, version, tags, blocks, etc.
        Returns error dict if workflow not found.
    """
    # Access shared resources from lifespan context
    app_ctx = ctx.request_context.lifespan_context
    registry = app_ctx.registry

    # Get workflow from registry
    if workflow not in registry:
        return {
            "error": f"Workflow not found: {workflow}",
            "available_workflows": registry.list_names(),
        }

    # Get metadata from registry
    metadata = registry.get_workflow_metadata(workflow)

    # Get workflow definition for block details
    workflow_def = registry.get(workflow)

    # Get schema if available for input/output information
    schema = registry.get_schema(workflow)

    # Build comprehensive info dictionary
    info: dict[str, Any] = {
        "name": metadata["name"],
        "description": metadata["description"],
        "version": metadata.get("version", "1.0"),
        "total_blocks": len(workflow_def.blocks),
        "blocks": [
            {
                "id": block["id"],
                "type": block["type"],
                "depends_on": block.get("depends_on", []),
            }
            for block in workflow_def.blocks
        ],
    }

    # Add optional metadata fields
    if "author" in metadata:
        info["author"] = metadata["author"]
    if "tags" in metadata:
        info["tags"] = metadata["tags"]

    # Add input/output schema if available
    if schema:
        # Convert input declarations to simple type mapping
        if schema.inputs:
            info["inputs"] = {
                name: {"type": decl.type.value, "description": decl.description}
                for name, decl in schema.inputs.items()
            }

        # Add output mappings if available
        if schema.outputs:
            info["outputs"] = schema.outputs

    return info


@mcp.tool()
async def get_workflow_schema() -> dict[str, Any]:
    """Get complete JSON Schema for workflow validation.

    Returns the auto-generated JSON Schema that describes the structure of
    workflow YAML files, including all registered block types and their inputs.

    This schema can be used for:
    - Pre-execution validation
    - Editor autocomplete (VS Code YAML extension)
    - Documentation generation
    - Client-side validation

    Returns:
        Complete JSON Schema for workflow definitions
    """
    # Schema can be generated from EXECUTOR_REGISTRY without context
    from .engine import EXECUTOR_REGISTRY

    # Use registry's schema generation method
    schema = EXECUTOR_REGISTRY.generate_workflow_schema()
    return schema


@mcp.tool()
async def validate_workflow_yaml(
    yaml_content: str,
) -> dict[str, Any]:
    """Validate workflow YAML against schema before execution.

    Performs comprehensive validation including:
    - YAML syntax validation
    - Schema compliance (structure, required fields)
    - Block type validation (registered executors)
    - Input schema validation (per block type)

    Args:
        yaml_content: YAML workflow definition as string

    Returns:
        Validation result with errors (if any)
        {
            "valid": bool,
            "errors": list[str],
            "warnings": list[str],
            "block_types_used": list[str]
        }
    """
    # Validation works without context

    # Parse workflow YAML
    load_result = load_workflow_from_yaml(yaml_content, source="<validation>")

    if not load_result.is_success:
        return {
            "valid": False,
            "errors": [f"YAML parsing error: {load_result.error}"],
            "warnings": [],
            "block_types_used": [],
        }

    workflow_def = load_result.value
    if workflow_def is None:
        return {
            "valid": False,
            "errors": ["Workflow definition parsing returned None"],
            "warnings": [],
            "block_types_used": [],
        }

    # Extract block types used
    block_types_used = list({block["type"] for block in workflow_def.blocks})

    # Validate block types against executor registry
    from .engine import EXECUTOR_REGISTRY

    errors: list[str] = []
    warnings: list[str] = []

    registered_types = EXECUTOR_REGISTRY.list_types()

    for block in workflow_def.blocks:
        block_type = block["type"]
        if block_type not in registered_types:
            errors.append(f"Unknown block type '{block_type}' in block '{block['id']}'")

    # If no errors, workflow is valid
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "block_types_used": block_types_used,
    }


# =============================================================================
# Checkpoint Management Tools
# =============================================================================


@mcp.tool()
async def resume_workflow(
    checkpoint_id: str,
    llm_response: str = "",
    *,
    ctx: AppContextType,
) -> WorkflowResponse:
    """Resume a paused or checkpointed workflow.

    Use this to continue a workflow that was paused for interactive input,
    or to restart a workflow from a crash recovery checkpoint.

    Output verbosity is controlled by WORKFLOWS_LOG_LEVEL environment variable:
    - Non-DEBUG (default): Returns empty blocks/metadata (minimal)
    - DEBUG: Returns full blocks/metadata (detailed)

    Args:
        checkpoint_id: Checkpoint token from pause or list_checkpoints
        llm_response: Your response to the pause prompt (required for paused workflows)
        ctx: Server context for accessing shared resources

    Returns:
        WorkflowResponse with consistent structure (same format as execute_workflow):
        {"status": "success", "outputs": {...}, "blocks": {...}, "metadata": {...}}
        - blocks/metadata are empty dicts when WORKFLOWS_LOG_LEVEL != DEBUG
        - blocks/metadata are fully populated when WORKFLOWS_LOG_LEVEL = DEBUG

    Example:
        # Resume paused workflow with confirmation
        resume_workflow(
            checkpoint_id="pause_abc123",
            llm_response="yes"
        )
    """
    # Access shared resources from lifespan context
    app_ctx = ctx.request_context.lifespan_context
    executor = app_ctx.executor

    # Resume workflow - executor returns WorkflowResponse directly
    response = await executor.resume_workflow(checkpoint_id, llm_response)
    return response


@mcp.tool()
async def list_checkpoints(
    workflow_name: str = "",
    *,
    ctx: AppContextType,
) -> dict[str, Any]:
    """List available workflow checkpoints.

    Shows all checkpoints, including both automatic checkpoints (for crash recovery)
    and pause checkpoints (for interactive workflows).

    Args:
        workflow_name: Filter by workflow name (empty = all workflows)
        ctx: Server context for accessing shared resources

    Returns:
        List of checkpoint metadata with creation time, pause status, etc.

    Example:
        list_checkpoints(workflow_name="python-ci-pipeline")
    """
    # Access shared resources from lifespan context
    app_ctx = ctx.request_context.lifespan_context
    executor = app_ctx.executor

    filter_name = workflow_name if workflow_name else None
    checkpoints = await executor.checkpoint_store.list_checkpoints(filter_name)

    return {
        "checkpoints": [
            {
                "checkpoint_id": c.checkpoint_id,
                "workflow": c.workflow_name,
                "created_at": c.created_at,
                "created_at_iso": datetime.fromtimestamp(c.created_at).isoformat(),
                "is_paused": c.paused_block_id is not None,
                "pause_prompt": c.pause_prompt,
                "type": "pause" if c.paused_block_id is not None else "automatic",
            }
            for c in checkpoints
        ],
        "total": len(checkpoints),
    }


@mcp.tool()
async def get_checkpoint_info(
    checkpoint_id: str,
    *,
    ctx: AppContextType,
) -> dict[str, Any]:
    """Get detailed information about a specific checkpoint.

    Useful for inspecting checkpoint state before resuming.

    Args:
        checkpoint_id: Checkpoint token
        ctx: Server context for accessing shared resources

    Returns:
        Detailed checkpoint information
    """
    # Access shared resources from lifespan context
    app_ctx = ctx.request_context.lifespan_context
    executor = app_ctx.executor

    state = await executor.checkpoint_store.load_checkpoint(checkpoint_id)
    if state is None:
        return {"found": False, "error": f"Checkpoint {checkpoint_id} not found or expired"}

    # Calculate progress percentage
    total_blocks = sum(len(wave) for wave in state.execution_waves)
    if total_blocks > 0:
        progress_percentage = len(state.completed_blocks) / total_blocks * 100
    else:
        progress_percentage = 0

    return {
        "found": True,
        "checkpoint_id": state.checkpoint_id,
        "workflow_name": state.workflow_name,
        "created_at": state.created_at,
        "created_at_iso": datetime.fromtimestamp(state.created_at).isoformat(),
        "is_paused": state.paused_block_id is not None,
        "paused_block_id": state.paused_block_id,
        "pause_prompt": state.pause_prompt,
        "completed_blocks": state.completed_blocks,
        "current_wave": state.current_wave_index,
        "total_waves": len(state.execution_waves),
        "progress_percentage": round(progress_percentage, 1),
    }


@mcp.tool()
async def delete_checkpoint(
    checkpoint_id: str,
    *,
    ctx: AppContextType,
) -> dict[str, Any]:
    """Delete a checkpoint.

    Useful for cleaning up paused workflows that are no longer needed.

    Args:
        checkpoint_id: Checkpoint token to delete
        ctx: Server context for accessing shared resources

    Returns:
        Deletion status
    """
    # Access shared resources from lifespan context
    app_ctx = ctx.request_context.lifespan_context
    executor = app_ctx.executor

    deleted = await executor.checkpoint_store.delete_checkpoint(checkpoint_id)

    return {
        "deleted": deleted,
        "checkpoint_id": checkpoint_id,
        "message": "Checkpoint deleted successfully" if deleted else "Checkpoint not found",
    }


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Response model (for executor imports)
    "WorkflowResponse",
    # Tool functions (all MCP tools)
    "execute_workflow",
    "execute_inline_workflow",
    "list_workflows",
    "get_workflow_info",
    "get_workflow_schema",
    "validate_workflow_yaml",
    "resume_workflow",
    "list_checkpoints",
    "get_checkpoint_info",
    "delete_checkpoint",
]
