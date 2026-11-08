# Security Model — QueryMind MCP

Security is a core feature, implemented at multiple independent layers.

## Target database access
- Default: **read-only** via a least-privilege target database role.
- SELECT-only, single-statement enforcement.
- Statement timeouts and result row limits.
- Query concurrency / connection pool limits.

## SQL validation pipeline
LLM-generated SQL → SQLGlot parse → AST validation → statement-type check →
schema/table allowlist → policy engine → read-only role → timeout → result
limit → controlled execution → audit log. Parsing alone is not the boundary;
database-level permissions enforce independently.

## Connection security
- Host/network allowlists; localhost/dev-only by default.
- Cloud metadata IP (`169.254.169.254`) and private ranges blocked (SSRF protection).
- Credentials never logged or returned; connection strings redacted.
- No arbitrary database host connections from AI agents.

## Authentication / authorization / tenant isolation
- Organization-level, connection-level, and database-level permissions.
- Every request establishes the authenticated organization and permitted connection.
- Cross-tenant access blocked (100% target in tests).
- Row-Level Security as defence in depth for the internal database.

## RAG security
- Retrieved schema comments, descriptions, and metadata treated as untrusted.
- Prompt injection: database content never overrides system policies.

## Audit logging
Records user, organization, connection, tool, operation, SQL hash/query,
status, timestamp, duration, and rejection reason. Sensitive data redacted;
configurable retention.

## Write-operation policy (v1)
No arbitrary writes or DDL/DML by the LLM. Index management (future) requires
human approval through a separate privileged workflow.

## Status

Credential redaction, host allowlisting, and SQL rejection are unit-tested.
AuthN/AuthZ/RBAC and full audit logging are architected; live enforcement
against a real PostgreSQL target requires provisioning.
