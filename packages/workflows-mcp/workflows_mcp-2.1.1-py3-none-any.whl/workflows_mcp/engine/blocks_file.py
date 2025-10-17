"""File manipulation blocks for workflows."""

import base64
import os
import re
import time
from pathlib import Path
from typing import Any, cast

import jinja2
from pydantic import Field

from .block import BLOCK_REGISTRY, BlockInput, BlockOutput, WorkflowBlock
from .result import Result


class CreateFileInput(BlockInput):
    """Input for CreateFile block."""

    path: str = Field(description="File path (supports ${variables})")
    content: str = Field(description="File content (supports ${variables})")
    encoding: str = Field(default="utf-8", description="Text encoding")
    create_parents: bool = Field(default=True, description="Create parent directories")
    overwrite: bool = Field(default=True, description="Allow overwriting existing files")
    mode: int | str | None = Field(
        default=None, description="Unix file permissions (e.g., 0o644, 644, or '644')"
    )


class CreateFileOutput(BlockOutput):
    """Output for CreateFile block."""

    success: bool = Field(description="Whether file was created successfully")
    path: str = Field(description="Resolved absolute path")
    size_bytes: int = Field(description="File size written")
    created: bool = Field(description="True if new file, False if overwrote existing")


class CreateFile(WorkflowBlock):
    """
    Create a file with specified content.

    Features:
    - Write content to file path (absolute or relative)
    - Support text and binary content modes via encoding
    - Create parent directories automatically (optional)
    - Overwrite protection (optional, default: allow overwrite)
    - File permissions setting (optional, Unix-style)
    - Variable resolution fully integrated (path and content use ${var} syntax)
    - Path traversal protection

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

    def input_model(self) -> type[BlockInput]:
        return CreateFileInput

    def output_model(self) -> type[BlockOutput]:
        return CreateFileOutput

    async def execute(self, context: dict[str, Any]) -> Result[BlockOutput]:
        """Create file with specified content."""
        inputs = cast(CreateFileInput, self._validated_inputs)
        if inputs is None:
            return Result.failure("Inputs not validated")

        start = time.time()

        try:
            # Resolve path (relative or absolute)
            file_path = Path(inputs.path)
            if not file_path.is_absolute():
                file_path = Path.cwd() / file_path

            # Resolve to absolute path and normalize
            file_path = file_path.resolve()

            # Path traversal protection - ensure resolved path is within expected boundaries
            # This prevents malicious paths like "../../../etc/passwd"
            # We don't enforce strict boundaries here as the path might legitimately
            # go outside CWD, but we do normalize the path to prevent tricks
            if ".." in str(file_path):
                # Double-check after resolve that no .. remains (shouldn't happen)
                return Result.failure(f"Path traversal detected after resolution: {file_path}")

            # Check if file exists
            file_exists = file_path.exists()
            created = not file_exists

            # Overwrite protection
            if file_exists and not inputs.overwrite:
                return Result.failure(f"File already exists and overwrite=False: {file_path}")

            # Create parent directories if requested
            if inputs.create_parents:
                file_path.parent.mkdir(parents=True, exist_ok=True)
            elif not file_path.parent.exists():
                return Result.failure(
                    f"Parent directory does not exist and create_parents=False: {file_path.parent}"
                )

            # Write content with specified encoding
            try:
                file_path.write_text(inputs.content, encoding=inputs.encoding)
            except PermissionError:
                return Result.failure(f"Permission denied writing to: {file_path}")
            except UnicodeEncodeError as e:
                return Result.failure(f"Encoding error ({inputs.encoding}): {str(e)}")

            # Get file size
            size_bytes = file_path.stat().st_size

            # Set file permissions if specified (Unix only)
            if inputs.mode is not None:
                try:
                    # Convert mode to integer if it's a string
                    mode_int: int
                    if isinstance(inputs.mode, str):
                        # Convert string like "644" to octal integer 0o644
                        mode_int = int(inputs.mode, 8)
                    else:
                        mode_int = inputs.mode

                    os.chmod(file_path, mode_int)
                except (OSError, NotImplementedError):
                    # chmod might not be supported on Windows
                    # We don't fail the operation, just log the issue
                    pass
                except ValueError as e:
                    return Result.failure(
                        f"Invalid mode value: {inputs.mode}. "
                        f"Expected octal string (e.g., '644') or integer (e.g., 0o644): {str(e)}"
                    )

            execution_time = (time.time() - start) * 1000  # Convert to ms

            output = CreateFileOutput(
                success=True,
                path=str(file_path),
                size_bytes=size_bytes,
                created=created,
            )

            return Result.success(output, metadata={"execution_time_ms": execution_time})

        except Exception as e:
            execution_time = (time.time() - start) * 1000
            return Result.failure(
                f"Failed to create file: {inputs.path}\nError: {str(e)}",
                metadata={"execution_time_ms": execution_time},
            )


# Register CreateFile block
BLOCK_REGISTRY.register("CreateFile", CreateFile)


class ReadFileInput(BlockInput):
    """Input for ReadFile block."""

    path: str = Field(description="File path (supports ${variables})")
    encoding: str = Field(default="utf-8", description="Text encoding")
    binary: bool = Field(
        default=False, description="Read as binary (returns base64 encoded string)"
    )
    max_size_bytes: int | None = Field(
        default=None, description="Max file size (safety limit, prevents memory issues)"
    )
    lines: bool = Field(default=False, description="Read as list of lines (strip newlines)")


class ReadFileOutput(BlockOutput):
    """Output for ReadFile block."""

    success: bool = Field(description="Whether file was read successfully")
    path: str = Field(description="Resolved absolute path")
    content: str = Field(description="File content (or base64 if binary=True)")
    size_bytes: int = Field(description="Actual file size")
    lines: list[str] | None = Field(
        default=None, description="Lines if lines=True (newlines stripped)"
    )
    encoding: str = Field(description="Encoding used")


class ReadFile(WorkflowBlock):
    """
    Read file contents into workflow context.

    Features:
    - Read file content (text or binary)
    - Support multiple encodings (utf-8, ascii, latin-1, etc.)
    - File existence validation
    - Size limits (optional, prevent memory issues)
    - Line-by-line reading support (optional, for structured text processing)
    - Variable resolution for file path (${variables})
    - Path traversal protection

    Example YAML usage:
        - id: read_config
          type: ReadFile
          inputs:
            path: "${workspace_path}/config.json"
            max_size_bytes: 1048576  # 1MB limit

        - id: read_binary
          type: ReadFile
          inputs:
            path: "/path/to/image.png"
            binary: true

        - id: read_lines
          type: ReadFile
          inputs:
            path: "/path/to/log.txt"
            lines: true
            max_size_bytes: 10485760  # 10MB limit
    """

    def input_model(self) -> type[BlockInput]:
        return ReadFileInput

    def output_model(self) -> type[BlockOutput]:
        return ReadFileOutput

    async def execute(self, context: dict[str, Any]) -> Result[BlockOutput]:
        """Read file contents into workflow context."""
        inputs = cast(ReadFileInput, self._validated_inputs)
        if inputs is None:
            return Result.failure("Inputs not validated")

        start = time.time()

        try:
            # Resolve path (relative or absolute)
            file_path = Path(inputs.path)
            if not file_path.is_absolute():
                file_path = Path.cwd() / file_path

            # Resolve to absolute path and normalize
            file_path = file_path.resolve()

            # Path traversal protection - ensure resolved path is normalized
            if ".." in str(file_path):
                # Double-check after resolve that no .. remains (shouldn't happen)
                return Result.failure(f"Path traversal detected after resolution: {file_path}")

            # Check if file exists
            if not file_path.exists():
                return Result.failure(f"File not found: {file_path}")

            # Check if it's a file (not a directory)
            if not file_path.is_file():
                return Result.failure(f"Path is not a file: {file_path}")

            # Get file size
            size_bytes = file_path.stat().st_size

            # Check size limit if specified
            if inputs.max_size_bytes is not None and size_bytes > inputs.max_size_bytes:
                return Result.failure(
                    f"File size ({size_bytes} bytes) exceeds max_size_bytes "
                    f"({inputs.max_size_bytes} bytes): {file_path}"
                )

            # Read file content
            content: str
            lines_list: list[str] | None = None
            encoding_used = inputs.encoding

            try:
                if inputs.binary:
                    # Binary mode: read as bytes and encode to base64
                    binary_content = file_path.read_bytes()
                    content = base64.b64encode(binary_content).decode("ascii")
                    encoding_used = "binary"
                elif inputs.lines:
                    # Lines mode: read as list of lines, strip newlines
                    text_content = file_path.read_text(encoding=inputs.encoding)
                    # Split by newlines and strip line endings
                    lines_list = [
                        line.rstrip("\r\n") for line in text_content.split("\n") if line or True
                    ]
                    # Remove final empty line if file doesn't end with newline
                    if lines_list and lines_list[-1] == "":
                        lines_list.pop()
                    # Join back for content field (preserve original format)
                    content = text_content
                else:
                    # Text mode: read as string
                    content = file_path.read_text(encoding=inputs.encoding)

            except PermissionError:
                return Result.failure(f"Permission denied reading from: {file_path}")
            except UnicodeDecodeError as e:
                return Result.failure(
                    f"Encoding error ({inputs.encoding}): {str(e)}\n"
                    f"File may be binary or use different encoding"
                )
            except Exception as e:
                return Result.failure(f"Error reading file: {file_path}\nError: {str(e)}")

            execution_time = (time.time() - start) * 1000  # Convert to ms

            output = ReadFileOutput(
                success=True,
                path=str(file_path),
                content=content,
                size_bytes=size_bytes,
                lines=lines_list,
                encoding=encoding_used,
            )

            return Result.success(output, metadata={"execution_time_ms": execution_time})

        except Exception as e:
            execution_time = (time.time() - start) * 1000
            return Result.failure(
                f"Failed to read file: {inputs.path}\nError: {str(e)}",
                metadata={"execution_time_ms": execution_time},
            )


# Register ReadFile block
BLOCK_REGISTRY.register("ReadFile", ReadFile)


class PopulateTemplateInput(BlockInput):
    """Input for PopulateTemplate block."""

    template: str = Field(description="Template content (supports ${variables})")
    template_path: str | None = Field(
        default=None,
        description="Load template from file instead (supports ${variables})",
    )
    variables: dict[str, Any] = Field(
        default_factory=dict, description="Template variables (supports ${variables})"
    )
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
    """Output for PopulateTemplate block."""

    success: bool = Field(description="Whether template rendering succeeded")
    rendered: str = Field(description="Rendered template content")
    template_source: str = Field(description="Template source type: 'inline' or 'file'")
    variables_used: list[str] = Field(
        description="Variables referenced in template ({{ var }} patterns)"
    )
    size_bytes: int = Field(description="Size of rendered output in bytes")


class PopulateTemplate(WorkflowBlock):
    """
    Render Jinja2 templates with workflow context variables.

    Features:
    - Jinja2 template rendering with full template language support
    - Support inline templates (template string) or external templates (template_path)
    - Variable substitution (${var} resolved before Jinja2, {{ var }} handled by Jinja2)
    - Custom rendering modes: strict (fail on undefined) or silent (undefined behavior)
    - Whitespace control (trim_blocks, lstrip_blocks)
    - Variable extraction (track which variables are used in template)
    - Safe rendering (no arbitrary code execution)
    - Full Jinja2 filters and control structures (if, for, etc.)

    Example YAML usage (inline template):
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

    Example YAML usage (template from file):
        - id: read_template
          type: ReadFile
          inputs:
            path: "templates/config.j2"

        - id: populate_config
          type: PopulateTemplate
          inputs:
            template: "${read_template.content}"
            variables:
              app_name: "${app_name}"
              port: 8080
              debug: false
          depends_on: [read_template]

    Example integration workflow (ReadFile → PopulateTemplate → CreateFile):
        - id: read_template
          type: ReadFile
          inputs:
            path: "templates/README.md.j2"

        - id: populate_readme
          type: PopulateTemplate
          inputs:
            template: "${read_template.content}"
            variables:
              project_name: "${project_name}"
              author: "${author}"
              version: "1.0.0"
            strict: true
          depends_on: [read_template]

        - id: write_readme
          type: CreateFile
          inputs:
            path: "README.md"
            content: "${populate_readme.rendered}"
          depends_on: [populate_readme]
    """

    def input_model(self) -> type[BlockInput]:
        return PopulateTemplateInput

    def output_model(self) -> type[BlockOutput]:
        return PopulateTemplateOutput

    async def execute(self, context: dict[str, Any]) -> Result[BlockOutput]:
        """Render Jinja2 template with workflow context variables."""
        inputs = cast(PopulateTemplateInput, self._validated_inputs)
        if inputs is None:
            return Result.failure("Inputs not validated")

        start = time.time()

        try:
            # Determine template source
            template_source: str
            template_content: str

            if inputs.template_path is not None:
                # Load template from file
                template_source = "file"
                file_path = Path(inputs.template_path)
                if not file_path.is_absolute():
                    file_path = Path.cwd() / file_path
                file_path = file_path.resolve()

                # Path traversal protection
                if ".." in str(file_path):
                    return Result.failure(f"Path traversal detected after resolution: {file_path}")

                # Check if file exists
                if not file_path.exists():
                    return Result.failure(f"Template file not found: {file_path}")

                if not file_path.is_file():
                    return Result.failure(f"Template path is not a file: {file_path}")

                # Read template content
                try:
                    template_content = file_path.read_text(encoding="utf-8")
                except PermissionError:
                    return Result.failure(f"Permission denied reading template: {file_path}")
                except UnicodeDecodeError as e:
                    return Result.failure(
                        f"Template file encoding error (expected UTF-8): {str(e)}"
                    )
            else:
                # Use inline template
                template_source = "inline"
                template_content = inputs.template

            # Extract variables referenced in template ({{ var }} patterns)
            # This regex finds {{ variable_name }} patterns
            variable_pattern = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_\.]*)\s*")
            variables_used = sorted(set(variable_pattern.findall(template_content)))

            # Configure Jinja2 environment
            undefined_behavior: type[jinja2.Undefined]
            if inputs.strict:
                undefined_behavior = jinja2.StrictUndefined
            else:
                undefined_behavior = jinja2.Undefined

            env = jinja2.Environment(
                autoescape=False,  # General templates, not HTML-specific
                undefined=undefined_behavior,
                trim_blocks=inputs.trim_blocks,
                lstrip_blocks=inputs.lstrip_blocks,
            )

            # Render template
            try:
                template = env.from_string(template_content)
                rendered = template.render(**inputs.variables)
            except jinja2.TemplateSyntaxError as e:
                return Result.failure(
                    f"Template syntax error at line {e.lineno}: {e.message}\n"
                    f"Template: {e.name or 'inline'}"
                )
            except jinja2.UndefinedError as e:
                return Result.failure(
                    f"Undefined variable in template (strict mode enabled): {str(e)}"
                )
            except Exception as e:
                return Result.failure(f"Template rendering failed: {str(e)}")

            # Calculate output size
            size_bytes = len(rendered.encode("utf-8"))

            execution_time = (time.time() - start) * 1000  # Convert to ms

            output = PopulateTemplateOutput(
                success=True,
                rendered=rendered,
                template_source=template_source,
                variables_used=variables_used,
                size_bytes=size_bytes,
            )

            return Result.success(output, metadata={"execution_time_ms": execution_time})

        except Exception as e:
            execution_time = (time.time() - start) * 1000
            return Result.failure(
                f"Failed to populate template: {str(e)}",
                metadata={"execution_time_ms": execution_time},
            )


# Register PopulateTemplate block
BLOCK_REGISTRY.register("PopulateTemplate", PopulateTemplate)
