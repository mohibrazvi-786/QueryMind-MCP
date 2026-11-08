# Implementation Plan — QueryMind MCP

## Roadmap status

| Stage | Focus | Status |
|-------|-------|--------|
| 0 | Repository audit | Complete |
| 1 | Architecture planning | Complete |
| 2 | Foundation | Complete |
| 3 | Discovery | Complete (offline-validated; live PG blocked) |
| 4 | MCP | Complete (19 tools / 6 resources / 6 prompts registered + tested) |
| 5 | RAG + SQL intelligence | Complete |
| 6 | Performance engineering | Complete |
| 7 | Machine learning | Complete |
| 8 | Production security | Complete (auth, RBAC, multitenancy, audit, secrets, rate limiting; +14 security tests) |
| 9 | Frontend | Source authored (Next.js); build unverified (network blocked) |
| 10 | Quality engineering | Complete (113 tests pass; integration blocked) |
| 11 | Deployment readiness | Authored (Dockerfile, compose, CI workflow); not executed |

## Stage 8 — Production security (complete)

New modules:
- `src/querymind/core/auth.py` — register/login/logout/refresh, bcrypt
  password hashing, JWT access/refresh tokens with rotation, session
  invalidation, `resolve_principal()`.
- `src/querymind/core/rbac.py` — 5 roles, centralized permission model,
  `PermissionChecker`, `principal_from_claims`.
- `src/querymind/core/multitenancy.py` — `TenantScope` for org isolation.
- `src/querymind/core/audit.py` — append-only, redacted audit logger.
- `src/querymind/core/secrets.py` — Fernet-encrypted credentials at rest,
  key rotation.
- `src/querymind/core/rate_limit.py` — sliding-window rate limiter.
- `src/querymind/mcp/authz.py` — MCP authorization (permission + tenant scope).
- `src/querymind/api/` — FastAPI auth routes + auth dependencies.
- `src/querymind/core/exceptions.py` — added `AuthenticationError`.

MCP tools enforce auth + permission + tenant scope. 15 security tests added.

## Stage 9 — Frontend (source authored)

Next.js 15 + React 19 + TypeScript + Tailwind dashboard under `frontend/`
with Overview, Connections, AI Assistant, SQL Workspace, Schema Explorer,
Performance, Anomaly Monitor, Audit Logs, Organization pages. Build/lint
unverified (npm tarball download blocked by network).

## Stage 11 — Deployment readiness (authored)

- `Dockerfile` (multi-stage, non-root user, health check)
- `docker-compose.yml` (backend + internal + target PG + dashboard; secrets;
  target DB bound to localhost only)
- `.github/workflows/ci.yml` (format, lint, type, unit, security, build,
  frontend, docker build)

## Environment constraints

No live PostgreSQL server or Docker in this session. npm tarball downloads
are blocked. Live-PG-dependent verification is BLOCKED — see
`docs/POSTGRESQL_INTEGRATION_CHECKLIST.md`.

## Next milestone

Provision a PostgreSQL 17+ target database, run Stage 10 integration tests,
execute Docker/CI, and complete live enforcement of auth/RBAC.
