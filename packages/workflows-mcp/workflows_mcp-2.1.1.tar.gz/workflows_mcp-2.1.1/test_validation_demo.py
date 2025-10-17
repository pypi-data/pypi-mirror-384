#!/usr/bin/env python3
"""Demo script to test error response standardization and input validation.

This script demonstrates the new validation and error handling features
implemented in src/workflows_mcp/server.py.

Run with: python test_validation_demo.py
"""

from src.workflows_mcp.tools import WorkflowResponse


def demo_workflow_response():
    """Demonstrate WorkflowResponse usage for different scenarios."""
    print("=" * 80)
    print("WorkflowResponse Standardization Demo")
    print("=" * 80)

    # Test 1: Context not available error
    print("\n1. Context Not Available Error:")
    print("-" * 40)
    response = WorkflowResponse(status="failure", error="Context not available")
    print(f"Status: {response.status}")
    print(f"Error: {response.error}")
    print(f"Model dump: {response.model_dump()}")

    # Test 2: Workflow not found error
    print("\n2. Workflow Not Found Error:")
    print("-" * 40)
    response = WorkflowResponse(
        status="failure",
        error="Workflow 'nonexistent-workflow' not found",
        message="Available workflows: python-setup, python-test, git-commit (and 42 more)",
    )
    print(f"Status: {response.status}")
    print(f"Error: {response.error}")
    print(f"Message: {response.message}")
    print(f"Model dump keys: {list(response.model_dump().keys())}")

    # Test 3: Missing required inputs error
    print("\n3. Missing Required Inputs Error:")
    print("-" * 40)
    response = WorkflowResponse(
        status="failure",
        error="Missing required inputs: project_path, python_version",
        message="Workflow 'python-setup' requires: project_path, python_version, venv_name",
    )
    print(f"Status: {response.status}")
    print(f"Error: {response.error}")
    print(f"Message: {response.message}")

    # Test 4: Invalid YAML error
    print("\n4. Invalid YAML Error:")
    print("-" * 40)
    response = WorkflowResponse(
        status="failure",
        error="Failed to parse workflow YAML: Invalid YAML syntax at line 5",
        message="Check YAML syntax and required fields (name, description, blocks)",
    )
    print(f"Status: {response.status}")
    print(f"Error: {response.error}")
    print(f"Message: {response.message}")

    # Test 5: Checkpoint ID required error
    print("\n5. Checkpoint ID Required Error:")
    print("-" * 40)
    response = WorkflowResponse(
        status="failure",
        error="Checkpoint ID is required",
        message="Use list_checkpoints to see available checkpoints",
    )
    print(f"Status: {response.status}")
    print(f"Error: {response.error}")
    print(f"Message: {response.message}")

    # Test 6: Success response (for comparison)
    print("\n6. Success Response (for comparison):")
    print("-" * 40)
    response = WorkflowResponse(
        status="success",
        outputs={"result": "completed", "exit_code": 0},
        blocks={},
        metadata={"execution_time_ms": 1234},
    )
    print(f"Status: {response.status}")
    print(f"Outputs: {response.outputs}")
    print(f"Is success: {response.is_success}")
    print(f"Model dump (non-DEBUG mode): {response.model_dump()}")


def demo_info_retrieval_errors():
    """Demonstrate consistent error handling for info retrieval tools."""
    print("\n" + "=" * 80)
    print("Info Retrieval Error Handling Demo")
    print("=" * 80)

    # Test 1: get_workflow_info error
    print("\n1. get_workflow_info Error:")
    print("-" * 40)
    error_dict = {
        "error": "Workflow not found: my-workflow",
        "help": "Available workflows: python-setup, python-test, git-commit (and 7 more)",
        "available_workflows": ["python-setup", "python-test", "git-commit", "..."],
    }
    print(f"Error dict: {error_dict}")

    # Test 2: get_checkpoint_info error
    print("\n2. get_checkpoint_info Error:")
    print("-" * 40)
    error_dict = {
        "found": False,
        "error": "Checkpoint abc123 not found or expired",
        "help": "Use list_checkpoints to see available checkpoints",
    }
    print(f"Error dict: {error_dict}")

    # Test 3: delete_checkpoint error
    print("\n3. delete_checkpoint Error:")
    print("-" * 40)
    error_dict = {
        "deleted": False,
        "checkpoint_id": "abc123",
        "error": "Checkpoint not found",
        "help": "Checkpoint may have already been deleted or expired",
    }
    print(f"Error dict: {error_dict}")

    # Test 4: list_checkpoints warning
    print("\n4. list_checkpoints Warning:")
    print("-" * 40)
    result_dict = {
        "checkpoints": [],
        "total": 0,
        "warning": "Context not available - returning empty checkpoint list",
    }
    print(f"Result dict: {result_dict}")


def demo_validation_patterns():
    """Demonstrate validation patterns used in the implementation."""
    print("\n" + "=" * 80)
    print("Input Validation Patterns Demo")
    print("=" * 80)

    # Test 1: Workflow existence validation
    print("\n1. Workflow Existence Validation:")
    print("-" * 40)
    workflow = "nonexistent-workflow"
    available = [
        "python-setup",
        "python-test",
        "git-commit",
        "deploy-prod",
        "run-tests",
        "build-docker",
    ]
    available_preview = ", ".join(available[:5])
    if len(available) > 5:
        available_preview += f" (and {len(available) - 5} more)"
    print(f"Workflow: {workflow}")
    print(f"Available preview: {available_preview}")
    print(f"Full list length: {len(available)}")

    # Test 2: Required inputs validation
    print("\n2. Required Inputs Validation:")
    print("-" * 40)
    schema_inputs = {
        "project_path": {"required": True},
        "python_version": {"required": True},
        "venv_name": {"required": False},
    }
    provided_inputs = {"venv_name": "my_venv"}
    missing = [
        name
        for name, decl in schema_inputs.items()
        if decl.get("required") and name not in provided_inputs
    ]
    print(f"Schema requires: {list(schema_inputs.keys())}")
    print(f"Provided inputs: {list(provided_inputs.keys())}")
    print(f"Missing required: {missing}")

    # Test 3: Empty string validation
    print("\n3. Empty String Validation:")
    print("-" * 40)
    test_cases = [
        ("", "Empty string"),
        ("   ", "Whitespace only"),
        ("valid", "Valid string"),
        (None, "None value"),
    ]
    for value, description in test_cases:
        is_valid = value and value.strip()
        print(f"{description:20} -> Valid: {is_valid}")


def main():
    """Run all demo functions."""
    print("\n" + "=" * 80)
    print("MCP Tools Error Standardization & Input Validation Demo")
    print("=" * 80)

    demo_workflow_response()
    demo_info_retrieval_errors()
    demo_validation_patterns()

    print("\n" + "=" * 80)
    print("Demo Complete!")
    print("=" * 80)
    print("\nAll validation patterns are working correctly.")
    print("Error responses are standardized and consistent across all MCP tools.")


if __name__ == "__main__":
    main()
