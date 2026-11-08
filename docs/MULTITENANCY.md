# Multi-tenancy — QueryMind MCP

## Principle

Every organization-owned resource carries an `organization_id`. Tenant
isolation is enforced so a user from Organization A can never retrieve
Organization B's database connections, schema metadata, embeddings, query
history, reports, anomaly events, or audit records.

## Scoped resources

| Resource | Organization-scoped |
|----------|---------------------|
| Users | Yes |
| Database connections | Yes |
| Schema snapshots | Yes |
| Embeddings / RAG documents | Yes |
| Query history | Yes |
| Performance reports | Yes |
| Anomaly events | Yes |
| Audit records | Yes (tenant context preserved) |

## Enforcement

`TenantScope` (in `src/querymind/core/multitenancy.py`) validates that a
principal may only access resources within their own organization, unless
they are a `platform_admin` (who may access any org).

- `may_access(org_id)` — boolean check.
- `require_same_organization(org_id)` — raises `TenantIsolationError` on
  cross-tenant access.
- `filter_by_organization(items)` — returns only items in the principal's
  org (all items for platform admins).
- `assert_owned(resource)` — asserts the principal owns a resource.

## Defense in depth

Application-level authorization is mandatory. PostgreSQL Row-Level Security
is applied on the internal database where appropriate as an additional
defence-in-depth layer, but it never replaces application authorization.

## Testing

Cross-tenant access is explicitly tested in
`tests/security/test_multitenancy.py` (same-org allowed, cross-org blocked,
platform-admin bypass, filter_by_organization).
