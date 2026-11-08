"""Role-based access control.

Centralized permission model. Roles map to sets of permissions; every
protected operation checks the caller's permissions through
PermissionChecker. Permission logic lives here, not in controllers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from querymind.core.exceptions import UnauthorizedError


# Granular permissions.
PERMISSION_DB_DISCOVER = "db:discover"
PERMISSION_TABLE_READ = "db:table:read"
PERMISSION_TABLE_DESCRIBE = "db:table:describe"
PERMISSION_RELATIONSHIPS_READ = "db:relationships:read"
PERMISSION_DATABASE_STATS_READ = "db:stats:read"

PERMISSION_SQL_GENERATE = "sql:generate"
PERMISSION_SQL_VALIDATE = "sql:validate"
PERMISSION_SQL_EXPLAIN = "sql:explain"
PERMISSION_SQL_EXECUTE_READONLY = "sql:execute:readonly"

PERMISSION_INDEX_RECOMMEND = "index:recommend"
PERMISSION_SLOW_QUERIES_READ = "slow_query:read"
PERMISSION_QUERY_COMPARE = "query:compare"
PERMISSION_INEFFICIENCY_DETECT = "query:inefficiency:detect"

PERMISSION_HEALTH_READ = "health:read"
PERMISSION_ANOMALY_DETECT = "anomaly:detect"

PERMISSION_DOCUMENTATION_GENERATE = "documentation:generate"
PERMISSION_KNOWLEDGE_SEARCH = "knowledge:search"

PERMISSION_CONNECTION_MANAGE = "connection:manage"
PERMISSION_ORG_MANAGE = "org:manage"
PERMISSION_USER_MANAGE = "user:manage"
PERMISSION_AUDIT_READ = "audit:read"
PERMISSION_CONFIG_MANAGE = "config:manage"

ALL_PERMISSIONS = {
    PERMISSION_DB_DISCOVER,
    PERMISSION_TABLE_READ,
    PERMISSION_TABLE_DESCRIBE,
    PERMISSION_RELATIONSHIPS_READ,
    PERMISSION_DATABASE_STATS_READ,
    PERMISSION_SQL_GENERATE,
    PERMISSION_SQL_VALIDATE,
    PERMISSION_SQL_EXPLAIN,
    PERMISSION_SQL_EXECUTE_READONLY,
    PERMISSION_INDEX_RECOMMEND,
    PERMISSION_SLOW_QUERIES_READ,
    PERMISSION_QUERY_COMPARE,
    PERMISSION_INEFFICIENCY_DETECT,
    PERMISSION_HEALTH_READ,
    PERMISSION_ANOMALY_DETECT,
    PERMISSION_DOCUMENTATION_GENERATE,
    PERMISSION_KNOWLEDGE_SEARCH,
    PERMISSION_CONNECTION_MANAGE,
    PERMISSION_ORG_MANAGE,
    PERMISSION_USER_MANAGE,
    PERMISSION_AUDIT_READ,
    PERMISSION_CONFIG_MANAGE,
}

# Role -> permissions.
ROLE_PERMISSIONS: dict[str, set[str]] = {
    "platform_admin": set(ALL_PERMISSIONS),
    "org_admin": {
        PERMISSION_DB_DISCOVER,
        PERMISSION_TABLE_READ,
        PERMISSION_TABLE_DESCRIBE,
        PERMISSION_RELATIONSHIPS_READ,
        PERMISSION_DATABASE_STATS_READ,
        PERMISSION_SQL_GENERATE,
        PERMISSION_SQL_VALIDATE,
        PERMISSION_SQL_EXPLAIN,
        PERMISSION_SQL_EXECUTE_READONLY,
        PERMISSION_INDEX_RECOMMEND,
        PERMISSION_SLOW_QUERIES_READ,
        PERMISSION_QUERY_COMPARE,
        PERMISSION_INEFFICIENCY_DETECT,
        PERMISSION_HEALTH_READ,
        PERMISSION_ANOMALY_DETECT,
        PERMISSION_DOCUMENTATION_GENERATE,
        PERMISSION_KNOWLEDGE_SEARCH,
        PERMISSION_CONNECTION_MANAGE,
        PERMISSION_ORG_MANAGE,
        PERMISSION_USER_MANAGE,
        PERMISSION_AUDIT_READ,
        PERMISSION_CONFIG_MANAGE,
    },
    "database_analyst": {
        PERMISSION_DB_DISCOVER,
        PERMISSION_TABLE_READ,
        PERMISSION_TABLE_DESCRIBE,
        PERMISSION_RELATIONSHIPS_READ,
        PERMISSION_DATABASE_STATS_READ,
        PERMISSION_SQL_GENERATE,
        PERMISSION_SQL_VALIDATE,
        PERMISSION_SQL_EXPLAIN,
        PERMISSION_SQL_EXECUTE_READONLY,
        PERMISSION_INDEX_RECOMMEND,
        PERMISSION_SLOW_QUERIES_READ,
        PERMISSION_QUERY_COMPARE,
        PERMISSION_INEFFICIENCY_DETECT,
        PERMISSION_HEALTH_READ,
        PERMISSION_ANOMALY_DETECT,
        PERMISSION_DOCUMENTATION_GENERATE,
        PERMISSION_KNOWLEDGE_SEARCH,
    },
    "viewer": {
        PERMISSION_DB_DISCOVER,
        PERMISSION_TABLE_READ,
        PERMISSION_TABLE_DESCRIBE,
        PERMISSION_RELATIONSHIPS_READ,
        PERMISSION_DATABASE_STATS_READ,
        PERMISSION_HEALTH_READ,
        PERMISSION_DOCUMENTATION_GENERATE,
        PERMISSION_KNOWLEDGE_SEARCH,
    },
    "service_account": {
        PERMISSION_DB_DISCOVER,
        PERMISSION_TABLE_READ,
        PERMISSION_TABLE_DESCRIBE,
        PERMISSION_RELATIONSHIPS_READ,
        PERMISSION_DATABASE_STATS_READ,
        PERMISSION_SQL_GENERATE,
        PERMISSION_SQL_VALIDATE,
        PERMISSION_SQL_EXPLAIN,
        PERMISSION_SQL_EXECUTE_READONLY,
        PERMISSION_HEALTH_READ,
        PERMISSION_ANOMALY_DETECT,
        PERMISSION_DOCUMENTATION_GENERATE,
        PERMISSION_KNOWLEDGE_SEARCH,
    },
}

VALID_ROLES = set(ROLE_PERMISSIONS)


@dataclass
class Principal:
    """Authenticated caller identity."""

    user_id: str
    username: str
    organization_id: str
    role: str
    permissions: set[str] = field(default_factory=set)
    is_service_account: bool = False

    def __post_init__(self) -> None:
        if not self.permissions:
            self.permissions = permissions_for_role(self.role)

    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions

    def has_all_permissions(self, permissions: list[str]) -> bool:
        return all(p in self.permissions for p in permissions)

    def has_any_permission(self, permissions: list[str]) -> bool:
        return any(p in self.permissions for p in permissions)


class AuthorizationError(UnauthorizedError):
    """Raised when the principal lacks a required permission."""


def permissions_for_role(role: str) -> set[str]:
    return set(ROLE_PERMISSIONS.get(role, set()))


def principal_from_claims(claims: dict) -> Principal:
    """Build a Principal from JWT claims."""
    role = claims.get("role", "viewer")
    permissions = permissions_for_role(role)
    return Principal(
        user_id=claims.get("sub", ""),
        username=claims.get("username", ""),
        organization_id=claims.get("organization_id", ""),
        role=role,
        permissions=permissions,
        is_service_account=role == "service_account",
    )


class PermissionChecker:
    """Enforces authorization at the service boundary."""

    def __init__(self, principal: Principal) -> None:
        self.principal = principal

    def require(self, permission: str) -> None:
        if not self.principal.has_permission(permission):
            raise AuthorizationError(
                f"Permission required: {permission}",
                code="permission_required",
            )

    def require_any(self, permissions: list[str]) -> None:
        if not self.principal.has_any_permission(permissions):
            raise AuthorizationError(
                f"One of these permissions required: {', '.join(permissions)}",
                code="permission_required",
            )

    def require_all(self, permissions: list[str]) -> None:
        if not self.principal.has_all_permissions(permissions):
            raise AuthorizationError(
                f"All of these permissions required: {', '.join(permissions)}",
                code="permission_required",
            )

    def require_organization(self, organization_id: str) -> None:
        if self.principal.organization_id != organization_id:
            raise AuthorizationError(
                "Cross-tenant access is not allowed",
                code="cross_tenant_forbidden",
            )

    def require_role(self, roles: list[str]) -> None:
        if self.principal.role not in roles:
            raise AuthorizationError(
                f"One of these roles required: {', '.join(roles)}",
                code="role_required",
            )

    def require_active(self) -> None:
        # Principal activity is enforced by the auth service at validation time.
        pass
