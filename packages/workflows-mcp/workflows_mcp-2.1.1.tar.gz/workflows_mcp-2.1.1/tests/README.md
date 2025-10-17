# Workflows MCP Test Suite

Comprehensive testing documentation for the workflows-mcp project.

## Overview

The workflows-mcp test suite provides comprehensive coverage of the MCP workflow engine through 427 tests organized into a clear hierarchical structure.

**Test Suite Metrics:**
- **Total Tests:** 427
- **Total Coverage:** 85%
- **Test Categories:** 5 (unit, blocks, integration, library, security)
- **Organization:** Hierarchical structure following pytest best practices

**Testing Philosophy:**
- **Clarity:** Tests organized by component and purpose
- **Isolation:** Shared fixtures ensure proper test isolation
- **Reusability:** DRY principle through fixture hierarchy
- **Completeness:** Integration tests validate end-to-end workflows

## Directory Structure

The test suite is organized into five main categories:

```bash
tests/
├── conftest.py                 # Root-level shared fixtures
│
├── unit/                       # Core engine component tests
│   ├── conftest.py            # Unit test-specific fixtures
│   ├── test_conditionals.py   # Conditional execution tests
│   ├── test_dag.py            # DAG resolution and dependency tests
│   ├── test_loader.py         # YAML workflow loading tests
│   ├── test_registry.py       # Workflow registry tests
│   ├── test_schema.py         # Schema validation tests
│   └── test_variables.py      # Variable resolution tests
│
├── blocks/                     # Block-specific functionality tests
│   ├── conftest.py            # Block test-specific fixtures
│   ├── test_async_block.py    # Async block execution tests
│   ├── test_bash_block.py     # Shell block tests
│   └── test_file_blocks.py    # File operation block tests
│
├── integration/                # End-to-end and cross-component tests
│   ├── conftest.py            # Integration test-specific fixtures
│   ├── test_mcp_server.py     # MCP server integration tests
│   ├── test_mcp_tools.py      # MCP tool functionality tests
│   ├── test_workflow_composition.py  # Workflow composition tests
│   └── test_workflow_integration.py  # Full workflow execution tests
│
├── library/                    # Workflow library validation
│   ├── conftest.py            # Library test-specific fixtures
│   └── test_library_workflows.py  # Built-in workflow template tests
│
└── security/                   # Security and output validation
    ├── conftest.py            # Security test-specific fixtures
    ├── test_custom_outputs.py      # Custom output validation tests
    ├── test_output_integration.py  # Output integration tests
    └── test_output_security.py     # Output security tests
```

### Category Descriptions

**`unit/`** - Core Engine Component Tests
- Tests for individual engine components (DAG resolver, executor, loader, registry)
- Isolated tests with minimal dependencies
- Focus on correctness of core algorithms and data structures
- Use mocked or simple fixtures for test data

**`blocks/`** - Block-Specific Tests
- Tests for individual workflow block types
- File operations (CreateFile, ReadFile, PopulateTemplate)
- Bash command execution
- Async block execution patterns
- Block input/output validation

**`integration/`** - End-to-End and Cross-Component Tests
- Multi-component interaction tests
- MCP server and tool integration
- Workflow composition (calling workflows from workflows)
- Full workflow execution with real blocks
- System-level behavior validation

**`library/`** - Library Workflow Validation
- Tests for built-in workflow templates
- Validates all workflows in `templates/` directory
- Ensures workflow library quality
- Regression testing for workflow changes

**`security/`** - Security and Output Validation
- Output security validation
- Custom output handling
- Stdout/stderr isolation
- Environment variable security
- Block output sanitization

## Running Tests

### Basic Test Execution

```bash
# Run all tests
uv run pytest tests/

# Run with verbose output
uv run pytest tests/ -v

# Run with very verbose output (shows test names)
uv run pytest tests/ -vv

# Run all tests with output capture disabled (see print statements)
uv run pytest tests/ -s
```

### Running Specific Test Categories

