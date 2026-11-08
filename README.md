# QueryMind MCP

**Understand your database. Query intelligently. Optimize confidently.**

AI-powered database intelligence, RAG & optimization platform built on the
Model Context Protocol (MCP). QueryMind lets backend developers, DBAs, and
data engineers interact with PostgreSQL using natural language, with
deterministic Python services enforcing security and business logic — the LLM
never independently controls database permissions or executes unrestricted SQL.

## Status

Stages 0–8 implemented. All service logic, MCP registration, validation,
retrieval, optimization, anomaly detection, authentication, RBAC,
multi-tenancy, audit logging, secrets management, and rate limiting are
unit-tested (**113 passing, 0 failed**).

Live execution against a real PostgreSQL instance is **BLOCKED** in this
environment (no PostgreSQL server available; see
`docs/POSTGRESQL_INTEGRATION_CHECKLIST.md`).

## Problem statement

Working with production databases requires deep SQL and performance expertise.
QueryMind bridges natural language and database intelligence: schema
discovery, NL-to-SQL with AST validation, execution-plan analysis, index
recommendations, health monitoring, and ML-based anomaly detection — all with
evidence-backed recommendations and strict read-only security.

## Key capabilities

- **Database discovery** — schemas, tables, columns, keys, indexes, statistics
  from PostgreSQL system catalogues (no hardcoded table names).
- **MCP server** — 19 tools, 6 resources, 6 prompts; STDIO + Streamable HTTP.
- **Schema RAG** — hybrid keyword + semantic retrieval of relevant schema only.
- **Natural-language-to-SQL** — provider-independent LLM, SQLGlot AST
  validation, read-only execution.
- **Performance intelligence** — EXPLAIN plan analysis, inefficiency rules,
  index advisor, slow-query ranking, structured reports.
- **Anomaly detection** — statistical baselines (Z-score, EWMA) + Isolation
  Forest.
- **Security (Stage 8)** — bcrypt password hashing, JWT access/refresh tokens
  with refresh rotation, 5-role RBAC, organization multi-tenancy, append-only
  audit logging, Fernet-encrypted credentials at rest, sliding-window rate
  limiting.

## MCP connection instructions

QueryMind exposes an MCP server. Connect any MCP-compatible client
(Claude Desktop, MCP Inspector, custom agent):

- **STDIO** (local): `python -m querymind.mcp.transports` (stdio mode).
- **Streamable HTTP** (remote): run the backend over streamable-http behind a
  reverse proxy + TLS.

Authenticate via the FastAPI `/auth/*` endpoints (`/auth/login`,
`/auth/register`, `/auth/refresh`) and pass the access token as a Bearer
token to MCP tools that require authorization.

## Architecture

Modular monolith:

```
MCP Client --> FastMCP (tools/resources/prompts) -->
Security & Policy (auth/RBAC/tenant/audit) -->
Intelligence Engine (RAG, NL-to-SQL, plans, anomaly) -->
Database Services --> Target PostgreSQL
                                    |--> Internal PostgreSQL (app records)
```

The MCP server is an interface layer; business logic lives in services.

## Technology stack

| Component | Technology | Version |
|-----------|------------|---------|
| Language | Python | 3.13 |
| MCP framework | FastMCP | 4.1.6 |
| Backend API | FastAPI | 0.162.2 |
| Target DB | PostgreSQL | 17+ |
| ORM | SQLAlchemy | 2.1.8 |
| Migrations | Alembic | 1.20.1 |
| SQL parser | SQLGlot | 30.30.0 |
| Validation | Pydantic | 2.14.3 |
| Password hashing | bcrypt | 5.0.0 |
| Tokens | PyJWT | 2.15.1 |
| Encryption | cryptography (Fernet) | 50.0.2 |
| Logging | Structlog | 26.1.0 |
| Testing | Pytest | 9.2.0 |
| ML | scikit-learn | 1.9.1 |
| Dashboard | Next.js / React / TypeScript | 15 / 19 |

See `pyproject.toml` for pinned versions.

## MCP explanation

QueryMind exposes 19 MCP tools (discovery, SQL intelligence, optimization,
monitoring, documentation), 6 resources (`querymind://database/{schema,
tables, relationships, health, documentation, metrics}`), and 6 prompts.
See `docs/MCP_REFERENCE.md`.

## RAG explanation

Schema metadata is discovered, normalized into traceable documents, embedded,
and retrieved via hybrid keyword + semantic search. Only relevant schema
context reaches the LLM. See `docs/RAG_PIPELINE.md`.

## Database discovery workflow

1. Register a connection (`connect_database`).
2. Discover schema (`discover_all` / `querymind://database/schema`).
3. Inspect tables, columns, keys, indexes, relationships, stats.

## SQL security pipeline

Generated SQL → SQLGlot AST parse → single-statement check → SELECT-only →
schema/table allowlist → disallowed functions → read-only role → timeout →
row limit → controlled execution → audit log.

## Roles and permissions

| Role | Can execute queries? | Can manage connections? | Can manage users/orgs? |
|------|----------------------|-------------------------|------------------------|
| Platform Administrator | Yes | Yes | Yes |
| Organization Administrator | Yes | Yes | Yes (own org) |
| Database Analyst | Yes (read-only) | Yes (own org) | No |
| Read-only Viewer | No | No | No |
| Service Account | Yes (read-only, scoped) | No | No |

See `docs/AUTHORIZATION_RBAC.md`.

## Installation

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .
```

A real PostgreSQL instance is required for live discovery/execution.

## Docker

`Dockerfile` and `docker-compose.yml` are authored (Stage 11) but cannot be
built/verified in this environment (Docker not installed). See `docs/DOCKER.md`.

## Example MCP interactions

See `docs/MCP_REFERENCE.md` for the full tool/resource/prompt catalogue.

## API documentation

FastAPI auth routes under `src/querymind/api/routes/`. MCP server is the
primary interface (`src/querymind/mcp/server.py`).

## Evaluation methodology

Deterministic synthetic workloads; mock LLM and embedding providers for
repeatable tests. Precision/recall/F1 recorded for anomaly detection.
See `docs/TESTING_GUIDE.md` and `tests/evaluation/`.

## Actual benchmark results

None claimed against a live database (no PostgreSQL available). All results
are from offline unit tests with synthetic data.

## Limitations

- No live PostgreSQL server in this environment (discovery/execution not
  live-verified).
- No Docker; Testcontainers integration tests not runnable locally.
- Mock LLM/embedding providers (no real AI provider configured).
- AuthN/AuthZ/RBAC implemented; live enforcement needs a provisioned target.
- Dashboard source authored; build unverified (npm download blocked).

## Future improvements

- Live PostgreSQL integration (provision a target DB per
  `docs/POSTGRESQL_INTEGRATION_CHECKLIST.md`).
- Docker / Compose, GitHub Actions CI execution.
- Real LLM/embedding provider integration; pgvector evaluation.
- Full AuthN/AuthZ/RBAC + audit logging live enforcement.
- Dashboard build and end-to-end verification.
