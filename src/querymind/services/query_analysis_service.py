"""PostgreSQL EXPLAIN JSON plan analysis.

Parses EXPLAIN (FORMAT JSON) output into a structured plan tree and
detects potential performance issues with supporting evidence. Does not
claim optimizations improve performance unless measured.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PlanFinding:
    """A single performance finding from a plan."""

    identifier: str
    severity: str  # info | low | medium | high
    node_type: str
    explanation: str
    evidence: dict[str, Any]
    suggested_action: str
    confidence: str  # low | medium | high


@dataclass
class PlanAnalysisResult:
    """Result of analyzing an EXPLAIN JSON plan."""

    plan_tree: dict[str, Any]
    total_cost: Optional[float] = None
    startup_cost: Optional[float] = None
    estimated_rows: Optional[int] = None
    estimated_width: Optional[int] = None
    findings: list[PlanFinding] = field(default_factory=list)
    raw_plan: list[dict[str, Any]] = field(default_factory=list)


class QueryPlanAnalyzer:
    """Analyzes a PostgreSQL EXPLAIN (FORMAT JSON) plan."""

    def analyze(self, explain_json: Any) -> PlanAnalysisResult:
        """Analyze an already-parsed EXPLAIN JSON structure."""
        if isinstance(explain_json, str):
            import json

            explain_json = json.loads(explain_json)

        # EXPLAIN (FORMAT JSON) returns a list with one plan object.
        plans = explain_json if isinstance(explain_json, list) else [explain_json]
        raw = plans
        plan_tree = plans[0].get("Plan", {}) if plans else {}

        result = PlanAnalysisResult(
            plan_tree=plan_tree,
            raw_plan=raw,
        )

        if plan_tree:
            result.total_cost = plan_tree.get("Total Cost")
            result.startup_cost = plan_tree.get("Startup Cost")
            result.estimated_rows = plan_tree.get("Plan Rows")
            result.estimated_width = plan_tree.get("Plan Width")

        result.findings = self._detect_findings(plan_tree)
        return result

    def _detect_findings(self, node: dict[str, Any]) -> list[PlanFinding]:
        findings: list[PlanFinding] = []
        if not isinstance(node, dict):
            return findings

        node_type = node.get("Node Type", "Unknown")
        plan_rows = node.get("Plan Rows")
        total_cost = node.get("Total Cost")

        # Sequential scan on a potentially large table.
        if node_type == "Seq Scan":
            rel = node.get("Relation Name")
            findings.append(
                PlanFinding(
                    identifier="seq_scan",
                    severity="medium",
                    node_type=node_type,
                    explanation=(
                        f"Sequential scan on '{rel}' reads every row. "
                        "Acceptable for small tables or low-selectivity queries;"
                        " consider an index for selective filters on large tables."
                    ),
                    evidence={
                        "relation": rel,
                        "plan_rows": plan_rows,
                        "total_cost": total_cost,
                    },
                    suggested_action=(
                        "Review filter selectivity and table size; add a "
                        "B-tree index on filtered columns if the table is large."
                    ),
                    confidence="medium",
                )
            )

        # Nested loop join.
        if node_type == "Nested Loop":
            findings.append(
                PlanFinding(
                    identifier="nested_loop_join",
                    severity="low",
                    node_type=node_type,
                    explanation=(
                        "Nested loop join detected. Efficient for small inner "
                        "relations; can be expensive with large outer/inner sets."
                    ),
                    evidence={"plan_rows": plan_rows, "total_cost": total_cost},
                    suggested_action=(
                        "Verify join columns are indexed; consider hash/merge "
                        "join alternatives for larger inputs."
                    ),
                    confidence="low",
                )
            )

        # Sort operation.
        if node_type == "Sort":
            findings.append(
                PlanFinding(
                    identifier="sort_operation",
                    severity="low",
                    node_type=node_type,
                    explanation=(
                        "Explicit sort detected. Can be avoided with an index "
                        "matching the ORDER BY column(s)."
                    ),
                    evidence={"plan_rows": plan_rows, "total_cost": total_cost},
                    suggested_action=(
                        "Add an index on ORDER BY columns to eliminate the sort."
                    ),
                    confidence="medium",
                )
            )

        # Hash join.
        if node_type == "Hash Join":
            findings.append(
                PlanFinding(
                    identifier="hash_join",
                    severity="info",
                    node_type=node_type,
                    explanation=(
                        "Hash join detected. Generally efficient for medium-to-large "
                        "inputs but requires memory work_mem."
                    ),
                    evidence={"plan_rows": plan_rows, "total_cost": total_cost},
                    suggested_action=(
                        "Ensure work_mem is sufficient; monitor for spills to disk."
                    ),
                    confidence="low",
                )
            )

        # Recurse into sub-plans.
        for key in ("Plans", "Subplans", "InitPlan", "SubPlan"):
            sub = node.get(key)
            if isinstance(sub, list):
                for child in sub:
                    findings.extend(self._detect_findings(child))
            elif isinstance(sub, dict):
                findings.extend(self._detect_findings(sub))

        return findings


def analyze_explain_json(explain_json: Any) -> PlanAnalysisResult:
    """Convenience wrapper around QueryPlanAnalyzer."""
    return QueryPlanAnalyzer().analyze(explain_json)
