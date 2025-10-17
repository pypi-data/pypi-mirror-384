# ADR-002: Checkpoint Strategy

**Status**: Accepted
**Date**: 2025-10-14
**Deciders**: Development Team
**Technical Story**: Pause/resume and crash recovery implementation

## Context and Problem Statement

Long-running workflows require the ability to pause execution and resume later, either for interactive user input or crash recovery. The workflow engine needs a checkpoint strategy that can:

- **Pause/Resume**: Support interactive workflows requiring LLM input during execution
- **Crash Recovery**: Enable recovery from server crashes or network failures
- **State Serialization**: Persist complete execution context reliably
- **Concurrent Workflows**: Support multiple workflows running simultaneously
- **Clean Expiration**: Automatically clean up stale checkpoints

The checkpoint system must balance simplicity, reliability, and future extensibility while avoiding premature complexity.

## Decision Drivers

- **Interactive Workflows**: Support user confirmation and input during execution
- **Reliability**: Enable crash recovery for mission-critical workflows
- **Simplicity**: Minimal dependencies and complexity for MVP
- **Concurrency**: Multiple workflows can checkpoint independently
- **Resource Management**: Automatic cleanup of expired checkpoints
- **Extensibility**: Easy to add database persistence later
- **Serialization**: Complete execution state must be serializable
- **Security**: Checkpoint data must be isolated per workflow

## Considered Options

### Option 1: In-Memory Only (No Persistence)

Checkpoints stored only in memory:
- Simple Python dictionary
- Lost on server restart
- No external dependencies

### Option 2: Database Persistence (PostgreSQL/SQLite)

Full database-backed checkpoint storage:
- PostgreSQL for production
- SQLite for development
- ACID guarantees
- Distributed deployment support

### Option 3: In-Memory with Optional Persistence (Chosen)

In-memory store as default with extensible interface:
- `InMemoryCheckpointStore` for single-server deployments
- Interface for future database backends
- No required external dependencies
- Production-ready with optional persistence layer

### Option 4: Redis/External Cache

External cache system for checkpoint storage:
- Redis for distributed caching
- TTL-based expiration
- High availability

## Decision Outcome

Chosen option: **In-Memory with Optional Persistence**, because it:

1. **Minimizes complexity**: No external dependencies required for core functionality
2. **Enables quick iteration**: Simple implementation for MVP
3. **Sufficient for most use cases**: Single-server deployments are common
4. **Extensible architecture**: Clean interface for future database backends
5. **Easy to test**: No database setup required for testing
6. **Production-ready**: Reliable for single-server production deployments

The interface-based design allows seamless migration to database persistence when distributed deployment becomes necessary.

### Positive Consequences

- ✅ **Zero Dependencies**: No PostgreSQL, Redis, or other external services required
- ✅ **Simple Implementation**: Easy to understand and maintain
- ✅ **Fast Performance**: In-memory operations are extremely fast
- ✅ **Easy Testing**: No database mocking or setup needed
- ✅ **Quick Development**: MVP shipped faster without database complexity
- ✅ **Extensible Design**: Clean interface for future persistence backends
- ✅ **Production-Ready**: Sufficient for single-server deployments

### Negative Consequences

- ⚠️ **Single Server Only**: Checkpoints lost on server restart (unless persistence added)
- ⚠️ **Memory Constraints**: Large workflows consume server memory
- ⚠️ **No Distributed Support**: Cannot share checkpoints across multiple servers
- ⚠️ **Manual Migration**: Future database backend requires migration path
- ⚠️ **Limited Durability**: Crash recovery only works if server restarts quickly

## Pros and Cons of the Options

### Option 1: In-Memory Only (No Persistence)

**Good:**
- Zero dependencies
- Simplest implementation
- Fastest performance
- Easy to test

**Bad:**
- Lost on restart (no durability)
- Single server only
- No distributed deployment support
- Memory constraints for large workflows

### Option 2: Database Persistence (PostgreSQL/SQLite)

**Good:**
- Full durability (survives restarts)
- Distributed deployment support
- ACID guarantees
- Unlimited storage capacity
- Query capability for monitoring

**Bad:**
- Complex setup (PostgreSQL installation)
- External dependency (database server)
- Slower performance (disk I/O)
- Harder to test (database mocking)
- Overkill for MVP

### Option 3: In-Memory with Optional Persistence (Chosen)

