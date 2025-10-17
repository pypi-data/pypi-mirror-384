# Workflows MCP Server

MCP (Model Context Protocol) server exposing DAG-based workflow execution as tools for LLM Agents.

## Overview

The Workflows MCP Server provides a comprehensive workflow orchestration system integrated with the Model Context Protocol. It enables LLM Agents to discover and execute complex multi-step workflows through natural language interactions.

### Core Capabilities

**DAG-Based Execution**:

- Dependency resolution via Kahn's algorithm
- Parallel wave detection and concurrent execution
- Branch/converge patterns (diamond DAGs)
- Topological sort for optimal execution order
- Cyclic dependency detection

**Checkpoint & Pause/Resume**:

- **Automatic Checkpointing**: Workflow state snapshots after each execution wave
- **Interactive Workflows**: Pause execution to request LLM input, then resume
- **Crash Recovery**: Resume workflows from last successful checkpoint
- **Multi-Pause Support**: Handle multiple pause/resume cycles in single workflow
- **Storage Options**: In-memory (default) or SQLite for production

**Variable Resolution System**:

- `${var}` syntax for workflow inputs
- `${block_id.field}` syntax for cross-block references
- Recursive resolution with nested references
- Integration throughout workflow definitions

**Conditional Execution**:

- Boolean expression evaluation with safe AST parsing
- Conditional block execution based on previous results
- Adaptive workflow behavior

**Workflow Composition**:

- Call workflows as blocks via ExecuteWorkflow
- Multi-level composition support
- Circular dependency detection
- Clean context isolation with automatic output namespacing

**File Operations**:

- **CreateFile**: Create files with permissions, encoding, overwrite protection
- **ReadFile**: Read text/binary files with size limits and line-by-line mode
- **PopulateTemplate**: Jinja2 template rendering with full language support

**Interactive Blocks**:

- **ConfirmOperation**: Yes/no confirmations for human-in-the-loop workflows
- **AskChoice**: Multiple choice selection from LLM
- **GetInput**: Free-form text input with optional regex validation

**Shell Integration**:

- **Shell**: Execute shell commands with timeout, environment variables, working directory control

## Installation

This project uses `uv` for package management:

```bash
# Install dependencies
uv sync

# Run validation
uv run python tests/validate_structure.py

# Run server (stdio transport)
uv run python -m workflows_mcp
```

## Quick Start

### Basic Workflow Example

```yaml
name: hello-world
description: Simple greeting workflow
version: 1.0.0

inputs:
  - name: username
    type: string
    description: Name to greet
    required: true

blocks:
  - id: greet
    type: Shell
    inputs:
      command: echo "Hello, ${inputs.username}!"
```

### Using Variable Resolution

```yaml
blocks:
  - id: create_file
    type: CreateFile
    inputs:
      path: "${workspace}/README.md"
      content: "# ${project_name}"

  - id: read_back
    type: ReadFile
    inputs:
      path: "${create_file.file_path}"
    depends_on: [create_file]
```

### Conditional Execution

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

### Workflow Composition

```yaml
blocks:
  - id: setup
    type: ExecuteWorkflow
    inputs:
      workflow: "setup-python-env"
      inputs:
        working_dir: "/path/to/project"
        python_version: "3.12"

  - id: test
    type: Shell
    inputs:
      command: "${setup.python_path} -m pytest"
      working_dir: "/path/to/project"
    depends_on: [setup]
```

### Interactive Workflows (Pause/Resume)

```yaml
name: interactive-deployment
description: Deployment with human approval

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
```

**Usage Flow**:

```python
# Execute workflow
result = await executor.execute_workflow("interactive-deployment", {})
# Returns: {"status": "paused", "checkpoint_id": "pause_abc123", "prompt": "Tests passed. Deploy to production?"}

# Resume with confirmation
result = await executor.resume_workflow("pause_abc123", "yes")
# Returns: {"status": "success", "outputs": {...}}
```

## Configuration

### Custom Workflow Templates

By default, the MCP server loads workflows from the built-in `templates/` directory. You can add your own custom workflow directories using the `WORKFLOWS_TEMPLATE_PATHS` environment variable.

**Priority System**: User templates **override** built-in templates by name.

#### Environment Variable

Set `WORKFLOWS_TEMPLATE_PATHS` to a comma-separated list of directory paths:

