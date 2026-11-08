"""MCP tools — Database discovery (6 tools).

Group A: connect_database, list_databases, list_tables, describe_table,
get_relationships, get_database_stats.
"""

from __future__ import annotations

from typing import Optional

from querymind.core.exceptions import ConnectionError, DatabaseError, NotFoundError
from querymind.core.security import is_allowed_host, redact
from querymind.database.connection import TargetConnection
from querymind.mcp.app import connection_registry, mcp
from querymind.mcp.authz import authorize
from querymind.core.rbac import (
    PERMISSION_CONNECTION_MANAGE,
    PERMISSION_DB_DISCOVER,
    PERMISSION_DATABASE_STATS_READ,
    PERMISSION_RELATIONSHIPS_READ,
    PERMISSION_TABLE_READ,
)
from querymind.services.discovery_service import DiscoveryService


def _get_connection(connection_id: str) -> TargetConnection:
    conn = connection_registry.get(connection_id)
    if conn is None:
        raise NotFoundError(f"Connection '{connection_id}' not registered", code="connection_not_found")
    return conn


def _host_from_url(database_url: str) -> Optional[str]:
    try:
        from urllib.parse import urlparse
        return urlparse(database_url).hostname
    except Exception:  # noqa: BLE001
        return None


@mcp.tool()
def connect_database(
    connection_id: str,
    database_url: str,
    *,
    statement_timeout_ms: int = 10000,
    max_result_rows: int = 1000,
    organization_id: Optional[str] = None,
    access_token: Optional[str] = None,
) -> dict:
    """Register and verify a read-only connection to a target PostgreSQL database.

    Requires the `connection:manage` permission when authenticated. The
    connection is scoped to an organization for multi-tenant isolation.
    Credentials are never returned.
    """
    principal = authorize(
        access_token=access_token,
        permission=PERMISSION_CONNECTION_MANAGE,
    )
    if principal is not None and organization_id is None:
        organization_id = principal.organization_id

    host = _host_from_url(database_url)
    if host and not is_allowed_host(host):
        raise ConnectionError(
            f"Host '{host}' is not in the connection allowlist", code="host_not_allowed"
        )

    connection = TargetConnection(
        database_url=database_url,
        statement_timeout_ms=statement_timeout_ms,
        max_result_rows=max_result_rows,
        organization_id=organization_id,
    )
    try:
        connection.connect()
        version = connection.execute("SELECT version() AS v")[0]["v"]
    except Exception as exc:  # noqa: BLE001
        connection.dispose()
        raise ConnectionError(f"Cannot connect: {exc}", code="connect_failed") from exc

    existing = connection_registry.get(connection_id)
    if existing is not None:
        existing.dispose()
    connection_registry[connection_id] = connection

    return {
        "connection_id": connection_id,
        "status": "connected",
        "host": redact(host or ""),
        "organization_id": organization_id,
        "database_version": version,
        "read_only": True,
        "statement_timeout_ms": statement_timeout_ms,
        "max_result_rows": max_result_rows,
    }


@mcp.tool()
def list_databases(
    connection_id: str,
    *,
    access_token: Optional[str] = None,
) -> dict:
    """List databases visible to the configured role on the target server."""
    principal = authorize(
        access_token=access_token,
        permission=PERMISSION_DB_DISCOVER,
        connection_id=connection_id,
    )
    conn = _get_connection(connection_id)
    try:
        rows = conn.execute(
            "SELECT datname FROM pg_database WHERE datistemplate = false ORDER BY datname"
        )
    except Exception as exc:  # noqa: BLE001
        raise DatabaseError(f"Failed to list databases: {exc}", code="list_databases_failed") from exc

    return {
        "connection_id": connection_id,
        "databases": [r["datname"] for r in rows],
        "count": len(rows),
    }


