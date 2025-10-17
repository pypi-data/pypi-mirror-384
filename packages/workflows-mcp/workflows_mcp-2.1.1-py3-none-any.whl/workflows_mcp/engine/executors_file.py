"""File operation executors - CreateFile, ReadFile, PopulateTemplate.

This module provides file-based workflow executors that leverage the utilities
from block_utils.py to eliminate code duplication. All executors follow the
stateless executor pattern with comprehensive error handling via Result types.
"""

from typing import Any, ClassVar

from jinja2 import Environment, StrictUndefined, TemplateSyntaxError, UndefinedError
from pydantic import Field

from .block import BlockInput, BlockOutput
from .block_utils import ExecutionTimer, FileOperations, PathResolver
from .executor_base import (
    EXECUTOR_REGISTRY,
    BlockExecutor,
    ExecutorCapabilities,
    ExecutorSecurityLevel,
)
from .result import Result

# ============================================================================
# CreateFile Executor
# ============================================================================


class CreateFileInput(BlockInput):
    """Input model for CreateFile executor."""

    path: str = Field(description="File path (absolute or relative)")
    content: str = Field(description="File content to write")
    encoding: str = Field(default="utf-8", description="Text encoding")
    mode: int | str | None = Field(
        default=None,
        description="File permissions (Unix only, e.g., 0o644, 644, or '644')",
    )
    overwrite: bool = Field(default=True, description="Whether to overwrite existing file")
    create_parents: bool = Field(default=True, description="Create parent directories if missing")


class CreateFileOutput(BlockOutput):
    """Output model for CreateFile executor."""

    success: bool = Field(description="Whether file was created successfully")
    path: str = Field(description="Absolute path to created file")
    size_bytes: int = Field(description="File size in bytes")
    created: bool = Field(description="True if file was created, False if overwritten")


class CreateFileExecutor(BlockExecutor):
    """File creation executor.

    Creates files with specified content, encoding, and permissions.
    Leverages FileOperations utility for all I/O operations.

    Features:
    - Write content to file path (absolute or relative)
    - Support text encoding modes
    - Create parent directories automatically (optional)
    - Overwrite protection (optional, default: allow overwrite)
    - File permissions setting (optional, Unix-style)
    - Path traversal protection via PathResolver

    Example YAML usage:
        - id: create_readme
          type: CreateFile
          inputs:
            path: "${workspace_path}/README.md"
            content: "# ${project_name}\\n\\n${description}"
            create_parents: true
            overwrite: false
            mode: "644"  # Also accepts integer: 0o644 or 420
    """

    type_name: ClassVar[str] = "CreateFile"
    input_type: ClassVar[type[BlockInput]] = CreateFileInput
    output_type: ClassVar[type[BlockOutput]] = CreateFileOutput

    security_level: ClassVar[ExecutorSecurityLevel] = ExecutorSecurityLevel.TRUSTED
    capabilities: ClassVar[ExecutorCapabilities] = ExecutorCapabilities(can_write_files=True)

    async def execute(
        self, inputs: CreateFileInput, context: dict[str, Any]
    ) -> Result[CreateFileOutput]:
        """Create file with content."""
        timer = ExecutionTimer()

        # Resolve path with security validation
        path_result = PathResolver.resolve_and_validate(inputs.path, allow_traversal=True)
        if not path_result.is_success:
            return Result.failure(f"Invalid path: {path_result.error}")

        file_path = path_result.value

        # Check overwrite protection
        file_existed = file_path.exists()
        if file_existed and not inputs.overwrite:
            return Result.failure(f"File exists and overwrite=False: {file_path}")

        # Convert mode to integer if it's a string
        mode_int: int | None = None
        if inputs.mode is not None:
            try:
                if isinstance(inputs.mode, str):
                    # Convert string like "644" to octal integer 0o644
                    mode_int = int(inputs.mode, 8)
                else:
                    mode_int = inputs.mode
            except ValueError as e:
                return Result.failure(
                    f"Invalid mode value: {inputs.mode}. "
                    f"Expected octal string (e.g., '644') or integer (e.g., 0o644): {str(e)}"
                )

        # Write file using utility
        write_result = FileOperations.write_text(
            path=file_path,
            content=inputs.content,
            encoding=inputs.encoding,
            mode=mode_int,
            create_parents=inputs.create_parents,
        )

        if not write_result.is_success:
            return Result.failure(write_result.error)

        # Build output
        output = CreateFileOutput(
            success=True,
            path=str(file_path),
            size_bytes=write_result.value,
            created=(not file_existed),
        )

        return Result.success(output, metadata={"execution_time_ms": timer.elapsed_ms()})


