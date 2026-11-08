# Deployment — QueryMind MCP

## Principle

Do not deploy to any external service. Do not publish a Docker image. Do not
push to GitHub. Deployment requires separate explicit authorization.

## Environments

- **Development**: local, stdio transport, mock LLM provider, reload enabled.
- **Test**: isolated CI database, security + unit suites.
- **Production**: Streamable HTTP behind reverse proxy + TLS, least-privilege
  target DB role, secrets via secret manager, rate limits applied.

## Configuration

Configuration is environment-variable based (`pydantic-settings`). See
`.env.example` for the full variable reference. Never commit `.env` or real
secrets.

## Database migration instructions

The internal QueryMind database uses Alembic migrations under `alembic/`.
Run `alembic upgrade head` against the internal database before starting the
backend in production. Target database schema is discovered dynamically and
is not managed by Alembic.

## Backup and recovery

- Back up the internal QueryMind database (users, orgs, audit logs,
  schema snapshots) regularly.
- Target databases are backed up by their owners; QueryMind only reads
  metadata and plans.
- Audit records are append-only; preserve them per retention policy.

## Secret management

- Database credentials encrypted at rest (Fernet) via `ENCRYPTION_KEY`.
- Rotate keys by re-encrypting existing secrets with the new key.
- Inject secrets via environment variables or a secret manager; never bake
  into images.

## Monitoring

Health and readiness endpoints are exposed by the backend. Structured JSON
logging and metrics are emitted. See `docs/OBSERVABILITY.md`.

## Rollback procedure

1. Roll back the backend image to the previous version.
2. Run `alembic downgrade` only if a migration is known-safe to reverse;
   otherwise forward-fix.
3. Restore the internal database from the most recent backup if data is
   corrupted.

## Deployment readiness checklist

- [ ] PostgreSQL 17+ target provisioned (read-only role)
- [ ] Internal QueryMind database provisioned + migrations applied
- [ ] `JWT_SECRET_KEY`, `ENCRYPTION_KEY`, `SECRET_KEY` set (not defaults)
- [ ] HTTPS reverse proxy + TLS configured
- [ ] Target database ports not exposed publicly
- [ ] Rate limits configured
- [ ] Audit log destination configured
- [ ] Health/readiness endpoints verified
