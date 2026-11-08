"""QueryMind MCP server.

Imports all tool, resource, and prompt modules so they register against the
shared FastMCP instance. The server is an interface layer — business logic
lives in services.
"""

from __future__ import annotations

# Import all MCP modules to trigger @mcp.tool / @mcp.resource / @mcp.prompt registration.
from querymind.mcp import app  # noqa: F401  (ensures mcp instance exists)
from querymind.mcp.tools import discovery  # noqa: F401
from querymind.mcp.tools import query  # noqa: F401
from querymind.mcp.tools import optimization  # noqa: F401
from querymind.mcp.tools import documentation  # noqa: F401
from querymind.mcp import resources  # noqa: F401
from querymind.mcp import prompts  # noqa: F401
from querymind.mcp import transports  # noqa: F401

from querymind.mcp.app import mcp, connection_registry

__all__ = ["mcp", "connection_registry", "transports"]
