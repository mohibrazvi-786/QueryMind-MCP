# Database Design — QueryMind MCP

## Principle

Two physically/logically separate PostgreSQL databases:

1. **Target database** — inspected e-commerce / customer PostgreSQL (read-only).
2. **Internal database** — QueryMind application records only.

Never mix application records with target database records.

## Internal database entities (core)

| Table | Purpose |
|-------|---------|
| users | User accounts |
| organizations | Multi-tenant organizations |
| organization_members | Membership + roles (RBAC) |
| database_connections | Secure connection profiles (encrypted credentials) |
| schema_snapshots | Versioned schema metadata per connection |
| table_metadata | Table and column information |
| query_history | Query execution history |
| query_analyses | Execution plans and recommendations |
| index_recommendations | Index suggestions |
| health_snapshots | Database monitoring history |
| anomaly_events | Detected anomalies |
| audit_logs | Security and operational audit trail |
| schema_embeddings | Optional semantic schema retrieval |

Additional (later): database permissions, saved queries, generated reports, agent sessions, usage records.

## Design requirements

- UUID primary keys
- UTC timestamps (`created_at`, `updated_at`)
- Foreign key constraints
- Proper indexes on FKs and query-filtered columns
- Transaction management
- Alembic migrations
- Organization-level isolation (every app row belongs to an org)
- PostgreSQL Row-Level Security as defence in depth
- Configurable retention policies
- Versioned schema snapshots
- Encrypted credentials; never plaintext passwords

## Target database access

QueryMind connects to target databases via registered `database_connections` profiles. It reads only through a least-privilege target role. No target data is persisted in the internal database except metadata snapshots (schema, plans, metrics) — never unrestricted customer records.

## Notes

- Internal DB migrations managed by Alembic under `alembic/`.
- Target database schema is discovered dynamically; not modeled in Alembic.