```bash
export WORKFLOWS_TEMPLATE_PATHS="~/my-workflows,/opt/company-workflows"
```

Paths can use `~` for home directory expansion.

#### Claude Desktop Configuration

Add the environment variable to your `.mcp.json`:

```json
{
  "mcpServers": {
    "workflows": {
      "command": "uvx",
      "args": [
        "--from", "workflows-mcp",
        "workflows-mcp"
      ],
      "env": {
        "WORKFLOWS_LOG_LEVEL": "INFO",
        "WORKFLOWS_TEMPLATE_PATHS": "~/my-workflows,/opt/team-workflows"
      }
    }
  }
}
```

#### Use Cases

**Personal Customizations**:

```bash
WORKFLOWS_TEMPLATE_PATHS="~/.workflows"
```

**Team-Specific Workflows**:

```bash
WORKFLOWS_TEMPLATE_PATHS="/opt/company-workflows,~/my-experiments"
```

**Override Built-in Workflow**:
If you create `~/my-workflows/python-ci-pipeline.yaml`, it will replace the built-in `python-ci-pipeline` workflow.

#### Directory Structure Example

```bash
~/my-workflows/
├── custom-deploy.yaml          # New workflow
├── python-ci-pipeline.yaml     # Overrides built-in
└── team/
    ├── code-review.yaml        # Team-specific workflow
    └── release-process.yaml    # Team-specific workflow
```

## MCP Tools

The server exposes workflows as MCP tools for LLM Agents:

### execute_workflow

Execute a DAG-based workflow with inputs.

**Parameters**:

- `workflow` (str): Workflow name (e.g., 'python-ci-pipeline', 'setup-python-env')
- `inputs` (dict): Runtime inputs as key-value pairs for block variable substitution
- `async_execution` (bool): Run workflow in background and return immediately

**Returns**:

- `status`: Execution status (success/failure/paused)
- `outputs`: Workflow output values (if success)
- `checkpoint_id`: Checkpoint token (if paused)
- `prompt`: LLM prompt (if paused)
- `execution_time`: Total execution time in seconds
- `error`: Error message (if failed)

**Example** (Interactive Workflow):

```javascript
// Execute workflow - may pause
const result = await use_mcp_tool("workflows", "execute_workflow", {
  workflow: "interactive-approval",
  inputs: {}
});

if (result.status === "paused") {
  // Workflow paused for input
  console.log(result.prompt);  // "Tests passed. Deploy to production?"

  // Resume with response
  const final = await use_mcp_tool("workflows", "resume_workflow", {
    checkpoint_id: result.checkpoint_id,
    llm_response: "yes"
  });
}
```

### resume_workflow

Resume a paused or checkpointed workflow.

**Parameters**:

- `checkpoint_id` (str): Checkpoint token from pause or list_checkpoints
- `llm_response` (str): LLM response to the pause prompt (required for paused workflows)

**Returns**:

- `status`: Execution status (success/failure/paused)
- `outputs`: Workflow output values (if success)
- `checkpoint_id`: New checkpoint token (if paused again)
- `prompt`: New LLM prompt (if paused again)
- `error`: Error message (if failed)

**Use Cases**:

- Resume paused interactive workflow with LLM input
- Restart workflow from crash recovery checkpoint
- Continue multi-pause workflow sequences

### list_checkpoints

List available workflow checkpoints.

**Parameters**:

- `workflow_name` (str, optional): Filter by workflow name (empty = all workflows)

**Returns**:

- `checkpoints`: List of checkpoint metadata
  - `checkpoint_id`: Checkpoint token
  - `workflow`: Workflow name
  - `created_at`: Unix timestamp
  - `created_at_iso`: ISO format timestamp
  - `is_paused`: Whether checkpoint is from pause
  - `pause_prompt`: Pause prompt (if paused)
  - `type`: "pause" or "automatic"
- `total`: Total checkpoint count

**Example**:

```python
checkpoints = await list_checkpoints(workflow_name="python-ci-pipeline")
# Returns checkpoints for specific workflow
```

### get_checkpoint_info

Get detailed information about a specific checkpoint.

**Parameters**:

- `checkpoint_id` (str): Checkpoint token

**Returns**:

