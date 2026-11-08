"""Shared FastMCP application instance.

Tool, resource, and prompt modules decorate against this instance to avoid
circular imports. The MCP server remains an interface layer — all business
logic lives in services.
"""

from datetime import datetime, timezone
from fastmcp import FastMCP

mcp = FastMCP(
    name="querymind-mcp",
    instructions=(
        "QueryMind MCP — AI database intelligence platform. "
        "Use the tools to inspect, analyze, and optimize PostgreSQL databases. "
        "All SQL execution is read-only and validated."
    ),
)

# Shared connection registry (session-scoped). Maps connection_id -> TargetConnection.
connection_registry: dict[str, "TargetConnection"] = {}
