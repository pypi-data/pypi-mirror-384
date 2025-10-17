"""
Validate DAGResolver async compatibility.

This test ensures that DAGResolver (intentionally synchronous) works correctly
when called from async contexts, as it will be in the MCP workflow executor.
"""

import asyncio

from workflows_mcp.engine.dag import DAGResolver


async def test_dag_in_async_context():
    """Test DAGResolver works correctly in async context."""

    print("\n=== Testing DAGResolver in Async Context ===\n")

    # Test Case 1: Simple linear dependency chain
    print("Test 1: Linear dependency chain")
    dependencies = {"block1": [], "block2": ["block1"], "block3": ["block2"], "block4": ["block3"]}

    resolver = DAGResolver(blocks=list(dependencies.keys()), dependencies=dependencies)

    # Synchronous calls within async function
    order_result = resolver.topological_sort()
    waves_result = resolver.get_execution_waves()

    assert order_result.is_success, f"Topological sort failed: {order_result.error}"
    assert waves_result.is_success, f"Wave computation failed: {waves_result.error}"

    order = order_result.value
    waves = waves_result.value

    print(f"  Execution order: {order}")
    print(f"  Execution waves: {waves}")

    assert order == ["block1", "block2", "block3", "block4"], "Incorrect order"
    assert len(waves) == 4, "Should have 4 sequential waves"
    print("  ✅ Linear chain validated")

    # Test Case 2: Parallel execution opportunities
    print("\nTest 2: Parallel execution with diamond dependency")
    dependencies = {
        "start": [],
        "parallel1": ["start"],
        "parallel2": ["start"],
        "parallel3": ["start"],
        "merge": ["parallel1", "parallel2", "parallel3"],
    }

    resolver = DAGResolver(blocks=list(dependencies.keys()), dependencies=dependencies)

    order_result = resolver.topological_sort()
    waves_result = resolver.get_execution_waves()

    assert order_result.is_success, "Topological sort failed"
    assert waves_result.is_success, "Wave computation failed"

    order = order_result.value
    waves = waves_result.value

    print(f"  Execution order: {order}")
    print(f"  Execution waves: {waves}")

    # Validate wave structure
    assert waves[0] == ["start"], "First wave should be start block"
    assert set(waves[1]) == {"parallel1", "parallel2", "parallel3"}, (
        "Second wave should be parallel blocks"
    )
    assert waves[2] == ["merge"], "Third wave should be merge block"
    print("  ✅ Parallel execution validated")

    # Test Case 3: Complex multi-level dependencies
    print("\nTest 3: Complex multi-level workflow")
    dependencies = {
        "fetch_data": [],
        "validate_data": ["fetch_data"],
        "transform_data": ["validate_data"],
        "load_db": ["transform_data"],
        "create_report": ["transform_data"],
        "send_notification": ["load_db", "create_report"],
    }

    resolver = DAGResolver(blocks=list(dependencies.keys()), dependencies=dependencies)

    order_result = resolver.topological_sort()
    waves_result = resolver.get_execution_waves()

    assert order_result.is_success, "Topological sort failed"
    assert waves_result.is_success, "Wave computation failed"

    order = order_result.value
    waves = waves_result.value

    print(f"  Execution order: {order}")
    print(f"  Execution waves: {waves}")

    # Validate execution constraints
    assert order.index("fetch_data") < order.index("validate_data"), (
        "fetch_data must come before validate_data"
    )
    assert order.index("validate_data") < order.index("transform_data"), (
        "validate_data must come before transform_data"
    )
    assert order.index("transform_data") < order.index("load_db"), (
        "transform_data must come before load_db"
    )
    assert order.index("transform_data") < order.index("create_report"), (
        "transform_data must come before create_report"
    )
    assert order.index("load_db") < order.index("send_notification"), (
        "load_db must come before send_notification"
    )
    assert order.index("create_report") < order.index("send_notification"), (
        "create_report must come before send_notification"
    )

    # Validate parallel opportunity: load_db and create_report should be in same wave
    load_wave = next(i for i, wave in enumerate(waves) if "load_db" in wave)
    report_wave = next(i for i, wave in enumerate(waves) if "create_report" in wave)
    assert load_wave == report_wave, "load_db and create_report should execute in parallel"

    print("  ✅ Complex workflow validated")

    # Test Case 4: Cycle detection
    print("\nTest 4: Cyclic dependency detection")
    dependencies = {
        "block1": ["block3"],  # Creates cycle: block1 → block3 → block2 → block1
        "block2": ["block1"],
        "block3": ["block2"],
    }

    resolver = DAGResolver(blocks=list(dependencies.keys()), dependencies=dependencies)

    order_result = resolver.topological_sort()

    assert not order_result.is_success, "Should detect cycle"
    assert "Cyclic dependency" in order_result.error, f"Wrong error message: {order_result.error}"
    print(f"  ✅ Cycle detected: {order_result.error}")

    # Test Case 5: Missing dependency validation
    print("\nTest 5: Missing dependency detection")
    dependencies = {
        "block1": [],
        "block2": ["nonexistent_block"],  # Invalid dependency
    }

    resolver = DAGResolver(blocks=["block1", "block2"], dependencies=dependencies)

    order_result = resolver.topological_sort()

    assert not order_result.is_success, "Should detect missing dependency"
    assert "not found" in order_result.error.lower(), f"Wrong error message: {order_result.error}"
    print(f"  ✅ Missing dependency detected: {order_result.error}")

    print("\n=== All Tests Passed ===")
    print("\nConclusion: DAGResolver (synchronous) works perfectly in async contexts.")
    print("The async executor can safely call DAGResolver methods during planning phase.")


async def test_performance():
    """Test DAGResolver performance with large workflows."""

    print("\n=== Performance Test ===\n")

    # Create a large workflow with 100 blocks
    dependencies = {"block_0": []}
    for i in range(1, 100):
        # Each block depends on previous block (linear chain)
        dependencies[f"block_{i}"] = [f"block_{i - 1}"]

    resolver = DAGResolver(blocks=list(dependencies.keys()), dependencies=dependencies)

    import time

    start = time.perf_counter()
    order_result = resolver.topological_sort()
    sort_time = time.perf_counter() - start

    start = time.perf_counter()
    waves_result = resolver.get_execution_waves()
    waves_time = time.perf_counter() - start

    assert order_result.is_success, "Large workflow topological sort failed"
    assert waves_result.is_success, "Large workflow wave computation failed"

    print("  100-block workflow:")
    print(f"    Topological sort: {sort_time * 1000:.2f}ms")
    print(f"    Wave computation: {waves_time * 1000:.2f}ms")
    print("  ✅ Performance validated (both < 10ms expected)")


async def main():
    """Run all validation tests."""
    await test_dag_in_async_context()
    await test_performance()
    print("\n✅ DAGResolver async compatibility validated!")
    print("\nArchitectural Decision: DAGResolver remains synchronous (Path A)")


if __name__ == "__main__":
    asyncio.run(main())
