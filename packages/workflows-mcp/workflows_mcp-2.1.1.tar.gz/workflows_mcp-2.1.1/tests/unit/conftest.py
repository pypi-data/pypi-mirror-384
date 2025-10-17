"""Unit test-specific fixtures.

Fixtures for pure unit tests that don't require I/O or integration.
"""

from typing import Any

import pytest

from workflows_mcp.engine.dag import DAGResolver
from workflows_mcp.engine.variables import VariableResolver


@pytest.fixture
def dag_resolver() -> DAGResolver:
    """Fresh DAG resolver for dependency resolution tests.

    Returns:
        DAGResolver instance for testing topological sort and cycle detection
    """
    return DAGResolver()


@pytest.fixture
def variable_resolver() -> VariableResolver:
    """Fresh variable resolver for substitution tests.

    Returns:
        VariableResolver instance for testing variable substitution
    """
    return VariableResolver()


@pytest.fixture
def sample_dag() -> dict[str, list[str]]:
    """Sample DAG structure for testing topological sort.

    Returns:
        Dictionary representing a simple DAG with dependencies:
        - a: no dependencies
        - b: depends on a
        - c: depends on a
        - d: depends on b and c
        - e: depends on d
    """
    return {
        "a": [],
        "b": ["a"],
        "c": ["a"],
        "d": ["b", "c"],
        "e": ["d"],
    }


@pytest.fixture
def cyclic_dag() -> dict[str, list[str]]:
    """DAG with circular dependency for error testing.

    Returns:
        Dictionary representing a cyclic graph:
        - a depends on b
        - b depends on c
        - c depends on a (creates cycle)
    """
    return {
        "a": ["b"],
        "b": ["c"],
        "c": ["a"],  # Creates cycle
    }


@pytest.fixture
def simple_dag_blocks() -> list[dict[str, Any]]:
    """Simple list of blocks for DAG testing.

    Returns:
        List of block definitions with dependencies for testing execution order
    """
    return [
        {"id": "step1", "depends_on": []},
        {"id": "step2", "depends_on": ["step1"]},
        {"id": "step3", "depends_on": ["step1"]},
        {"id": "step4", "depends_on": ["step2", "step3"]},
    ]
