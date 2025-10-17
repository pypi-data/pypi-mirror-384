"""Shared context types for MCP server.

This module contains context types used across server and tools modules,
separated to avoid circular imports.
"""

from dataclasses import dataclass

from mcp.server.fastmcp import Context
from mcp.server.session import ServerSession

from .engine import WorkflowExecutor, WorkflowRegistry


@dataclass
class AppContext:
    """Application context containing shared resources for MCP tools.

    This context is created during server startup and made available to all tools
    via dependency injection through the Context parameter.
    """

    registry: WorkflowRegistry
    executor: WorkflowExecutor


# Type alias for MCP tool context parameter
AppContextType = Context[ServerSession, AppContext]


__all__ = ["AppContext", "AppContextType"]
