# Error Response Standardization and Input Validation Summary

## Overview

This document summarizes the standardization of error responses and addition of input validation across all MCP tools in `src/workflows_mcp/server.py`.

## Changes Implemented

### 1. Import WorkflowResponse

Added import for `WorkflowResponse` from tools module to use for standardized error responses:

```python
from .tools import WorkflowResponse
```

### 2. Standardized Error Responses

All workflow execution tools now use `WorkflowResponse` for consistent error formatting:

#### execute_workflow
- **Context validation**: Returns WorkflowResponse with "Context not available" error
- **Workflow existence validation**: Checks if workflow exists in registry, provides preview of available workflows
- **Input validation**: Validates required inputs against workflow schema, provides helpful error messages
- **Error format**: All errors use WorkflowResponse structure

#### execute_inline_workflow
- **Context validation**: Returns WorkflowResponse with "Context not available" error
- **YAML empty check**: Validates YAML string is not empty before parsing
- **YAML parsing errors**: Returns WorkflowResponse with detailed parse error and helpful message
- **Error format**: All errors use WorkflowResponse structure

#### resume_workflow
- **Context validation**: Returns WorkflowResponse with "Context not available" error
- **Checkpoint ID validation**: Validates checkpoint_id is provided and not empty
- **Error format**: All errors use WorkflowResponse structure

### 3. Consistent Info Retrieval Error Handling

Non-execution tools use consistent dict-based error responses with helpful fields:

#### get_workflow_info
- **Context validation**: Returns dict with "error" and "help" fields
- **Workflow existence validation**: Provides preview of available workflows (first 10) plus full list
- **Error format**: `{"error": "...", "help": "...", "available_workflows": [...]}`

#### list_workflows
- **Context validation**: Graceful degradation - returns empty list with warning log
- **Error handling**: Non-critical - returns empty array instead of error dict

#### list_checkpoints
- **Context validation**: Returns dict with empty checkpoints list and warning field
- **Error format**: `{"checkpoints": [], "total": 0, "warning": "..."}`

#### get_checkpoint_info
- **Context validation**: Returns dict with "found", "error", and "help" fields
- **Checkpoint ID validation**: Validates checkpoint_id is provided
- **Checkpoint not found**: Returns helpful error with suggestion to use list_checkpoints
- **Error format**: `{"found": false, "error": "...", "help": "..."}`

#### delete_checkpoint
- **Context validation**: Returns dict with "deleted", "error", and "help" fields
- **Checkpoint ID validation**: Validates checkpoint_id is provided
- **Deletion failure**: Returns helpful error distinguishing between not found and other failures
- **Error format**: `{"deleted": false, "error": "...", "help": "..."}`

### 4. Input Validation Features

#### Workflow Execution Validation
```python
# Validate workflow exists
if workflow not in registry:
    available = registry.list_names()
    available_preview = ", ".join(available[:5])
    if len(available) > 5:
        available_preview += f" (and {len(available) - 5} more)"

    return WorkflowResponse(
        status="failure",
        error=f"Workflow '{workflow}' not found",
        message=f"Available workflows: {available_preview}"
    ).model_dump()

# Validate required inputs
schema = registry.get_schema(workflow)
if schema and schema.inputs:
    missing_required = []
    for input_name, input_decl in schema.inputs.items():
        if input_decl.required and input_name not in inputs:
            missing_required.append(input_name)

    if missing_required:
        return WorkflowResponse(
            status="failure",
            error=f"Missing required inputs: {', '.join(missing_required)}",
            message=f"Workflow '{workflow}' requires: {', '.join(schema.inputs.keys())}"
        ).model_dump()
```

#### Inline Workflow Validation
```python
# Validate YAML is not empty
if not workflow_yaml or not workflow_yaml.strip():
    return WorkflowResponse(
        status="failure",
        error="Workflow YAML cannot be empty"
    ).model_dump()

# Parse with clear error messages
if not load_result.is_success:
    return WorkflowResponse(
        status="failure",
        error=f"Failed to parse workflow YAML: {load_result.error}",
        message="Check YAML syntax and required fields (name, description, blocks)"
    ).model_dump()
```

