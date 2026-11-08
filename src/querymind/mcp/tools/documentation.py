"""MCP tools — Monitoring (2 tools) and Documentation (2 tools).

Group D: get_database_health, detect_database_anomalies.
Group E: generate_schema_documentation, search_database_knowledge.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from querymind.core.exceptions import DatabaseError, NotFoundError
from querymind.core.rbac import (
    PERMISSION_ANOMALY_DETECT,
    PERMISSION_DOCUMENTATION_GENERATE,
    PERMISSION_HEALTH_READ,
    PERMISSION_KNOWLEDGE_SEARCH,
)
from querymind.database.connection import TargetConnection
from querymind.intelligence.embeddings.provider import MockEmbeddingProvider
from querymind.intelligence.retrieval.service import RetrievedDocument
from querymind.mcp.app import connection_registry, mcp
from querymind.mcp.authz import authorize
from querymind.services.discovery_service import DiscoveryService
from querymind.services.performance_service import PerformanceService
from querymind.services.rag_service import RAGService


def _get_connection(connection_id: str) -> TargetConnection:
    conn = connection_registry.get(connection_id)
    if conn is None:
        raise NotFoundError(f"Connection '{connection_id}' not registered", code="connection_not_found")
    return conn


# Shared rag service (created lazily per connection).
_rag_service: Optional[RAGService] = None


def _rag(connection_id: str) -> RAGService:
    global _rag_service
    if _rag_service is None:
        conn = _get_connection(connection_id)
        from querymind.intelligence.retrieval.service import RetrievalService

        retrieval = RetrievalService(embedding_provider=MockEmbeddingProvider())
        _rag_service = RAGService(
            discovery_service=DiscoveryService(conn),
            retrieval_service=retrieval,
            embedding_provider=MockEmbeddingProvider(),
        )
    return _rag_service


@mcp.tool()
def get_database_health(
    connection_id: str, *, access_token: Optional[str] = None
) -> dict:
    """Retrieve database health metrics with configurable-threshold status."""
    authorize(
        access_token=access_token,
        permission=PERMISSION_HEALTH_READ,
        connection_id=connection_id,
    )
    conn = _get_connection(connection_id)
    svc = PerformanceService(connection=conn, discovery_service=DiscoveryService(conn))
    try:
        report = svc.health()
    except Exception as exc:  # noqa: BLE001
        raise DatabaseError(f"Health collection failed: {exc}", code="health_failed") from exc

    return {
        "connection_id": connection_id,
        "status": report.status,
        "metrics": [
            {
                "name": m.name,
                "value": m.value,
                "status": m.status,
                "threshold": m.threshold,
                "unit": m.unit,
                "collected_at": m.collected_at,
            }
            for m in report.metrics
        ],
        "warnings": report.warnings,
        "collected_at": report.collected_at,
    }


@mcp.tool()
def detect_database_anomalies(
    connection_id: str, *, access_token: Optional[str] = None
) -> dict:
    """Identify unusual database patterns using statistical + ML detection."""
    authorize(
        access_token=access_token,
        permission=PERMISSION_ANOMALY_DETECT,
        connection_id=connection_id,
    )
    from querymind.services.anomaly_detection_service import (
        AnomalyDetector,
        MetricObservation,
    )

    conn = _get_connection(connection_id)
    discovery = DiscoveryService(conn)

    detector = AnomalyDetector(z_score_threshold=3.0)
    events = []

    # Build observations from table stats (row counts) as example metrics.
    try:
        stats = discovery.discover_table_stats()
    except Exception as exc:  # noqa: BLE001
        raise DatabaseError(f"Could not collect metrics: {exc}", code="metrics_failed") from exc

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()

    for s in stats:
        row_est = s.get("row_estimate")
        if row_est is None:
            continue
        obs = MetricObservation(
            metric="table_row_count",
            value=float(row_est),
            timestamp=now,
            database="target",
            dimensions={"table": f"{s.get('table_schema')}.{s.get('table_name')}"},
        )
        detector.observe(obs)
        # Train isolation forest if enough data.
        if len(detector._baselines) >= 1 and not detector.model_trained:
            feature_rows = [
                [float(x.get("row_estimate") or 0)] for x in stats if x.get("row_estimate")
            ]
            if len(feature_rows) >= 10:
                detector.train_isolation_forest(feature_rows)
        event = detector.detect(obs, feature_vector=[float(row_est)])
        events.extend(event)

    # If no anomalies detected, report baseline state honestly.
    return {
        "connection_id": connection_id,
        "anomalies": [
            {
                "event_id": e.event_id,
                "metric": e.metric,
                "observed_value": e.observed_value,
                "expected_baseline": e.expected_baseline,
                "anomaly_score": e.anomaly_score,
                "severity": e.severity,
                "detection_algorithm": e.detection_algorithm,
                "explanation": e.explanation,
                "timestamp": e.timestamp,
                "model_version": e.model_version,
            }
            for e in events
        ],
        "count": len(events),
        "sklearn_available": detector.sklearn_available,
        "model_trained": detector.model_trained,
        "note": "Simulated anomaly detection over collected metrics; no synthetic results are presented as real.",
    }


@mcp.tool()
def generate_schema_documentation(
    connection_id: str,
    *,
    format: str = "markdown",
    access_token: Optional[str] = None,
) -> dict:
    """Generate schema documentation (Markdown or JSON) grounded in discovered metadata."""
    authorize(
        access_token=access_token,
        permission=PERMISSION_DOCUMENTATION_GENERATE,
        connection_id=connection_id,
    )
    conn = _get_connection(connection_id)
    discovery = DiscoveryService(conn)
    try:
        catalogue = discovery.discover_all()
    except Exception as exc:  # noqa: BLE001
        raise DatabaseError(f"Failed to discover schema: {exc}", code="discover_failed") from exc

    if format == "json":
        content = {
            "database_version": catalogue.get("database_version"),
            "schemas": catalogue.get("schemas", []),
            "tables": catalogue.get("tables", []),
            "relationships": catalogue.get("relationships", []),
            "indexes": catalogue.get("indexes", []),
        }
    else:
        lines = [f"# Schema Documentation — {catalogue.get('database_version', 'unknown')}", ""]
        lines.append(f"## Schemas\n{', '.join(catalogue.get('schemas', []))}\n")
        lines.append("## Tables\n")
        for t in catalogue.get("tables", []):
            lines.append(f"### {t['schema']}.{t['name']} ({t.get('type')})")
            lines.append(f"- Primary keys: {', '.join(t.get('primary_keys', [])) or 'none'}")
            lines.append(f"- Columns: {len(t.get('columns', []))}")
            lines.append(f"- Indexes: {len(t.get('indexes', []))}")
            stats = t.get("stats", {})
            if stats.get("row_estimate") is not None:
                lines.append(f"- Row estimate: {stats['row_estimate']}")
            lines.append("")
        lines.append("## Relationships\n")
        for r in catalogue.get("relationships", []):
            lines.append(
                f"- {r['source_schema']}.{r['source_table']}.{r['source_column']} → "
                f"{r['target_schema']}.{r['target_table']}.{r['target_column']} "
                f"({r.get('constraint_name')})"
            )
        if not catalogue.get("relationships"):
            lines.append("- None discovered.\n")
        content = "\n".join(lines)

    return {
        "connection_id": connection_id,
        "format": format,
        "database_version": catalogue.get("database_version"),
        "content": content,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


@mcp.tool()
def search_database_knowledge(
    connection_id: str,
    query: str,
    *,
    top_k: int = 5,
    schema_filter: Optional[str] = None,
    access_token: Optional[str] = None,
) -> dict:
    """Search indexed schema knowledge (hybrid keyword + semantic retrieval)."""
    authorize(
        access_token=access_token,
        permission=PERMISSION_KNOWLEDGE_SEARCH,
        connection_id=connection_id,
    )
    rag = _rag(connection_id)
    # Ensure schema is indexed first.
    try:
        rag.ingest_schema()
    except Exception as exc:  # noqa: BLE001
        raise DatabaseError(f"Schema indexing failed: {exc}", code="indexing_failed") from exc

    result = rag.search_schema(query, top_k=top_k, schema_filter=schema_filter)
    return {
        "connection_id": connection_id,
        "query": result.query,
        "documents": [
            {
                "doc_id": d.doc_id,
                "content": d.content,
                "relevance_score": d.relevance_score,
                "source": d.source,
                "doc_type": d.doc_type,
                "schema": d.schema,
                "table": d.table,
                "column": d.column,
                "retrieval_method": d.retrieval_method,
            }
            for d in result.documents
        ],
        "total_retrieved": result.total_retrieved,
    }