**Good:**
- Simple default (no dependencies)
- Extensible to database later
- Fast in-memory performance
- Easy testing without database
- Production-ready for single server
- Clean interface for future backends

**Bad:**
- No durability by default
- Single server limitation
- Requires migration for distributed deployment
- Two codepaths to maintain

### Option 4: Redis/External Cache

**Good:**
- Fast performance
- Distributed support
- Built-in TTL expiration
- High availability

**Bad:**
- External dependency (Redis server)
- Additional operational complexity
- Network latency for checkpoint access
- Redis-specific knowledge required
- Overkill for MVP

## Implementation Details

### Core Architecture

**CheckpointState Data Structure:**

```python
@dataclass
class CheckpointState:
    """Complete workflow execution state."""

    checkpoint_id: str              # Unique checkpoint identifier
    workflow_name: str              # Workflow being executed
    workflow_inputs: Dict[str, Any] # Original workflow inputs
    execution_waves: List[List[BlockDefinition]]  # DAG execution waves
    completed_waves: int            # Number of completed waves
    context: Dict[str, Any]         # Full execution context
    created_at: datetime            # Checkpoint creation time
    pause_metadata: Optional[PauseMetadata] = None  # For interactive pause

@dataclass
class PauseMetadata:
    """Metadata for interactive pause."""

    block_id: str                   # Block that paused execution
    prompt: str                     # Prompt to display to user
    llm_response: Optional[str]     # Response from LLM (when resuming)
```

**CheckpointStore Interface:**

```python
class CheckpointStore(ABC):
    """Abstract interface for checkpoint persistence."""

    @abstractmethod
    def save(self, state: CheckpointState) -> None:
        """Persist checkpoint state."""
        pass

    @abstractmethod
    def load(self, checkpoint_id: str) -> Optional[CheckpointState]:
        """Retrieve checkpoint state."""
        pass

    @abstractmethod
    def delete(self, checkpoint_id: str) -> None:
        """Remove checkpoint."""
        pass

    @abstractmethod
    def list(self, workflow_name: Optional[str] = None) -> List[CheckpointState]:
        """List all checkpoints, optionally filtered by workflow."""
        pass

    @abstractmethod
    def cleanup_expired(self, max_age_hours: int = 24) -> int:
        """Remove expired checkpoints."""
        pass
```

**InMemoryCheckpointStore Implementation:**

```python
class InMemoryCheckpointStore(CheckpointStore):
    """In-memory checkpoint storage (default)."""

    def __init__(self):
        self._checkpoints: Dict[str, CheckpointState] = {}

    def save(self, state: CheckpointState) -> None:
        """Store checkpoint in memory."""
        self._checkpoints[state.checkpoint_id] = state

    def load(self, checkpoint_id: str) -> Optional[CheckpointState]:
        """Retrieve checkpoint from memory."""
        return self._checkpoints.get(checkpoint_id)

    def delete(self, checkpoint_id: str) -> None:
        """Remove checkpoint from memory."""
        self._checkpoints.pop(checkpoint_id, None)

    def list(self, workflow_name: Optional[str] = None) -> List[CheckpointState]:
        """List checkpoints, optionally filtered."""
        checkpoints = list(self._checkpoints.values())
        if workflow_name:
            return [cp for cp in checkpoints if cp.workflow_name == workflow_name]
        return checkpoints

    def cleanup_expired(self, max_age_hours: int = 24) -> int:
        """Remove checkpoints older than max_age_hours."""
        now = datetime.utcnow()
        expired = [
            cp_id for cp_id, cp in self._checkpoints.items()
            if (now - cp.created_at).total_seconds() > max_age_hours * 3600
        ]
        for cp_id in expired:
            del self._checkpoints[cp_id]
        return len(expired)
```

### Checkpoint Creation and Resume

**Pause Workflow:**

```python
def pause_workflow(
    executor: WorkflowExecutor,
    block_id: str,
    prompt: str
) -> str:
    """Create checkpoint for interactive pause."""
    checkpoint_id = str(uuid.uuid4())
    state = CheckpointState(
        checkpoint_id=checkpoint_id,
        workflow_name=executor.workflow_name,
        workflow_inputs=executor.inputs,
        execution_waves=executor.waves,
        completed_waves=executor.current_wave,
        context=executor.context.copy(),
        created_at=datetime.utcnow(),
        pause_metadata=PauseMetadata(
            block_id=block_id,
            prompt=prompt,
            llm_response=None
        )
    )
    checkpoint_store.save(state)
    return checkpoint_id
```