```bash
# Run only unit tests
uv run pytest tests/unit/

# Run only block tests
uv run pytest tests/blocks/

# Run only integration tests
uv run pytest tests/integration/

# Run only library workflow tests
uv run pytest tests/library/

# Run only security tests
uv run pytest tests/security/
```

### Running Specific Test Files

```bash
# Run a single test file
uv run pytest tests/unit/test_registry.py

# Run a specific test file with verbose output
uv run pytest tests/blocks/test_bash_block.py -v

# Run multiple specific files
uv run pytest tests/unit/test_dag.py tests/unit/test_variables.py
```

### Running Specific Tests

```bash
# Run a specific test class
uv run pytest tests/unit/test_registry.py::TestRegistryBasics

# Run a specific test method
uv run pytest tests/unit/test_registry.py::TestRegistryBasics::test_register_workflow

# Run all tests matching a pattern (keyword)
uv run pytest tests/ -k "registry"

# Run all tests NOT matching a pattern
uv run pytest tests/ -k "not slow"
```

### Coverage Reports

```bash
# Run tests with coverage report
uv run pytest tests/ --cov=workflows_mcp --cov-report=term-missing

# Generate HTML coverage report
uv run pytest tests/ --cov=workflows_mcp --cov-report=html

# View HTML report (opens in browser)
open htmlcov/index.html

# Coverage with branch coverage
uv run pytest tests/ --cov=workflows_mcp --cov-branch --cov-report=term-missing
```

### Advanced Testing Options

```bash
# Run tests in parallel (requires pytest-xdist)
uv run pytest tests/ -n auto

# Stop on first failure
uv run pytest tests/ -x

# Drop into debugger on failure
uv run pytest tests/ --pdb

# Show local variables on failure
uv run pytest tests/ -l

# Run only failed tests from last run
uv run pytest tests/ --lf

# Run failed tests first, then all others
uv run pytest tests/ --ff

# Measure test duration
uv run pytest tests/ --durations=10

# Show slow tests (>1s)
uv run pytest tests/ --durations=0 --durations-min=1.0
```

## Shared Fixtures

The test suite uses a hierarchical fixture system to reduce duplication and ensure consistent test setup.

### Root Fixtures (`tests/conftest.py`)

Available to all tests across all categories:

**Directory Fixtures** (Session Scope):
- `project_root` - Project root directory
- `src_dir` - Source code directory (`src/workflows_mcp/`)
- `templates_dir` - Templates directory
- `examples_dir` - Example workflows directory

**Registry Fixtures** (Function Scope):
- `registry` - Fresh empty WorkflowRegistry
- `registry_with_examples` - Registry pre-loaded with example workflows

**Executor Fixtures** (Function Scope):
- `executor` - Fresh WorkflowExecutor with empty context
- `executor_with_registry` - Executor with example workflows loaded

**Workflow Definition Fixtures** (Function Scope):
- `simple_workflow_def` - Minimal single-block workflow
- `multi_block_workflow_def` - Multi-block workflow with dependencies
- `sample_workflow_schema` - Standard WorkflowSchema instance

**Temporary File Fixtures** (Function Scope):
- `temp_workflow_file` - Single temporary workflow YAML file
- `temp_workflow_dir` - Directory with multiple workflow YAML files

**Test Data Fixtures** (Function Scope):
- `sample_block_inputs` - Sample block input values
- `sample_context` - Sample workflow execution context

### Category-Specific Fixtures

**Block Tests** (`tests/blocks/conftest.py`):
- `temp_file_path` - Temporary file path for file operations
- `temp_output_dir` - Temporary output directory
- `sample_template_content` - Jinja2 template content
- `sample_template_variables` - Template rendering variables
- `mock_bash_env` - Mock environment variables
- `bash_test_env` - Test environment for bash execution

**Integration Tests** (`tests/integration/conftest.py`):
- `populated_registry` - Registry loaded with temp workflows
- `executor_with_context` - Executor with pre-populated context
- `mock_workflow_dir` - Directory with mock workflow files
- `temp_template_dir` - Temporary directory for templates
- `integration_context` - Pre-populated integration context