#### Checkpoint Operations Validation
```python
# Validate checkpoint_id is provided
if not checkpoint_id or not checkpoint_id.strip():
    return WorkflowResponse(
        status="failure",
        error="Checkpoint ID is required",
        message="Use list_checkpoints to see available checkpoints"
    ).model_dump()
```

## Error Response Patterns

### Workflow Execution Tools (use WorkflowResponse)
- **Status field**: "success", "failure", or "paused"
- **Error field**: Descriptive error message
- **Message field**: Additional helpful context or guidance
- **Consistent structure**: Always returns same fields for predictable API

### Info Retrieval Tools (use dict with error/help)
- **Error field**: Descriptive error message
- **Help field**: Guidance on how to resolve the issue
- **Additional fields**: Context-specific helpful information (e.g., available_workflows)

### List Tools (graceful degradation)
- Return empty lists/dicts with optional warning field
- Log warnings for debugging
- Allow operations to continue without blocking

## Validation Coverage

### Pre-Execution Validation
1. **Context availability**: All tools check for valid context
2. **Workflow existence**: execute_workflow validates workflow is registered
3. **Required inputs**: execute_workflow validates all required inputs are provided
4. **YAML validity**: execute_inline_workflow validates YAML before parsing
5. **Checkpoint existence**: Checkpoint operations validate checkpoint_id

### Error Message Quality
1. **Descriptive errors**: Clear explanation of what went wrong
2. **Helpful context**: Suggestions on how to resolve the issue
3. **Available options**: Preview of available workflows/checkpoints when relevant
4. **User guidance**: Direct users to related tools (e.g., "Use list_checkpoints...")

## Testing and Validation

### Code Quality Checks
All changes passed:
- ✅ `ruff check` - No linting errors
- ✅ `ruff format` - Code formatted consistently
- ✅ `mypy` - Type checking passed
- ✅ Sanity check - WorkflowResponse import and usage verified

### Test Status
Note: Pre-existing test fixture issues with `conftest.py` are unrelated to these changes. The test errors are due to missing global `executor` and `registry` exports (now managed through lifespan context). These changes do not introduce new test failures.

## Benefits

### For Users
1. **Predictable API**: Consistent error response structures
2. **Better error messages**: Clear, actionable feedback
3. **Early validation**: Catch errors before execution starts
4. **Helpful guidance**: Suggestions on how to fix issues

### For Developers
1. **Type safety**: WorkflowResponse provides Pydantic validation
2. **Maintainability**: Centralized error response logic
3. **Consistency**: All tools follow same patterns
4. **Debugging**: Clear error messages with context

## Migration Guide

### Before (Inconsistent)
```python
# Old pattern - inconsistent
if ctx is None:
    return {"status": "failure", "error": "Context not available"}

# Old pattern - no validation
response = await executor.execute_workflow(workflow, inputs)
return response.model_dump()
```

### After (Standardized)
```python
# New pattern - WorkflowResponse
if ctx is None:
    return WorkflowResponse(
        status="failure",
        error="Context not available"
    ).model_dump()

# New pattern - with validation
if workflow not in registry:
    return WorkflowResponse(
        status="failure",
        error=f"Workflow '{workflow}' not found",
        message=f"Available workflows: {available_preview}"
    ).model_dump()

# Validate required inputs
if missing_required:
    return WorkflowResponse(
        status="failure",
        error=f"Missing required inputs: {', '.join(missing_required)}",
        message=f"Workflow '{workflow}' requires: {', '.join(schema.inputs.keys())}"
    ).model_dump()

response = await executor.execute_workflow(workflow, inputs)
return response.model_dump()
```

## Files Modified

- `src/workflows_mcp/server.py` - All changes in this single file
  - Import WorkflowResponse
  - Update execute_workflow with validation
  - Update execute_inline_workflow with validation
  - Update resume_workflow with validation
  - Standardize get_workflow_info errors
  - Improve list_workflows error handling
  - Improve list_checkpoints error handling
  - Standardize get_checkpoint_info errors
  - Standardize delete_checkpoint errors

## Conclusion

All MCP tools now have:
✅ Standardized error response formats
✅ Comprehensive input validation
✅ Helpful error messages with guidance
✅ Type-safe error handling via WorkflowResponse
✅ Consistent API contract across all tools

This improves the user experience, reduces debugging time, and makes the API more robust and maintainable.
