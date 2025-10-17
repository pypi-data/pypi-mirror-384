"""
Tests for variable resolution system.

Tests cover:
- Namespaced variable resolution (${inputs.var}, ${blocks.id.outputs.field})
- Security boundary (__internal__ namespace blocked)
- Recursive resolution in dicts and lists
- Missing variable error handling
- Complex nested structures
"""

import pytest

from workflows_mcp.engine.variables import VariableNotFoundError, VariableResolver


class TestVariableResolver:
    """Test cases for VariableResolver."""

    def test_resolve_simple_string_input(self):
        """Test resolving workflow input in string."""
        context = {"inputs": {"branch": "main"}}
        resolver = VariableResolver(context)

        result = resolver.resolve("Branch: ${inputs.branch}")
        assert result == "Branch: main"

    def test_resolve_block_output_field(self):
        """Test resolving block output field."""
        context = {"blocks": {"create_worktree": {"outputs": {"worktree_path": "/tmp/worktree"}}}}
        resolver = VariableResolver(context)

        result = resolver.resolve("Path: ${blocks.create_worktree.outputs.worktree_path}")
        assert result == "Path: /tmp/worktree"

    def test_resolve_multiple_variables(self):
        """Test resolving multiple variables in one string."""
        context = {
            "inputs": {
                "project": "my-project",
                "version": "1.0",
            }
        }
        resolver = VariableResolver(context)

        result = resolver.resolve("${inputs.project}-v${inputs.version}")
        assert result == "my-project-v1.0"

    def test_resolve_integer_value(self):
        """Test resolving integer variable."""
        context = {"blocks": {"run_tests": {"outputs": {"exit_code": 0}}}}
        resolver = VariableResolver(context)

        result = resolver.resolve("Exit code: ${blocks.run_tests.outputs.exit_code}")
        assert result == "Exit code: 0"

    def test_resolve_boolean_value(self):
        """Test resolving boolean variable."""
        context = {"blocks": {"run_tests": {"outputs": {"success": True}}}}
        resolver = VariableResolver(context)

        result = resolver.resolve("Success: ${blocks.run_tests.outputs.success}")
        assert result == "Success: True"

    def test_resolve_none_value(self):
        """Test resolving None variable."""
        context = {"inputs": {"optional_field": None}}
        resolver = VariableResolver(context)

        result = resolver.resolve("Value: ${inputs.optional_field}")
        assert result == "Value: "

    def test_resolve_dict_values(self):
        """Test recursive resolution in dictionaries."""
        context = {
            "inputs": {"base_path": "/project"},
            "blocks": {"create_worktree": {"outputs": {"name": "feature-123"}}},
        }
        resolver = VariableResolver(context)

        input_dict = {
            "path": "${inputs.base_path}/${blocks.create_worktree.outputs.name}",
            "config": {"name": "${blocks.create_worktree.outputs.name}"},
        }

        result = resolver.resolve(input_dict)
        assert result == {
            "path": "/project/feature-123",
            "config": {"name": "feature-123"},
        }

    def test_resolve_list_values(self):
        """Test recursive resolution in lists."""
        context = {"inputs": {"repo": "my-repo", "branch": "main"}}
        resolver = VariableResolver(context)

        input_list = ["${inputs.repo}", "${inputs.branch}", "fixed-value"]

        result = resolver.resolve(input_list)
        assert result == ["my-repo", "main", "fixed-value"]

    def test_resolve_nested_structures(self):
        """Test resolution in deeply nested structures."""
        context = {
            "inputs": {"project": "workflows", "version": "1.0"},
            "blocks": {"create_worktree": {"outputs": {"path": "/tmp/worktree"}}},
        }
        resolver = VariableResolver(context)

        input_data = {
            "metadata": {
                "name": "${inputs.project}",
                "version": "${inputs.version}",
                "paths": [
                    "${blocks.create_worktree.outputs.path}/src",
                    "${blocks.create_worktree.outputs.path}/tests",
                ],
            },
            "config": {"base": "${blocks.create_worktree.outputs.path}"},
        }

        result = resolver.resolve(input_data)
        assert result == {
            "metadata": {
                "name": "workflows",
                "version": "1.0",
                "paths": ["/tmp/worktree/src", "/tmp/worktree/tests"],
            },
            "config": {"base": "/tmp/worktree"},
        }

    def test_resolve_primitive_types_passthrough(self):
        """Test that primitive types pass through unchanged."""
        resolver = VariableResolver({})

        assert resolver.resolve(42) == 42
        assert resolver.resolve(3.14) == 3.14
        assert resolver.resolve(True) is True
        assert resolver.resolve(None) is None

    def test_resolve_no_variables(self):
        """Test string without variables passes through."""
        resolver = VariableResolver({})

        result = resolver.resolve("No variables here")
        assert result == "No variables here"

    def test_missing_variable_error(self):
        """Test error when variable not found in context."""
        context = {"inputs": {"existing": "value"}}
        resolver = VariableResolver(context)

        with pytest.raises(VariableNotFoundError) as exc_info:
            resolver.resolve("Missing: ${inputs.missing_var}")

        assert "inputs.missing_var" in str(exc_info.value)
        assert "existing" in str(exc_info.value)

    def test_missing_block_output_error(self):
        """Test error when block output field not found."""
        context = {"blocks": {"other_block": {"outputs": {"field": "value"}}}}
        resolver = VariableResolver(context)

        with pytest.raises(VariableNotFoundError) as exc_info:
            resolver.resolve("${blocks.missing_block.outputs.field}")

        assert "blocks.missing_block.outputs.field" in str(exc_info.value)

    def test_complex_variable_names(self):
        """Test variables with underscores and numbers."""
        context = {
            "inputs": {"input_var_1": "value1"},
            "blocks": {"block_2": {"outputs": {"output_field_3": "value2"}}},
        }
        resolver = VariableResolver(context)

        result = resolver.resolve(
            "${inputs.input_var_1} and ${blocks.block_2.outputs.output_field_3}"
        )
        assert result == "value1 and value2"

    def test_partial_variable_syntax(self):
        """Test that incomplete variable syntax is left unchanged."""
        resolver = VariableResolver({"inputs": {"var": "value"}})

        # Missing closing brace
        result = resolver.resolve("${inputs.var")
        assert result == "${inputs.var"

        # Missing opening brace
        result = resolver.resolve("inputs.var}")
        assert result == "inputs.var}"

    def test_empty_context(self):
        """Test resolver with empty context."""
        resolver = VariableResolver({})

        # Should work for non-variable strings
        assert resolver.resolve("plain text") == "plain text"
        assert resolver.resolve(42) == 42

        # Should fail for variables
        with pytest.raises(VariableNotFoundError):
            resolver.resolve("${inputs.nonexistent}")

    def test_resolve_with_mixed_content(self):
        """Test resolution with both variables and literals."""
        context = {
            "inputs": {"user": "alice", "action": "commit"},
            "blocks": {"repo": {"outputs": {"name": "my-repo"}}},
        }
        resolver = VariableResolver(context)

        result = resolver.resolve(
            "User ${inputs.user} performed ${inputs.action} on ${blocks.repo.outputs.name}"
        )
        assert result == "User alice performed commit on my-repo"

    def test_resolve_empty_string_value(self):
        """Test resolving variable with empty string value."""
        context = {"inputs": {"empty": ""}}
        resolver = VariableResolver(context)

        result = resolver.resolve("Value: [${inputs.empty}]")
        assert result == "Value: []"

    def test_resolve_list_and_dict_in_string(self):
        """Test resolving complex types in string context."""
        context = {"inputs": {"my_list": [1, 2, 3], "my_dict": {"key": "value"}}}
        resolver = VariableResolver(context)

        result = resolver.resolve("List: ${inputs.my_list}, Dict: ${inputs.my_dict}")
        assert "List: [1, 2, 3]" in result
        assert "Dict: {'key': 'value'}" in result

    def test_internal_namespace_blocked(self):
        """Test that __internal__ namespace cannot be accessed."""
        context = {"inputs": {"param": "value"}, "__internal__": {"executor": "secret"}}

        resolver = VariableResolver(context)

        with pytest.raises(VariableNotFoundError) as exc:
            resolver.resolve("${__internal__.executor}")

        assert "Access to internal namespace is not allowed" in str(exc.value)

    def test_internal_namespace_blocked_nested(self):
        """Test that nested __internal__ access is blocked."""
        context = {
            "blocks": {"test": {"outputs": {"result": "ok"}, "__internal__": {"state": "secret"}}}
        }

        resolver = VariableResolver(context)

        with pytest.raises(VariableNotFoundError) as exc:
            resolver.resolve("${blocks.test.__internal__.state}")

        assert "Access to internal namespace is not allowed" in str(exc.value)
