"""Tests for file operation executors."""

import tempfile
from pathlib import Path

import pytest

from workflows_mcp.engine.block import Block
from workflows_mcp.engine.executor_base import EXECUTOR_REGISTRY
from workflows_mcp.engine.executors_file import (
    CreateFileExecutor,
    CreateFileInput,
    PopulateTemplateExecutor,
    PopulateTemplateInput,
    ReadFileExecutor,
    ReadFileInput,
)


@pytest.fixture(autouse=True)
def ensure_executors_registered():
    """Ensure executors are registered before each test."""
    # Re-register if registry was cleared
    if not EXECUTOR_REGISTRY.has_type("CreateFile"):
        # Re-register file executors
        create_exec = CreateFileExecutor()
        read_exec = ReadFileExecutor()
        template_exec = PopulateTemplateExecutor()
        EXECUTOR_REGISTRY.register(create_exec)
        EXECUTOR_REGISTRY.register(read_exec)
        EXECUTOR_REGISTRY.register(template_exec)
    yield


@pytest.mark.asyncio
async def test_create_file_simple():
    """Test CreateFile executor with simple file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "test.txt"

        executor = CreateFileExecutor()
        inputs = CreateFileInput(path=str(file_path), content="Hello, World!")

        result = await executor.execute(inputs, context={})

        assert result.is_success
        assert result.value.success is True
        assert result.value.created is True
        assert file_path.exists()
        assert file_path.read_text() == "Hello, World!"


@pytest.mark.asyncio
async def test_create_file_overwrite_protection():
    """Test CreateFile overwrite protection."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "existing.txt"
        file_path.write_text("original")

        executor = CreateFileExecutor()
        inputs = CreateFileInput(path=str(file_path), content="new content", overwrite=False)

        result = await executor.execute(inputs, context={})

        assert not result.is_success
        assert "exists" in result.error.lower()
        assert file_path.read_text() == "original"  # Unchanged


@pytest.mark.asyncio
async def test_create_file_overwrite_allowed():
    """Test CreateFile with overwrite=True."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "existing.txt"
        file_path.write_text("original")

        executor = CreateFileExecutor()
        inputs = CreateFileInput(path=str(file_path), content="new content", overwrite=True)

        result = await executor.execute(inputs, context={})

        assert result.is_success
        assert result.value.created is False  # Overwrote, not created
        assert file_path.read_text() == "new content"


@pytest.mark.asyncio
async def test_create_file_with_parents():
    """Test CreateFile creating parent directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "nested" / "dir" / "test.txt"

        executor = CreateFileExecutor()
        inputs = CreateFileInput(path=str(file_path), content="content", create_parents=True)

        result = await executor.execute(inputs, context={})

        assert result.is_success
        assert file_path.exists()
        assert file_path.parent.exists()


@pytest.mark.asyncio
async def test_create_file_mode_string():
    """Test CreateFile with string mode."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "test.txt"

        executor = CreateFileExecutor()
        inputs = CreateFileInput(path=str(file_path), content="content", mode="644")

        result = await executor.execute(inputs, context={})

        assert result.is_success
        # Mode setting is Unix-specific, we just verify it doesn't fail


@pytest.mark.asyncio
async def test_create_file_mode_int():
    """Test CreateFile with integer mode."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "test.txt"

        executor = CreateFileExecutor()
        inputs = CreateFileInput(path=str(file_path), content="content", mode=0o644)

        result = await executor.execute(inputs, context={})

        assert result.is_success


@pytest.mark.asyncio
async def test_create_file_invalid_mode():
    """Test CreateFile with invalid mode string."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "test.txt"

        executor = CreateFileExecutor()
        inputs = CreateFileInput(path=str(file_path), content="content", mode="invalid")

        result = await executor.execute(inputs, context={})

        assert not result.is_success
        assert "invalid mode" in result.error.lower()


@pytest.mark.asyncio
async def test_create_file_encoding():
    """Test CreateFile with different encoding."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "test.txt"
        content = "Héllo, Wörld!"

        executor = CreateFileExecutor()
        inputs = CreateFileInput(path=str(file_path), content=content, encoding="utf-8")

        result = await executor.execute(inputs, context={})

        assert result.is_success
        assert file_path.read_text(encoding="utf-8") == content