# ============================================================================
# ReadFile Executor
# ============================================================================


class ReadFileInput(BlockInput):
    """Input model for ReadFile executor."""

    path: str = Field(description="File path to read")
    encoding: str = Field(default="utf-8", description="Text encoding")
    required: bool = Field(
        default=True, description="Whether file must exist (False returns empty string)"
    )
    max_size_bytes: int | None = Field(
        default=None, description="Maximum file size to read (safety limit)"
    )


class ReadFileOutput(BlockOutput):
    """Output model for ReadFile executor."""

    success: bool = Field(description="Whether file was read successfully")
    content: str = Field(description="File content")
    path: str = Field(description="Absolute path to file")
    size_bytes: int = Field(description="File size in bytes")
    found: bool = Field(description="Whether file was found")


class ReadFileExecutor(BlockExecutor):
    """File reading executor.

    Reads text files with encoding support and size limits.
    Leverages FileOperations utility for all I/O operations.

    Features:
    - Read file content (text mode)
    - Support multiple encodings (utf-8, ascii, latin-1, etc.)
    - File existence validation
    - Size limits (optional, prevent memory issues)
    - Path traversal protection via PathResolver
    - Optional mode: returns empty string if file not found

    Example YAML usage:
        - id: read_config
          type: ReadFile
          inputs:
            path: "${workspace_path}/config.json"
            max_size_bytes: 1048576  # 1MB limit

        - id: read_optional
          type: ReadFile
          inputs:
            path: "/path/to/optional.txt"
            required: false  # Returns empty string if missing
    """

    type_name: ClassVar[str] = "ReadFile"
    input_type: ClassVar[type[BlockInput]] = ReadFileInput
    output_type: ClassVar[type[BlockOutput]] = ReadFileOutput

    security_level: ClassVar[ExecutorSecurityLevel] = ExecutorSecurityLevel.TRUSTED
    capabilities: ClassVar[ExecutorCapabilities] = ExecutorCapabilities(can_read_files=True)

    async def execute(
        self, inputs: ReadFileInput, context: dict[str, Any]
    ) -> Result[ReadFileOutput]:
        """Read file content."""
        timer = ExecutionTimer()

        # Resolve path
        path_result = PathResolver.resolve_and_validate(inputs.path, allow_traversal=True)
        if not path_result.is_success:
            return Result.failure(f"Invalid path: {path_result.error}")

        file_path = path_result.value

        # Check if file exists
        if not file_path.exists():
            if inputs.required:
                return Result.failure(f"File not found: {file_path}")
            else:
                # Graceful: return empty content
                output = ReadFileOutput(
                    success=True,
                    content="",
                    path=str(file_path),
                    size_bytes=0,
                    found=False,
                )
                return Result.success(output, metadata={"execution_time_ms": timer.elapsed_ms()})

        # Read file using utility
        read_result = FileOperations.read_text(
            path=file_path,
            encoding=inputs.encoding,
            max_size_bytes=inputs.max_size_bytes,
        )

        if not read_result.is_success:
            return Result.failure(read_result.error)

        # Build output
        output = ReadFileOutput(
            success=True,
            content=read_result.value,
            path=str(file_path),
            size_bytes=file_path.stat().st_size,
            found=True,
        )

        return Result.success(output, metadata={"execution_time_ms": timer.elapsed_ms()})


# ============================================================================
# PopulateTemplate Executor
# ============================================================================


class PopulateTemplateInput(BlockInput):
    """Input model for PopulateTemplate executor."""

    template: str = Field(description="Jinja2 template string")
    variables: dict[str, Any] = Field(default_factory=dict, description="Template variables")
    output_path: str | None = Field(
        default=None, description="Optional file path to write rendered template"
    )
    encoding: str = Field(default="utf-8", description="Text encoding for output file")
    overwrite: bool = Field(default=True, description="Whether to overwrite existing output file")
    create_parents: bool = Field(default=True, description="Create parent directories if missing")
    strict: bool = Field(
        default=False,
        description="Fail on undefined variables (vs silent undefined behavior)",
    )
    trim_blocks: bool = Field(
        default=True, description="Trim whitespace after template blocks ({%...%})"
    )
    lstrip_blocks: bool = Field(
        default=True, description="Strip leading whitespace before template blocks"
    )


