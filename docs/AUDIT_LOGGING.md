# Audit Logging — QueryMind MCP

## Overview

QueryMind maintains append-only audit records for security and operational
events. Audit records are immutable once written and are protected from
ordinary user modification.

## Logged events

- Authentication events (login, logout, refresh, token validation failures)
- Authorization failures (permission denied, role escalation attempts)
- User and organization administration
- Database connection creation and changes
- Schema discovery
- SQL generation
- SQL validation
- Read-only query execution
- Performance analysis
- Index recommendations
- Anomaly detection
- Security configuration changes

## Audit record fields

| Field | Description |
|-------|-------------|
| `event_id` | Unique identifier |
| `timestamp` | UTC ISO-8601 |
| `actor_user_id` | Acting user (if authenticated) |
| `actor_username` | Acting username |
| `organization_id` | Tenant context |
| `action` | Action performed |
| `resource_type` | Type of resource |
| `resource_id` | Resource identifier |
| `outcome` | `success`, `failure`, `denied`, or `error` |
| `correlation_id` | Request correlation ID |
| `metadata` | Safe metadata (sensitive values redacted) |

## Redaction

The following are never logged: passwords, tokens, API keys, raw
credentials, sensitive SQL parameter values. Metadata keys matching
`password`, `secret`, `api_key`, `token`, `credential`, `private_key`,
`connection_string`, `dsn` are redacted to `***`.

## Implementation

`AuditLogger` (in `src/querymind/core/audit.py`) writes structured audit
records as JSON log entries and keeps them in memory for querying.
Production deployments should forward these records to an immutable audit
store (write-once table or SIEM).

## Testing

Audit append-only behavior, sensitive-key redaction, listing/filtering by
organization/action/outcome are covered in `tests/security/test_audit.py`.
