"""MCP tools — Database optimization (4 tools).

Group C: recommend_indexes, analyze_slow_queries, compare_query_performance,
detect_query_inefficiencies.
"""

from __future__ import annotations

from typing import Optional

from querymind.core.exceptions import DatabaseError, NotFoundError
from querymind.core.rbac import (
    PERMISSION_INDEX_RECOMMEND,
    PERMISSION_INEFFICIENCY_DETECT,
    PERMISSION_SLOW_QUERIES_READ,
    PERMISSION_SQL_EXPLAIN,
)
from querymind.database.connection import TargetConnection
from querymind.mcp.app import connection_registry, mcp
from querymind.mcp.authz import authorize
from querymind.services.discovery_service import DiscoveryService
from querymind.services.performance_service import PerformanceService


def _get_connection(connection_id: str) -> TargetConnection:
    conn = connection_registry.get(connection_id)
    if conn is None:
        raise NotFoundError(f"Connection '{connection_id}' not registered", code="connection_not_found")
    return conn


@mcp.tool()
def recommend_indexes(
    connection_id: str,
    table: str,
    *,
    predicates: Optional[list[str]] = None,
    join_columns: Optional[list[str]] = None,
    order_by: Optional[list[str]] = None,
    group_by: Optional[list[str]] = None,
    access_token: Optional[str] = None,
) -> dict:
    """Generate index recommendations for a table.

    Returns proposed CREATE INDEX SQL with reasoning and trade-offs.
    Never executes DDL.
    """
    authorize(
        access_token=access_token,
        permission=PERMISSION_INDEX_RECOMMEND,
        connection_id=connection_id,
    )
    conn = _get_connection(connection_id)
    discovery = DiscoveryService(conn)
    try:
        catalogue = discovery.discover_all()
    except Exception as exc:  # noqa: BLE001
        raise DatabaseError(f"Failed to discover schema: {exc}", code="discover_failed") from exc

    # Locate table stats and existing indexes.
    row_estimate = None
    existing_indexes = []
    for t in catalogue.get("tables", []):
        if t["schema"] == "public" and t["name"] == table:
            row_estimate = t.get("stats", {}).get("row_estimate")
            existing_indexes = t.get("indexes", [])
            break

    svc = PerformanceService(connection=conn, discovery_service=discovery)
    try:
        recs = svc.recommend_indexes(
            table=table,
            context={
                "predicates": predicates or [],
                "join_columns": join_columns or [],
                "order_by": order_by or [],
                "group_by": group_by or [],
                "existing_indexes": existing_indexes,
                "row_estimate": row_estimate,
            },
        )
    except Exception as exc:  # noqa: BLE001
        raise DatabaseError(f"Index recommendation failed: {exc}", code="index_recommendation_failed") from exc

    return {
        "connection_id": connection_id,
        "table": table,
        "row_estimate": row_estimate,
        "recommendations": recs,
        "count": len(recs),
        "note": "Recommendations are proposed SQL only — no DDL is executed automatically.",
    }


@mcp.tool()
def analyze_slow_queries(
    connection_id: str, *, limit: int = 10, access_token: Optional[str] = None
) -> dict:
    """Identify expensive queries from pg_stat_statements.

    Degrades gracefully when the extension or permissions are unavailable.
    """
    authorize(
        access_token=access_token,
        permission=PERMISSION_SLOW_QUERIES_READ,
        connection_id=connection_id,
    )
    conn = _get_connection(connection_id)
    svc = PerformanceService(connection=conn, discovery_service=DiscoveryService(conn))
    try:
        report = svc.generate_report("target")
    except Exception as exc:  # noqa: BLE001
        raise DatabaseError(f"Slow-query analysis failed: {exc}", code="slow_query_failed") from exc

    return {
        "connection_id": connection_id,
        "slow_queries": report.slow_queries[:limit],
        "count": len(report.slow_queries),
        "data_limitations": report.data_limitations,
    }


@mcp.tool()
def compare_query_performance(
    connection_id: str,
    query_a: str,
    query_b: str,
    *,
    access_token: Optional[str] = None,
) -> dict:
    """Compare two query variants using EXPLAIN plan cost (safe, no ANALYZE).

    Does not fabricate execution-time measurements.
    """
    authorize(
        access_token=access_token,
        permission=PERMISSION_SQL_EXPLAIN,
        connection_id=connection_id,
    )
    conn = _get_connection(connection_id)
    svc = PerformanceService(connection=conn, discovery_service=DiscoveryService(conn))

    variants = []
    for label, sql in (("a", query_a), ("b", query_b)):
        try:
            analysis = svc.analyze_query_plan(sql)
            variants.append(
                {
                    "label": label,
                    "sql": sql,
                    "total_cost": analysis.get("total_cost"),
                    "startup_cost": analysis.get("startup_cost"),
                    "estimated_rows": analysis.get("estimated_rows"),
                    "findings": analysis.get("findings", []),
                }
            )
        except Exception as exc:  # noqa: BLE001
            variants.append(
                {"label": label, "sql": sql, "error": str(exc)}
            )

    return {
        "connection_id": connection_id,
        "variants": variants,
        "note": "Comparison based on EXPLAIN (FORMAT JSON) estimated cost, not measured execution time.",
    }


@mcp.tool()
def detect_query_inefficiencies(
    connection_id: str,
    sql: str,
    *,
    access_token: Optional[str] = None,
) -> dict:
    """Detect static SQL inefficiencies (SELECT *, missing LIMIT, etc.)."""
    authorize(
        access_token=access_token,
        permission=PERMISSION_INEFFICIENCY_DETECT,
        connection_id=connection_id,
    )
    conn = _get_connection(connection_id)
    # First get plan findings if possible to mark plan_confirmed.
    plan_findings = []
    try:
        svc = PerformanceService(connection=conn, discovery_service=DiscoveryService(conn))
        analysis = svc.analyze_query_plan(sql)
        plan_findings = [
            type("PF", (), {"identifier": f["identifier"]})() for f in analysis.get("findings", [])
        ]
    except Exception:
        plan_findings = []

    from querymind.services.query_optimization_service import analyze_inefficiencies

    findings = analyze_inefficiencies(sql, plan_findings=plan_findings)
    return {
        "connection_id": connection_id,
        "sql": sql,
        "inefficiencies": findings,
        "count": len(findings),
    }
