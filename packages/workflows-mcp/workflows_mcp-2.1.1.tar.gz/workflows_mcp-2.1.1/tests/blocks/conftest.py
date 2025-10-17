"""Block test-specific fixtures.

Fixtures for testing workflow blocks (file operations, bash, composition).
"""

import os
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def temp_file_path(tmp_path: Path) -> Path:
    """Temporary file path for file operation tests.

    Args:
        tmp_path: pytest's temporary directory fixture

    Returns:
        Path to a temporary file (not created yet)
    """
    return tmp_path / "test_file.txt"


@pytest.fixture
def temp_output_dir(tmp_path: Path) -> Path:
    """Temporary output directory for block outputs.

    Args:
        tmp_path: pytest's temporary directory fixture

    Returns:
        Path to temporary output directory (created)
    """
    output_dir = tmp_path / "outputs"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def sample_template_content() -> str:
    """Sample Jinja2 template content for PopulateTemplate tests.

    Returns:
        String containing a Jinja2 template with variables
    """
    return """# {{ project_name }}

Version: {{ version }}
Author: {{ author }}

## Description
{{ description }}

## Features
{% for feature in features %}
- {{ feature }}
{% endfor %}
"""


@pytest.fixture
def sample_template_variables() -> dict[str, Any]:
    """Sample variables for template rendering.

    Returns:
        Dictionary of variables for Jinja2 template rendering
    """
    return {
        "project_name": "Test Project",
        "version": "1.0.0",
        "author": "Test Author",
        "description": "Test description",
        "features": ["Feature 1", "Feature 2", "Feature 3"],
    }


@pytest.fixture
def mock_bash_env() -> dict[str, str]:
    """Mock environment variables for bash block tests.

    Returns:
        Dictionary of environment variables for bash command execution
    """
    return {
        "TEST_VAR": "test_value",
        "PATH": os.environ.get("PATH", ""),
        "HOME": str(Path.home()),
    }


@pytest.fixture
def bash_test_env(tmp_path: Path) -> dict[str, str]:
    """Test environment variables for bash execution.

    Args:
        tmp_path: pytest's temporary directory fixture

    Returns:
        Dictionary with test environment variables including a test workspace
    """
    return {
        "TEST_WORKSPACE": str(tmp_path),
        "TEST_VAR": "test_value",
        "PATH": os.environ.get("PATH", ""),
    }
