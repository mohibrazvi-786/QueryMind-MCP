# Architecture — QueryMind MCP

## System overview

QueryMind MCP is a modular monolith. The MCP server is a thin interface layer; business logic, security policy, and database operations live in deterministic Python services. The LLM provides intelligence; it never independently controls database permissions or executes unrestricted SQL.

## Architectural layers

```
MCP Client (Claude Desktop / Inspector / custom agent)
        ↓  (STDIO or Streamable HTTP)
MCP Interface (FastMCP)  →  tools, resources, prompts; input validation only
        ↓
Security & Policy Engine (auth, RBAC, org isolation, SQL validation, allowlists, audit)
        ↓
Intelligence Engine (NL→SQL, schema RAG, plan analysis, index advisor, anomaly detection)
        ↓
Database Services (connection management, discovery, schema extraction, query execution, health)
        ↓
Target PostgreSQL (inspected database)   |   Internal PostgreSQL (app records)
```

### Layer responsibilities

| Layer | Responsibility | Depends on LLM? |
|-------|----------------|-----------------|
| 1 AI Client | MCP-compatible client sessions | No |
| 2 MCP Interface | Tools/resources/prompts, validation, structured responses | No |
| 3 Security & Policy | AuthN/AuthZ, RBAC, org isolation, SQL allowlists, audit logging | No |
| 4 Intelligence Engine | NL→SQL, schema RAG, plan/index analysis, anomaly detection | Yes (bounded) |
| 5 Database Services | PG connections, discovery, schema, execution, health monitoring | No |
| 6 Observability | Structured logs, metrics, traces, query history, security events | No |

## Architectural rules

1. MCP server is an interface, not the business logic layer.
2. Database services must not depend on an LLM provider.
3. AI providers must be replaceable via a provider interface + deterministic mock.
4. Security validation operates independently of AI-generated decisions.
5. All database operations pass through controlled services.
6. Internal application database remains separate from target databases.

## Technology stack (baseline, pinned at implementation)

| Component | Technology |
|-----------|------------|
| Language | Python 3.12+ (env: 3.13) |
| MCP framework | FastMCP |
| Backend API | FastAPI |
| Target DB | PostgreSQL 17+ |
| ORM | SQLAlchemy 2.x |
| Migrations | Alembic |
| SQL parser | SQLGlot |
| Validation | Pydantic v2 |
| Password hashing | bcrypt |
| Tokens | PyJWT (HS256) |
| Encryption at rest | cryptography (Fernet) |
| AI integration | Provider-independent LLM adapter |
| Embeddings | Sentence Transformers (optional, where justified) |
| Vector storage | pgvector only if evaluation proves advantage |
| Testing | Pytest + Testcontainers |
| Logging | Structlog |
| Observability | OpenTelemetry + Prometheus |
| Containers | Docker |
| CI/CD | GitHub Actions |

## Security architecture (Stage 8)

- **Authentication**: register/login/logout/refresh, bcrypt password hashing,
  JWT access + refresh tokens with rotation, session invalidation.
- **Authorization/RBAC**: 5 roles (platform_admin, org_admin,
  database_analyst, viewer, service_account), centralized permission model in
  `src/querymind/core/rbac.py`, enforced at the service boundary for both MCP
  tools and FastAPI routes.
- **Multi-tenancy**: organization-scoped connections, schema snapshots,
  embeddings, query history, reports, anomaly events, audit records;
  cross-tenant access blocked.
- **Audit logging**: append-only, redacted (no passwords/tokens/keys), tenant
  context preserved.
- **Secrets management**: Fernet-encrypted credentials at rest, configurable
  key, key rotation support.
- **Rate limiting**: sliding window, configurable requests/window.
- **SQL validation**: SQLGlot AST, SELECT-only, single-statement,
  allowlists, disallowed functions, statement timeouts, result limits.

## MCP surface

- **19 tools** across discovery (6), query intelligence (5), optimization (4),
  monitoring (2), documentation (2).
- **6 resources:** `querymind://database/{schema,tables,relationships,health,documentation,metrics}`
- **6 prompts:** `database_health_audit`, `sql_query_optimization`,
  `database_schema_explanation`, `database_security_review`,
  `slow_query_investigation`, `database_performance_report`
- **Transports:** STDIO and Streamable HTTP.

All tools enforce authentication (when a token is presented), the relevant
permission, and organization scope.

## Database architecture

Two separate environments:

- **Target database** — the PostgreSQL being inspected (read-only access for QueryMind).
- **Internal database** — QueryMind's own PostgreSQL storing users, orgs, connections, schema snapshots, query history, analyses, health snapshots, anomaly events, audit logs.

Never mix application records with target database records.

## Security boundaries (non-negotiable)

- SELECT-only policy; single statement; restricted functions; max result rows; statement timeouts.
- SQLGlot AST validation + database-level least-privilege role (defence in depth).
- Host/network allowlists; no SSRF; no cloud-metadata access; no public PG ports.
- Credentials never in plaintext; environment variables or secret manager only.
- Prompt injection: database content treated as untrusted.
- Audit logging of every tool invocation with redaction and retention.

## MCP surface

- **19 tools** across discovery (6), query intelligence (5), optimization (4), monitoring (2), documentation (2).
- **6 resources:** `querymind://database/{schema,tables,relationships,health,documentation,metrics}`
- **6 prompts:** `database_health_audit`, `sql_query_optimization`, `database_schema_explanation`, `database_security_review`, `slow_query_investigation`, `database_performance_report`
- **Transports:** STDIO and Streamable HTTP.

## Decision log

| Decision | Rationale |
|----------|-----------|
| Modular monolith | Avoids unnecessary microservice complexity; layers stay logically separated |
| FastMCP | Current supported MCP framework; matches mandated stack |
| SQLAlchemy + pg catalogues | Discovery must not hardcode table names; works across PG databases |
| SQLGlot AST validation | Keyword matching alone is insufficient for SQL security |
| Deterministic mock LLM provider | Tests must be reproducible without external LLM calls |
| pgvector deferred | Start with deterministic + keyword schema retrieval; add semantic only if evaluation proves advantage |

## Out of scope (v1)

- Arbitrary DDL/DML execution by the LLM
- Automatic `EXPLAIN ANALYZE` against unrestricted production targets
- Automatic index creation without human approval
- pgvector (unless evaluation justifies it)
