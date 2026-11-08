# PostgreSQL Integration Checklist — QueryMind MCP

The development environment in this session has **no live PostgreSQL server**
(EnterpriseDB CDN returns HTTP 403; Docker not installed; no existing binaries).
All service logic is implemented and unit-tested offline, but live execution
against a real PostgreSQL instance is **BLOCKED** until provisioned.

## 1. Required PostgreSQL version
PostgreSQL 17+ (target database).

## 2. Required extensions
- `pg_stat_statements` (slow-query ranking; optional — degrades gracefully).
- `pgvector` (optional — only if semantic schema retrieval is later justified).

## 3. Target database creation
Create a read-only target database (e.g. `ecommerce`) with the synthetic
e-commerce schema (customers, orders, order_items, products, payments) and a
least-privilege `readonly` role.

## 4. Internal database setup
Create the QueryMind internal database (`querymind` on port 5433 by default)
for users, organizations, connections, schema snapshots, query history,
analyses, health snapshots, anomaly events, and audit logs. Migrations via
Alembic (`alembic/`).

## 5. Read-only database role requirements
The target role must be able to:
- `SELECT` on `information_schema`, `pg_catalog`, `pg_class`, `pg_attribute`,
  `pg_constraint`, `pg_indexes`, `pg_stat_user_tables`, `pg_stat_activity`.
- `EXPLAIN` on target tables.
- Must NOT have INSERT/UPDATE/DELETE/DDL privileges (enforced at the DB role,
  not only in application code).

## 6. Environment variables
Copy `.env.example` to `.env` and set:
- `DATABASE_URL` — internal QueryMind database.
- `TARGET_DATABASE_URL` — target read-only database.
- `SECRET_KEY`, `ENCRYPTION_KEY`.
- `LLM_PROVIDER=mock` (tests) or a real provider.
- `MAX_RESULT_ROWS`, `STATEMENT_TIMEOUT_MS`.
- `MCP_TRANSPORT=stdio` or `streamable-http`.

## 7. Migration commands
```powershell
.venv\Scripts\python.exe -m alembic upgrade head
```

## 8. Integration test commands
```powershell
.venv\Scripts\python.exe -m pytest tests/integration -q
```

## 9. Expected successful outputs
Discovery against a live target returns JSON with:
- `database_version` (PostgreSQL 17+).
- `schemas`, `tables` (with columns, PKs, FKs, indexes, stats).
- `relationships`, `indexes`, `table_stats`.

## 10. Security verification steps
- Confirm `connect_database` rejects non-allowlisted hosts.
- Confirm `validate_sql` rejects DROP/DELETE/UPDATE/INSERT/multi-statement.
- Confirm `execute_readonly_query` enforces read-only transaction and row limit.
- Confirm credentials never appear in logs or tool outputs.

## Status
**BLOCKED** — no live PostgreSQL available in this environment. Provision a
target PostgreSQL 17+ instance and run the steps above to complete live
verification.
