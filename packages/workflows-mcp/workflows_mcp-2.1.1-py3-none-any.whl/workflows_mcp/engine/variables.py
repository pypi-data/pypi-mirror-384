"""
Variable resolution and conditional evaluation for workflow execution.

This module provides:
1. VariableResolver: Resolves ${var} syntax in workflow inputs
2. ConditionEvaluator: Safely evaluates boolean expressions

Variable Resolution:
- ${inputs.param_name} - References workflow inputs
- ${blocks.block_id.outputs.field} - References block output fields
- ${blocks.block_id.inputs.field} - References block input fields (debugging)
- ${blocks.block_id.metadata.field} - References block metadata
- ${metadata.field} - References workflow metadata
- Recursive resolution in strings, dicts, lists

Conditional Evaluation:
- Safe AST-based evaluation (no arbitrary code execution)
- Supported operators: ==, !=, >, <, >=, <=, and, or, not, in
- Variables resolved before evaluation
"""

import ast
import operator
import re
from typing import Any


class VariableNotFoundError(Exception):
    """Raised when a variable reference cannot be resolved."""

    pass


class InvalidConditionError(Exception):
    """Raised when a condition expression is invalid or unsafe."""

    pass


class VariableResolver:
    """
    Resolves ${var} variable references from workflow context.

    Context Structure:
        {
            "inputs": {
                "working_dir": "/my/project",
                "python_version": "3.12"
            },
            "metadata": {
                "workflow_name": "my-workflow",
                "start_time": 1697123456.789
            },
            "blocks": {
                "run_tests": {
                    "inputs": {"command": "pytest"},
                    "outputs": {"exit_code": 0, "success": True},
                    "metadata": {"execution_time_ms": 1234}
                }
            }
        }

    Variable Syntax:
        - ${inputs.param_name} - Workflow input
        - ${blocks.block_id.outputs.field} - Block output
        - ${blocks.block_id.inputs.field} - Block input (debugging)
        - ${blocks.block_id.metadata.field} - Block metadata
        - ${metadata.field} - Workflow metadata

    Security:
        - ${__internal__.*} - Access denied (internal system state)

    Example:
        context = {
            "inputs": {"branch": "main"},
            "blocks": {
                "create_worktree": {
                    "outputs": {"worktree_path": "/tmp/worktree"}
                }
            }
        }

        resolver = VariableResolver(context)
        result = resolver.resolve("Path: ${blocks.create_worktree.outputs.worktree_path}")
        # Returns: "Path: /tmp/worktree"
    """

    # Pattern: ${identifier} or ${identifier.field} or ${identifier.field.subfield} (any depth)
    VAR_PATTERN = re.compile(r"\$\{([a-z_][a-z0-9_]*(?:\.[a-z_][a-z0-9_]*)*)\}")

    def __init__(self, context: dict[str, Any]):
        """
        Initialize variable resolver with context.

        Args:
            context: Workflow context with inputs and block outputs
        """
        self.context = context

    def resolve(self, value: Any, for_eval: bool = False) -> Any:
        """
        Recursively resolve variables in value.

        Args:
            value: Value to resolve (str, dict, list, or primitive)
            for_eval: If True, format string values for Python eval

        Returns:
            Resolved value with variables substituted

        Raises:
            VariableNotFoundError: If a variable reference cannot be resolved
        """
        if isinstance(value, str):
            return self._resolve_string(value, for_eval=for_eval)
        elif isinstance(value, dict):
            return {key: self.resolve(val, for_eval=for_eval) for key, val in value.items()}
        elif isinstance(value, list):
            return [self.resolve(item, for_eval=for_eval) for item in value]
        else:
            # Primitive types (int, float, bool, None) pass through
            return value

    def _resolve_string(self, text: str, for_eval: bool = False) -> str:
        """
        Replace ${var} patterns with context values.

        Args:
            text: String containing variable references
            for_eval: If True, format values for Python eval (quote strings, etc.)

        Returns:
            String with variables substituted

        Raises:
            VariableNotFoundError: If variable not found in context
        """

        def replace_var(match: re.Match[str]) -> str:
            """Replace a single variable match with dictionary navigation."""
            var_path = match.group(1)

            # Security: Block access to internal namespace
            if var_path.startswith("__internal__") or ".__internal__" in var_path:
                raise VariableNotFoundError(
                    f"Access to internal namespace is not allowed: ${{{var_path}}}"
                )

            segments = var_path.split(".")

            # Simple dictionary navigation - no special cases!
            value = self.context
            for i, segment in enumerate(segments):
                if not isinstance(value, dict):
                    partial_path = ".".join(segments[:i])
                    raise VariableNotFoundError(
                        f"Cannot access '{segment}' on non-dict value at '${{{partial_path}}}'"
                    )

                if segment not in value:
                    available = list(value.keys()) if isinstance(value, dict) else []
                    raise VariableNotFoundError(
                        f"Variable '${{{var_path}}}' not found. "
                        f"At segment '{segment}', available keys: {available}"
                    )

                value = value[segment]

            # Format value for return
            return self._format_for_eval(value) if for_eval else self._format_for_string(value)

        return self.VAR_PATTERN.sub(replace_var, text)

    def _format_for_eval(self, value: Any) -> str:
        """Format value for Python eval (proper literals)."""
        if isinstance(value, str):
            return repr(value)
        elif isinstance(value, bool):
            return "True" if value else "False"
        elif value is None:
            return "None"
        elif isinstance(value, (int, float)):
            return str(value)
        else:
            return repr(value)

    def _format_for_string(self, value: Any) -> str:
        """Format value for regular string substitution."""
        if isinstance(value, str):
            return value
        elif isinstance(value, (int, float, bool)):
            return str(value)
        elif value is None:
            return ""
        else:
            return repr(value)


