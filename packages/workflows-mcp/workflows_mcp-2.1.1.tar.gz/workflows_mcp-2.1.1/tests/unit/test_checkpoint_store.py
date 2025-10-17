"""Tests for checkpoint storage system.

Following TDD: Write tests FIRST, then implement.
"""

import time

import pytest


@pytest.mark.asyncio
async def test_save_and_load_checkpoint(create_checkpoint):
    """Checkpoint must be retrievable after save."""
    from workflows_mcp.engine.checkpoint_store import InMemoryCheckpointStore

    store = InMemoryCheckpointStore()
    state = create_checkpoint("chk_123", "test-workflow")

    checkpoint_id = await store.save_checkpoint(state)
    assert checkpoint_id == "chk_123"

    loaded = await store.load_checkpoint("chk_123")
    assert loaded is not None
    assert loaded.checkpoint_id == "chk_123"
    assert loaded.workflow_name == "test-workflow"


@pytest.mark.asyncio
async def test_load_nonexistent_returns_none():
    """Loading nonexistent checkpoint must return None."""
    from workflows_mcp.engine.checkpoint_store import InMemoryCheckpointStore

    store = InMemoryCheckpointStore()
    loaded = await store.load_checkpoint("nonexistent")

    assert loaded is None


@pytest.mark.asyncio
async def test_list_checkpoints_all(create_checkpoint):
    """List all checkpoints must return all saved."""
    from workflows_mcp.engine.checkpoint_store import InMemoryCheckpointStore

    store = InMemoryCheckpointStore()

    await store.save_checkpoint(create_checkpoint("chk_1", "workflow_a"))
    await store.save_checkpoint(create_checkpoint("chk_2", "workflow_a"))
    await store.save_checkpoint(create_checkpoint("chk_3", "workflow_b"))

    all_checkpoints = await store.list_checkpoints()
    assert len(all_checkpoints) == 3


@pytest.mark.asyncio
async def test_list_checkpoints_filter_by_workflow(create_checkpoint):
    """List must filter by workflow name."""
    from workflows_mcp.engine.checkpoint_store import InMemoryCheckpointStore

    store = InMemoryCheckpointStore()

    await store.save_checkpoint(create_checkpoint("chk_1", "workflow_a"))
    await store.save_checkpoint(create_checkpoint("chk_2", "workflow_a"))
    await store.save_checkpoint(create_checkpoint("chk_3", "workflow_b"))

    workflow_a = await store.list_checkpoints(workflow_name="workflow_a")
    assert len(workflow_a) == 2
    assert all(c.workflow_name == "workflow_a" for c in workflow_a)


@pytest.mark.asyncio
async def test_delete_checkpoint(create_checkpoint):
    """Delete must remove checkpoint."""
    from workflows_mcp.engine.checkpoint_store import InMemoryCheckpointStore

    store = InMemoryCheckpointStore()
    await store.save_checkpoint(create_checkpoint("chk_1", "test"))

    deleted = await store.delete_checkpoint("chk_1")
    assert deleted is True

    loaded = await store.load_checkpoint("chk_1")
    assert loaded is None


@pytest.mark.asyncio
async def test_delete_nonexistent_returns_false():
    """Deleting nonexistent checkpoint must return False."""
    from workflows_mcp.engine.checkpoint_store import InMemoryCheckpointStore

    store = InMemoryCheckpointStore()
    deleted = await store.delete_checkpoint("nonexistent")

    assert deleted is False


@pytest.mark.asyncio
async def test_cleanup_expired(create_checkpoint):
    """Expired checkpoints must be cleaned up."""
    from workflows_mcp.engine.checkpoint_store import InMemoryCheckpointStore

    store = InMemoryCheckpointStore()

    # Create checkpoint with old timestamp
    old_checkpoint = create_checkpoint("chk_old", "test")
    old_checkpoint.created_at = time.time() - 1000  # 1000 seconds ago

    # Create recent checkpoint
    recent_checkpoint = create_checkpoint("chk_recent", "test")

    await store.save_checkpoint(old_checkpoint)
    await store.save_checkpoint(recent_checkpoint)

    # Cleanup checkpoints older than 500 seconds
    count = await store.cleanup_expired(max_age_seconds=500)
    assert count == 1

    # Old should be gone, recent should remain
    assert await store.load_checkpoint("chk_old") is None
    assert await store.load_checkpoint("chk_recent") is not None


@pytest.mark.asyncio
async def test_concurrent_access(create_checkpoint):
    """Store must handle concurrent operations safely."""
    import asyncio

    from workflows_mcp.engine.checkpoint_store import InMemoryCheckpointStore

    store = InMemoryCheckpointStore()

    async def save_many(prefix: str, count: int):
        for i in range(count):
            state = create_checkpoint(f"{prefix}_{i}", "test")
            await store.save_checkpoint(state)

    # Run 3 concurrent tasks
    await asyncio.gather(save_many("a", 10), save_many("b", 10), save_many("c", 10))

    checkpoints = await store.list_checkpoints()
    assert len(checkpoints) == 30