### Using Fixtures in Tests

```python
def test_with_fixtures(executor, simple_workflow_def):
    """Example test using shared fixtures."""
    # executor is a fresh WorkflowExecutor instance
    # simple_workflow_def is a dict with workflow definition

    result = executor.execute_workflow(simple_workflow_def)
    assert result.is_success
```

**Fixture Scoping:**
- **Session:** Created once, shared across all tests (read-only paths)
- **Module:** Created once per test module
- **Function:** Created fresh for each test (default, ensures isolation)

## Adding New Tests

### Guidelines for Where to Add Tests

**Add to `unit/` when:**
- Testing a single component in isolation
- Testing core algorithms (DAG resolution, variable substitution)
- Testing data structures (schema validation, registry operations)
- Minimal external dependencies required

**Add to `blocks/` when:**
- Testing a specific block type
- Testing block input/output validation
- Testing block-specific functionality
- File operations, bash commands, async execution

**Add to `integration/` when:**
- Testing multiple components together
- Testing MCP server/tool functionality
- Testing full workflow execution
- Testing cross-component interactions

**Add to `library/` when:**
- Adding new workflow templates to the library
- Testing built-in workflow quality
- Validating workflow examples

**Add to `security/` when:**
- Testing output security
- Testing environment isolation
- Testing output sanitization
- Security-critical functionality

### Test Naming Conventions

**Test Files:**
- Prefix with `test_`
- Descriptive component name: `test_registry.py`, `test_bash_block.py`
- Place in appropriate category directory

**Test Classes:**
- Prefix with `Test`
- Use descriptive component name: `TestRegistryBasics`, `TestDAGResolver`
- Group related tests in classes

**Test Functions:**
- Prefix with `test_`
- Use descriptive action: `test_register_workflow`, `test_execute_bash_command`
- Be specific about what is being tested

### Example Test Templates

**Unit Test Example:**

```python
"""Test module for ComponentName.

Comprehensive tests for ComponentName functionality including:
- Basic operations
- Error handling
- Edge cases
"""

import pytest
from workflows_mcp.engine.component import ComponentName

class TestComponentBasics:
    """Basic ComponentName functionality tests."""

    def test_basic_operation(self):
        """Test basic component operation."""
        component = ComponentName()
        result = component.do_something()
        assert result.is_success

    def test_error_handling(self):
        """Test component error handling."""
        component = ComponentName()
        result = component.do_invalid_operation()
        assert not result.is_success
        assert "error message" in result.error

class TestComponentAdvanced:
    """Advanced ComponentName functionality tests."""

    def test_complex_scenario(self, fixture_name):
        """Test complex scenario using fixture."""
        component = ComponentName()
        result = component.complex_operation(fixture_name)
        assert result.is_success
        assert result.value.expected_field == "expected_value"
```

**Block Test Example:**

```python
"""Test module for BlockName block.

Tests for BlockName block including:
- Input validation
- Execution behavior
- Output validation
- Error conditions
"""

import pytest
from workflows_mcp.engine.blocks_category import BlockName, BlockNameInput

class TestBlockNameBasics:
    """Basic BlockName block tests."""

    def test_valid_input(self):
        """Test block with valid input."""
        inputs = {"param": "value"}
        block = BlockName(
            id="test_block",
            inputs=inputs,
            depends_on=[]
        )

        result = block.execute({})
        assert result.is_success
        assert result.value.output_field == "expected_value"

    def test_invalid_input(self):
        """Test block with invalid input."""
        with pytest.raises(ValueError):
            BlockName(
                id="test_block",
                inputs={"invalid": "param"},
                depends_on=[]
            )

class TestBlockNameExecution:
    """BlockName execution tests."""

    def test_execution_with_context(self, sample_context):
        """Test block execution with workflow context."""
        inputs = {"param": "${context_var}"}
        block = BlockName(
            id="test_block",
            inputs=inputs,
            depends_on=[]
        )

        result = block.execute(sample_context)
        assert result.is_success
```

