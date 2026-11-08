"""Static SQL inefficiency detection and evidence-based index recommendations.

Inefficiency rules are pure static analysis - they flag patterns that
commonly indicate avoidable work. Each finding is clearly separated from
plan-confirmed issues. The index advisor recommends indexes but never
executes DDL.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import re
import sqlglot
from sqlglot import exp


@dataclass
class InefficiencyFinding:
    """A single inefficiency finding."""

    rule_id: str
    severity: str  # info | low | medium | high
    explanation: str
    evidence: dict
    recommendation: str
    plan_confirmed: bool = False  # True only if backed by EXPLAIN evidence


@dataclass
class IndexRecommendation:
    """A single index recommendation."""

    table: str
    columns: list[str]
    index_type: str  # btree | composite | partial | covering | expression
    proposed_sql: str
    reason: str
    supported_by: list[str]  # query patterns / plan evidence
    existing_index_overlap: list[str]
    expected_benefit: str  # low | medium | high
    write_overhead: str  # low | medium | high
    storage_implication: str
    confidence: str  # low | medium | high


class SQLInefficiencyAnalyzer:
    """Detects static SQL inefficiencies using SQLGlot AST."""

    RULES = {
        "select_star": "QI-001",
        "missing_limit": "QI-002",
        "leading_wildcard_like": "QI-003",
        "function_on_predicate_column": "QI-004",
        "redundant_distinct": "QI-005",
        "excessive_or": "QI-006",
        "unbounded_aggregation": "QI-007",
        "potential_n_plus_one": "QI-008",
    }

    def analyze(self, sql: str, *, plan_findings=None) -> list[InefficiencyFinding]:
        """Analyze SQL and return a list of inefficiency findings."""
        plan_findings = plan_findings or []
        plan_confirmed_ids = {f.identifier for f in plan_findings}

        try:
            parsed = sqlglot.parse_one(sql, read="postgres")
        except Exception:  # noqa: BLE001
            return []

        findings: list[InefficiencyFinding] = []

        findings.extend(self._rule_select_star(parsed, plan_confirmed_ids))
        findings.extend(self._rule_missing_limit(parsed, plan_confirmed_ids))
        findings.extend(
            self._rule_leading_wildcard_like(parsed, plan_confirmed_ids)
        )
        findings.extend(
            self._rule_function_on_predicate_column(parsed, plan_confirmed_ids)
        )
        findings.extend(self._rule_redundant_distinct(parsed, plan_confirmed_ids))
        findings.extend(self._rule_excessive_or(parsed, plan_confirmed_ids))
        findings.extend(
            self._rule_unbounded_aggregation(parsed, plan_confirmed_ids)
        )
        findings.extend(
            self._rule_potential_n_plus_one(parsed, plan_confirmed_ids)
        )

        return findings

    # ---- individual rules ----

    def _rule_select_star(self, node, plan_confirmed_ids):
        findings = []
        for sel in node.find_all(exp.Select):
            for star in sel.find_all(exp.Star):
                findings.append(
                    InefficiencyFinding(
                        rule_id=self.RULES["select_star"],
                        severity="low",
                        explanation="SELECT * retrieves all columns, increasing I/O and network transfer. Prefer explicit column lists.",
                        evidence={"node": "SELECT *"},
                        recommendation="List only the columns actually needed.",
                        plan_confirmed="seq_scan" in plan_confirmed_ids,
                    )
                )
        return findings

    def _rule_missing_limit(self, node, plan_confirmed_ids):
        findings = []
        for sel in node.find_all(exp.Select):
            if not sel.find(exp.Limit):
                findings.append(
                    InefficiencyFinding(
                        rule_id=self.RULES["missing_limit"],
                        severity="low",
                        explanation="No LIMIT clause. Exploratory queries without LIMIT may return unexpectedly large result sets.",
                        evidence={"node": "SELECT without LIMIT"},
                        recommendation="Add a LIMIT for exploratory or ad-hoc queries.",
                        plan_confirmed=False,
                    )
                )
        return findings

    def _rule_leading_wildcard_like(self, node, plan_confirmed_ids):
        findings = []
        for like in node.find_all(exp.Like):
            pattern = like.args.get("expression")
            if isinstance(pattern, exp.Literal) and pattern.this.startswith("%"):
                findings.append(
                    InefficiencyFinding(
                        rule_id=self.RULES["leading_wildcard_like"],
                        severity="medium",
                        explanation="LIKE pattern with a leading wildcard cannot use a standard B-tree index efficiently.",
                        evidence={"pattern": pattern.this},
                        recommendation="Consider full-text search or an index on the expression if this pattern is frequent.",
                        plan_confirmed=False,
                    )
                )
        return findings

    def _rule_function_on_predicate_column(self, node, plan_confirmed_ids):
        findings = []
        for where in node.find_all(exp.Where):
            for func in where.find_all(exp.Func):
                for col in func.find_all(exp.Column):
                    findings.append(
                        InefficiencyFinding(
                            rule_id=self.RULES["function_on_predicate_column"],
                            severity="medium",
                            explanation=f"Function {func.name}() applied to a column in a predicate prevents index usage on that column.",
                            evidence={"function": func.name, "column": col.name},
                            recommendation="Rewrite the predicate to keep the column bare so an index can be used.",
                            plan_confirmed=False,
                        )
                    )
        return findings

    def _rule_redundant_distinct(self, node, plan_confirmed_ids):
        findings = []
        for sel in node.find_all(exp.Select):
            if sel.args.get("distinct"):
                if sel.find(exp.Group):
                    findings.append(
                        InefficiencyFinding(
                            rule_id=self.RULES["redundant_distinct"],
                            severity="low",
                            explanation="DISTINCT combined with GROUP BY is redundant because GROUP BY already produces unique rows.",
                            evidence={"node": "SELECT DISTINCT with GROUP BY"},
                            recommendation="Remove DISTINCT when GROUP BY is present.",
                            plan_confirmed=False,
                        )
                    )
        return findings

    def _rule_excessive_or(self, node, plan_confirmed_ids):
        findings = []
        for where in node.find_all(exp.Where):
            or_count = sum(1 for _ in where.find_all(exp.Or))
            if or_count >= 3:
                findings.append(
                    InefficiencyFinding(
                        rule_id=self.RULES["excessive_or"],
                        severity="low",
                        explanation=f"{or_count} OR predicates in WHERE may prevent efficient index use.",
                        evidence={"or_count": or_count},
                        recommendation="Consider UNION or an IN list instead of many ORs.",
                        plan_confirmed=False,
                    )
                )
        return findings

    def _rule_unbounded_aggregation(self, node, plan_confirmed_ids):
        findings = []
        for sel in node.find_all(exp.Select):
            has_agg = bool(sel.find(exp.AggFunc))
            if has_agg and not sel.find(exp.Group) and not sel.find(exp.Limit):
                findings.append(
                    InefficiencyFinding(
                        rule_id=self.RULES["unbounded_aggregation"],
                        severity="medium",
                        explanation="Aggregation without GROUP BY over an unbounded scan processes the whole table.",
                        evidence={"node": "aggregate without GROUP BY/LIMIT"},
                        recommendation="Add WHERE filters, GROUP BY, or LIMIT to bound the scan.",
                        plan_confirmed=False,
                    )
                )
        return findings

    def _rule_potential_n_plus_one(self, node, plan_confirmed_ids):
        findings = []
        subqueries = list(node.find_all(exp.Subquery))
        if len(subqueries) >= 2:
            findings.append(
                InefficiencyFinding(
                    rule_id=self.RULES["potential_n_plus_one"],
                    severity="info",
                    explanation="Multiple scalar subqueries may indicate an N+1 pattern that could be rewritten as a JOIN.",
                    evidence={"subquery_count": len(subqueries)},
                    recommendation="Rewrite correlated subqueries as JOINs where possible.",
                    plan_confirmed=False,
                )
            )
        return findings


def analyze_inefficiencies(
    sql: str, *, plan_findings=None
) -> list[InefficiencyFinding]:
    """Convenience wrapper around SQLInefficiencyAnalyzer."""
    return SQLInefficiencyAnalyzer().analyze(sql, plan_findings=plan_findings)


class IndexAdvisor:
    """Generates index recommendations from schema + query context."""

    def recommend(
        self,
        *,
        table: str,
        predicates: Optional[list[str]] = None,
        join_columns: Optional[list[str]] = None,
        order_by: Optional[list[str]] = None,
        group_by: Optional[list[str]] = None,
        existing_indexes: Optional[list[dict]] = None,
        table_row_estimate: Optional[int] = None,
    ) -> list[IndexRecommendation]:
        """Produce index recommendations for a table."""
        predicates = predicates or []
        join_columns = join_columns or []
        order_by = order_by or []
        group_by = group_by or []
        existing_indexes = existing_indexes or []

        existing_cols = self._existing_indexed_columns(existing_indexes)
        existing_col_names = {c for tup in existing_cols for c in tup}
        recommendations: list[IndexRecommendation] = []

        for col in predicates:
            if not col or col in existing_cols or col in existing_col_names:
                continue
            recommendations.append(
                IndexRecommendation(
                    table=table,
                    columns=[col],
                    index_type="btree",
                    proposed_sql=(
                        f"CREATE INDEX CONCURRENTLY idx_{table}_{col} "
                        f"ON {table} ({col});"
                    ),
                    reason=f"Column {col!r} appears in query predicates.",
                    supported_by=["query predicate analysis"],
                    existing_index_overlap=[],
                    expected_benefit="medium",
                    write_overhead="low",
                    storage_implication="one B-tree entry per row",
                    confidence=("medium" if table_row_estimate and table_row_estimate > 10000 else "low"),
                )
            )

        composite_cols = [c for c in predicates if c] + [
            c for c in order_by if c and c not in predicates
        ]
        if len(composite_cols) >= 2:
            key = tuple(composite_cols)
            if key not in existing_cols:
                recommendations.append(
                    IndexRecommendation(
                        table=table,
                        columns=list(composite_cols),
                        index_type="composite",
                        proposed_sql=(
                            "CREATE INDEX CONCURRENTLY idx_"
                            + table
                            + "_"
                            + "_".join(composite_cols)
                            + " ON "
                            + table
                            + " ("
                            + ", ".join(composite_cols)
                            + ");"
                        ),
                        reason="Composite index supports filtering and ordering.",
                        supported_by=["predicate + ORDER BY analysis"],
                        existing_index_overlap=[],
                        expected_benefit="high",
                        write_overhead="medium",
                        storage_implication="larger B-tree key per row",
                        confidence="medium",
                    )
                )

        # Deduplicate by (table, columns, index_type).
        seen = set()
        deduped = []
        for rec in recommendations:
            sig = (rec.table, tuple(rec.columns), rec.index_type)
            if sig in seen:
                continue
            seen.add(sig)
            deduped.append(rec)

        return deduped

    @staticmethod
    def _existing_indexed_columns(indexes: list[dict]) -> set:
        """Return a set of column tuples covered by existing indexes."""
        covered = set()
        for idx in indexes:
            cols = idx.get("columns") or idx.get("column_names") or []
            if cols:
                covered.add(tuple(cols))
            defn = idx.get("indexdef") or ""
            m = re.search(r"\(([^)]+)\)", defn)
            if m:
                inner = m.group(1)
                parts = [p.strip() for p in inner.split(",")]
                if parts:
                    covered.add(tuple(parts))
        return covered
