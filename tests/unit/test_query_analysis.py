"""Unit tests for query plan analysis service."""

from __future__ import annotations

from querymind.services.query_analysis_service import (
    PlanFinding,
    QueryPlanAnalyzer,
    analyze_explain_json,
)


def test_analyze_seq_scan_finding():
    plan = {
        "Plan": {
            "Node Type": "Seq Scan",
            "Relation Name": "orders",
            "Plan Rows": 500000,
            "Total Cost": 12345.0,
            "Startup Cost": 0.0,
        }
    }
    result = QueryPlanAnalyzer().analyze(plan)
    assert result.total_cost == 12345.0
    assert result.estimated_rows == 500000
    assert any(f.identifier == "seq_scan" for f in result.findings)
    seq = next(f for f in result.findings if f.identifier == "seq_scan")
    assert seq.severity == "medium"
    assert "orders" in seq.explanation


def test_analyze_nested_loop_finding():
    plan = {
        "Plan": {
            "Node Type": "Nested Loop",
            "Plan Rows": 100,
            "Total Cost": 50.0,
        }
    }
    result = QueryPlanAnalyzer().analyze(plan)
    assert any(f.identifier == "nested_loop_join" for f in result.findings)


def test_analyze_sort_finding():
    plan = {
        "Plan": {
            "Node Type": "Sort",
            "Plan Rows": 1000,
            "Total Cost": 200.0,
        }
    }
    result = QueryPlanAnalyzer().analyze(plan)
    assert any(f.identifier == "sort_operation" for f in result.findings)


def test_analyze_empty_plan():
    result = QueryPlanAnalyzer().analyze({})
    assert result.total_cost is None
    assert result.findings == []


def test_convenience_wrapper():
    plan = [{"Plan": {"Node Type": "Seq Scan", "Relation Name": "t", "Plan Rows": 10, "Total Cost": 1.0}}]
    result = analyze_explain_json(plan)
    assert len(result.findings) >= 1
