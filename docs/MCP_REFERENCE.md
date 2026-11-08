# MCP Reference — QueryMind MCP

Complete catalogue of the Model Context Protocol (MCP) surface: 19 tools, 6
resources, and 6 prompts.

## Transport

- **STDIO** — local development and desktop MCP clients (Claude Desktop, MCP Inspector).
- **Streamable HTTP** — remote MCP access (localhost by default; use a reverse proxy + TLS in production).

Start the server:

```powershell
# stdio
.venv\Scripts\python.exe -m querymind.mcp.transports run-stdio

# streamable-http
.venv\Scripts\python.exe -m querymind.mcp.transports run-http
```

## Tools — 19

### Group A: Database discovery (6)

| Tool | Purpose |
|------|---------|
| `connect_database` | Register and verify a read-only target database connection |
| `list_databases` | List databases visible to the configured role |
| `list_tables` | Retrieve schemas and tables (filter, paginate) |
| `describe_table` | Inspect columns, keys, indexes, stats for one table |
| `get_relationships` | Retrieve foreign-key relationship graph |
| `get_database_stats` | Retrieve database/table statistics |

### Group B: SQL intelligence (5)

| Tool | Purpose |
|------|---------|
| `generate_sql` | Generate PostgreSQL SQL from natural language (not executed) |
| `validate_sql` | SQLGlot AST validation — read-only, single-statement, allowlists |
| `explain_sql` | EXPLAIN (FORMAT JSON) plan — no EXPLAIN ANALYZE |
| `execute_readonly_query` | Execute one validated read-only SELECT (timeout, row limit) |
| `analyze_query_plan` | Evidence-based plan analysis findings |

### Group C: Database optimization (4)

| Tool | Purpose |
|------|---------|
| `recommend_indexes` | Evidence-based CREATE INDEX proposals (DDL never executed) |
| `analyze_slow_queries` | Rank expensive queries via pg_stat_statements (degrades gracefully) |
| `compare_query_performance` | Compare two query variants by EXPLAIN estimated cost |
| `detect_query_inefficiencies` | Static SQL inefficiency rules (SELECT *, missing LIMIT, etc.) |

### Group D: Monitoring (2)

| Tool | Purpose |
|------|---------|
| `get_database_health` | Health metrics with configurable-threshold status |
| `detect_database_anomalies` | Statistical + Isolation Forest anomaly detection |

### Group E: Documentation & schema knowledge (2)

| Tool | Purpose |
|------|---------|
| `generate_schema_documentation` | Markdown/JSON schema documentation from discovered metadata |
| `search_database_knowledge` | Hybrid keyword + semantic schema search |

## Resources — 6

| URI | Purpose |
|-----|---------|
| `querymind://database/schema` | Full schema catalogue snapshot (JSON) |
| `querymind://database/tables` | Tables and columns snapshot |
| `querymind://database/relationships` | Foreign-key relationship snapshot |
| `querymind://database/health` | Health metrics snapshot |
| `querymind://database/documentation` | Schema documentation (Markdown) |
| `querymind://database/metrics` | Table stats and size metrics snapshot |

All resources return current, timestamped snapshots from the first registered connection.

## Prompts — 6

| Prompt | Purpose |
|--------|---------|
| `database_health_audit` | Audit database health, produce prioritized findings |
| `sql_query_optimization` | Optimize a SQL query using plan analysis + index recommendations |
| `database_schema_explanation` | Explain a database schema in plain language |
| `database_security_review` | Review database access security and configuration |
| `slow_query_investigation` | Investigate a slow query using plan evidence |
| `database_performance_report` | Generate a complete database performance report |

## Security

- Every tool validates its inputs via Pydantic/FastMCP schemas.
- Credentials are never returned; connection strings are redacted in logs.
- All SQL execution is read-only, single-statement, AST-validated, allowlist-checked, timeout-limited, and row-limited.
- Cross-tenant and unauthorized host access is blocked.

## Status

Live execution against a real PostgreSQL instance requires a provisioned target database (see `docs/POSTGRESQL_INTEGRATION_CHECKLIST.md`). All service logic, validation, registration, and transport wiring are unit-tested.
