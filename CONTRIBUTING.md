# Contributing — QueryMind MCP

## Guidelines

- Preserve the layered architecture: MCP is an interface; business logic in services.
- Never allow the LLM to independently control database permissions or execute unrestricted SQL.
- All database operations pass through controlled, read-only services.
- Do not hardcode schemas, table names, or column names.
- Do not fabricate schema, statistics, or evaluation results.
- No secrets or credentials in source code.

## Submitting changes

1. Inspect the existing repository and architecture documents first.
2. Implement the smallest complete change that satisfies the requirement.
3. Add or update unit tests for any new logic.
4. Run `pytest tests/ -q` and ensure existing tests still pass.
5. Update documentation for any user-facing behavior.

## Testing

Tests must be deterministic and not require external services (LLM, live
PostgreSQL) unless explicitly marked as integration/blocked.
