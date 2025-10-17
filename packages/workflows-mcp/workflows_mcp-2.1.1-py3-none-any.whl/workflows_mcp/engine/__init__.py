"""Workflow engine core components.

This package contains the core workflow execution engine components adapted from the legacy
workflow system. Key components:

- Result: Type-safe Result monad for error handling
- DAGResolver: Dependency resolution via Kahn's algorithm (synchronous)
- WorkflowBlock: Async base class for workflow blocks
- BlockInput/BlockOutput: Pydantic v2 base classes for validation
- BLOCK_REGISTRY: Global registry for workflow block types
- WorkflowExecutor: Async workflow executor
- WorkflowDefinition: Workflow definition container
- WorkflowRegistry: Central registry for managing loaded workflow definitions
- WorkflowSchema: Pydantic v2 schema for YAML workflow validation
"""

# Import blocks to register in BLOCK_REGISTRY
from . import (
    blocks_bash,  # noqa: F401 - Register Shell
    blocks_example,  # noqa: F401 - Register EchoBlock
    blocks_file,  # noqa: F401 - Register CreateFile, ReadFile
    blocks_interactive,  # noqa: F401 - Register ConfirmOperation, AskChoice, GetInput
    blocks_state,  # noqa: F401 - Register ReadJSONState, WriteJSONState, MergeJSONState
    blocks_workflow,  # noqa: F401 - Register ExecuteWorkflow (Phase 2.2)
    executors_core,  # noqa: F401 - Register Shell and ExecuteWorkflow executors
    executors_file,  # noqa: F401 - Register CreateFile, ReadFile, PopulateTemplate executors
    executors_interactive,  # noqa: F401 - Register ConfirmOperation, AskChoice, GetInput executors
    executors_state,  # noqa: F401 - Register ReadJSONState, WriteJSONState, MergeJSONState executors
)
from .block import BLOCK_REGISTRY, BlockInput, BlockOutput, BlockRegistry, WorkflowBlock
from .dag import DAGResolver
from .executor import WorkflowDefinition, WorkflowExecutor
from .executor_base import EXECUTOR_REGISTRY
from .executors_core import (
    ExecuteWorkflowExecutor,
    ExecuteWorkflowInput,
    ExecuteWorkflowOutput,
    ShellExecutor,
    ShellInput,
    ShellOutput,
)
from .executors_file import (
    CreateFileExecutor,
    CreateFileInput,
    CreateFileOutput,
    PopulateTemplateExecutor,
    PopulateTemplateInput,
    PopulateTemplateOutput,
    ReadFileExecutor,
    ReadFileInput,
    ReadFileOutput,
)
from .executors_interactive import (
    AskChoiceExecutor,
    AskChoiceInput,
    AskChoiceOutput,
    ConfirmOperationExecutor,
    ConfirmOperationInput,
    ConfirmOperationOutput,
    GetInputExecutor,
    GetInputInput,
    GetInputOutput,
)
from .executors_state import (
    MergeJSONStateExecutor,
    MergeJSONStateInput,
    MergeJSONStateOutput,
    ReadJSONStateExecutor,
    ReadJSONStateInput,
    ReadJSONStateOutput,
    WriteJSONStateExecutor,
    WriteJSONStateInput,
    WriteJSONStateOutput,
)
from .loader import load_workflow_from_yaml
from .registry import WorkflowRegistry
from .response import WorkflowResponse
from .result import Result
from .schema import WorkflowSchema

__all__ = [
    "Result",
    "DAGResolver",
    "WorkflowBlock",
    "BlockInput",
    "BlockOutput",
    "BLOCK_REGISTRY",
    "BlockRegistry",
    "EXECUTOR_REGISTRY",
    "WorkflowExecutor",
    "WorkflowDefinition",
    "WorkflowRegistry",
    "WorkflowResponse",
    "WorkflowSchema",
    "load_workflow_from_yaml",
    "blocks_example",
    # Core Executors
    "ShellExecutor",
    "ShellInput",
    "ShellOutput",
    "ExecuteWorkflowExecutor",
    "ExecuteWorkflowInput",
    "ExecuteWorkflowOutput",
    # File Executors
    "CreateFileExecutor",
    "CreateFileInput",
    "CreateFileOutput",
    "ReadFileExecutor",
    "ReadFileInput",
    "ReadFileOutput",
    "PopulateTemplateExecutor",
    "PopulateTemplateInput",
    "PopulateTemplateOutput",
    # Interactive Executors
    "ConfirmOperationExecutor",
    "ConfirmOperationInput",
    "ConfirmOperationOutput",
    "AskChoiceExecutor",
    "AskChoiceInput",
    "AskChoiceOutput",
    "GetInputExecutor",
    "GetInputInput",
    "GetInputOutput",
    # State Executors
    "ReadJSONStateExecutor",
    "ReadJSONStateInput",
    "ReadJSONStateOutput",
    "WriteJSONStateExecutor",
    "WriteJSONStateInput",
    "WriteJSONStateOutput",
    "MergeJSONStateExecutor",
    "MergeJSONStateInput",
    "MergeJSONStateOutput",
]
