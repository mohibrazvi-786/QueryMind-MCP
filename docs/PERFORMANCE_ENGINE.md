# Performance Engine — QueryMind MCP

Evidence-driven PostgreSQL performance investigation.

## Components

### Query plan analyzer (`services/query_analysis_service.py`)
`QueryPlanAnalyzer.analyze(explain_json)` parses `EXPLAIN (FORMAT JSON)`
output into a structured plan tree and detects:
- Sequential scans (with table, rows, cost evidence).
- Nested-loop joins.
- Sort operations.
- Hash joins.

Each finding is a `PlanFinding` with identifier, severity, node type,
explanation, evidence, suggested action, and confidence. Defaults to
`EXPLAIN (FORMAT JSON)` — never `EXPLAIN ANALYZE` automatically.

### SQL inefficiency analyzer (`services/query_optimization_service.py`)
Static analysis rules (each with a stable ID, description, severity,
evidence, recommendation, unit tests):
- QI-001 SELECT *
- QI-002 missing LIMIT
- QI-003 leading-wildcard LIKE
- QI-004 function on predicate column
- QI-005 redundant DISTINCT with GROUP BY
- QI-006 excessive OR predicates
- QI-007 unbounded aggregation
- QI-008 potential N+1 (multiple subqueries)

Findings are marked `plan_confirmed` only when backed by EXPLAIN evidence.

### Index advisor (`services/query_optimization_service.py`)
`IndexAdvisor.recommend(...)` produces evidence-based `CREATE INDEX`
proposals (single-column B-tree, composite, covering) with reason, expected
benefit, write overhead, storage implications, confidence, and existing-index
overlap. **Never executes DDL.**

### Performance service (`services/performance_service.py`)
Orchestrates health collection, `EXPLAIN` plan analysis, inefficiency
detection, index recommendations, slow-query ranking (via `pg_stat_statements`,
degrading gracefully when unavailable), and structured `PerformanceReport`
(JSON/Markdown via `reporting_service`).

## Rules

- `EXPLAIN` is the default analysis method; `EXPLAIN ANALYZE` executes the
  query and is never run automatically against an unrestricted target.
- Never claim an optimization improves performance unless measured.
- Recommendations are proposed SQL only; no automatic index creation.

## Status

Implemented and unit-tested with synthetic EXPLAIN plans. Live `EXPLAIN`
execution and `pg_stat_statements` integration require a real PostgreSQL
instance (see `docs/POSTGRESQL_INTEGRATION_CHECKLIST.md`).
