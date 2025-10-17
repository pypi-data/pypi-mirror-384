"""Tests for DAG dependency resolution and execution wave computation.

Tests the DAGResolver class which performs topological sorting and parallel
execution wave computation using Kahn's algorithm.
"""

from workflows_mcp.engine.dag import DAGResolver


class TestTopologicalSort:
    """Tests for topological sort algorithm."""

    def test_topological_sort_linear(self):
        """Test linear dependency chain: A → B → C."""
        blocks = ["A", "B", "C"]
        dependencies = {"B": ["A"], "C": ["B"]}

        resolver = DAGResolver(blocks, dependencies)
        result = resolver.topological_sort()

        assert result.is_success
        assert result.value == ["A", "B", "C"]

    def test_topological_sort_diamond(self):
        """Test diamond dependency: A → B, A → C, B → D, C → D."""
        blocks = ["A", "B", "C", "D"]
        dependencies = {"B": ["A"], "C": ["A"], "D": ["B", "C"]}

        resolver = DAGResolver(blocks, dependencies)
        result = resolver.topological_sort()

        assert result.is_success
        # A must be first, D must be last
        assert result.value[0] == "A"
        assert result.value[-1] == "D"
        # B and C can be in any order (both depend on A)
        assert set(result.value[1:3]) == {"B", "C"}

    def test_topological_sort_no_dependencies(self):
        """Test blocks with no dependencies execute in any valid order."""
        blocks = ["A", "B", "C"]
        dependencies = {}

        resolver = DAGResolver(blocks, dependencies)
        result = resolver.topological_sort()

        assert result.is_success
        # All blocks should be included
        assert set(result.value) == {"A", "B", "C"}
        assert len(result.value) == 3

    def test_topological_sort_parallel_chains(self):
        """Test multiple independent chains: A → B and C → D."""
        blocks = ["A", "B", "C", "D"]
        dependencies = {"B": ["A"], "D": ["C"]}

        resolver = DAGResolver(blocks, dependencies)
        result = resolver.topological_sort()

        assert result.is_success
        # Check that dependencies are respected
        a_idx = result.value.index("A")
        b_idx = result.value.index("B")
        c_idx = result.value.index("C")
        d_idx = result.value.index("D")
        assert a_idx < b_idx
        assert c_idx < d_idx

    def test_topological_sort_cycle_detection_simple(self):
        """Test cyclic dependency detection: A → B → A."""
        blocks = ["A", "B"]
        dependencies = {"B": ["A"], "A": ["B"]}

        resolver = DAGResolver(blocks, dependencies)
        result = resolver.topological_sort()

        assert not result.is_success
        assert "cyclic" in result.error.lower()

    def test_topological_sort_cycle_detection_complex(self):
        """Test cyclic dependency detection: A → B → C → A."""
        blocks = ["A", "B", "C"]
        dependencies = {"B": ["A"], "C": ["B"], "A": ["C"]}

        resolver = DAGResolver(blocks, dependencies)
        result = resolver.topological_sort()

        assert not result.is_success
        assert "cyclic" in result.error.lower()

    def test_topological_sort_self_dependency(self):
        """Test self-dependency detection: A → A."""
        blocks = ["A", "B"]
        dependencies = {"A": ["A"], "B": []}

        resolver = DAGResolver(blocks, dependencies)
        result = resolver.topological_sort()

        assert not result.is_success
        assert "cyclic" in result.error.lower()

    def test_topological_sort_missing_dependency(self):
        """Test error when dependency references non-existent block."""
        blocks = ["A", "B"]
        dependencies = {"B": ["A", "C"]}  # C doesn't exist

        resolver = DAGResolver(blocks, dependencies)
        result = resolver.topological_sort()

        assert not result.is_success
        assert "not found" in result.error.lower()
        assert "C" in result.error

    def test_topological_sort_dependency_not_in_blocks(self):
        """Test error when block in dependencies is not in blocks list."""
        blocks = ["A", "B"]
        dependencies = {"C": ["A"]}  # C is in dependencies but not blocks

        resolver = DAGResolver(blocks, dependencies)
        result = resolver.topological_sort()

        assert not result.is_success
        assert "not in blocks list" in result.error.lower()

    def test_topological_sort_empty_blocks(self):
        """Test empty block list."""
        blocks = []
        dependencies = {}

        resolver = DAGResolver(blocks, dependencies)
        result = resolver.topological_sort()

        assert result.is_success
        assert result.value == []

    def test_topological_sort_single_block(self):
        """Test single block with no dependencies."""
        blocks = ["A"]
        dependencies = {}

        resolver = DAGResolver(blocks, dependencies)
        result = resolver.topological_sort()

        assert result.is_success
        assert result.value == ["A"]


