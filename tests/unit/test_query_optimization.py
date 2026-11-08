"""Unit tests for SQL inefficiency detection and index advisor."""

from __future__ import annotations

from querymind.services.query_optimization_service import (
    IndexAdvisor,
    SQLInefficiencyAnalyzer,
    analyze_inefficiencies,
)


def test_select_star_detected():
    findings = SQLInefficiencyAnalyzer().analyze("SELECT * FROM customers")
    assert any(f.rule_id == "QI-001" for f in findings)


def test_missing_limit_detected():
    findings = SQLInefficiencyAnalyzer().analyze("SELECT id FROM customers")
    assert any(f.rule_id == "QI-002" for f in findings)


def test_leading_wildcard_detected():
    findings = SQLInefficiencyAnalyzer().analyze("SELECT id FROM customers WHERE email LIKE '%@x.com'")
    assert any(f.rule_id == "QI-003" for f in findings)


def test_function_on_predicate_column_detected():
    findings = SQLInefficiencyAnalyzer().analyze("SELECT id FROM customers WHERE lower(email) = 'a@b.c'")
    assert any(f.rule_id == "QI-004" for f in findings)


def test_redundant_distinct_detected():
    findings = SQLInefficiencyAnalyzer().analyze("SELECT DISTINCT id FROM customers GROUP BY id")
    assert any(f.rule_id == "QI-005" for f in findings)


def test_excessive_or_detected():
    sql = "SELECT id FROM customers WHERE a = 1 OR b = 2 OR c = 3 OR d = 4"
    findings = SQLInefficiencyAnalyzer().analyze(sql)
    assert any(f.rule_id == "QI-006" for f in findings)


def test_unbounded_aggregation_detected():
    findings = SQLInefficiencyAnalyzer().analyze("SELECT count(*) FROM customers")
    assert any(f.rule_id == "QI-007" for f in findings)


def test_potential_n_plus_one_detected():
    findings = SQLInefficiencyAnalyzer().analyze(
        "SELECT id, (SELECT 1), (SELECT 2) FROM customers"
    )
    assert any(f.rule_id == "QI-008" for f in findings)


def test_clean_query_no_findings():
    findings = SQLInefficiencyAnalyzer().analyze("SELECT id, email FROM customers WHERE id = 1 LIMIT 10")
    assert findings == []


def test_index_advisor_single_column():
    advisor = IndexAdvisor()
    recs = advisor.recommend(
        table="orders",
        predicates=["customer_id"],
        table_row_estimate=500000,
    )
    assert len(recs) == 1
    assert recs[0].columns == ["customer_id"]
    assert recs[0].proposed_sql.startswith("CREATE INDEX")
    assert recs[0].confidence == "medium"


def test_index_advisor_composite():
    advisor = IndexAdvisor()
    recs = advisor.recommend(
        table="orders",
        predicates=["customer_id"],
        order_by=["order_date"],
    )
    composite = [r for r in recs if r.index_type == "composite"]
    assert len(composite) == 1
    assert composite[0].columns == ["customer_id", "order_date"]


def test_index_advisor_existing_overlap_skipped():
    advisor = IndexAdvisor()
    recs = advisor.recommend(
        table="orders",
        predicates=["customer_id"],
        existing_indexes=[{"index_name": "idx_orders_customer_id", "indexdef": "CREATE INDEX idx_orders_customer_id ON orders (customer_id)"}],
    )
    assert recs == []