@pytest.mark.asyncio
async def test_read_file_success():
    """Test ReadFile executor."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "read.txt"
        content = "File content to read"
        file_path.write_text(content)

        executor = ReadFileExecutor()
        inputs = ReadFileInput(path=str(file_path))

        result = await executor.execute(inputs, context={})

        assert result.is_success
        assert result.value.content == content
        assert result.value.found is True


@pytest.mark.asyncio
async def test_read_file_not_found_required():
    """Test ReadFile with required=True on missing file."""
    executor = ReadFileExecutor()
    inputs = ReadFileInput(path="/nonexistent/file.txt", required=True)

    result = await executor.execute(inputs, context={})

    assert not result.is_success
    assert "not found" in result.error.lower()


@pytest.mark.asyncio
async def test_read_file_not_found_optional():
    """Test ReadFile with required=False on missing file."""
    executor = ReadFileExecutor()
    inputs = ReadFileInput(path="/nonexistent/file.txt", required=False)

    result = await executor.execute(inputs, context={})

    assert result.is_success
    assert result.value.content == ""
    assert result.value.found is False


@pytest.mark.asyncio
async def test_read_file_encoding():
    """Test ReadFile with different encoding."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "test.txt"
        content = "Héllo, Wörld!"
        file_path.write_text(content, encoding="utf-8")

        executor = ReadFileExecutor()
        inputs = ReadFileInput(path=str(file_path), encoding="utf-8")

        result = await executor.execute(inputs, context={})

        assert result.is_success
        assert result.value.content == content


@pytest.mark.asyncio
async def test_read_file_max_size():
    """Test ReadFile with max_size_bytes limit."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "test.txt"
        content = "a" * 1000
        file_path.write_text(content)

        # Should succeed under limit
        executor = ReadFileExecutor()
        inputs = ReadFileInput(path=str(file_path), max_size_bytes=2000)
        result = await executor.execute(inputs, context={})
        assert result.is_success

        # Should fail over limit
        inputs = ReadFileInput(path=str(file_path), max_size_bytes=500)
        result = await executor.execute(inputs, context={})
        assert not result.is_success
        assert "too large" in result.error.lower()


@pytest.mark.asyncio
async def test_populate_template_simple():
    """Test PopulateTemplate executor."""
    executor = PopulateTemplateExecutor()
    inputs = PopulateTemplateInput(template="Hello, {{ name }}!", variables={"name": "World"})

    result = await executor.execute(inputs, context={})

    assert result.is_success
    assert result.value.content == "Hello, World!"


@pytest.mark.asyncio
async def test_populate_template_complex():
    """Test PopulateTemplate with loops and conditionals."""
    template = """Project: {{ project_name }}
{% for item in items %}
- {{ item }}
{% endfor %}"""

    executor = PopulateTemplateExecutor()
    inputs = PopulateTemplateInput(
        template=template,
        variables={"project_name": "MyProject", "items": ["item1", "item2", "item3"]},
    )

    result = await executor.execute(inputs, context={})

    assert result.is_success
    assert "MyProject" in result.value.content
    assert "- item1" in result.value.content


@pytest.mark.asyncio
async def test_populate_template_with_output():
    """Test PopulateTemplate writing to file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "output.txt"

        executor = PopulateTemplateExecutor()
        inputs = PopulateTemplateInput(
            template="Content: {{ value }}",
            variables={"value": 42},
            output_path=str(output_path),
        )

        result = await executor.execute(inputs, context={})

        assert result.is_success
        # Compare resolved paths to handle /var vs /private/var on macOS
        assert Path(result.value.output_path).resolve() == output_path.resolve()
        assert output_path.exists()
        assert output_path.read_text() == "Content: 42"


