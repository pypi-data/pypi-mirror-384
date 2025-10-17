# ADR-001: Executor Pattern Redesign

**Status**: Accepted
**Date**: 2025-10-14
**Deciders**: Development Team
**Technical Story**: Executor pattern migration (Phase 6)

## Context and Problem Statement

The legacy workflow block system used mutable `WorkflowBlock` instances with tight coupling between block logic and state. Each block execution created new instances, making the system difficult to test, extend, and secure. The original design had several limitations:

- **State Management**: Mutable block instances carried state across executions, leading to potential side effects
- **Testability**: Testing required complex mocking of block state and dependencies
- **Extensibility**: Adding new block types required modifying core engine code
- **Security**: No mechanism to classify or audit security implications of different block types
- **Schema Generation**: Manual schema definitions separate from implementation
- **Performance**: Each block execution instantiated new objects unnecessarily

We needed an architecture that would enable:
- Plugin-based extensibility for third-party block types
- Auto-generated JSON schemas for editor autocomplete and validation
- Per-block security classification and auditing
- Improved testability through pure functions
- Better performance through singleton pattern

## Decision Drivers

- **Extensibility**: Support plugin-based block types via entry points
- **Type Safety**: Leverage Pydantic for automatic schema generation
- **Security**: Enable security classification per executor type
- **Testability**: Pure functions without mocking requirements
- **Performance**: Singleton pattern for executor reuse
- **Maintainability**: Clear separation between execution logic and state
- **Developer Experience**: Automatic JSON schema for IDE autocomplete

## Considered Options

### Option 1: Enhanced WorkflowBlock Pattern

Improve the existing `WorkflowBlock` class-based pattern:
- Add input validation
- Separate state from logic
- Keep existing architecture

### Option 2: Full Executor Pattern (Chosen)

Complete redesign with stateless executors:
- `BlockExecutor` base class with pure `execute()` method
- Singleton instances per executor type
- Type-safe Pydantic models for inputs/outputs
- Security classification per executor
- Plugin discovery via entry points

### Option 3: Hybrid Approach

Combine blocks and executors:
- Keep `WorkflowBlock` for core blocks
- Add `BlockExecutor` for plugins only
- Gradual migration path

## Decision Outcome

Chosen option: **Full Executor Pattern**, because it provides:

1. **Complete separation of concerns**: Execution logic completely separated from state
2. **True extensibility**: Third-party plugins without modifying core code
3. **Automatic schema generation**: Single source of truth for validation and documentation
4. **Clear security model**: Security classification built into executor design
5. **Superior testability**: Pure functions with no mocking needed
6. **Performance optimization**: Singleton pattern eliminates unnecessary object creation

### Positive Consequences

- ✅ **Plugin System**: Entry point-based discovery enables third-party executors
- ✅ **Schema Generation**: Auto-generated JSON Schema from Pydantic models
- ✅ **Security Audit**: Clear security classification per executor type
- ✅ **Testability**: Pure functions are trivial to test (no mocking required)
- ✅ **Performance**: Singleton instances reduce memory footprint
- ✅ **Type Safety**: Pydantic validation prevents runtime errors
- ✅ **Developer Experience**: IDE autocomplete via JSON schema
- ✅ **Maintainability**: Clear architecture with well-defined boundaries

### Negative Consequences

- ⚠️ **Migration Effort**: Existing workflows need updating to new executor names
- ⚠️ **Breaking Changes**: Not backward compatible with legacy block definitions
- ⚠️ **Learning Curve**: Developers must learn new executor pattern
- ⚠️ **Documentation**: All examples and guides require updates

## Pros and Cons of the Options

### Option 1: Enhanced WorkflowBlock Pattern

**Good:**
- Minimal migration effort
- Backward compatible
- Familiar to existing developers
- Incremental improvement path

**Bad:**
- Doesn't solve extensibility problem
- Schema generation still manual
- No security model
- State management complexity remains
- Testing still requires mocking
- Performance issues persist

### Option 2: Full Executor Pattern (Chosen)

**Good:**
- Complete separation of concerns
- Plugin-based extensibility
- Automatic schema generation
- Built-in security model
- Pure functions (easy testing)
- Performance optimization
- Type-safe by design

