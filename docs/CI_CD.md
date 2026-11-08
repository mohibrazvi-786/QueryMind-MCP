# CI/CD — QueryMind MCP

## Pipeline

`.github/workflows/ci.yml` runs on push/PR to `main`:

1. Checkout repository
2. Set up Python 3.13 + PostgreSQL 17 service container
3. Install dependencies (`-e ".[test,dev]"`)
4. Formatting check (`ruff format --check`)
5. Linting (`ruff check`)
6. Type checking (`mypy`)
7. Backend unit tests (`tests/unit`, `tests/security`, `tests/mcp`,
   `tests/evaluation`)
8. Security tests (`tests/security`)
9. Build verification (sdist + wheel)
10. Frontend install, lint, type check, tests (if `frontend/` exists)
11. Docker backend image build (no push)

## Secrets

No secrets stored in workflow source files. Workflow uses
`contents: read` least-privilege permission.

## Status

CI is authored but not executed (no GitHub push authorized, no runner
available in this environment).