@pytest.mark.asyncio
async def test_populate_template_output_overwrite_protection():
    """Test PopulateTemplate overwrite protection."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "existing.txt"
        output_path.write_text("original")

        executor = PopulateTemplateExecutor()
        inputs = PopulateTemplateInput(
            template="New content",
            variables={},
            output_path=str(output_path),
            overwrite=False,
        )

        result = await executor.execute(inputs, context={})

        assert not result.is_success
        assert "exists" in result.error.lower()
        assert output_path.read_text() == "original"


@pytest.mark.asyncio
async def test_populate_template_syntax_error():
    """Test PopulateTemplate with syntax error."""
    executor = PopulateTemplateExecutor()
    inputs = PopulateTemplateInput(template="{{ unclosed", variables={})

    result = await executor.execute(inputs, context={})

    assert not result.is_success
    assert "syntax error" in result.error.lower()


@pytest.mark.asyncio
async def test_populate_template_undefined_variable():
    """Test PopulateTemplate with undefined variable in strict mode."""
    executor = PopulateTemplateExecutor()
    inputs = PopulateTemplateInput(template="{{ undefined_var }}", variables={}, strict=True)

    result = await executor.execute(inputs, context={})

    assert not result.is_success
    assert "undefined" in result.error.lower()


@pytest.mark.asyncio
async def test_populate_template_undefined_variable_non_strict():
    """Test PopulateTemplate with undefined variable in non-strict mode."""
    executor = PopulateTemplateExecutor()
    inputs = PopulateTemplateInput(template="{{ undefined_var }}", variables={}, strict=False)

    result = await executor.execute(inputs, context={})

    # Non-strict mode should succeed with empty/undefined output
    assert result.is_success


@pytest.mark.asyncio
async def test_populate_template_whitespace_control():
    """Test PopulateTemplate whitespace control."""
    template = """
{% for i in range(3) %}
Item {{ i }}
{% endfor %}
"""

    executor = PopulateTemplateExecutor()

    # With trim_blocks and lstrip_blocks
    inputs = PopulateTemplateInput(
        template=template,
        variables={},
        trim_blocks=True,
        lstrip_blocks=True,
    )
    result = await executor.execute(inputs, context={})
    assert result.is_success
    content_trimmed = result.value.content

    # Without trim_blocks and lstrip_blocks
    inputs = PopulateTemplateInput(
        template=template,
        variables={},
        trim_blocks=False,
        lstrip_blocks=False,
    )
    result = await executor.execute(inputs, context={})
    assert result.is_success
    content_untrimmed = result.value.content

    # Trimmed version should be shorter
    assert len(content_trimmed) < len(content_untrimmed)


@pytest.mark.asyncio
async def test_populate_template_rendered_alias():
    """Test PopulateTemplate output has both content and rendered."""
    executor = PopulateTemplateExecutor()
    inputs = PopulateTemplateInput(template="Test", variables={})

    result = await executor.execute(inputs, context={})

    assert result.is_success
    assert result.value.content == "Test"
    assert result.value.rendered == "Test"  # Alias property


@pytest.mark.asyncio
async def test_file_executors_via_block():
    """Test file executors via Block class."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Test all three file executors are registered
        assert EXECUTOR_REGISTRY.has_type("CreateFile")
        assert EXECUTOR_REGISTRY.has_type("ReadFile")
        assert EXECUTOR_REGISTRY.has_type("PopulateTemplate")

        # Create file via block
        create_block = Block(
            id="create",
            type="CreateFile",
            inputs={"path": str(Path(tmpdir) / "test.txt"), "content": "test content"},
        )

        result = await create_block.execute(context={})
        assert result.is_success

        # Read file via block
        read_block = Block(
            id="read",
            type="ReadFile",
            inputs={"path": str(Path(tmpdir) / "test.txt")},
        )

        result = await read_block.execute(context={})
        assert result.is_success
        assert result.value.content == "test content"


@pytest.mark.asyncio
async def test_create_file_execution_time_metadata():
    """Test CreateFile includes execution_time_ms in metadata."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "test.txt"

        executor = CreateFileExecutor()
        inputs = CreateFileInput(path=str(file_path), content="content")

        result = await executor.execute(inputs, context={})

        assert result.is_success
        assert "execution_time_ms" in result.metadata
        assert result.metadata["execution_time_ms"] > 0


@pytest.mark.asyncio
async def test_read_file_execution_time_metadata():
    """Test ReadFile includes execution_time_ms in metadata."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "test.txt"
        file_path.write_text("content")

        executor = ReadFileExecutor()
        inputs = ReadFileInput(path=str(file_path))

        result = await executor.execute(inputs, context={})

        assert result.is_success
        assert "execution_time_ms" in result.metadata
        assert result.metadata["execution_time_ms"] > 0


@pytest.mark.asyncio
async def test_populate_template_execution_time_metadata():
    """Test PopulateTemplate includes execution_time_ms in metadata."""
    executor = PopulateTemplateExecutor()
    inputs = PopulateTemplateInput(template="Test", variables={})

    result = await executor.execute(inputs, context={})

    assert result.is_success
    assert "execution_time_ms" in result.metadata
    assert result.metadata["execution_time_ms"] > 0
