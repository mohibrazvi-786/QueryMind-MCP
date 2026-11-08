# Production Readiness — QueryMind MCP

## Implemented and tested (offline)

- Database discovery engine (SQL validated via SQLGlot; assembly unit-tested)
- MCP server: 19 tools, 6 resources, 6 prompts registered and tested
- Authentication: bcrypt password hashing, JWT access/refresh tokens,
  refresh rotation, session invalidation
- RBAC: 5 roles, centralized permission model
- Multi-tenancy: organization scoping with cross-tenant blocking
- Audit logging: append-only, redacted, tenant-contextual
- Secrets management: Fernet encryption at rest, key rotation
- Rate limiting: sliding window, configurable
- SQL security: SELECT-only, single-statement, AST validation, allowlists
- RAG + NL-to-SQL: hybrid retrieval, mock providers, deterministic tests
- Performance: EXPLAIN analysis, 8 inefficiency rules, index advisor
- Anomaly detection: Z-score/EWMA baselines + Isolation Forest

## Blocked (no live PostgreSQL / network)

- Live PostgreSQL integration (discovery, execution, EXPLAIN, pg_stat_statements)
- Internal database migrations against a live server
- Testcontainers / Docker Compose execution
- Docker image build
- Frontend build/lint (npm tarball download blocked)
- End-to-end MCP against a real database

## Production readiness checklist

- [ ] Target PostgreSQL 17+ provisioned (read-only role)
- [ ] Internal QueryMind database provisioned + Alembic migrations applied
- [ ] Secrets not defaults; key rotation procedure in place
- [ ] HTTPS + TLS reverse proxy
- [ ] Target DB ports not public
- [ ] Rate limits configured
- [ ] Audit log destination (immutable store) configured
- [ ] Health/readiness endpoints verified
- [ ] CI pipeline passing

## Known limitations

- AuthN/AuthZ/RBAC implemented but live enforcement needs a provisioned target.
- Dashboard unverified (build blocked by network).
- No real LLM/embedding provider configured (mock used).
