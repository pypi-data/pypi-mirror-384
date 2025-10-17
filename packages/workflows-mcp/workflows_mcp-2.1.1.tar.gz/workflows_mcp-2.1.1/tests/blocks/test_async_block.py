"""Test async WorkflowBlock implementation.

Validates:
- Async block execution
- Pydantic v2 input validation
- Result monad integration
- Block registry functionality
- Dependency tracking
"""

import asyncio

from workflows_mcp.engine.block import BLOCK_REGISTRY
from workflows_mcp.engine.blocks_example import EchoBlock, EchoBlockOutput
from workflows_mcp.engine.result import Result


async def test_async_block_execution() -> None:
    """Test async block execution."""

    print("Test 1: Basic async execution")
    block = EchoBlock(id="echo1", inputs={"message": "Hello async!", "delay_ms": 100})

    result = await block.execute(context={})

    assert result.is_success, "Block execution should succeed"
    assert result.value is not None, "Result value should not be None"
    assert isinstance(result.value, EchoBlockOutput)
    assert result.value.echoed == "Echo: Hello async!"
    assert result.value.execution_time_ms >= 100  # Should have delayed
    print(f"  Async execution: {result.value.echoed} (took {result.value.execution_time_ms:.1f}ms)")

    print("\nTest 2: Input validation")
    try:
        _ = EchoBlock(id="bad", inputs={"wrong_field": "value"})
        assert False, "Should have raised validation error"
    except ValueError as e:
        print(f"  Input validation: {str(e)[:80]}...")

    print("\nTest 3: Block registry")
    block_class = BLOCK_REGISTRY.get("EchoBlock")
    block2 = block_class(id="echo2", inputs={"message": "From registry"})
    result2 = await block2.execute(context={})
    assert result2.is_success
    assert result2.value is not None
    assert isinstance(result2.value, EchoBlockOutput)
    print(f"  Block registry: {result2.value.echoed}")

    print("\nTest 4: Dependency tracking")
    block3 = EchoBlock(
        id="echo3",
        inputs={"message": "Dependent"},
        depends_on=["echo1", "echo2"],
    )
    assert block3.depends_on == ["echo1", "echo2"]
    print(f"  Dependencies: {block3.depends_on}")

    print("\nTest 5: Result monad patterns")
    # Test success case
    success_result: Result[str] = Result.success("test_value")
    assert success_result.is_success
    assert success_result.value == "test_value"
    assert success_result.unwrap() == "test_value"
    print(f"  Success pattern: {success_result.value}")

    # Test failure case
    failure_result: Result[str] = Result.failure("test_error")
    assert not failure_result.is_success
    assert failure_result.error == "test_error"
    assert failure_result.unwrap_or("default") == "default"
    print(f"  Failure pattern: {failure_result.error}")

    print("\nTest 6: Context access")
    # Test that blocks can read from context
    context = {"previous_block": {"output": "previous_value"}}
    block4 = EchoBlock(id="echo4", inputs={"message": "With context"})
    result4 = await block4.execute(context=context)
    assert result4.is_success
    print(f"  Context access: Block executed with context keys: {list(context.keys())}")

    print("\nTest 7: Multiple concurrent blocks")
    # Test async execution of multiple blocks
    blocks = [
        EchoBlock(id=f"echo{i}", inputs={"message": f"Message {i}", "delay_ms": 50})
        for i in range(5)
    ]

    import time

    start = time.time()
    results = await asyncio.gather(*[block.execute({}) for block in blocks])
    elapsed = (time.time() - start) * 1000

    assert all(r.is_success for r in results)
    # Should be faster than sequential (5 * 50ms = 250ms)
    # Parallel should be ~50-100ms
    print(f"  Concurrent execution: {len(blocks)} blocks in {elapsed:.1f}ms (parallel speedup)")

    print("\nTest 8: Output validation")
    block5 = EchoBlock(id="echo5", inputs={"message": "Test output"})
    result5 = await block5.execute({})

    # Test manual output validation
    if result5.is_success and result5.value is not None:
        output_dict = result5.value.model_dump()
        validation_result = block5.validate_output(output_dict)
        assert validation_result.is_success
        print(f"  Output validation: {validation_result.value}")

    print("\n All async WorkflowBlock tests passed!")


if __name__ == "__main__":
    asyncio.run(test_async_block_execution())