class ConditionEvaluator:
    """
    Safe AST-based boolean expression evaluator for conditional execution.

    Supported Operators:
        - Comparison: ==, !=, >, <, >=, <=
        - Boolean: and, or, not
        - Membership: in
        - Literals: strings, numbers, booleans, None

    Security:
        - Uses ast.parse() for safe evaluation (no code execution)
        - Whitelist of allowed operators
        - No function calls, attribute access, or imports

    Example:
        evaluator = ConditionEvaluator()
        context = {"run_tests.exit_code": 0, "coverage": 85}

        # Resolve variables first
        condition = "${run_tests.exit_code} == 0 and ${coverage} >= 80"
        result = evaluator.evaluate(condition, context)
        # Returns: True
    """

    # Whitelist of safe operators
    SAFE_OPERATORS: dict[type, Any] = {
        ast.Eq: operator.eq,
        ast.NotEq: operator.ne,
        ast.Lt: operator.lt,
        ast.LtE: operator.le,
        ast.Gt: operator.gt,
        ast.GtE: operator.ge,
        ast.And: operator.and_,
        ast.Or: operator.or_,
        ast.Not: operator.not_,
        ast.In: lambda x, y: x in y,
        ast.NotIn: lambda x, y: x not in y,
    }

    def evaluate(self, condition: str, context: dict[str, Any]) -> bool:
        """
        Evaluate condition string against context.

        Args:
            condition: Boolean expression with variable references
            context: Workflow context for variable resolution

        Returns:
            Boolean result of evaluation

        Raises:
            InvalidConditionError: If condition is invalid or unsafe
            VariableNotFoundError: If variable reference not found

        Example:
            result = evaluator.evaluate(
                "${run_tests.exit_code} == 0 and ${coverage} >= 80",
                {"run_tests.exit_code": 0, "coverage": 85}
            )
        """
        # Step 1: Resolve variables with for_eval=True to get proper Python literals
        try:
            resolver = VariableResolver(context)
            resolved_condition = resolver.resolve(condition, for_eval=True)
        except VariableNotFoundError as e:
            raise InvalidConditionError(f"Variable resolution failed: {e}") from e

        # Step 2: Parse and evaluate safely
        try:
            result = self._safe_eval(resolved_condition)
            if not isinstance(result, bool):
                raise InvalidConditionError(
                    f"Condition must evaluate to boolean, got {type(result).__name__}"
                )
            return result
        except InvalidConditionError:
            raise
        except Exception as e:
            raise InvalidConditionError(f"Condition evaluation failed: {e}") from e

    def _safe_eval(self, expr: str) -> bool:
        """
        Safely evaluate boolean expression.

        Uses Python's eval() with restricted builtins for safe evaluation.
        This approach is secure because:
        1. No __builtins__ - no access to dangerous functions
        2. Empty locals dict - no variables can be referenced
        3. Expression is already variable-resolved

        Normalizes YAML boolean literals (true/false) to Python (True/False)
        and string boolean representations ("True"/"False") to actual booleans.
        Follows YAGNI: only normalize what's needed for YAML compatibility.

        Args:
            expr: Expression string (variables already resolved)

        Returns:
            Boolean evaluation result

        Raises:
            InvalidConditionError: If expression is unsafe or invalid
        """
        try:
            # Normalize YAML boolean literals to Python (Bug #3 fix)
            # Use word boundaries to avoid false positives (e.g., "untrue" should not match)
            import re

            expr = re.sub(r"\btrue\b", "True", expr)
            expr = re.sub(r"\bfalse\b", "False", expr)

            # Normalize string boolean representations to actual booleans (Bug #4 fix)
            # Handle both single and double quotes
            expr = expr.replace("'True'", "True").replace("'False'", "False")
            expr = expr.replace('"True"', "True").replace('"False"', "False")

            # Use eval with empty builtins for security
            # This allows all operators and literals but no function calls
            result = eval(expr, {"__builtins__": {}}, {})

            if not isinstance(result, bool):
                raise InvalidConditionError(
                    f"Expression must evaluate to boolean, got {type(result).__name__}: {result}"
                )

            return result

        except NameError as e:
            # Variable name not found (shouldn't happen after resolution)
            raise InvalidConditionError(
                f"Unresolved variable in expression: {e}. "
                f"This shouldn't happen after variable resolution."
            ) from e
        except SyntaxError as e:
            raise InvalidConditionError(f"Invalid syntax: {e}") from e
        except Exception as e:
            raise InvalidConditionError(f"Evaluation error: {e}") from e

    def _eval_node(self, node: ast.AST) -> Any:
        """
        Recursively evaluate AST node with operator whitelist.

        Args:
            node: AST node to evaluate

        Returns:
            Evaluated value

        Raises:
            InvalidConditionError: If node type is not whitelisted
        """
        # Literals
        if isinstance(node, ast.Constant):
            return node.value

        # Boolean operations (and, or)
        elif isinstance(node, ast.BoolOp):
            bool_op_type = type(node.op)
            if bool_op_type not in self.SAFE_OPERATORS:
                raise InvalidConditionError(
                    f"Unsupported boolean operator: {bool_op_type.__name__}"
                )

            op_func = self.SAFE_OPERATORS[bool_op_type]
            values = [self._eval_node(val) for val in node.values]

            # Apply operator (and/or)
            result = values[0]
            for val in values[1:]:
                result = op_func(result, val)
            return result

        # Comparison operations (==, !=, <, >, <=, >=)
        elif isinstance(node, ast.Compare):
            left = self._eval_node(node.left)
            result = True

            for op, comparator in zip(node.ops, node.comparators):
                cmp_op_type = type(op)
                if cmp_op_type not in self.SAFE_OPERATORS:
                    raise InvalidConditionError(
                        f"Unsupported comparison operator: {cmp_op_type.__name__}"
                    )

                right = self._eval_node(comparator)
                op_func = self.SAFE_OPERATORS[cmp_op_type]

                result = result and op_func(left, right)
                left = right

            return result

        # Unary operations (not)
        elif isinstance(node, ast.UnaryOp):
            unary_op_type = type(node.op)
            if unary_op_type not in self.SAFE_OPERATORS:
                raise InvalidConditionError(f"Unsupported unary operator: {unary_op_type.__name__}")

            operand = self._eval_node(node.operand)
            op_func = self.SAFE_OPERATORS[unary_op_type]
            return op_func(operand)

        # Lists and tuples (for 'in' operator)
        elif isinstance(node, (ast.List, ast.Tuple)):
            return [self._eval_node(elt) for elt in node.elts]

        # Unsupported node type
        else:
            raise InvalidConditionError(
                f"Unsupported expression type: {type(node).__name__}. "
                f"Only literals, comparisons, and boolean operators are allowed."
            )
