# Docker — QueryMind MCP

## Images

- `Dockerfile`: multi-stage build for the QueryMind backend. Installs
  dependencies in a builder stage, runs as a non-root `querymind` user in the
  runtime stage. Pinned Python 3.13. Health check included.

## Docker Compose

`docker-compose.yml` defines:
- `querymind-db`: internal PostgreSQL 17 for application records (not
  exposed publicly).
- `querymind-target`: target PostgreSQL 17 for discovery (bound to
  `127.0.0.1:5432` only — never public).
- `querymind-backend`: QueryMind MCP backend.
- `querymind-dashboard`: Next.js dashboard.

## Security

- Secrets mounted as Docker secrets (not in images or environment where
  avoidable).
- Internal and target databases not exposed publicly.
- Non-root runtime user.
- Health checks on all services.

## Local development

```bash
docker compose up
```

The backend listens on `127.0.0.1:8000`; the dashboard on `127.0.0.1:3000`.

## Status

Docker is not installed in this environment, so images cannot be built or
verified here. Dockerfile and Compose are authored but untested.