- `found`: Whether checkpoint exists
- `checkpoint_id`: Checkpoint token
- `workflow_name`: Workflow name
- `created_at`: Unix timestamp
- `created_at_iso`: ISO format timestamp
- `is_paused`: Whether checkpoint is from pause
- `paused_block_id`: Block that paused (if paused)
- `pause_prompt`: Pause prompt (if paused)
- `completed_blocks`: List of completed block IDs
- `current_wave`: Current execution wave index
- `total_waves`: Total number of waves
- `progress_percentage`: Workflow completion percentage

**Use Cases**:

- Inspect checkpoint state before resuming
- Monitor workflow execution progress
- Debug checkpoint issues

### delete_checkpoint

Delete a checkpoint.

**Parameters**:

- `checkpoint_id` (str): Checkpoint token to delete

**Returns**:

- `deleted`: Whether checkpoint was deleted
- `checkpoint_id`: Checkpoint token
- `message`: Status message

**Use Cases**:

- Clean up paused workflows that are no longer needed
- Manage checkpoint storage
- Remove old automatic checkpoints

### list_workflows

List available workflows with optional tag filtering.

**Parameters**:

- `tags` (list[str], optional): Filter workflows by tags (uses AND semantics)

**Returns**:
List of workflow metadata dictionaries with name, description, tags, blocks, inputs.

**Examples**:

- `list_workflows()` - All workflows
- `list_workflows(tags=["python"])` - All Python-related workflows
- `list_workflows(tags=["python", "testing"])` - Workflows with both tags

### get_workflow_info

Get detailed information about a specific workflow.

**Parameters**:

- `workflow` (str): Workflow name/identifier

**Returns**:
Comprehensive workflow metadata including name, description, version, tags, blocks with dependencies, inputs, and outputs.

## Architecture

### Core Components

**DAGResolver** (`engine/dag.py`):

- Synchronous graph algorithms (pure in-memory operations)
- Kahn's algorithm for topological sort with O(V + E) complexity
- Execution wave detection for parallel execution opportunities
- Cyclic dependency detection with meaningful error messages

**Result Monad** (`engine/result.py`):

- Type-safe error handling without exceptions
- Success/failure pattern with metadata support
- Unwrap methods for value extraction

**WorkflowBlock** (`engine/block.py`):

- Async base class for workflow execution units
- Pydantic v2 validation for inputs and outputs
- Result monad integration for error handling
- Block registry for dynamic instantiation from YAML

**WorkflowSchema** (`engine/schema.py`):

- Pydantic models for YAML workflow definitions
- Comprehensive validation (blocks, inputs, dependencies)
- Type-safe workflow representation

**WorkflowLoader** (`engine/loader.py`):

- Directory scanning with recursive template discovery
- YAML parsing with error handling
- Validation against WorkflowSchema

**WorkflowRegistry** (`engine/registry.py`):

- In-memory workflow storage with tag-based filtering
- Metadata extraction (name, description, blocks, inputs, tags)
- Fast lookup by workflow name
- Multi-directory loading with priority-based override

**FastMCP Server** (`server.py`):

- Official Anthropic MCP Python SDK
- Stdio transport (default)
- Tool registration via decorators

### Design Principles

Following official Anthropic MCP SDK patterns:

- Minimal structure (not single file, not over-engineered)
- Type hints throughout (Pydantic v2 compatible)
- Async-first patterns for I/O operations
- Pure algorithms for graph operations (DAG, Result)

### Execution Model

The workflow engine follows a **declarative DAG-based execution model**:

1. **Workflow Definition** (YAML) → blocks with dependencies
2. **DAG Resolution** → topological sort determines execution order
3. **Variable Resolution** → cross-block references resolved from context
4. **Wave Execution** → blocks run in parallel waves based on dependencies
5. **Result Accumulation** → each block's output stored in shared context

## Development

### Requirements

- Python 3.12+
- uv package manager
- Dependencies: `mcp[cli]`, `pydantic>=2.0`, `pyyaml`

### Testing

Run the test suite:

```bash
# Run all tests
uv run pytest

# Run with coverage report
uv run pytest --cov=workflows_mcp --cov-report=term-missing

# Run specific test suites
uv run pytest tests/test_schema_integration.py    # YAML schema tests
uv run pytest tests/test_loader.py                # Workflow loader tests
uv run pytest tests/test_registry.py              # Registry tests
uv run pytest tests/test_bash_block.py            # Shell block tests
uv run pytest tests/test_file_blocks.py           # File blocks tests
uv run pytest tests/test_variables.py             # Variable resolution tests
uv run pytest tests/test_conditionals.py          # Conditional execution tests
uv run pytest tests/test_workflow_composition.py  # ExecuteWorkflow composition tests
uv run pytest tests/test_mcp_integration.py       # End-to-end MCP tests
```

