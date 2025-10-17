# Workflows MCP Server Architecture

Comprehensive system architecture for the DAG-based workflow orchestration MCP server.

## Table of Contents

- [System Overview](#system-overview)
- [Design Principles](#design-principles)
- [Core Components](#core-components)
- [Workflow Execution Model](#workflow-execution-model)
- [Variable Resolution System](#variable-resolution-system)
- [Conditional Execution](#conditional-execution)
- [Workflow Composition](#workflow-composition)
- [Block System](#block-system)
- [MCP Integration](#mcp-integration)
- [Security Model](#security-model)
- [Error Handling](#error-handling)

## System Overview

The Workflows MCP Server is a Model Context Protocol server that provides DAG-based workflow orchestration for LLM Agents. The system enables complex multi-step automation through YAML-defined workflows with dependency resolution, variable substitution, conditional execution, and workflow composition.

### Key Characteristics

- **Declarative**: Workflows defined in YAML with clear semantics
- **Async-First**: Non-blocking I/O operations throughout
- **Type-Safe**: Pydantic v2 validation for all data structures
- **Composable**: Workflows can call other workflows as blocks
- **Extensible**: Custom blocks and user-defined workflows
- **MCP-Native**: Exposes workflows as MCP tools to LLM Agent

## Design Principles

### 1. Simplicity Over Complexity

Follow YAGNI (You Aren't Gonna Need It) and KISS (Keep It Simple, Stupid) principles:

- Minimal abstractions: only DAGResolver, WorkflowBlock, WorkflowExecutor
- No over-engineering: single workflow type (no template/workflow distinction)
- Clear execution model: DAG resolution → variable resolution → execution
- Straightforward composition: ExecuteWorkflow block for calling workflows

### 2. Separation of Concerns

**Synchronous vs Async**:

- DAGResolver: Synchronous pure graph algorithms (no I/O)
- WorkflowExecutor: Async orchestration with block execution
- WorkflowBlock: Async execution units with I/O operations

**Validation vs Execution**:

- Schema validation at load time (Pydantic models)
- Input validation before execution (type checking)
- Output validation after execution (result verification)

**Planning vs Execution**:

- Planning phase: DAG resolution, topological sort, wave detection (synchronous)
- Execution phase: Block execution, variable resolution, output collection (async)

### 3. Explicit Over Implicit

- Dependencies declared via `depends_on` (no implicit ordering)
- Variable resolution via explicit `${var}` syntax
- Context isolation in workflow composition (no implicit parent context)
- Type annotations throughout (Pydantic v2, Python type hints)

### 4. Fail-Fast Validation

- YAML schema validation at load time
- Cyclic dependency detection before execution
- Variable reference validation during resolution
- Type validation for all inputs and outputs
- Circular workflow dependency detection

## Core Components

### DAGResolver (`engine/dag.py`)

**Purpose**: Dependency resolution and execution order determination

**Characteristics**:

- **Synchronous**: Pure in-memory graph algorithms, no I/O
- **Algorithm**: Kahn's algorithm for topological sort (O(V + E))
- **Wave Detection**: Parallel execution opportunity identification
- **Validation**: Cyclic dependency detection with clear error messages

**API**:

```python
class DAGResolver:
    def topological_sort(self) -> Result[list[str]]:
        """
        Perform topological sort to determine execution order.

        Returns:
            Result containing ordered list of block names or error if cyclic dependency
        """

    def get_execution_waves(self) -> Result[list[list[str]]]:
        """
        Group blocks into waves that can be executed in parallel.

        Returns:
            Result containing list of waves (each wave is a list of blocks that can run in parallel)
        """
```

**Execution Waves**: Groups of blocks that can execute in parallel:

```python
# Each wave is a list of block IDs that have no dependencies on each other
waves: list[list[str]] = [["block1"], ["block2", "block3"], ["block4"]]
```

### WorkflowExecutor (`engine/executor.py`)

**Purpose**: Async workflow orchestration and execution

**Characteristics**:

- **Async**: Non-blocking I/O operations
- **Wave-Based Execution**: Parallel execution within waves via `asyncio.gather`
- **Context Management**: Shared context for cross-block data flow
- **Variable Resolution**: Resolves `${var}` syntax before block execution
- **Conditional Execution**: Evaluates conditions before executing blocks

**Execution Flow**:

```text
1. Load workflow definition (YAML → Pydantic model)
2. Resolve DAG (synchronous planning phase)
3. For each execution wave:
   a. Resolve variables for all blocks in wave
   b. Evaluate conditions for all blocks in wave
   c. Execute blocks in parallel (asyncio.gather)
   d. Collect outputs into shared context
4. Return final outputs
```

**API**:

```python
class WorkflowExecutor:
    async def execute_workflow(
        self,
        workflow_name: str,
        inputs: dict[str, Any]
    ) -> Result[dict[str, Any]]:
        """Execute workflow with given inputs."""
```

### WorkflowBlock (`engine/block.py`)

**Purpose**: Base class for all workflow execution units

**Characteristics**:

- **Async**: Supports I/O operations (files, network, subprocesses)
- **Type-Safe**: Pydantic v2 validation for inputs and outputs
- **Result Monad**: Explicit success/failure handling without exceptions
- **Registry**: Dynamic block instantiation from YAML type names

**Block Lifecycle**:

```text
1. Instantiation from YAML block definition
2. Input validation (Pydantic model)
3. Async execution (user-defined logic)
4. Output validation (Pydantic model)
5. Result wrapping (success or failure)
```

**API**:

```python
class WorkflowBlock(ABC):
    @abstractmethod
    def input_model(self) -> type[BlockInput]:
        """Return Pydantic model for inputs."""

    @abstractmethod
    def output_model(self) -> type[BlockOutput]:
        """Return Pydantic model for outputs."""

    @abstractmethod
    async def execute(self, context: dict[str, Any]) -> Result[BlockOutput]:
        """Execute block logic asynchronously."""
```

### WorkflowRegistry (`engine/registry.py`)

**Purpose**: In-memory workflow storage and discovery

**Characteristics**:

- **Multi-Directory Loading**: Built-in + user-defined templates
- **Priority System**: User templates override built-in templates by name
- **Tag-Based Filtering**: Discover workflows by tags (AND semantics)
- **Metadata Extraction**: Name, description, blocks, inputs, tags
- **Source Tracking**: Know where each workflow came from

**API**:

```python
class WorkflowRegistry:
    def register(self, workflow: WorkflowDefinition) -> None:
        """Register workflow in registry."""

    def get(self, name: str) -> WorkflowDefinition | None:
        """Retrieve workflow by name."""

    def filter_by_tags(self, tags: list[str]) -> list[WorkflowDefinition]:
        """Filter workflows by tags (AND semantics)."""

    def load_from_directories(
        self,
        directories: list[Path],
        on_duplicate: Literal["skip", "overwrite", "error"] = "skip"
    ) -> Result[dict[str, int]]:
        """Load workflows from multiple directories with priority."""
```

### WorkflowSchema (`engine/schema.py`)

**Purpose**: Pydantic model defining YAML workflow structure with comprehensive validation

**Characteristics**:

- **Type-Safe Validation**: Validates workflow YAML files with detailed error messages
- **Schema Definition**: Defines required fields (name, description, blocks) and optional fields (inputs, outputs, tags)
- **Dependency Validation**: Validates block dependencies form a valid DAG with no cycles
- **Variable Reference Validation**: Validates `${var}` and `${block.outputs.field}` syntax against available inputs and blocks
- **Block Type Validation**: Ensures all block types exist in BLOCK_REGISTRY
- **Input Type Validation**: Validates input declarations with type checking for defaults
- **Conversion**: Transforms validated schema to WorkflowDefinition for executor

**Schema Structure**:

```python
class WorkflowSchema(BaseModel):
    # Metadata fields
    name: str                                           # Unique workflow identifier (kebab-case)
    description: str                                    # Human-readable description
    version: str = "1.0"                               # Semantic version
    author: str | None = None                          # Optional author
    tags: list[str] = []                               # Searchable tags

    # Workflow structure
    inputs: dict[str, WorkflowInputDeclaration] = {}   # Input parameter declarations
    blocks: list[BlockDefinition]                      # Block definitions (required)
    outputs: dict[str, str | WorkflowOutputSchema] = {}  # Output mappings

    def to_workflow_definition(self) -> WorkflowDefinition:
        """Convert to executor-compatible WorkflowDefinition."""

    @staticmethod
    def validate_yaml_dict(data: dict[str, Any]) -> Result[WorkflowSchema]:
        """Validate YAML dictionary with detailed error messages."""
```

**Validation Example**:

```python
import yaml
from workflows_mcp.engine.schema import WorkflowSchema

# Load and validate YAML
with open("workflow.yaml") as f:
    data = yaml.safe_load(f)

result = WorkflowSchema.validate_yaml_dict(data)
if result.is_success:
    schema = result.value
    workflow_def = schema.to_workflow_definition()
    # Ready for execution
else:
    print(f"Validation failed: {result.error}")
```

**YAML Example**:

```yaml
name: example-workflow
description: Example workflow with inputs and outputs
version: "1.0"
tags: [python, testing]

inputs:
  project_path:
    type: string
    description: Path to project directory
    default: "."

  branch_name:
    type: string
    description: Git branch name
    required: true

blocks:
  - id: setup
    type: CreateWorktree
    inputs:
      branch: "${branch_name}"
      path: ".worktrees/${branch_name}"

  - id: run_tests
    type: Shell
    inputs:
      command: "pytest ${project_path}"
    depends_on:
      - setup

  - id: deploy
    type: Shell
    inputs:
      command: "echo 'Deploying...'"
    condition: "${run_tests.outputs.exit_code} == 0"
    depends_on:
      - run_tests

outputs:
  test_result: "${run_tests.outputs.exit_code}"
```

### WorkflowDefinition (`engine/executor.py`)

**Purpose**: Validated, executor-compatible representation of a loaded workflow

**Characteristics**:

- **Executor Format**: Simplified data structure optimized for execution
- **Immutable After Load**: Represents validated workflow ready for execution
- **Context Integration**: Blocks contain raw inputs for variable resolution at runtime
- **No Validation Logic**: Assumes data is already validated by WorkflowSchema
- **Factory Method**: Can be created from dictionary for programmatic workflows

**API**:

```python
class WorkflowDefinition:
    def __init__(
        self,
        name: str,
        description: str,
        blocks: list[dict[str, Any]],
        inputs: dict[str, dict[str, Any]] | None = None,
    ):
        """Create workflow definition with validated data."""

    @staticmethod
    def from_dict(data: dict[str, Any]) -> WorkflowDefinition:
        """Create from dictionary (for programmatic workflows)."""
```

**Programmatic Example**:

```python
from workflows_mcp.engine.executor import WorkflowDefinition, WorkflowExecutor

# Create workflow programmatically
workflow_def = WorkflowDefinition(
    name="simple-workflow",
    description="Programmatic workflow example",
    blocks=[
        {
            "id": "echo_hello",
            "type": "EchoBlock",
            "inputs": {"message": "Hello ${name}"},
            "depends_on": []
        },
        {
            "id": "echo_goodbye",
            "type": "EchoBlock",
            "inputs": {"message": "Goodbye ${name}"},
            "depends_on": ["echo_hello"]
        }
    ],
    inputs={
        "name": {
            "type": "string",
            "description": "User name",
            "default": "World",
            "required": False
        }
    }
)

# Execute workflow
executor = WorkflowExecutor()
executor.load_workflow(workflow_def)
result = await executor.execute_workflow("simple-workflow", {"name": "Claude"})
```

**YAML Loading Pattern**:

```python
# Load from YAML (via WorkflowSchema)
from workflows_mcp.engine.loader import load_workflow_from_file

result = load_workflow_from_file("workflow.yaml")
if result.is_success:
    workflow_def = result.value  # WorkflowDefinition instance
    executor.load_workflow(workflow_def)
```

### WorkflowLoader (`engine/loader.py`)

**Purpose**: YAML workflow file loading with validation and discovery

**Characteristics**:

- **File Loading**: Reads YAML files and converts to WorkflowDefinition
- **Validation Integration**: Uses WorkflowSchema for comprehensive validation
- **Discovery**: Finds and loads all workflows in a directory
- **Error Handling**: Clear error messages for file I/O, YAML parsing, and validation failures
- **Batch Loading**: Discover workflows with partial failure tolerance (skip invalid, load valid)

**API**:

```python
def load_workflow_from_file(file_path: str | Path) -> Result[WorkflowDefinition]:
    """Load and validate a workflow from YAML file."""

def load_workflow_from_yaml(
    yaml_content: str,
    source: str = "<string>"
) -> Result[WorkflowDefinition]:
    """Load and validate a workflow from YAML string."""

def discover_workflows(directory: str | Path) -> Result[list[WorkflowDefinition]]:
    """Discover and load all YAML workflows in a directory."""

def validate_workflow_file(file_path: str | Path) -> Result[WorkflowSchema]:
    """Validate a workflow file without converting to WorkflowDefinition."""
```

**File Loading Example**:

```python
from workflows_mcp.engine.loader import load_workflow_from_file
from workflows_mcp.engine.executor import WorkflowExecutor

# Load single workflow
result = load_workflow_from_file("workflows/python-ci.yaml")
if result.is_success:
    workflow_def = result.value

    # Execute workflow
    executor = WorkflowExecutor()
    executor.load_workflow(workflow_def)
    exec_result = await executor.execute_workflow("python-ci", {"project_path": "."})
else:
    print(f"Failed to load: {result.error}")
```

**Directory Discovery Example**:

```python
from workflows_mcp.engine.loader import discover_workflows
from workflows_mcp.engine.registry import WorkflowRegistry

# Discover all workflows in directory
result = discover_workflows("templates/python")
if result.is_success:
    # Register all discovered workflows
    registry = WorkflowRegistry()
    for workflow_def in result.value:
        registry.register(workflow_def)

    print(f"Loaded {len(result.value)} workflows")
```

**YAML String Loading Example**:

```python
from workflows_mcp.engine.loader import load_workflow_from_yaml

yaml_content = """
name: inline-workflow
description: Workflow defined as string
blocks:
  - id: echo
    type: EchoBlock
    inputs:
      message: "Hello from inline workflow"
"""

result = load_workflow_from_yaml(yaml_content, source="inline-definition")
if result.is_success:
    executor.load_workflow(result.value)
```

**Validation-Only Example** (for linting tools):

```python
from workflows_mcp.engine.loader import validate_workflow_file

# Validate without executing
result = validate_workflow_file("workflow.yaml")
if result.is_success:
    schema = result.value
    print(f"✓ Valid workflow: {schema.name}")
    print(f"  Version: {schema.version}")
    print(f"  Blocks: {len(schema.blocks)}")
    print(f"  Tags: {', '.join(schema.tags)}")
else:
    print(f"✗ Validation failed: {result.error}")
```

### Result Monad (`engine/result.py`)

**Purpose**: Type-safe error handling with three-state model (success/failure/paused)

**Characteristics**:

- **Three-State Model**: Success, failure, or paused for interactive workflows
- **Metadata Support**: Additional context for debugging
- **Unwrap Methods**: Extract values with clear error handling
- **Composability**: Chain operations with error propagation
- **Pause Support**: Enable workflow interruption for LLM input

**API**:

```python
@dataclass
class Result[T]:
    value: T | None
    error: str | None
    metadata: dict[str, Any]
    is_paused: bool = False
    pause_data: PauseData | None = None

    @staticmethod
    def success(value: T, metadata: dict = None) -> Result[T]:
        """Create success result."""

    @staticmethod
    def failure(error: str, metadata: dict = None) -> Result[T]:
        """Create failure result."""

    @staticmethod
    def pause(prompt: str, **metadata) -> Result[T]:
        """Create paused result for interactive workflows."""

    def is_success(self) -> bool:
        """Check if result is successful."""

    def unwrap(self) -> T:
        """Extract value or raise exception."""
```

**Three-State Model**:

- `is_success=True`: Block completed successfully
- `is_success=False, is_paused=False`: Block failed (error)
- `is_success=False, is_paused=True`: Block paused (waiting for LLM input)

## Workflow Execution Model

The workflow engine executes workflows in distinct phases with optional checkpointing and pause/resume support.

### 1. DAG Resolution Phase (Synchronous)

**Input**: List of block definitions from YAML
**Output**: List of execution waves (groups of parallel blocks)

**Algorithm** (Kahn's Topological Sort):

```text
1. Identify blocks with no dependencies (in-degree = 0) → Wave 1
2. Remove Wave 1 blocks from graph
3. Identify newly independent blocks → Wave 2
4. Repeat until all blocks assigned to waves
5. If any blocks remain, cyclic dependency exists → error
```

**Parallel Execution Opportunities**:

```yaml
# Example: Diamond DAG pattern
blocks:
  - id: start
    type: Shell

  - id: parallel_a
    type: Shell
    depends_on: [start]

  - id: parallel_b
    type: Shell
    depends_on: [start]

  - id: merge
    type: Shell
    depends_on: [parallel_a, parallel_b]
```

**Execution Waves**:

- Wave 1: `[start]`
- Wave 2: `[parallel_a, parallel_b]` (execute in parallel)
- Wave 3: `[merge]`

### 2. Variable Resolution Phase

**Purpose**: Replace `${var}` syntax with actual values from context

**Resolution Rules**:

1. Workflow inputs: `${input_name}` → from runtime inputs (top-level)
2. Block outputs: `${block_id.outputs.field}` → from previous block results
3. Nested references: `${create_file.outputs.${input_var}}` → recursive resolution

**Resolution Order**:

```text
1. Resolve workflow inputs (from runtime inputs dict)
2. Resolve block outputs (from shared context)
3. Recursive resolution for nested references
4. Validation: fail if reference not found
```

**Example**:

```yaml
blocks:
  - id: create_dir
    type: Shell
    inputs:
      command: mkdir -p ${workspace}/output

  - id: write_file
    type: CreateFile
    inputs:
      path: "${create_dir.outputs.stdout}/data.txt"  # Depends on create_dir output
    depends_on: [create_dir]
```

### 3. Conditional Execution Phase

**Purpose**: Evaluate conditions to determine if blocks should execute

**Condition Evaluation**:

- **Safe AST Evaluation**: No arbitrary code execution
- **Boolean Expressions**: Comparisons, logical operators (and, or, not)
- **Access to Context**: Can reference inputs and previous block outputs

**Supported Operators**:

- Comparison: `==`, `!=`, `<`, `>`, `<=`, `>=`
- Logical: `and`, `or`, `not`
- Membership: `in`, `not in`

**Example**:

```yaml
blocks:
  - id: run_tests
    type: Shell
    inputs:
      command: pytest tests/

  - id: deploy
    type: ExecuteWorkflow
    inputs:
      workflow: "deploy-production"
    condition: "${run_tests.exit_code} == 0"
    depends_on: [run_tests]
```

### 4. Async Execution Phase

**Purpose**: Execute blocks in parallel waves with async I/O, checkpoint support, and pause detection

**Execution Strategy**:

```python
for wave_idx, wave in enumerate(execution_waves):
    # Resolve variables for all blocks in wave
    resolved_blocks = [resolve_variables(block, context) for block in wave]

    # Filter blocks based on conditions
    blocks_to_execute = [
        block for block in resolved_blocks
        if evaluate_condition(block.condition, context)
    ]

    # Execute blocks in parallel within wave
    results = await asyncio.gather(*[
        block.execute(context)
        for block in blocks_to_execute
    ])

    # Collect outputs into shared context
    for block, result in zip(blocks_to_execute, results):
        # Check for pause (interactive blocks)
        if result.is_paused:
            # Create pause checkpoint
            checkpoint_id = await create_pause_checkpoint(
                wave_index=wave_idx,
                paused_block=block,
                pause_data=result.pause_data
            )
            # Return pause result to LLM
            result.pause_data.checkpoint_id = checkpoint_id
            return result

        if result.is_success:
            context[block.id] = result.value
        else:
            return Result.failure(f"Block {block.id} failed: {result.error}")

    # Checkpoint after wave completion (if enabled)
    if checkpoint_config.enabled:
        await checkpoint_after_wave(wave_idx, context)
```

## Four-Namespace Context Architecture

### Overview

The workflow engine uses a **four-namespace architecture** that aligns with industry standard patterns from GitHub Actions, Tekton Pipelines, and Argo Workflows. This design provides clear separation between workflow inputs, block execution results, workflow metadata, and internal system state.

### The Four Root-Level Namespaces

The execution context has four distinct root-level namespaces:

1. **`inputs`**: Workflow input parameters provided at runtime
2. **`metadata`**: Workflow-level metadata (name, timestamps, execution info)
3. **`blocks`**: Block execution results with three-namespace structure per block
4. **`__internal__`**: System state (not accessible via variables, security boundary)

### Context Structure

During workflow execution, the context is organized as follows:

```python
context = {
    "inputs": {
        # Workflow input parameters
        "project_name": "my-project",
        "version": "1.0.0",
        "workspace": "/path/to/workspace"
    },
    "metadata": {
        # Workflow metadata
        "workflow_name": "build-project",
        "start_time": 1234567890.123,
        "execution_id": "exec_abc123"
    },
    "blocks": {
        # Block execution results
        "run_tests": {
            "inputs": {
                # Resolved inputs for this block
                "command": "pytest tests/",
                "working_dir": "/path/to/workspace"
            },
            "outputs": {
                # Block outputs (domain-specific data)
                "exit_code": 0,
                "success": True,
                "stdout": "All tests passed"
            },
            "metadata": {
                # Execution metadata
                "wave": 0,
                "execution_order": 0,
                "execution_time_ms": 1234.56,
                "started_at": "2025-10-11T14:00:00Z",
                "completed_at": "2025-10-11T14:00:01Z",
                "status": "success"
            }
        },
        "build": {
            "inputs": {...},
            "outputs": {...},
            "metadata": {...}
        }
    },
    "__internal__": {
        # System state (not accessible via variables)
        "executor": <WorkflowExecutor>,
        "workflow_stack": [],
        "checkpoint_store": <CheckpointStore>
    }
}
```

### Three-Namespace Block Structure

Each block in the `blocks` namespace has three sub-namespaces:

1. **`inputs`**: Resolved input values passed to the block
2. **`outputs`**: Results produced by the block (domain-specific data)
3. **`metadata`**: Execution metadata added by the orchestrator

### Variable Reference Syntax

Variable references use explicit namespace paths:

**Workflow Inputs:**
```yaml
${inputs.project_name}               # Access workflow input parameter
${inputs.workspace}                  # Access workflow input parameter
```

**Workflow Metadata:**
```yaml
${metadata.workflow_name}            # Access workflow metadata
${metadata.start_time}               # Access workflow metadata
```

**Block Outputs (explicit):**
```yaml
${blocks.run_tests.outputs.exit_code}      # Command exit code
${blocks.run_tests.outputs.stdout}         # Command output
${blocks.run_tests.outputs.success}        # Success boolean
```

**Block Outputs (shortcut):**
```yaml
${blocks.run_tests.exit_code}              # Auto-expands to outputs.exit_code
${blocks.run_tests.stdout}                 # Auto-expands to outputs.stdout
```

**Block Inputs (for debugging):**
```yaml
${blocks.run_tests.inputs.command}         # Access block input
```

**Block Metadata:**
```yaml
${blocks.run_tests.metadata.execution_time_ms}  # How long it took
${blocks.run_tests.metadata.wave}               # Which execution wave
```

**Security Boundary:**
```yaml
${__internal__.executor}                   # ❌ Blocked for security
```

### Complete Example

```yaml
name: build-and-test
description: Build project and run tests with conditional deployment

inputs:
  project_name:
    type: string
    description: Project name
    default: "my-project"

  version:
    type: string
    description: Version number
    required: true

  workspace:
    type: string
    description: Working directory
    default: "."

blocks:
  - id: run_tests
    type: Shell
    inputs:
      command: "pytest tests/"
      working_dir: "${inputs.workspace}"

  - id: build_package
    type: Shell
    inputs:
      command: "python -m build"
      working_dir: "${inputs.workspace}"
    depends_on: [run_tests]
    condition: "${blocks.run_tests.outputs.exit_code} == 0"

  - id: create_readme
    type: CreateFile
    inputs:
      path: "${inputs.workspace}/README.md"
      content: |
        # ${inputs.project_name}
        Version: ${inputs.version}

        ## Test Results
        Tests: ${blocks.run_tests.outputs.success}
        Build time: ${blocks.build_package.metadata.execution_time_ms}ms
    depends_on: [build_package]

outputs:
  test_success: "${blocks.run_tests.outputs.success}"
  build_success: "${blocks.build_package.outputs.success}"
  total_time: "${metadata.execution_time_seconds}"
```

### Industry Pattern Alignment

The four-namespace architecture aligns with industry standard workflow engines:

**GitHub Actions:**
```yaml
${{ inputs.parameter }}              # Workflow inputs
${{ steps.step_id.outputs.field }}   # Step outputs
```

**Tekton Pipelines:**
```yaml
$(params.parameter)                  # Pipeline parameters
$(tasks.task_id.results.field)      # Task results
```

**Argo Workflows:**
```yaml
{{inputs.parameters.parameter}}      # Workflow inputs
{{steps.step_id.outputs.result}}    # Step outputs
```

**Workflows MCP:**
```yaml
${inputs.parameter}                  # Workflow inputs
${blocks.block_id.outputs.field}     # Block outputs (explicit)
${blocks.block_id.field}             # Block outputs (shortcut)
${metadata.workflow_name}            # Workflow metadata
```

### Workflow Result Structure

When a workflow completes, the executor returns a dictionary with `outputs` and `metadata`:

```python
{
    "outputs": {
        # User-defined workflow outputs (from outputs: section in YAML)
        "test_success": True,
        "build_success": True,
        "total_time": 5.67
    },
    "metadata": {
        "workflow_name": "build-and-test",
        "execution_time_seconds": 5.67,
        "total_blocks": 3,
        "execution_waves": 2,
        "blocks": {
            # Each block with full three-namespace structure
            "run_tests": {
                "inputs": {
                    "command": "pytest tests/",
                    "working_dir": "/path/to/workspace"
                },
                "outputs": {
                    "exit_code": 0,
                    "success": True,
                    "stdout": "All tests passed"
                },
                "metadata": {
                    "wave": 0,
                    "execution_order": 0,
                    "execution_time_ms": 1234.56
                }
            },
            "build_package": {
                "inputs": {...},
                "outputs": {...},
                "metadata": {...}
            }
        }
    }
}
```

### Design Rationale

**Why Four Root-Level Namespaces?**

1. **Industry Alignment**: Matches patterns from GitHub Actions, Tekton, and Argo Workflows
2. **Clear Separation**: Workflow inputs, block results, and metadata are distinct
3. **Security Boundary**: `__internal__` namespace protects system state from variable access
4. **Predictable Structure**: Consistent organization improves debuggability
5. **Workflow Composition**: Clean isolation between parent and child workflow contexts

**Why Three Namespaces Per Block?**

1. **Separation of Concerns**:
   - `inputs` = what the workflow author provided
   - `outputs` = what the block produced (domain logic)
   - `metadata` = what the orchestrator tracked (system info)
2. **Observability**: Metadata enables debugging without mixing with business data
3. **Input Debugging**: Access to resolved input values for troubleshooting
4. **Consistency**: Same structure for all blocks simplifies tooling

**Block Output Examples:**

```yaml
# Shell block
${blocks.run_tests.outputs.exit_code}              # Command exit code
${blocks.run_tests.outputs.stdout}                 # Command output
${blocks.run_tests.outputs.success}                # Success boolean
${blocks.run_tests.metadata.execution_time_ms}     # How long it took

# EchoBlock
${blocks.echo.outputs.echoed}                      # Echoed message
${blocks.echo.inputs.message}                      # Original input
${blocks.echo.metadata.wave}                       # Which execution wave

# CreateFile block
${blocks.create_file.outputs.file_path}            # Created file path
${blocks.create_file.inputs.path}                  # Requested path
${blocks.create_file.metadata.started_at}          # When block started
```

## Variable Resolution System

### VariableResolver (`engine/variables.py`)

**Purpose**: Resolve `${var}` syntax in block inputs with four-namespace architecture support

**Resolution Patterns**:

1. **Workflow Inputs**: `${inputs.input_name}`

   ```yaml
   inputs:
     username:
       type: string
       description: User name

   blocks:
     - id: greet
       type: Shell
       inputs:
         command: echo "Hello, ${inputs.username}!"
   ```

2. **Workflow Metadata**: `${metadata.field_name}`

   ```yaml
   blocks:
     - id: log_workflow
       type: EchoBlock
       inputs:
         message: "Running workflow: ${metadata.workflow_name}"
   ```

3. **Block Outputs (explicit)**: `${blocks.block_id.outputs.field_name}`

   ```yaml
   blocks:
     - id: setup
       type: Shell
       inputs:
         command: which python

     - id: test
       type: Shell
       inputs:
         command: "${blocks.setup.outputs.stdout} -m pytest"
       depends_on: [setup]
   ```

4. **Block Outputs (shortcut)**: `${blocks.block_id.field_name}` (auto-expands to `outputs.field_name`)

   ```yaml
   blocks:
     - id: run_tests
       type: Shell
       inputs:
         command: pytest tests/

     - id: deploy
       type: Shell
       inputs:
         command: deploy.sh
       depends_on: [run_tests]
       condition: "${blocks.run_tests.exit_code} == 0"  # Shortcut for outputs.exit_code
   ```

5. **Block Inputs**: `${blocks.block_id.inputs.param_name}` (for debugging/logging)

   ```yaml
   blocks:
     - id: log_params
       type: EchoBlock
       inputs:
         message: "Test ran with: ${blocks.test.inputs.command}"
       depends_on: [test]
   ```

6. **Block Metadata**: `${blocks.block_id.metadata.field_name}` (orchestration info)

   ```yaml
   blocks:
     - id: report
       type: EchoBlock
       inputs:
         message: "Tests completed in ${blocks.test.metadata.execution_time_ms}ms"
       depends_on: [test]
   ```

**Recursive Resolution**:

```python
def resolve(value: str, context: dict[str, Any]) -> str:
    """
    Recursively resolve variables in value.

    Example:
        value = "${blocks.create_file.outputs.${inputs.field_name}}"
        context = {
            "inputs": {"field_name": "file_path"},
            "blocks": {
                "create_file": {
                    "outputs": {"file_path": "/tmp/file.txt"}
                }
            }
        }
        result = "/tmp/file.txt"
    """
    while "${" in value:
        # Extract variable reference
        var_ref = extract_variable(value)  # e.g., "blocks.create_file.outputs.file_path"

        # Resolve reference from context (with namespace awareness)
        resolved = lookup_in_context(var_ref, context)

        # Replace in value
        value = value.replace(f"${{{var_ref}}}", resolved)

    return value
```

**Namespace Resolution Order**:

1. Check if reference starts with `inputs.` → resolve from `context["inputs"]`
2. Check if reference starts with `metadata.` → resolve from `context["metadata"]`
3. Check if reference starts with `blocks.` → resolve from `context["blocks"]`
4. Check if reference starts with `__internal__.` → raise security error
5. Otherwise, for backward compatibility, check top-level context (deprecated)

## Conditional Execution

### ConditionEvaluator (`engine/variables.py`)

**Purpose**: Safe evaluation of boolean expressions for conditional execution with four-namespace support

**Safety Model**:

- **AST-Based Parsing**: Python's `ast` module for safe expression parsing
- **No Arbitrary Code**: Only allowed operations (comparisons, logical operators)
- **Sandboxed Execution**: Limited variable access (only context)
- **Security Boundary**: Blocks access to `__internal__` namespace

**Supported Expressions**:

```python
# Comparisons with block outputs
"${blocks.run_tests.outputs.exit_code} == 0"
"${blocks.analyze.outputs.count} > 10"
"${blocks.config.outputs.enabled} != False"

# Comparisons with workflow inputs
"${inputs.environment} == 'production'"
"${inputs.version} >= '2.0.0'"

# Logical operators
"${blocks.test.outputs.success} and ${blocks.lint.outputs.success}"
"${blocks.analyze.outputs.error_count} > 0 or ${blocks.analyze.outputs.warning_count} > 100"
"not ${inputs.skip_deployment}"

# Membership
"'error' in ${blocks.run_tests.outputs.stdout}"
"${inputs.status} not in ['failed', 'cancelled']"

# Shortcut syntax (auto-expands to outputs)
"${blocks.run_tests.exit_code} == 0"  # Same as blocks.run_tests.outputs.exit_code
```

**Evaluation Algorithm**:

```python
def evaluate(condition: str, context: dict[str, Any]) -> bool:
    """
    Safely evaluate boolean condition with namespace awareness.

    1. Resolve variables in condition string (with namespace support)
    2. Parse expression into AST
    3. Validate AST (only allowed operations, no __internal__ access)
    4. Evaluate AST with context
    5. Return boolean result
    """
    # Resolve variables (supports inputs, metadata, blocks namespaces)
    resolved_condition = resolve_variables(condition, context)

    # Parse AST
    tree = ast.parse(resolved_condition, mode='eval')

    # Validate (no function calls, no attribute access except allowed)
    validate_ast(tree)

    # Evaluate with empty builtins for security
    result = eval(compile(tree, '<string>', 'eval'), {"__builtins__": {}}, context)

    return bool(result)
```

**Complete Example**:

```yaml
blocks:
  - id: run_tests
    type: Shell
    inputs:
      command: pytest tests/

  - id: run_linter
    type: Shell
    inputs:
      command: ruff check .

  - id: deploy_staging
    type: Shell
    inputs:
      command: deploy.sh staging
    depends_on: [run_tests, run_linter]
    condition: >
      ${blocks.run_tests.outputs.exit_code} == 0 and
      ${blocks.run_linter.outputs.exit_code} == 0

  - id: deploy_production
    type: Shell
    inputs:
      command: deploy.sh production
    depends_on: [deploy_staging]
    condition: >
      ${blocks.deploy_staging.outputs.success} and
      ${inputs.environment} == 'production'
```

## Workflow Composition

### ExecuteWorkflow Block (`engine/blocks_workflow.py`)

**Purpose**: Call workflows as blocks for composition with clean context isolation

**Design Principles**:

- **Clean Isolation**: Child workflows receive ONLY explicitly passed inputs
- **No Parent Context**: Child workflows don't inherit parent's full context
- **Four-Namespace Structure**: Child workflows maintain the same namespace architecture
- **Automatic Namespacing**: Child outputs stored under `parent_context["blocks"][block_id]`
- **Circular Detection**: Prevent infinite recursion via execution stack tracking

**Context Management**:

```python
# Parent workflow execution context
parent_context = {
    "inputs": {
        "username": "alice",
        "environment": "production"
    },
    "metadata": {
        "workflow_name": "parent-workflow",
        "start_time": 1234567890.123
    },
    "blocks": {
        "setup": {
            "inputs": {"command": "which python"},
            "outputs": {"python_path": "/usr/bin/python3"},
            "metadata": {"wave": 0}
        }
    }
}

# ExecuteWorkflow block
block = ExecuteWorkflowBlock(
    id="run_tests",
    workflow="pytest-workflow",
    inputs={
        "python_path": "${blocks.setup.outputs.python_path}",  # Resolved before passing
        "test_dir": "tests/",
        "env": "${inputs.environment}"
    }
)

# Child workflow receives ONLY explicitly passed inputs:
child_context = {
    "inputs": {
        "python_path": "/usr/bin/python3",  # Resolved value from parent
        "test_dir": "tests/",
        "env": "production"  # Resolved value from parent
    },
    "metadata": {
        "workflow_name": "pytest-workflow",
        "start_time": 1234567891.456
    },
    "blocks": {
        # Child workflow's own blocks
    }
}

# Child outputs stored in parent context as:
parent_context["blocks"]["run_tests"] = {
    "inputs": {
        "workflow": "pytest-workflow",
        "inputs": {
            "python_path": "/usr/bin/python3",
            "test_dir": "tests/",
            "env": "production"
        }
    },
    "outputs": {
        # Child workflow's outputs
        "exit_code": 0,
        "coverage": 85.5,
        "passed": 42
    },
    "metadata": {
        "wave": 1,
        "execution_time_ms": 5678.90
    }
}
```

**Complete Example**:

```yaml
name: parent-workflow
description: Workflow that composes other workflows

inputs:
  project_path:
    type: string
    default: "."

blocks:
  - id: setup_env
    type: Shell
    inputs:
      command: which python

  - id: run_tests
    type: ExecuteWorkflow
    inputs:
      workflow: "pytest-workflow"
      inputs:
        python_path: "${blocks.setup_env.outputs.stdout}"
        test_dir: "${inputs.project_path}/tests"
    depends_on: [setup_env]

  - id: build_package
    type: ExecuteWorkflow
    inputs:
      workflow: "build-workflow"
      inputs:
        project_path: "${inputs.project_path}"
    depends_on: [run_tests]
    condition: "${blocks.run_tests.outputs.exit_code} == 0"

outputs:
  tests_passed: "${blocks.run_tests.outputs.passed}"
  build_success: "${blocks.build_package.outputs.success}"
```

**Circular Dependency Prevention**:

```python
class WorkflowExecutionStack:
    """Track workflow execution to prevent circular calls."""

    def __init__(self):
        self.stack: list[str] = []

    def enter(self, workflow_name: str):
        """Enter workflow execution."""
        if workflow_name in self.stack:
            raise CircularDependencyError(
                f"Circular workflow call: {' → '.join(self.stack + [workflow_name])}"
            )
        self.stack.append(workflow_name)

    def exit(self, workflow_name: str):
        """Exit workflow execution."""
        self.stack.pop()
```

**Context Isolation Benefits**:

1. **Predictable Behavior**: Child workflows only see their declared inputs
2. **Security**: Parent's internal state and other blocks not exposed
3. **Reusability**: Child workflows can be tested independently
4. **Composition**: Clean boundaries enable deep workflow nesting

## Checkpoint & Pause/Resume System

The workflow engine provides automatic checkpointing and interactive workflow capabilities through a comprehensive checkpoint and pause/resume system.

### Overview

**Three Core Features**:

1. **Automatic Checkpointing**: Workflow state snapshots after each execution wave
2. **Interactive Workflows**: Pause execution to request LLM input, then resume
3. **Crash Recovery**: Resume workflows from last successful checkpoint

**Design Philosophy**:

- **Zero Configuration**: Automatic checkpointing works out of the box
- **Backward Compatible**: Existing workflows work unchanged
- **Opt-In Complexity**: Interactive blocks are optional
- **Storage Flexible**: In-memory (default) with database migration path

### Core Components

#### CheckpointState (`engine/checkpoint.py`)

Complete workflow state snapshot for persistence:

```python
@dataclass
class CheckpointState:
    # Identification
    checkpoint_id: str                    # Format: "chk_<uuid>" or "pause_<uuid>"
    workflow_name: str
    created_at: float                     # Unix timestamp
    schema_version: int = 1               # For future migrations

    # Execution state
    runtime_inputs: dict[str, Any]        # Original workflow inputs
    context: dict[str, Any]               # Serialized context (filtered)
    completed_blocks: list[str]           # Block IDs completed so far
    current_wave_index: int               # Current wave in execution
    execution_waves: list[list[str]]      # All waves from DAG resolution
    block_definitions: dict[str, dict]    # Block configs for reconstruction

    # Nested workflow support
    workflow_stack: list[str]             # For circular dependency detection
    parent_checkpoint_id: str | None      # Link to parent if nested

    # Pause-specific (optional)
    paused_block_id: str | None           # Block that triggered pause
    pause_prompt: str | None              # Prompt for LLM
    pause_metadata: dict[str, Any] | None # Block-specific pause data
```

#### PauseData (`engine/checkpoint.py`)

Data structure for paused execution:

```python
@dataclass
class PauseData:
    checkpoint_id: str                              # Token for resuming
    prompt: str                                     # Message to LLM requesting input
    expected_response_schema: dict | None = None    # Optional JSON schema
    pause_metadata: dict[str, Any]                  # Block-specific context
```

#### CheckpointStore (`engine/checkpoint_store.py`)

Abstract interface for checkpoint persistence with pluggable backends:

```python
class CheckpointStore(ABC):
    async def save_checkpoint(self, state: CheckpointState) -> str:
        """Save checkpoint and return checkpoint_id."""

    async def load_checkpoint(self, checkpoint_id: str) -> CheckpointState | None:
        """Load checkpoint by ID."""

    async def list_checkpoints(
        self,
        workflow_name: str | None = None
    ) -> list[CheckpointMetadata]:
        """List all checkpoints, optionally filtered by workflow."""

    async def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """Delete checkpoint."""

    async def cleanup_expired(self, max_age_seconds: int) -> int:
        """Remove checkpoints older than max_age_seconds."""
```

**InMemoryCheckpointStore**: Thread-safe in-memory implementation (default)

**Future**: SQLite/PostgreSQL backends (see `docs/DATABASE_MIGRATION.md`)

#### InteractiveBlock (`engine/interactive.py`)

Base class for blocks that can pause workflow execution:

```python
class InteractiveBlock(WorkflowBlock):
    """Base class for blocks that can pause and request LLM input."""

    @abstractmethod
    async def execute(self, context: dict[str, Any]) -> Result[BlockOutput]:
        """Initial execution - may return Result.pause()."""

    @abstractmethod
    async def resume(
        self,
        context: dict[str, Any],
        llm_response: str,
        pause_metadata: dict[str, Any]
    ) -> Result[BlockOutput]:
        """Resume execution with LLM response."""
```

### Automatic Checkpointing

The executor creates checkpoints automatically after each execution wave without requiring any workflow changes.

**Checkpoint Creation**:

```python
# After each wave completes successfully
checkpoint_id = f"chk_{uuid.uuid4().hex}"
state = CheckpointState(
    checkpoint_id=checkpoint_id,
    workflow_name=workflow_name,
    runtime_inputs=original_inputs,
    context=serialize_context(context),  # Filtered for JSON serialization
    completed_blocks=completed_blocks,
    current_wave_index=wave_idx,
    execution_waves=execution_waves,
    block_definitions=block_defs,
    workflow_stack=context.get("__workflow_stack__", []),
    created_at=time.time()
)

await checkpoint_store.save_checkpoint(state)
```

**Context Serialization** (`engine/serialization.py`):

- Filters non-serializable values (executor references, file handles)
- Converts Path objects to strings
- Converts datetime objects to ISO format
- Validates checkpoint size limits
- Preserves workflow stack for circular dependency detection

### Interactive Workflows

Interactive blocks enable workflows to pause and request input from the LLM.

#### Built-In Interactive Blocks (`engine/blocks_interactive.py`)

**ConfirmOperation**: Yes/no confirmations

```yaml
- id: confirm_deploy
  type: ConfirmOperation
  inputs:
    message: "Deploy to production?"
    operation: "deploy_production"
```

**AskChoice**: Multiple choice selection

```yaml
- id: select_environment
  type: AskChoice
  inputs:
    question: "Select deployment environment:"
    choices: ["development", "staging", "production"]
```

**GetInput**: Free-form text input with validation

```yaml
- id: get_version
  type: GetInput
  inputs:
    prompt: "Enter version number (e.g., 1.2.3):"
    validation_pattern: "^\\d+\\.\\d+\\.\\d+$"
```

#### Pause/Resume Flow

```text
1. Workflow starts → Blocks execute in parallel waves
2. Interactive block pauses → Returns Result.pause(prompt="...")
3. Executor creates pause checkpoint → checkpoint_id = "pause_<uuid>"
4. Return to LLM → {status: "paused", checkpoint_id, prompt}
5. LLM provides input → Calls resume_workflow(checkpoint_id, response)
6. Executor restores context → Calls block.resume(context, response, metadata)
7. Block processes response → Returns Result.success() or Result.pause() again
8. Workflow continues → Remaining blocks execute
```

#### Multi-Pause Support

Workflows support multiple pause/resume cycles:

```yaml
blocks:
  - id: confirm_start
    type: ConfirmOperation
    inputs:
      message: "Start deployment?"

  - id: select_version
    type: AskChoice
    inputs:
      question: "Select version:"
      choices: ["1.0.0", "2.0.0", "3.0.0"]
    depends_on: [confirm_start]
    condition: "${confirm_start.confirmed} == true"

  - id: confirm_final
    type: ConfirmOperation
    inputs:
      message: "Proceed with version ${select_version.choice}?"
    depends_on: [select_version]
```

Each pause creates a new checkpoint, allowing the workflow to pause multiple times.

### Crash Recovery

Resume workflows from automatic checkpoints after crashes or failures.

**Resume Workflow**:

```python
# Load checkpoint
state = await checkpoint_store.load_checkpoint(checkpoint_id)

# Restore context
context = deserialize_context(state.context, executor)
context["__workflow_stack__"] = state.workflow_stack

# Continue execution from next wave
result = await continue_execution_from_wave(
    workflow_name=state.workflow_name,
    start_wave_index=state.current_wave_index + 1,
    context=context,
    completed_blocks=state.completed_blocks
)
```

**Resume from Pause**:

```python
# Load pause checkpoint
state = await checkpoint_store.load_checkpoint(checkpoint_id)

# Restore context
context = deserialize_context(state.context, executor)

# Resume paused block with LLM response
block = instantiate_block(state.paused_block_id)
result = await block.resume(context, llm_response, state.pause_metadata)

# If block completed, continue from next wave
# If block paused again, create new pause checkpoint and return
```

### Checkpoint Configuration

Configure checkpoint behavior via `CheckpointConfig`:

```python
@dataclass
class CheckpointConfig:
    enabled: bool = True                    # Feature toggle
    max_per_workflow: int = 10              # Keep last N checkpoints per workflow
    ttl_seconds: int = 86400                # 24 hours (automatic checkpoints)
    keep_paused: bool = True                # Never auto-delete paused checkpoints
    auto_cleanup: bool = True               # Trim old checkpoints after save
    cleanup_interval_seconds: int = 3600    # Background cleanup every hour
    max_checkpoint_size_mb: float = 10.0    # Size limit validation
```

**Production Configuration**:

```python
from workflows_mcp.engine.checkpoint_store import InMemoryCheckpointStore
from workflows_mcp.engine.checkpoint import CheckpointConfig

checkpoint_store = InMemoryCheckpointStore()
checkpoint_config = CheckpointConfig(
    enabled=True,
    max_per_workflow=50,
    ttl_seconds=7 * 86400,  # 7 days
    keep_paused=True,
    auto_cleanup=True
)

executor = WorkflowExecutor(
    checkpoint_store=checkpoint_store,
    checkpoint_config=checkpoint_config
)
```

### Example Workflows

#### Interactive Approval Workflow

```yaml
name: interactive-approval
description: Deployment with human approval checkpoint

blocks:
  - id: run_tests
    type: Shell
    inputs:
      command: "pytest tests/ -v"

  - id: confirm_deploy
    type: ConfirmOperation
    inputs:
      message: "Tests passed. Deploy to production?"
      operation: "deploy_production"
    depends_on: [run_tests]
    condition: "${run_tests.exit_code} == 0"

  - id: deploy
    type: Shell
    inputs:
      command: "kubectl apply -f k8s/"
    depends_on: [confirm_deploy]
    condition: "${confirm_deploy.confirmed} == true"

outputs:
  deployment_approved: "${confirm_deploy.confirmed}"
  deployment_success: "${deploy.success}"
```

**Usage**:

```python
# Execute workflow
result = await executor.execute_workflow("interactive-approval", {})

# Workflow pauses at confirm_deploy
# result = {
#   "status": "paused",
#   "checkpoint_id": "pause_abc123",
#   "prompt": "Confirm operation: Tests passed. Deploy to production?\n\nRespond with 'yes' or 'no'"
# }

# Resume with approval
result = await executor.resume_workflow("pause_abc123", "yes")

# Workflow completes
# result = {
#   "status": "success",
#   "outputs": {"deployment_approved": true, "deployment_success": true}
# }
```

#### Multi-Step Configuration Wizard

```yaml
name: config-wizard
description: Interactive project setup with multiple pauses

blocks:
  - id: select_type
    type: AskChoice
    inputs:
      question: "What type of project?"
      choices: ["python-fastapi", "node-express", "react-app"]

  - id: get_name
    type: GetInput
    inputs:
      prompt: "Enter project name (lowercase, hyphens):"
      validation_pattern: "^[a-z0-9-]+$"
    depends_on: [select_type]

  - id: confirm_creation
    type: ConfirmOperation
    inputs:
      message: "Create ${get_name.input_value} (${select_type.choice})?"
      operation: "create_project"
    depends_on: [get_name]

  - id: create_project
    type: Shell
    inputs:
      command: "mkdir -p ${get_name.input_value}"
    depends_on: [confirm_creation]
    condition: "${confirm_creation.confirmed} == true"

outputs:
  project_name: "${get_name.input_value}"
  project_type: "${select_type.choice}"
  created: "${create_project.success}"
```

This workflow pauses 3 times for user input, demonstrating multi-pause capabilities.

### Production Deployment

**Recommended Storage**: SQLite for production deployments

- Checkpoints survive server restarts
- Handles 100k-1M checkpoints
- File-based: no additional infrastructure
- ACID transactions for data safety
- Built into Python standard library

**Migration Path**: See `docs/DATABASE_MIGRATION.md` for complete SQLite migration guide with `SQLiteCheckpointStore` implementation.

**Cleanup Strategies**:

1. **Automatic Cleanup**: Cleanup on save (default, recommended)
2. **Background Task**: Periodic cleanup task
3. **Manual Cleanup**: On-demand via MCP tool

**Monitoring**:

- Checkpoint storage metrics (total, paused, automatic)
- Database size monitoring
- Performance monitoring (save/load latency)

For detailed production deployment guidance, monitoring patterns, and best practices, see `CHECKPOINT_ARCHITECTURE.md` sections on "Production Deployment" and "Monitoring and Observability".

## Block System

### Built-In Blocks

#### Shell (`blocks_bash.py`)

Execute shell commands with timeout and environment control.

**Inputs**:

- `command`: Shell command to execute
- `working_dir`: Working directory (optional)
- `timeout`: Timeout in seconds (default: 120)
- `env`: Environment variables (dict)

**Outputs**:

- `exit_code`: Command exit code
- `stdout`: Standard output
- `stderr`: Standard error
- `success`: Boolean (exit_code == 0)

#### CreateFile (`blocks_file.py`)

Create files with permissions and encoding control.

**Inputs**:

- `path`: File path
- `content`: File content
- `permissions`: Unix permissions (default: 0o644)
- `encoding`: Text encoding (default: utf-8)
- `overwrite`: Allow overwrite (default: false)

**Outputs**:

- `file_path`: Created file path
- `success`: Boolean

#### ReadFile (`blocks_file.py`)

Read text or binary files with size limits.

**Inputs**:

- `path`: File path
- `mode`: 'text' or 'binary' (default: text)
- `encoding`: Text encoding (default: utf-8)
- `max_size_mb`: Maximum file size (default: 10)

**Outputs**:

- `content`: File content
- `size_bytes`: File size
- `success`: Boolean

#### PopulateTemplate (`blocks_file.py`)

Render Jinja2 templates with variables.

**Inputs**:

- `template`: Jinja2 template string
- `variables`: Template variables (dict)
- `strict`: Strict mode (undefined variables are errors)

**Outputs**:

- `rendered`: Rendered template
- `success`: Boolean

#### ExecuteWorkflow (`blocks_workflow.py`)

Call another workflow as a block.

**Inputs**:

- `workflow`: Workflow name
- `inputs`: Workflow inputs (dict)
- `timeout`: Execution timeout (default: 600)

**Outputs**:

- All outputs from child workflow
- `workflow_name`: Executed workflow name
- `success`: Boolean
- `execution_time`: Time in seconds

#### ConfirmOperation (`blocks_interactive.py`)

Pause workflow to request yes/no confirmation from LLM.

**Inputs**:

- `message`: Confirmation message to display
- `operation`: Operation being confirmed
- `details`: Additional context (dict)

**Outputs**:

- `confirmed`: Boolean (whether user confirmed)
- `response`: Full LLM response

#### AskChoice (`blocks_interactive.py`)

Pause workflow to request multiple choice selection from LLM.

**Inputs**:

- `question`: Question to ask
- `choices`: Available choices (list of strings)

**Outputs**:

- `choice`: Selected choice (string)
- `choice_index`: Index of selected choice (int)

#### GetInput (`blocks_interactive.py`)

Pause workflow to request free-form text input from LLM.

**Inputs**:

- `prompt`: Prompt for LLM
- `validation_pattern`: Regex pattern for validation (optional)

**Outputs**:

- `input_value`: Input provided by LLM

### Custom Block Development

**Create Input/Output Models**:

```python
from workflows_mcp.engine.block import BlockInput, BlockOutput
from pydantic import Field

class MyBlockInput(BlockInput):
    param: str = Field(description="Parameter description")

class MyBlockOutput(BlockOutput):
    result: str
    success: bool
```

**Implement Block**:

```python
from workflows_mcp.engine.block import WorkflowBlock
from workflows_mcp.engine.result import Result

class MyBlock(WorkflowBlock):
    def input_model(self) -> type[BlockInput]:
        return MyBlockInput

    def output_model(self) -> type[BlockOutput]:
        return MyBlockOutput

    async def execute(self, context: dict[str, Any]) -> Result[BlockOutput]:
        inputs = self._validated_inputs

        # Implement block logic
        result = await some_async_operation(inputs.param)

        return Result.success(MyBlockOutput(
            result=result,
            success=True
        ))
```

**Register Block**:

```python
from workflows_mcp.engine.block import BLOCK_REGISTRY

BLOCK_REGISTRY["MyBlock"] = MyBlock
```

## MCP Integration

### Server Architecture (`server.py`, `tools.py`)

**FastMCP Integration**:

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("workflows")

@mcp.tool()
async def execute_workflow(workflow: str, inputs: dict = None) -> dict:
    """Execute a DAG-based workflow with inputs."""
    executor = WorkflowExecutor()
    result = await executor.execute_workflow(workflow, inputs or {})

    if result.is_paused:
        # Workflow paused for LLM input
        return {
            "status": "paused",
            "checkpoint_id": result.pause_data.checkpoint_id,
            "prompt": result.pause_data.prompt,
            "message": "Workflow paused - use resume_workflow to continue"
        }
    elif result.is_success:
        return {
            "status": "success",
            "outputs": result.value,
            "message": "Workflow completed successfully"
        }
    else:
        return {
            "status": "failure",
            "error": result.error,
            "message": "Workflow execution failed"
        }

@mcp.tool()
async def resume_workflow(checkpoint_id: str, llm_response: str = "") -> dict:
    """
    Resume a paused or checkpointed workflow.

    Use this to continue a workflow that was paused for interactive input,
    or to restart a workflow from a crash recovery checkpoint.
    """
    executor = get_global_executor()
    result = await executor.resume_workflow(checkpoint_id, llm_response)

    if result.is_paused:
        return {
            "status": "paused",
            "checkpoint_id": result.pause_data.checkpoint_id,
            "prompt": result.pause_data.prompt,
            "message": "Workflow paused again - use resume_workflow to continue"
        }
    elif result.is_success:
        return {
            "status": "success",
            "outputs": result.value,
            "message": "Workflow completed successfully"
        }
    else:
        return {
            "status": "failure",
            "error": result.error,
            "message": "Workflow execution failed"
        }

@mcp.tool()
async def list_checkpoints(workflow_name: str = "") -> dict:
    """
    List available workflow checkpoints.

    Shows all checkpoints, including both automatic checkpoints (for crash recovery)
    and pause checkpoints (for interactive workflows).
    """
    executor = get_global_executor()
    checkpoints = await executor.checkpoint_store.list_checkpoints(
        workflow_name if workflow_name else None
    )

    return {
        "checkpoints": [
            {
                "checkpoint_id": c.checkpoint_id,
                "workflow": c.workflow_name,
                "created_at": c.created_at,
                "created_at_iso": datetime.fromtimestamp(c.created_at).isoformat(),
                "is_paused": c.is_paused,
                "pause_prompt": c.pause_prompt,
                "type": "pause" if c.is_paused else "automatic"
            }
            for c in checkpoints
        ],
        "total": len(checkpoints)
    }

@mcp.tool()
async def get_checkpoint_info(checkpoint_id: str) -> dict:
    """
    Get detailed information about a specific checkpoint.

    Useful for inspecting checkpoint state before resuming.
    """
    executor = get_global_executor()
    state = await executor.checkpoint_store.load_checkpoint(checkpoint_id)

    if state is None:
        return {
            "found": False,
            "error": f"Checkpoint {checkpoint_id} not found or expired"
        }

    return {
        "found": True,
        "checkpoint_id": state.checkpoint_id,
        "workflow_name": state.workflow_name,
        "created_at": state.created_at,
        "created_at_iso": datetime.fromtimestamp(state.created_at).isoformat(),
        "is_paused": state.paused_block_id is not None,
        "paused_block_id": state.paused_block_id,
        "pause_prompt": state.pause_prompt,
        "completed_blocks": state.completed_blocks,
        "current_wave": state.current_wave_index,
        "total_waves": len(state.execution_waves),
        "progress_percentage": (
            len(state.completed_blocks) /
            sum(len(wave) for wave in state.execution_waves) * 100
        )
    }

@mcp.tool()
async def delete_checkpoint(checkpoint_id: str) -> dict:
    """
    Delete a checkpoint.

    Useful for cleaning up paused workflows that are no longer needed.
    """
    executor = get_global_executor()
    deleted = await executor.checkpoint_store.delete_checkpoint(checkpoint_id)

    return {
        "deleted": deleted,
        "checkpoint_id": checkpoint_id,
        "message": (
            "Checkpoint deleted successfully" if deleted
            else "Checkpoint not found"
        )
    }

@mcp.tool()
async def list_workflows(tags: list[str] | None = None) -> list[dict]:
    """List available workflows by tags."""
    workflows = registry.filter_by_tags(tags) if tags else registry.all()
    return [workflow.metadata() for workflow in workflows]

@mcp.tool()
async def get_workflow_info(workflow: str) -> dict:
    """Get detailed workflow metadata."""
    workflow_def = registry.get(workflow)
    if not workflow_def:
        return {"error": f"Workflow '{workflow}' not found"}

    return workflow_def.full_metadata()
```

### Workflow Discovery Flow

```text
User: "Run Python tests"
  ↓
LLM discovers tools: list_workflows, get_workflow_info, execute_workflow
  ↓
LLM: list_workflows(tags=["python", "testing"])
  ↓
MCP Server returns: [{"name": "run-pytest", ...}, ...]
  ↓
LLM: get_workflow_info("run-pytest")
  ↓
MCP Server returns: {"inputs": [...], "blocks": [...]}
  ↓
LLM: execute_workflow("run-pytest", {"test_dir": "tests/"})
  ↓
MCP Server executes workflow and returns results
  ↓
LLM presents results to user
```

## Security Model

### File Operations Security

**Safe Mode (Default)**:

- Only relative paths allowed
- No path traversal (`../`)
- No symlinks
- Size limits (10MB default)
- Must be within working directory

**Unsafe Mode (Opt-In)**:

- Absolute paths allowed
- Still blocks symlinks
- Still enforces size limits
- Requires explicit `unsafe: true` flag

### Custom File-Based Outputs

**Path Validation**:

```python
def validate_output_path(path: str, unsafe: bool = False) -> Result[Path]:
    """Validate output file path for security."""
    resolved = Path(path).resolve()

    if not unsafe:
        # Safe mode checks
        if resolved.is_absolute():
            return Result.failure("Absolute paths not allowed in safe mode")

        if ".." in path:
            return Result.failure("Path traversal not allowed")

        if not resolved.is_relative_to(Path.cwd()):
            return Result.failure("Path must be within working directory")

    if resolved.is_symlink():
        return Result.failure("Symlinks not allowed")

    if resolved.stat().st_size > MAX_FILE_SIZE:
        return Result.failure(f"File exceeds size limit: {MAX_FILE_SIZE}")

    return Result.success(resolved)
```

### Command Execution Security

**Shell Safety**:

- Timeout enforcement (prevents infinite loops)
- Environment variable isolation
- No shell injection (command passed as list when possible)
- Working directory validation

## Error Handling

### Result Monad Pattern

All workflow operations return `Result[T]`:

```python
# Success case
result = await block.execute(context)
if result.is_success:
    outputs = result.value
else:
    handle_error(result.error)

# Chaining operations
result = (
    await load_workflow(name)
    .and_then(lambda w: resolve_dag(w))
    .and_then(lambda waves: execute_waves(waves))
)
```

### Error Categories

**Load-Time Errors**:

- Invalid YAML syntax
- Schema validation failures
- Circular dependencies in DAG
- Invalid variable references

**Runtime Errors**:

- Block execution failures
- Timeout errors
- Variable resolution failures
- Condition evaluation errors

**Error Propagation**:

```text
Block fails → Wave fails → Workflow fails → MCP tool returns error
```

## Summary

The Workflows MCP Server provides a clean, composable architecture for DAG-based workflow orchestration:

- **Simple Abstractions**: DAGResolver, WorkflowBlock, WorkflowExecutor
- **Type-Safe**: Pydantic v2 validation throughout
- **Async-First**: Non-blocking I/O with parallel execution
- **Composable**: Workflows call workflows via ExecuteWorkflow
- **MCP-Native**: Natural LLM Agents integration
- **Secure**: Safe defaults with opt-in unsafe modes

This architecture enables complex automation while maintaining clarity, type safety, and extensibility.
