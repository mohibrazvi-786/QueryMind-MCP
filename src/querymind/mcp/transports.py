"""MCP transport runners.

Supports stdio (local desktop clients) and Streamable HTTP (remote access).
"""

from __future__ import annotations

from querymind.mcp.app import mcp


def run_stdio(*, show_banner: bool = True, log_level: str | None = None) -> None:
    """Run the MCP server over stdio (for Claude Desktop, MCP Inspector, etc.)."""
    mcp.run_stdio_async(show_banner=show_banner, log_level=log_level)


def run_http(
    *,
    host: str = "127.0.0.1",
    port: int = 8000,
    transport: str = "streamable-http",
    log_level: str | None = None,
    path: str = "/mcp",
    stateless_http: bool = True,
) -> None:
    """Run the MCP server over Streamable HTTP.

    Defaults to localhost only; do not expose publicly without a reverse proxy
    and TLS in production.
    """
    mcp.run_http_async(
        show_banner=True,
        transport=transport,  # type: ignore[arg-type]
        host=host,
        port=port,
        log_level=log_level,
        path=path,
        stateless_http=stateless_http,
    )


def http_app():
    """Return the ASGI app for Streamable HTTP (useful behind a reverse proxy)."""
    return mcp.http_app(
        path="/mcp",
        transport="streamable-http",  # type: ignore[arg-type]
        stateless_http=True,
    )
