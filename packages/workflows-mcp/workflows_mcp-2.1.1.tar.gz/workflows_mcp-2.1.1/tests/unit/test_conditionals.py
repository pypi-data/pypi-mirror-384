"""
Tests for conditional execution system.

Tests cover:
- Boolean expression evaluation
- Comparison operators (==, !=, >, <, >=, <=)
- Boolean operators (and, or, not)
- Membership operator (in)
- Variable resolution in conditions
- Error handling for invalid expressions
"""

import pytest

from workflows_mcp.engine.variables import (
    ConditionEvaluator,
    InvalidConditionError,
)


class TestConditionEvaluator:
    """Test cases for ConditionEvaluator."""

    def test_simple_equality_true(self):
        """Test simple equality condition that is true."""
        evaluator = ConditionEvaluator()
        context = {"run_tests": {"outputs": {"exit_code": 0}}}

        result = evaluator.evaluate("${run_tests.outputs.exit_code} == 0", context)
        assert result is True

    def test_simple_equality_false(self):
        """Test simple equality condition that is false."""
        evaluator = ConditionEvaluator()
        context = {"run_tests": {"outputs": {"exit_code": 1}}}

        result = evaluator.evaluate("${run_tests.outputs.exit_code} == 0", context)
        assert result is False

    def test_not_equal(self):
        """Test not equal operator."""
        evaluator = ConditionEvaluator()
        context = {"status": "failed"}

        result = evaluator.evaluate("${status} != 'success'", context)
        assert result is True

    def test_greater_than(self):
        """Test greater than operator."""
        evaluator = ConditionEvaluator()
        context = {"coverage": 85}

        result = evaluator.evaluate("${coverage} > 80", context)
        assert result is True

    def test_greater_than_or_equal(self):
        """Test greater than or equal operator."""
        evaluator = ConditionEvaluator()
        context = {"score": 80}

        assert evaluator.evaluate("${score} >= 80", context) is True
        assert evaluator.evaluate("${score} >= 81", context) is False

    def test_less_than(self):
        """Test less than operator."""
        evaluator = ConditionEvaluator()
        context = {"errors": 5}

        result = evaluator.evaluate("${errors} < 10", context)
        assert result is True

    def test_less_than_or_equal(self):
        """Test less than or equal operator."""
        evaluator = ConditionEvaluator()
        context = {"warnings": 3}

        assert evaluator.evaluate("${warnings} <= 3", context) is True
        assert evaluator.evaluate("${warnings} <= 2", context) is False

    def test_boolean_and_true(self):
        """Test boolean AND with both true."""
        evaluator = ConditionEvaluator()
        context = {
            "run_tests": {"outputs": {"exit_code": 0}},
            "coverage": 85,
        }

        result = evaluator.evaluate(
            "${run_tests.outputs.exit_code} == 0 and ${coverage} >= 80", context
        )
        assert result is True

    def test_boolean_and_false(self):
        """Test boolean AND with one false."""
        evaluator = ConditionEvaluator()
        context = {
            "run_tests": {"outputs": {"exit_code": 0}},
            "coverage": 75,
        }

        result = evaluator.evaluate(
            "${run_tests.outputs.exit_code} == 0 and ${coverage} >= 80", context
        )
        assert result is False

    def test_boolean_or_true(self):
        """Test boolean OR with one true."""
        evaluator = ConditionEvaluator()
        context = {
            "run_tests": {"outputs": {"exit_code": 1}},
            "force_deploy": True,
        }

        result = evaluator.evaluate(
            "${run_tests.outputs.exit_code} == 0 or ${force_deploy} == True", context
        )
        assert result is True

    def test_boolean_or_false(self):
        """Test boolean OR with both false."""
        evaluator = ConditionEvaluator()
        context = {
            "run_tests": {"outputs": {"exit_code": 1}},
            "force_deploy": False,
        }

        result = evaluator.evaluate(
            "${run_tests.outputs.exit_code} == 0 or ${force_deploy} == True", context
        )
        assert result is False

    def test_boolean_not(self):
        """Test boolean NOT operator."""
        evaluator = ConditionEvaluator()
        context = {"has_errors": False}

        result = evaluator.evaluate("not ${has_errors}", context)
        assert result is True

    def test_membership_in(self):
        """Test membership 'in' operator."""
        evaluator = ConditionEvaluator()
        context = {"status": "success"}

        result = evaluator.evaluate("${status} in ['success', 'passed']", context)
        assert result is True

    def test_membership_not_in(self):
        """Test membership 'not in' operator."""
        evaluator = ConditionEvaluator()
        context = {"status": "failed"}

        result = evaluator.evaluate("${status} not in ['success', 'passed']", context)
        assert result is True

    def test_complex_expression(self):
        """Test complex condition with multiple operators."""
        evaluator = ConditionEvaluator()
        context = {
            "run_tests": {"outputs": {"exit_code": 0}},
            "coverage": 85,
            "has_warnings": False,
        }

        result = evaluator.evaluate(
            "${run_tests.outputs.exit_code} == 0 and ${coverage} >= 80 and not ${has_warnings}",
            context,
        )
        assert result is True

    def test_string_comparison(self):
        """Test string comparison."""
        evaluator = ConditionEvaluator()
        context = {"branch": "main"}

        assert evaluator.evaluate("${branch} == 'main'", context) is True
        assert evaluator.evaluate("${branch} == 'develop'", context) is False

    def test_boolean_literal_comparison(self):
        """Test boolean literal comparison."""
        evaluator = ConditionEvaluator()
        context = {"success": True}

        assert evaluator.evaluate("${success} == True", context) is True
        assert evaluator.evaluate("${success} == False", context) is False

    def test_missing_variable_error(self):
        """Test error when variable not found."""
        evaluator = ConditionEvaluator()
        context = {"existing": "value"}

        with pytest.raises(InvalidConditionError) as exc_info:
            evaluator.evaluate("${nonexistent} == 'value'", context)

        assert "Variable resolution failed" in str(exc_info.value)

    def test_invalid_syntax_error(self):
        """Test error for invalid syntax."""
        evaluator = ConditionEvaluator()
        context = {"var": "value"}

        with pytest.raises(InvalidConditionError) as exc_info:
            evaluator.evaluate("${var} ===", context)

        assert "Invalid syntax" in str(exc_info.value) or "failed" in str(exc_info.value)

    def test_non_boolean_result_error(self):
        """Test error when expression doesn't return boolean."""
        evaluator = ConditionEvaluator()
        context = {"value": 42}

        with pytest.raises(InvalidConditionError) as exc_info:
            evaluator.evaluate("${value}", context)

        assert "boolean" in str(exc_info.value).lower()

    def test_unsafe_expression_error(self):
        """Test error for unsafe expressions (function calls, etc)."""
        evaluator = ConditionEvaluator()
        context = {"var": "value"}

        # Function call should be rejected
        with pytest.raises(InvalidConditionError):
            evaluator.evaluate("len(${var}) > 0", context)

    def test_multiple_comparisons(self):
        """Test chained comparisons."""
        evaluator = ConditionEvaluator()
        context = {"value": 50}

        result = evaluator.evaluate("10 < ${value} < 100", context)
        assert result is True

    def test_parentheses_grouping(self):
        """Test expression grouping with parentheses."""
        evaluator = ConditionEvaluator()
        context = {
            "a": True,
            "b": False,
            "c": True,
        }

        # Without parentheses: a and b or c = (a and b) or c = False or True = True
        result1 = evaluator.evaluate("${a} and ${b} or ${c}", context)
        assert result1 is True

        # With parentheses: a and (b or c) = a and True = True
        result2 = evaluator.evaluate("${a} and (${b} or ${c})", context)
        assert result2 is True

    def test_numeric_comparison_float(self):
        """Test numeric comparison with floats."""
        evaluator = ConditionEvaluator()
        context = {"pi": 3.14159}

        assert evaluator.evaluate("${pi} > 3.0", context) is True
        assert evaluator.evaluate("${pi} < 3.2", context) is True

    def test_empty_context(self):
        """Test evaluation with empty context for literal expressions."""
        evaluator = ConditionEvaluator()
        context = {}

        # Literal expressions should work
        assert evaluator.evaluate("True", context) is True
        assert evaluator.evaluate("False", context) is False
        assert evaluator.evaluate("1 == 1", context) is True

    def test_comparison_with_none(self):
        """Test comparison with None value."""
        evaluator = ConditionEvaluator()
        context = {"optional": None}

        # In eval mode, None resolves to Python None literal
        result = evaluator.evaluate("${optional} == None", context)
        assert result is True

        # Also test is None
        result2 = evaluator.evaluate("${optional} is None", context)
        assert result2 is True

    def test_logical_short_circuit(self):
        """Test that logical operators short-circuit properly."""
        evaluator = ConditionEvaluator()
        context = {"first": False, "second": True}

        # AND short-circuits on first False
        result = evaluator.evaluate("${first} and ${second}", context)
        assert result is False

        # OR short-circuits on first True
        context2 = {"first": True, "second": False}
        result2 = evaluator.evaluate("${first} or ${second}", context2)
        assert result2 is True

    def test_comparison_type_mismatch(self):
        """Test comparison between different types."""
        evaluator = ConditionEvaluator()
        context = {"number": 42, "string": "42"}

        # String vs number comparison (should be False)
        result = evaluator.evaluate("${number} == ${string}", context)
        assert result is False

    def test_complex_real_world_condition(self):
        """Test realistic complex condition from CI/CD pipeline."""
        evaluator = ConditionEvaluator()
        context = {
            "run_tests": {"outputs": {"exit_code": 0}},
            "run_lint": {"outputs": {"exit_code": 0}},
            "coverage": {"outputs": {"percentage": 87}},
            "branch": "main",
            "is_production": True,
        }

        condition = (
            "${run_tests.outputs.exit_code} == 0 and "
            "${run_lint.outputs.exit_code} == 0 and "
            "${coverage.outputs.percentage} >= 80 and "
            "${branch} == 'main' and "
            "${is_production} == True"
        )

        result = evaluator.evaluate(condition, context)
        assert result is True