All async tests are properly configured with pytest-asyncio auto mode.

### Validation

Run the comprehensive validation script:

```bash
uv run python tests/validate_structure.py
```

This validates:
- Directory structure
- All imports resolve correctly
- FastMCP server initializes
- DAGResolver algorithms work
- Result monad functions correctly
- WorkflowBlock async patterns work
- YAML workflow loading system
- pyproject.toml configuration

## Documentation

### Architecture & Guides

- [ARCHITECTURE.md](ARCHITECTURE.md) - Comprehensive system architecture and design
- [CHECKPOINT_ARCHITECTURE.md](CHECKPOINT_ARCHITECTURE.md) - Checkpoint system technical details
- [docs/INTERACTIVE_BLOCKS_TUTORIAL.md](docs/INTERACTIVE_BLOCKS_TUTORIAL.md) - Interactive blocks guide
- [docs/DATABASE_MIGRATION.md](docs/DATABASE_MIGRATION.md) - SQLite migration guide
- [Workflow Templates](src/workflows_mcp/templates/README.md) - Built-in workflow catalog
- [Example Workflows](src/workflows_mcp/templates/examples/README.md) - Tutorial workflows

## Project Structure

```bash
workflows-mcp/
├── src/workflows_mcp/
│   ├── __init__.py              # Package initialization
│   ├── __main__.py              # Entry point for uv run
│   ├── server.py                # FastMCP initialization
│   ├── tools.py                 # MCP tool implementations
│   ├── templates/               # Workflow templates
│   │   ├── ci/                  # CI/CD pipeline workflows
│   │   ├── examples/            # Tutorial workflows
│   │   │   ├── interactive-approval.yaml          # Interactive approval workflow
│   │   │   └── multi-step-questionnaire.yaml     # Multi-pause configuration wizard
│   │   ├── files/               # File processing workflows
│   │   ├── git/                 # Git operation workflows
│   │   ├── node/                # Node.js project workflows
│   │   └── python/              # Python project workflows
│   └── engine/                  # Workflow engine
│       ├── __init__.py          # Engine exports
│       ├── dag.py               # DAG dependency resolution
│       ├── result.py            # Result monad with pause support
│       ├── block.py             # WorkflowBlock base class
│       ├── blocks_example.py    # Example async blocks (EchoBlock)
│       ├── blocks_bash.py       # Shell block
│       ├── blocks_file.py       # File blocks: CreateFile, ReadFile, PopulateTemplate
│       ├── blocks_workflow.py   # ExecuteWorkflow block
│       ├── blocks_interactive.py # Interactive blocks: ConfirmOperation, AskChoice, GetInput
│       ├── checkpoint.py        # CheckpointState, PauseData, CheckpointConfig
│       ├── checkpoint_store.py  # CheckpointStore interface, InMemoryCheckpointStore
│       ├── serialization.py     # Context serialization utilities
│       ├── interactive.py       # InteractiveBlock base class
│       ├── variables.py         # Variable resolution & conditional execution
│       ├── executor.py          # Async workflow executor with checkpointing
│       ├── schema.py            # YAML workflow schema
│       ├── loader.py            # YAML workflow loader
│       └── registry.py          # Workflow registry
├── docs/                        # Documentation
│   ├── INTERACTIVE_BLOCKS_TUTORIAL.md  # Interactive blocks guide (~800 lines)
│   └── DATABASE_MIGRATION.md           # SQLite migration guide (~900 lines)
├── tests/                       # Test suite
├── pyproject.toml               # uv project configuration
├── ARCHITECTURE.md              # Architecture documentation
└── CLAUDE.md                    # Development guide
```

## References

- [MCP Official Docs](https://modelcontextprotocol.io/docs/develop/build-server)
- [Anthropic Python MCP SDK](https://github.com/modelcontextprotocol/python-sdk)
- [CLAUDE.md](CLAUDE.md) - Development guidelines
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture

## License

See LICENSE file for details
