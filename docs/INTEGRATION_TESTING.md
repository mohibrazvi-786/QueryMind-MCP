# Integration Testing — QueryMind MCP

## Status

Integration tests require a live PostgreSQL instance and are **BLOCKED** in
this environment (no PostgreSQL server available; EnterpriseDB CDN returns
HTTP 403; Docker not installed).

## What would be verified

When a PostgreSQL instance is provisioned, integration tests cover:

- Connection establishment to target database
- Database listing
- Schema discovery (tables, columns, constraints, relationships, indexes)
- Database statistics
- SQL validation (safe SQL accepted, unsafe rejected)
- Read-only query execution
- EXPLAIN JSON plan extraction
- Slow-query statistics (`pg_stat_statements`)
- Index recommendation evidence
- Schema synchronization / RAG retrieval
- Internal database migrations (Alembic)
- Audit persistence
- Tenant isolation (cross-tenant access blocked)

## Synthetic e-commerce database

Tests use a synthetic e-commerce database with tables:
- customers, orders, order_items, products, payments

Deterministic synthetic data is used. No real customer data is ever used in
the test environment.

## Blocked classification

Any test requiring a live PostgreSQL connection, `pg_stat_statements`,
`EXPLAIN ANALYZE`, or pgvector is classified **BLOCKED**, not PASSED.

## Provisioning

See `docs/POSTGRESQL_INTEGRATION_CHECKLIST.md` for the steps required to
provision a target PostgreSQL 17+ instance and run integration tests.