**Integration Test Example:**

```python
"""Integration tests for FeatureName.

End-to-end tests for FeatureName functionality including:
- Multi-component interaction
- Full workflow execution
- System-level behavior
"""

import pytest
from workflows_mcp.engine.executor import WorkflowExecutor

class TestFeatureIntegration:
    """FeatureName integration tests."""

    def test_end_to_end_workflow(self, executor, registry_with_examples):
        """Test complete workflow execution."""
        workflow_def = {
            "name": "test-integration",
            "description": "Integration test workflow",
            "version": "1.0",
            "blocks": [
                {
                    "id": "step1",
                    "type": "BlockType1",
                    "inputs": {"param": "value"}
                },
                {
                    "id": "step2",
                    "type": "BlockType2",
                    "inputs": {"param": "${step1.output}"},
                    "depends_on": ["step1"]
                }
            ]
        }

        result = executor.execute_workflow(workflow_def)
        assert result.is_success
        assert "step1" in executor.context
        assert "step2" in executor.context

    def test_cross_component_interaction(
        self,
        executor_with_registry,
        integration_context
    ):
        """Test interaction between multiple components."""
        # Test implementation
        pass
```

## Best Practices

### Test Isolation

**Always use fresh fixtures:**
```python
def test_isolated(executor):
    # executor is a fresh instance for this test
    result = executor.execute_workflow(workflow_def)
    assert result.is_success
```

**Avoid shared mutable state:**
```python
# GOOD: Fresh fixture
def test_good(registry):
    registry.register_workflow(workflow)
    # Isolated to this test
```

### Assertion Style

**Use descriptive assertions:**
```python
# GOOD: Clear assertion with message
assert result.is_success, f"Expected success, got error: {result.error}"

# GOOD: Specific assertions
assert result.value.status == "completed"
assert result.value.exit_code == 0
assert "expected output" in result.value.stdout
```

**Assert one thing per test:**
```python
# GOOD: Focused test
def test_workflow_success(executor, simple_workflow_def):
    result = executor.execute_workflow(simple_workflow_def)
    assert result.is_success

def test_workflow_output(executor, simple_workflow_def):
    result = executor.execute_workflow(simple_workflow_def)
    assert "echo" in executor.context
```

### Error Testing

**Test expected errors explicitly:**
```python
# GOOD: Explicit error testing
def test_invalid_workflow(executor):
    invalid_workflow = {"name": "test"}  # Missing required fields

    with pytest.raises(ValueError) as exc_info:
        executor.execute_workflow(invalid_workflow)

    assert "blocks" in str(exc_info.value)

# GOOD: Result-based error testing
def test_block_failure(executor):
    result = executor.execute_block(failing_block)
    assert not result.is_success
    assert "expected error" in result.error
```

### Async Test Handling

**Use pytest-asyncio for async tests:**
```python
import pytest

@pytest.mark.asyncio
async def test_async_operation():
    """Test async operation."""
    result = await some_async_function()
    assert result.is_success
```

### Using Fixtures Effectively

**Request only needed fixtures:**
```python
# GOOD: Minimal fixtures
def test_simple(registry):
    result = registry.register_workflow(workflow)
    assert result.is_success
```

**Compose fixtures when needed:**
```python
@pytest.fixture
def configured_executor(executor, sample_context):
    """Executor with pre-configured context."""
    executor.context = sample_context
    return executor
```

## Troubleshooting

### Common Issues and Solutions

**Issue: Fixture not found**
```text
ERROR: fixture 'my_fixture' not found
```