@mcp.tool()
def list_tables(
    connection_id: str,
    *,
    schema: Optional[str] = None,
    table_pattern: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    access_token: Optional[str] = None,
) -> dict:
    """Retrieve schemas and tables with optional filtering and pagination."""
    principal = authorize(
        access_token=access_token,
        permission=PERMISSION_TABLE_READ,
        connection_id=connection_id,
    )
    conn = _get_connection(connection_id)
    service = DiscoveryService(conn)
    try:
        tables = service.discover_tables()
    except Exception as exc:  # noqa: BLE001
        raise DatabaseError(f"Failed to list tables: {exc}", code="list_tables_failed") from exc

    filtered = []
    for t in tables:
        if schema and t["table_schema"] != schema:
            continue
        if table_pattern and table_pattern.lower() not in t["table_name"].lower():
            continue
        filtered.append(t)

    total = len(filtered)
    page = filtered[offset : offset + limit]
    return {
        "connection_id": connection_id,
        "tables": [
            {"schema": t["table_schema"], "name": t["table_name"], "type": t["table_type"]}
            for t in page
        ],
        "count": len(page),
        "total": total,
        "offset": offset,
        "limit": limit,
    }


@mcp.tool()
def describe_table(
    connection_id: str,
    *,
    schema: str,
    table: str,
    access_token: Optional[str] = None,
) -> dict:
    """Inspect columns, constraints, indexes, and stats for a single table."""
    principal = authorize(
        access_token=access_token,
        permission=PERMISSION_TABLE_DESCRIBE,
        connection_id=connection_id,
    )
    conn = _get_connection(connection_id)
    service = DiscoveryService(conn)
    try:
        catalogue = service.discover_all()
    except Exception as exc:  # noqa: BLE001
        raise DatabaseError(f"Failed to discover schema: {exc}", code="discover_failed") from exc

    for t in catalogue["tables"]:
        if t["schema"] == schema and t["name"] == table:
            return {
                "schema": t["schema"],
                "name": t["name"],
                "type": t["type"],
                "columns": t["columns"],
                "primary_keys": t["primary_keys"],
                "foreign_keys": t["foreign_keys"],
                "indexes": t["indexes"],
                "stats": t.get("stats", {}),
            }

    raise NotFoundError(
        f"Table {schema}.{table} not found", code="table_not_found"
    )


@mcp.tool()
def get_relationships(
    connection_id: str,
    *,
    schema: Optional[str] = None,
    access_token: Optional[str] = None,
) -> dict:
    """Retrieve foreign-key relationships as a safe relationship graph."""
    authorize(
        access_token=access_token,
        permission=PERMISSION_RELATIONSHIPS_READ,
        connection_id=connection_id,
    )
    conn = _get_connection(connection_id)
    service = DiscoveryService(conn)
    try:
        catalogue = service.discover_all()
    except Exception as exc:  # noqa: BLE001
        raise DatabaseError(f"Failed to discover relationships: {exc}", code="discover_failed") from exc

    relationships = catalogue["relationships"]
    if schema:
        relationships = [
            r for r in relationships
            if r["source_schema"] == schema or r["target_schema"] == schema
        ]

    return {
        "connection_id": connection_id,
        "relationships": relationships,
        "count": len(relationships),
    }


@mcp.tool()
def get_database_stats(connection_id: str, *, access_token: Optional[str] = None) -> dict:
    """Retrieve database statistics, clearly identifying unavailable metrics."""
    authorize(
        access_token=access_token,
        permission=PERMISSION_DATABASE_STATS_READ,
        connection_id=connection_id,
    )
    conn = _get_connection(connection_id)
    service = DiscoveryService(conn)
    try:
        catalogue = service.discover_all()
    except Exception as exc:  # noqa: BLE001
        raise DatabaseError(f"Failed to gather stats: {exc}", code="stats_failed") from exc

    table_stats = catalogue.get("table_stats", [])
    total_bytes = 0
    unavailable = []
    for s in table_stats:
        if s.get("total_bytes") is None:
            unavailable.append(f"{s.get('table_schema')}.{s.get('table_name')}.total_bytes")
        else:
            total_bytes += int(s.get("total_bytes") or 0)

    return {
        "connection_id": connection_id,
        "database_version": catalogue.get("database_version"),
        "database_size_bytes": total_bytes,
        "table_count": len(table_stats),
        "table_stats": table_stats,
        "unavailable_metrics": unavailable,
        "note": "Unavailable statistics are reported as null/omitted, never confused with zero.",
    }
