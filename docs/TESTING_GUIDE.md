# Testing Guide — QueryMind MCP

## Test layers

| Layer | Location | Focus |
|-------|----------|-------|
| Unit | `tests/unit/` | SQL validation, plan analysis, inefficiencies, index advisor, anomaly detection, retrieval, embeddings, RAG, SQL generation |
| MCP | `tests/mcp/` | Tool/resource/prompt registration (19/6/6) |
| Security | `tests/security/` | Unsafe SQL rejection, credential redaction, host allowlisting |
| Evaluation | `tests/evaluation/` | Synthetic anomaly precision/recall/F1 |
| Integration | `tests/integration/` | Blocked without a live PostgreSQL |

## Running tests

```powershell
.venv\Scripts\python.exe -m pytest tests/ -q
```

## Test results (this session)

- **68 passed**, 0 failed, 0 skipped.
- Live-PostgreSQL-dependent tests are classified as **BLOCKED** (no server
  available in this environment) — see `docs/POSTGRESQL_INTEGRATION_CHECKLIST.md`.
- External LLM services are mocked; all tests are deterministic.

## Coverage areas

- SQLGlot AST parsing of all discovery + validation SQL (PostgreSQL dialect).
- Catalogue assembly from synthetic rows.
- MCP tool/resource/prompt registration counts.
- Every inefficiency rule (QI-001 … QI-008).
- Index advisor single-column, composite, overlap-skip.
- Statistical baseline (insufficient data, Z-score, normal vs anomaly).
- Isolation Forest training + inference (scikit-learn).
- Embedding determinism, batch, cosine similarity, hybrid retrieval.
- RAG ingestion + search.
- NL-to-SQL generation + validation of mock output.

## Lint / type check

`ruff` and `mypy` are listed as dev dependencies but not installed in this
environment. Install and run:

```powershell
.venv\Scripts\python.exe -m pip install ruff mypy
.venv\Scripts\ruff check src tests
.venv\Scripts\mypy src
```

## Blocked tests

Any test requiring a live PostgreSQL connection, `pg_stat_statements`,
`EXPLAIN ANALYZE`, or pgvector is marked BLOCKED, not PASSED.
