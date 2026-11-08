# Changelog — QueryMind MCP

## [0.1.0] — Unreleased

### Added
- Repository audit (`docs/REPOSITORY_AUDIT.md`).
- Architecture (`docs/ARCHITECTURE.md`) and database design (`docs/DATABASE_DESIGN.md`).
- Python project scaffold: `pyproject.toml` (pinned deps), package layout under `src/querymind`.
- Core modules: `config`, `exceptions`, `logging`, `security`.
- Database connection layer (`database/connection.py`) — read-only `TargetConnection` with statement timeouts and row limits.
- Database discovery engine (`services/discovery_service.py`) — information_schema + pg_catalog queries; JSON schema catalogue with no hardcoded table names.
- SQL validation service (`services/sql_validation_service.py`) — SQLGlot AST-based read-only validation.
- SQL generation service (`services/sql_generation_service.py`) — provider-independent NL-to-SQL with mock LLM.
- Query plan analyzer (`services/query_analysis_service.py`) — EXPLAIN JSON parsing + findings.
- Query optimization service (`services/query_optimization_service.py`) — 8 inefficiency rules + index advisor.
- Anomaly detection service (`services/anomaly_detection_service.py`) — Z-score/EWMA baselines + Isolation Forest.
- Reporting service (`services/reporting_service.py`) — Markdown/JSON reports.
- RAG pipeline (`services/rag_service.py`, `intelligence/embeddings/`, `intelligence/retrieval/`) — ingestion + hybrid retrieval.
- MCP server (`src/querymind/mcp/`) — 19 tools, 6 resources, 6 prompts; STDIO + Streamable HTTP.
- Unit, MCP, security, and evaluation tests (68 passing).

### Changed
- `pyproject.toml` dependency versions pinned to installed, Python 3.13-compatible releases.

### Blocked (environment)
- Live PostgreSQL integration (no server available; EnterpriseDB CDN HTTP 403; Docker not installed).
- Testcontainers / Docker Compose integration tests.
- Alembic migrations against a live internal database.