class PopulateTemplateOutput(BlockOutput):
    """Output model for PopulateTemplate executor."""

    success: bool = Field(description="Whether template was rendered successfully")
    content: str = Field(description="Rendered template content (alias: rendered)")
    output_path: str | None = Field(
        default=None, description="Path to output file (if output_path was provided)"
    )
    size_bytes: int = Field(description="Rendered content size in bytes")

    @property
    def rendered(self) -> str:
        """Alias for content to match old API."""
        return self.content


class PopulateTemplateExecutor(BlockExecutor):
    """Jinja2 template rendering executor.

    Renders Jinja2 templates with variables, optionally writing to file.

    Features:
    - Jinja2 template rendering with full template language support
    - Variable substitution via Jinja2 ({{ var }} patterns)
    - Custom rendering modes: strict (fail on undefined) or silent
    - Whitespace control (trim_blocks, lstrip_blocks)
    - Optional file output
    - Safe rendering (no arbitrary code execution)
    - Full Jinja2 filters and control structures (if, for, etc.)

    Example YAML usage (simple):
        - id: generate_readme
          type: PopulateTemplate
          inputs:
            template: |
              # {{ project_name }}

              Version: {{ version }}

              {% if features %}
              ## Features
              {% for feature in features %}
              - {{ feature }}
              {% endfor %}
              {% endif %}
            variables:
              project_name: "My Project"
              version: "1.0.0"
              features: ["Fast", "Reliable", "Simple"]
            strict: true

    Example YAML usage (with file output):
        - id: render_config
          type: PopulateTemplate
          inputs:
            template: |
              app_name: {{ app_name }}
              port: {{ port }}
              debug: {{ debug }}
            variables:
              app_name: "MyApp"
              port: 8080
              debug: false
            output_path: "${workspace}/config.yaml"
    """

    type_name: ClassVar[str] = "PopulateTemplate"
    input_type: ClassVar[type[BlockInput]] = PopulateTemplateInput
    output_type: ClassVar[type[BlockOutput]] = PopulateTemplateOutput

    security_level: ClassVar[ExecutorSecurityLevel] = ExecutorSecurityLevel.SAFE
    capabilities: ClassVar[ExecutorCapabilities] = ExecutorCapabilities(
        can_read_files=False,  # Only writes if output_path specified
        can_write_files=False,  # Will be upgraded dynamically
    )

    async def execute(
        self, inputs: PopulateTemplateInput, context: dict[str, Any]
    ) -> Result[PopulateTemplateOutput]:
        """Render Jinja2 template."""
        timer = ExecutionTimer()

        try:
            # Configure Jinja2 environment
            env_kwargs = {
                "autoescape": False,  # General templates, not HTML-specific
                "trim_blocks": inputs.trim_blocks,
                "lstrip_blocks": inputs.lstrip_blocks,
            }

            # Add undefined behavior only in strict mode
            if inputs.strict:
                env_kwargs["undefined"] = StrictUndefined

            env = Environment(**env_kwargs)

            # Parse and render template
            template = env.from_string(inputs.template)
            rendered = template.render(**inputs.variables)

        except TemplateSyntaxError as e:
            return Result.failure(f"Template syntax error at line {e.lineno}: {e.message}")
        except UndefinedError as e:
            return Result.failure(f"Undefined variable in template: {e}")
        except Exception as e:
            return Result.failure(f"Template rendering failed: {e}")

        # Write to file if output_path specified
        output_path_str = None
        if inputs.output_path:
            # Resolve path
            path_result = PathResolver.resolve_and_validate(
                inputs.output_path, allow_traversal=True
            )
            if not path_result.is_success:
                return Result.failure(f"Invalid output_path: {path_result.error}")

            file_path = path_result.value

            # Check overwrite protection
            if file_path.exists() and not inputs.overwrite:
                return Result.failure(f"Output file exists and overwrite=False: {file_path}")

            # Write file using utility
            write_result = FileOperations.write_text(
                path=file_path,
                content=rendered,
                encoding=inputs.encoding,
                create_parents=inputs.create_parents,
            )

            if not write_result.is_success:
                return Result.failure(write_result.error)

            output_path_str = str(file_path)

        # Build output
        output = PopulateTemplateOutput(
            success=True,
            content=rendered,
            output_path=output_path_str,
            size_bytes=len(rendered.encode(inputs.encoding)),
        )

        return Result.success(output, metadata={"execution_time_ms": timer.elapsed_ms()})


# ============================================================================
# Registration
# ============================================================================

# Register executors
EXECUTOR_REGISTRY.register(CreateFileExecutor())
EXECUTOR_REGISTRY.register(ReadFileExecutor())
EXECUTOR_REGISTRY.register(PopulateTemplateExecutor())