**Solution:**
- Check fixture is defined in `conftest.py` in the test directory or parent
- Check fixture name spelling
- Check fixture scope (session fixtures in test module won't work)

**Issue: Import errors**
```text
ImportError: cannot import name 'ComponentName'
```

**Solution:**
- Check that you're importing from correct module
- Ensure `__init__.py` exists in all package directories
- Check Python path includes `src/` directory
- Run tests with `uv run pytest tests/` not `python -m pytest`

**Issue: Async test not running**
```text
RuntimeWarning: coroutine 'test_async' was never awaited
```

**Solution:**
- Add `@pytest.mark.asyncio` decorator
- Ensure async function uses `async def`

**Issue: Fixture scope problems**
```text
ScopeMismatch: fixture 'session_fixture' has scope 'session', but...
```

**Solution:**
- Function-scoped test can't use session-scoped fixture that depends on function-scoped fixture
- Change fixture scope or restructure dependencies
- Use function-scoped fixtures for test isolation

**Issue: Tests pass individually but fail together**
```bash
# uv run pytest test_file.py::test_one  # PASS
# uv run pytest test_file.py::test_two  # PASS
# uv run pytest test_file.py  # FAIL
```

**Solution:**
- Tests are sharing mutable state
- Use fresh fixtures instead of module/session scope
- Clean up state in teardown
- Check for global variables being modified

**Issue: Temporary files not cleaned up**
```text
# Test creates files that persist
```

**Solution:**
- Use `tmp_path` fixture provided by pytest
- Files in `tmp_path` are automatically cleaned up
- Don't use `/tmp` directly in tests

## Test Coverage

### Current Coverage Metrics

**Overall Coverage: 85%**

Coverage breakdown by module:
- Core engine: High coverage (90%+)
- Block implementations: Good coverage (85%+)
- MCP server: Moderate coverage (80%+)
- Utility modules: Variable coverage

### Coverage Goals

**Minimum Acceptable Coverage:**
- Core engine components: 90%
- Block implementations: 85%
- Integration components: 80%
- Overall project: 85%

**Critical Path Coverage:**
- 100% for security-critical code
- 100% for error handling paths
- 90%+ for main execution paths

### Checking Coverage

**Generate coverage report:**
```bash
# Terminal report
uv run pytest tests/ --cov=workflows_mcp --cov-report=term-missing

# HTML report (most detailed)
uv run pytest tests/ --cov=workflows_mcp --cov-report=html
open htmlcov/index.html

# XML report (for CI/CD)
uv run pytest tests/ --cov=workflows_mcp --cov-report=xml
```

**Coverage report interpretation:**
```text
Name                                Stmts   Miss  Cover   Missing
-----------------------------------------------------------------
src/workflows_mcp/__init__.py          12      0   100%
src/workflows_mcp/engine/dag.py       145     15    90%   23-25, 67-70
src/workflows_mcp/engine/executor.py  234     28    88%   145-150, 234-240
```

- **Stmts:** Total statements in file
- **Miss:** Statements not covered by tests
- **Cover:** Percentage covered
- **Missing:** Line numbers not covered

## Contributing Tests

When contributing to the test suite:

1. **Follow the structure** - Place tests in appropriate category directory
2. **Use shared fixtures** - Leverage existing fixtures when possible
3. **Write descriptive tests** - Clear test names and docstrings
4. **Test errors** - Include error condition tests
5. **Maintain coverage** - Ensure new code has test coverage
6. **Update documentation** - Add new fixtures to this README if created
7. **Run full suite** - Ensure all tests pass before committing

**Pre-commit checklist:**
```bash
# Run all tests
uv run pytest tests/

# Check coverage
uv run pytest tests/ --cov=workflows_mcp --cov-report=term-missing

# Run linting
uv run ruff check src/ tests/

# Run type checking
uv run mypy src/
```

## Additional Resources

**pytest Documentation:**
- Official docs: https://docs.pytest.org/
- Fixtures guide: https://docs.pytest.org/en/stable/fixture.html
- Parametrization: https://docs.pytest.org/en/stable/parametrize.html

**Project-Specific:**
- `ARCHITECTURE.md` - System architecture and design
- `CLAUDE.md` - Development guidelines and conventions
- `src/workflows_mcp/engine/` - Core engine implementation

**Testing Best Practices:**
- Test behavior, not implementation
- Use descriptive names and clear assertions
- Keep tests simple and focused
- Follow YAGNI, DRY, and KISS principles
