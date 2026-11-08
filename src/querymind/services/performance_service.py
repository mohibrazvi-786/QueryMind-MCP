"""Database performance intelligence service.

Ties together query plan analysis, inefficiency detection, index
recommendations, slow-query statistics, and health monitoring into
structured reports. All evidence comes from actual database metadata and
EXPLAIN plans — no fabricated measurements.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from querymind.core.exceptions import DatabaseError
from querymind.database.connection import TargetConnection
from querymind.services.discovery_service import DiscoveryService
from querymind.services.query_analysis_service import QueryPlanAnalyzer
from querymind.services.query_optimization_service import (
    IndexAdvisor,
    SQLInefficiencyAnalyzer,
)


@dataclass
class HealthMetric:
    """A single health metric with status."""

    name: str
    value: Any
    status: str  # ok | warn | critical | unknown
    threshold: Optional[Any] = None
    unit: str = ""
    collected_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class HealthReport:
    """Database health report."""

    database: str
    status: str  # ok | warn | critical
    metrics: list[HealthMetric] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    collected_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class PerformanceReport:
    """Structured performance report."""

    database: str
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    slow_queries: list[dict] = field(default_factory=list)
    plan_findings: list[dict] = field(default_factory=list)
    index_recommendations: list[dict] = field(default_factory=list)
    inefficiencies: list[dict] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    data_limitations: list[str] = field(default_factory=list)


class PerformanceService:
    """Orchestrates performance analysis against a target database."""

    def __init__(
        self,
        *,
        connection: TargetConnection,
        discovery_service: DiscoveryService,
    ) -> None:
        self.connection = connection
        self.discovery = discovery_service
        self.plan_analyzer = QueryPlanAnalyzer()
        self.inefficiency_analyzer = SQLInefficiencyAnalyzer()
        self.index_advisor = IndexAdvisor()

    def health(self) -> HealthReport:
        """Collect database health metrics, degrading gracefully when
        statistics are unavailable or permissions are insufficient."""
        metrics: list[HealthMetric] = []
        warnings: list[str] = []
        overall = "ok"

        # Database size and table stats from discovery (safe, read-only).
        try:
            stats = self.discovery.discover_table_stats()
            total_bytes = 0
            for s in stats:
                total_bytes += int(s.get("total_bytes") or 0)
            metrics.append(
                HealthMetric(
                    name="database_size_bytes",
                    value=total_bytes,
                    status="ok",
                    unit="bytes",
                )
            )
            metrics.append(
                HealthMetric(
                    name="table_count",
                    value=len(stats),
                    status="ok",
                )
            )
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"Could not collect table statistics: {exc}")
            overall = "unknown"

        # Connection health via a cheap query.
        try:
            rows = self.connection.execute(
                "SELECT count(*) AS n FROM pg_stat_activity"
            )
            active = int(rows[0]["n"]) if rows else 0
            metrics.append(
                HealthMetric(
                    name="active_connections",
                    value=active,
                    status="warn" if active > 80 else "ok",
                    threshold=100,
                )
            )
            if active > 80:
                warnings.append(f"High connection count: {active}")
                overall = "warn"
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"Could not collect connection stats: {exc}")
            if overall == "ok":
                overall = "unknown"

        return HealthReport(
            database="target",
            status=overall,
            metrics=metrics,
            warnings=warnings,
        )

    def analyze_query_plan(self, sql: str) -> dict:
        """Run EXPLAIN (FORMAT JSON) on a read-only SQL statement and analyze it."""
        from querymind.services.sql_validation_service import validate_readonly_sql

        # Validate first — only read-only, single statement.
        validate_readonly_sql(sql)

        explain_sql = f"EXPLAIN (FORMAT JSON) {sql}"
        try:
            rows = self.connection.execute(explain_sql)
        except Exception as exc:  # noqa: BLE001
            raise DatabaseError(f"EXPLAIN failed: {exc}") from exc

        if not rows:
            raise DatabaseError("EXPLAIN returned no plan")

        # pg returns the JSON plan as the first column of the first row.
        plan = rows[0]
        plan_value = None
        for key, value in plan.items():
            plan_value = value
            break

        analysis = self.plan_analyzer.analyze(plan_value)
        return {
            "plan_tree": analysis.plan_tree,
            "total_cost": analysis.total_cost,
            "startup_cost": analysis.startup_cost,
            "estimated_rows": analysis.estimated_rows,
            "estimated_width": analysis.estimated_width,
            "findings": [
                {
                    "identifier": f.identifier,
                    "severity": f.severity,
                    "node_type": f.node_type,
                    "explanation": f.explanation,
                    "evidence": f.evidence,
                    "suggested_action": f.suggested_action,
                    "confidence": f.confidence,
                }
                for f in analysis.findings
            ],
        }

    def detect_inefficiencies(self, sql: str) -> list[dict]:
        """Static inefficiency detection for a SQL statement."""
        findings = self.inefficiency_analyzer.analyze(sql)
        return [
            {
                "rule_id": f.rule_id,
                "severity": f.severity,
                "explanation": f.explanation,
                "evidence": f.evidence,
                "recommendation": f.recommendation,
                "plan_confirmed": f.plan_confirmed,
            }
            for f in findings
        ]

    def recommend_indexes(self, *, table: str, context: dict) -> list[dict]:
        """Index recommendations for a table given query context."""
        recs = self.index_advisor.recommend(
            table=table,
            predicates=context.get("predicates", []),
            join_columns=context.get("join_columns", []),
            order_by=context.get("order_by", []),
            group_by=context.get("group_by", []),
            existing_indexes=context.get("existing_indexes", []),
            table_row_estimate=context.get("row_estimate"),
        )
        return [
            {
                "table": r.table,
                "columns": r.columns,
                "index_type": r.index_type,
                "proposed_sql": r.proposed_sql,
                "reason": r.reason,
                "supported_by": r.supported_by,
                "existing_index_overlap": r.existing_index_overlap,
                "expected_benefit": r.expected_benefit,
                "write_overhead": r.write_overhead,
                "storage_implication": r.storage_implication,
                "confidence": r.confidence,
            }
            for r in recs
        ]

    def generate_report(self, database: str) -> PerformanceReport:
        """Generate a full structured performance report."""
        report = PerformanceReport(database=database)

        # Health.
        health = self.health()
        report.data_limitations.extend(health.warnings)

        # Slow queries: attempt pg_stat_statements, degrade gracefully.
        try:
            rows = self.connection.execute(
                """
                SELECT query, calls, total_exec_time, mean_exec_time, rows
                FROM pg_stat_statements
                ORDER BY total_exec_time DESC
                LIMIT 10
                """
            )
            report.slow_queries = [
                {
                    "query": r.get("query"),
                    "calls": r.get("calls"),
                    "total_exec_time": r.get("total_exec_time"),
                    "mean_exec_time": r.get("mean_exec_time"),
                    "rows": r.get("rows"),
                }
                for r in rows
            ]
        except Exception as exc:  # noqa: BLE001
            report.data_limitations.append(
                f"pg_stat_statements unavailable: {exc}. Slow-query ranking degraded."
            )

        return report