class TestExecutionWaves:
    """Tests for execution wave computation (parallel execution grouping)."""

    def test_execution_waves_linear(self):
        """Test linear chain produces sequential waves: A → B → C."""
        blocks = ["A", "B", "C"]
        dependencies = {"B": ["A"], "C": ["B"]}

        resolver = DAGResolver(blocks, dependencies)
        result = resolver.get_execution_waves()

        assert result.is_success
        assert result.value == [["A"], ["B"], ["C"]]

    def test_execution_waves_parallel(self):
        """Test independent blocks execute in same wave."""
        blocks = ["A", "B", "C"]
        dependencies = {}

        resolver = DAGResolver(blocks, dependencies)
        result = resolver.get_execution_waves()

        assert result.is_success
        # All blocks can execute in parallel (wave 0)
        assert len(result.value) == 1
        assert set(result.value[0]) == {"A", "B", "C"}

    def test_execution_waves_diamond(self):
        """Test diamond pattern: A → B,C → D produces 3 waves."""
        blocks = ["A", "B", "C", "D"]
        dependencies = {"B": ["A"], "C": ["A"], "D": ["B", "C"]}

        resolver = DAGResolver(blocks, dependencies)
        result = resolver.get_execution_waves()

        assert result.is_success
        assert len(result.value) == 3
        # Wave 0: A (no dependencies)
        assert result.value[0] == ["A"]
        # Wave 1: B and C (both depend on A, can run in parallel)
        assert set(result.value[1]) == {"B", "C"}
        # Wave 2: D (depends on B and C)
        assert result.value[2] == ["D"]

    def test_execution_waves_mixed_parallel_sequential(self):
        """Test mixed parallel and sequential: A → B,C,D → E."""
        blocks = ["A", "B", "C", "D", "E"]
        dependencies = {"B": ["A"], "C": ["A"], "D": ["A"], "E": ["B", "C", "D"]}

        resolver = DAGResolver(blocks, dependencies)
        result = resolver.get_execution_waves()

        assert result.is_success
        assert len(result.value) == 3
        # Wave 0: A
        assert result.value[0] == ["A"]
        # Wave 1: B, C, D (all parallel)
        assert set(result.value[1]) == {"B", "C", "D"}
        # Wave 2: E
        assert result.value[2] == ["E"]

    def test_execution_waves_multiple_independent_chains(self):
        """Test multiple independent chains: A → B and C → D."""
        blocks = ["A", "B", "C", "D"]
        dependencies = {"B": ["A"], "D": ["C"]}

        resolver = DAGResolver(blocks, dependencies)
        result = resolver.get_execution_waves()

        assert result.is_success
        assert len(result.value) == 2
        # Wave 0: A and C (no dependencies, parallel)
        assert set(result.value[0]) == {"A", "C"}
        # Wave 1: B and D (depend on their respective chains, parallel)
        assert set(result.value[1]) == {"B", "D"}

    def test_execution_waves_complex_dependency_graph(self):
        """Test complex graph with multiple dependency levels."""
        blocks = ["A", "B", "C", "D", "E", "F"]
        dependencies = {
            "B": ["A"],
            "C": ["A"],
            "D": ["B"],
            "E": ["B", "C"],
            "F": ["D", "E"],
        }

        resolver = DAGResolver(blocks, dependencies)
        result = resolver.get_execution_waves()

        assert result.is_success
        # Wave 0: A
        assert result.value[0] == ["A"]
        # Wave 1: B and C (both depend on A)
        assert set(result.value[1]) == {"B", "C"}
        # Wave 2: D and E
        # D depends on B, E depends on B and C
        # Both can execute after wave 1 completes
        assert set(result.value[2]) == {"D", "E"}
        # Wave 3: F (depends on D and E)
        assert result.value[3] == ["F"]

    def test_execution_waves_cycle_detection(self):
        """Test cyclic dependency detection in wave computation."""
        blocks = ["A", "B", "C"]
        dependencies = {"B": ["A"], "C": ["B"], "A": ["C"]}

        resolver = DAGResolver(blocks, dependencies)
        result = resolver.get_execution_waves()

        assert not result.is_success
        assert "cyclic" in result.error.lower() or "isolated" in result.error.lower()

    def test_execution_waves_missing_dependency(self):
        """Test error when dependency is missing."""
        blocks = ["A", "B"]
        dependencies = {"B": ["C"]}  # C doesn't exist

        resolver = DAGResolver(blocks, dependencies)
        result = resolver.get_execution_waves()

        assert not result.is_success
        assert "not found" in result.error.lower()

    def test_execution_waves_empty_blocks(self):
        """Test empty block list."""
        blocks = []
        dependencies = {}

        resolver = DAGResolver(blocks, dependencies)
        result = resolver.get_execution_waves()

        assert result.is_success
        assert result.value == []

    def test_execution_waves_single_block(self):
        """Test single block with no dependencies."""
        blocks = ["A"]
        dependencies = {}

        resolver = DAGResolver(blocks, dependencies)
        result = resolver.get_execution_waves()

        assert result.is_success
        assert result.value == [["A"]]


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_large_linear_chain(self):
        """Test performance with large linear chain (100 blocks)."""
        blocks = [f"block_{i}" for i in range(100)]
        dependencies = {f"block_{i}": [f"block_{i - 1}"] for i in range(1, 100)}

        resolver = DAGResolver(blocks, dependencies)
        result = resolver.topological_sort()

        assert result.is_success
        assert len(result.value) == 100
        # First block should be block_0
        assert result.value[0] == "block_0"
        # Last block should be block_99
        assert result.value[-1] == "block_99"

    def test_large_parallel_blocks(self):
        """Test performance with many parallel blocks (100 blocks, no dependencies)."""
        blocks = [f"block_{i}" for i in range(100)]
        dependencies = {}

        resolver = DAGResolver(blocks, dependencies)
        result = resolver.get_execution_waves()

        assert result.is_success
        # All blocks should be in wave 0
        assert len(result.value) == 1
        assert set(result.value[0]) == set(blocks)

    def test_multiple_dependencies_per_block(self):
        """Test block with many dependencies."""
        blocks = ["A", "B", "C", "D", "E", "final"]
        dependencies = {"final": ["A", "B", "C", "D", "E"]}

        resolver = DAGResolver(blocks, dependencies)
        result = resolver.get_execution_waves()

        assert result.is_success
        assert len(result.value) == 2
        # Wave 0: All independent blocks
        assert set(result.value[0]) == {"A", "B", "C", "D", "E"}
        # Wave 1: Final block
        assert result.value[1] == ["final"]

    def test_special_characters_in_block_names(self):
        """Test blocks with special characters in names."""
        blocks = ["block-1", "block_2", "block.3", "block:4"]
        dependencies = {"block_2": ["block-1"], "block.3": ["block_2"]}

        resolver = DAGResolver(blocks, dependencies)
        result = resolver.topological_sort()

        assert result.is_success
        # Verify all blocks are included
        assert set(result.value) == set(blocks)
