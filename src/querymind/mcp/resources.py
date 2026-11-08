"""MCP Resources — 6 structured snapshots.

URIs: querymind://database/{schema,tables,relationships,health,documentation,metrics}
Returns current/timestamped snapshots from the first registered connection.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from querymind.core.exceptions import NotFoundError
from querymind.mcp.app import connection_registry, mcp
from querymind.services.discovery_service import DiscoveryService
from querymind.services.performance_service import PerformanceService


def _default_connection():
    if not connection_registry:
        raise NotFoundError("No database connection registered", code="no_connection")
    return next(iter(connection_registry.values()))


def _snapshot(payload: dict) -> str:
    payload["collected_at"] = datetime.now(timezone.utc).isoformat()
    return json.dumps(payload, default=str, indent=2)


@mcp.resource("querymind://database/schema")
def database_schema() -> str:
    """Full schema catalogue snapshot."""
    conn = _default_connection()
    service = DiscoveryService(conn)
    try:
        catalogue = service.discover_all()
    except Exception as exc:  # noqa: BLE001
        return json.dumps({"error": str(exc), "collected_at": datetime.now(timezone.utc).isoformat()})
    return _snapshot(catalogue)


@mcp.resource("querymind://database/tables")
def database_tables() -> str:
    """Tables and columns snapshot."""
    conn = _default_connection()
    service = DiscoveryService(conn)
    try:
        catalogue = service.discover_all()
    except Exception as exc:  # noqa: BLE001
        return json.dumps({"error": str(exc), "collected_at": datetime.now(timezone.utc).isoformat()})
    return _snapshot(
        {
            "tables": catalogue.get("tables", []),
            "schemas": catalogue.get("schemas", []),
        }
    )


@mcp.resource("querymind://database/relationships")
def database_relationships() -> str:
    """Table relationships (foreign keys) snapshot."""
    conn = _default_connection()
    service = DiscoveryService(conn)
    try:
        catalogue = service.discover_all()
    except Exception as exc:  # noqa: BLE001
        return json.dumps({"error": str(exc), "collected_at": datetime.now(timezone.utc).isoformat()})
    return _snapshot(
        {
            "relationships": catalogue.get("relationships", []),
            "count": len(catalogue.get("relationships", [])),
        }
    )


@mcp.resource("querymind://database/health")
def database_health() -> str:
    """Database health metrics snapshot."""
    conn = _default_connection()
    svc = PerformanceService(connection=conn, discovery_service=DiscoveryService(conn))
    try:
        report = svc.health()
    except Exception as exc:  # noqa: BLE001
        return json.dumps({"error": str(exc), "collected_at": datetime.now(timezone.utc).isoformat()})
    return _snapshot(
        {
            "status": report.status,
            "metrics": [
                {"name": m.name, "value": m.value, "status": m.status, "unit": m.unit}
                for m in report.metrics
            ],
            "warnings": report.warnings,
        }
    )


@mcp.resource("querymind://database/documentation")
def database_documentation() -> str:
    """Schema documentation snapshot (Markdown)."""
    conn = _default_connection()
    service = DiscoveryService(conn)
    try:
        catalogue = service.discover_all()
    except Exception as exc:  # noqa: BLE001
        return json.dumps({"error": str(exc), "collected_at": datetime.now(timezone.utc).isoformat()})
    lines = [f"# Schema Documentation — {catalogue.get('database_version', 'unknown')}", ""]
    lines.append(f"## Schemas\n{', '.join(catalogue.get('schemas', []))}\n")
    lines.append("## Tables\n")
    for t in catalogue.get("tables", []):
        lines.append(f"### {t['schema']}.{t['name']} ({t.get('type')})")
        lines.append(f"- Primary keys: {', '.join(t.get('primary_keys', [])) or 'none'}")
        lines.append(f"- Columns: {len(t.get('columns', []))}")
        lines.append(f"- Indexes: {len(t.get('indexes', []))}")
        lines.append("")
    return _snapshot({"markdown": "\n".join(lines)})


@mcp.resource("querymind://database/metrics")
def database_metrics() -> str:
    """Database metrics snapshot (table stats, size, connections)."""
    conn = _default_connection()
    service = DiscoveryService(conn)
    try:
        catalogue = service.discover_all()
    except Exception as exc:  # noqa: BLE001
        return json.dumps({"error": str(exc), "collected_at": datetime.now(timezone.utc).isoformat()})
    table_stats = catalogue.get("table_stats", [])
    total_bytes = sum(int(s.get("total_bytes") or 0) for s in table_stats)
    return _snapshot(
        {
            "database_size_bytes": total_bytes,
            "table_count": len(table_stats),
            "table_stats": table_stats,
        }
    )