**Bad:**
- Breaking change (requires migration)
- Upfront development effort
- New pattern to learn
- Documentation overhaul needed

### Option 3: Hybrid Approach

**Good:**
- Gradual migration path
- Partial backward compatibility
- Lower initial effort

**Bad:**
- Two patterns to maintain
- Confusing mental model
- Technical debt accumulates
- Schema generation inconsistent
- Security model incomplete
- Testing complexity remains for legacy blocks

## Implementation Details

### Core Architecture

**BlockExecutor Base Class:**

```python
class BlockExecutor(ABC):
    """Stateless executor for workflow blocks."""

    @abstractmethod
    def input_model(self) -> Type[BlockInput]:
        """Return Pydantic input model."""
        pass

    @abstractmethod
    def output_model(self) -> Type[BlockOutput]:
        """Return Pydantic output model."""
        pass

    @abstractmethod
    def execute(
        self,
        block_id: str,
        inputs: BlockInput,
        context: Dict[str, Any]
    ) -> Result[BlockOutput]:
        """Execute block logic (pure function)."""
        pass

    def security_level(self) -> ExecutorSecurityLevel:
        """Security classification."""
        return ExecutorSecurityLevel.TRUSTED

    def capabilities(self) -> ExecutorCapabilities:
        """Security capability flags."""
        return ExecutorCapabilities()
```

**Executor Registry:**

```python
class ExecutorRegistry:
    """Singleton registry for executor types."""

    _executors: Dict[str, BlockExecutor] = {}

    @classmethod
    def register(cls, name: str, executor: BlockExecutor):
        """Register executor instance (singleton)."""
        cls._executors[name] = executor

    @classmethod
    def get(cls, name: str) -> BlockExecutor:
        """Retrieve executor by name."""
        return cls._executors[name]
```

**Security Classification:**

```python
class ExecutorSecurityLevel(Enum):
    SAFE = "safe"              # Read-only, no system access
    TRUSTED = "trusted"        # File I/O, safe operations
    PRIVILEGED = "privileged"  # Full system access
```

**Module Organization:**

- `executor_base.py`: Base classes and interfaces
- `executors_core.py`: EchoBlock executor
- `executors_file.py`: File operation executors
- `executors_interactive.py`: Pause/input executors
- `executors_state.py`: ExecuteWorkflow executor

### Plugin Discovery

Third-party executors register via entry points in `pyproject.toml`:

```toml
[project.entry-points."workflows_mcp.executors"]
my_custom_executor = "my_package.executors:MyCustomExecutor"
```

### Schema Generation

Automatic JSON Schema generation from Pydantic models:

```python
def generate_block_schema(executor: BlockExecutor) -> dict:
    """Generate JSON Schema for block type."""
    input_schema = executor.input_model().model_json_schema()
    output_schema = executor.output_model().model_json_schema()
    return {
        "input": input_schema,
        "output": output_schema,
        "security": {
            "level": executor.security_level().value,
            "capabilities": executor.capabilities().model_dump()
        }
    }
```

## Migration Path

1. ✅ **Phase 1**: Create executor base classes and registry
2. ✅ **Phase 2**: Migrate core blocks (Echo, CreateFile, Shell)
3. ✅ **Phase 3**: Migrate specialized blocks (Pause, ExecuteWorkflow)
4. ✅ **Phase 4**: Update all built-in workflow templates
5. ✅ **Phase 5**: Update tests and documentation
6. ✅ **Phase 6**: Remove legacy WorkflowBlock code
7. 🔜 **Phase 7**: Implement plugin discovery system
8. 🔜 **Phase 8**: Create plugin development guide

## Links

- [ADR-003: Security Model](ADR-003-security-model.md) - Related security classification system
- [EXECUTOR_PATTERN_ANALYSIS.md](../../EXECUTOR_PATTERN_ANALYSIS.md) - Detailed technical analysis
- [EXECUTOR_REDESIGN_COMPLETE.md](../../EXECUTOR_REDESIGN_COMPLETE.md) - Implementation summary
- [PHASE_6_COMPLETE.md](../../PHASE_6_COMPLETE.md) - Phase 6 completion report
