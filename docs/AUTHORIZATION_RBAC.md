# Authorization & RBAC — QueryMind MCP

## Model

Authorization is centralized in `src/querymind/core/rbac.py`. Every protected
operation checks the caller's permissions through `PermissionChecker`.
Permission logic lives in one place — it is not duplicated across
controllers or dashboard components.

## Roles

| Role | Summary |
|------|---------|
| `platform_admin` | All permissions. Manage users, organizations, platform config. |
| `org_admin` | Nearly all permissions scoped to their organization. Manage members, roles, connections, reports. |
| `database_analyst` | Discover metadata, generate/validate/execute read-only SQL, analyze performance, view reports. |
| `viewer` | Read-only: discover metadata, view docs/health/reports. Cannot execute queries or modify config. |
| `service_account` | Machine-to-machine MCP access with explicitly scoped permissions; revocable. |

## Permissions

Granular permissions include:
- `db:discover`, `db:table:read`, `db:table:describe`,
  `db:relationships:read`, `db:stats:read`
- `sql:generate`, `sql:validate`, `sql:explain`,
  `sql:execute:readonly`
- `index:recommend`, `slow_query:read`, `query:compare`,
  `query:inefficiency:detect`
- `health:read`, `anomaly:detect`
- `documentation:generate`, `knowledge:search`
- `connection:manage`, `org:manage`, `user:manage`, `audit:read`,
  `config:manage`

## Enforcement

- Every protected MCP tool enforces the relevant permission + organization
  scope via `src/querymind/mcp/authz.py`.
- FastAPI HTTP routes enforce permissions via dependencies in
  `src/querymind/api/dependencies.py` (`require_permissions`,
  `require_any_permission`).
- A principal is built from JWT claims via `principal_from_claims`;
  permissions are derived from role.

## Cross-tenant

Authorization is applied before retrieval and again before data exposure.
Organization-scoped resources require the principal to belong to the same
organization (unless platform admin). See `docs/MULTITENANCY.md`.

## Testing

Unauthenticated access, invalid/expired/revoked tokens, role escalation,
organization boundary violations, and unauthorized MCP tool/resource calls
are covered in `tests/security/`.