**Resume Workflow:**

```python
def resume_workflow(
    checkpoint_id: str,
    llm_response: str = ""
) -> Result[WorkflowOutput]:
    """Resume workflow from checkpoint."""
    state = checkpoint_store.load(checkpoint_id)
    if not state:
        return Result.failure(f"Checkpoint not found: {checkpoint_id}")

    # Restore execution context
    executor = WorkflowExecutor(
        workflow_name=state.workflow_name,
        inputs=state.workflow_inputs
    )
    executor.context = state.context.copy()
    executor.waves = state.execution_waves
    executor.current_wave = state.completed_waves

    # Add LLM response to context if this was a pause
    if state.pause_metadata and llm_response:
        executor.context["blocks"][state.pause_metadata.block_id]["outputs"]["llm_response"] = llm_response

    # Continue execution from next wave
    return executor.execute_from_wave(executor.current_wave + 1)
```

### Serialization Strategy

**Current Approach (Pickle):**

For MVP, checkpoints use Python's `pickle` module:
- Simple serialization of complete state
- Supports all Python objects
- Internal use only (not exposed to users)

**Future Database Backend:**

For database persistence, switch to JSON serialization:
- `context` serialized as JSONB (PostgreSQL) or TEXT (SQLite)
- Manual serialization of non-JSON-serializable objects
- Schema versioning for migration

### Checkpoint Lifecycle

1. **Creation**: Workflow pauses or crashes → checkpoint created with full state
2. **Storage**: State persisted to in-memory store (or database backend)
3. **Resume**: User resumes → state loaded and execution continues
4. **Completion**: Workflow finishes → checkpoint deleted
5. **Expiration**: Automatic cleanup after 24 hours (configurable)

### Automatic Cleanup

Background task runs periodically to remove expired checkpoints:

```python
def periodic_cleanup(checkpoint_store: CheckpointStore, interval_minutes: int = 60):
    """Run cleanup task every interval_minutes."""
    while True:
        try:
            expired_count = checkpoint_store.cleanup_expired(max_age_hours=24)
            if expired_count > 0:
                logger.info(f"Cleaned up {expired_count} expired checkpoints")
        except Exception as e:
            logger.error(f"Checkpoint cleanup failed: {e}")
        time.sleep(interval_minutes * 60)
```

## Future Extensions

### Database Backend (Phase 2)

**PostgreSQL Implementation:**

```python
class PostgresCheckpointStore(CheckpointStore):
    """PostgreSQL-backed checkpoint storage."""

    def __init__(self, connection_string: str):
        self.conn = psycopg2.connect(connection_string)
        self._create_table()

    def _create_table(self):
        """Create checkpoints table."""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS workflow_checkpoints (
                checkpoint_id TEXT PRIMARY KEY,
                workflow_name TEXT NOT NULL,
                workflow_inputs JSONB NOT NULL,
                execution_waves JSONB NOT NULL,
                completed_waves INTEGER NOT NULL,
                context JSONB NOT NULL,
                created_at TIMESTAMP NOT NULL,
                pause_metadata JSONB,
                INDEX idx_workflow_name (workflow_name),
                INDEX idx_created_at (created_at)
            )
        """)

    def save(self, state: CheckpointState) -> None:
        """Persist checkpoint to PostgreSQL."""
        # Implementation...
        pass
```

**Configuration:**

```bash
# Environment variable for backend selection
export WORKFLOW_CHECKPOINT_BACKEND="postgres"
export WORKFLOW_CHECKPOINT_DSN="postgresql://user:pass@localhost/workflows"
```

### Distributed Checkpoints (Phase 3)

For multi-server deployments:
- Shared PostgreSQL database across all servers
- Redis cache layer for hot checkpoints
- Distributed locks for checkpoint access
- Eventual consistency model

### Checkpoint Compression (Phase 4)

For large workflow contexts:
- gzip compression of serialized state
- Incremental checkpoints (delta from previous)
- Checkpoint pruning (remove old completed blocks)

## Links

- [ADR-001: Executor Pattern Redesign](ADR-001-executor-pattern-redesign.md) - Related executor architecture
- [Pause Block Implementation](../../src/workflows_mcp/engine/executors_interactive.py)
- [Checkpoint Store Tests](../../tests/test_checkpoint_store.py)
