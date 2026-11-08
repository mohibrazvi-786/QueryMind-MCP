"""Multi-tenancy: organization-level isolation.

Every organization-owned resource carries an organization_id. TenantScope
validates that a principal may only access resources within their own
organization (unless they are a platform admin).
"""

from __future__ import annotations

from querymind.core.exceptions import UnauthorizedError
from querymind.core.rbac import Principal


class TenantIsolationError(UnauthorizedError):
    """Raised on cross-tenant access attempts."""


class TenantScope:
    """Enforces organization-level isolation for a principal."""

    def __init__(self, principal: Principal) -> None:
        self.principal = principal

    def organization_id(self) -> str:
        return self.principal.organization_id

    def may_access(self, resource_organization_id: str) -> bool:
        """Return True if the principal may access a resource in the given org."""
        if self.principal.role == "platform_admin":
            return True
        return self.principal.organization_id == resource_organization_id

    def require_same_organization(self, resource_organization_id: str) -> None:
        if not self.may_access(resource_organization_id):
            raise TenantIsolationError(
                "Cross-tenant access is not allowed",
                code="cross_tenant_forbidden",
            )

    def filter_by_organization(
        self, items: list[dict], org_field: str = "organization_id"
    ) -> list[dict]:
        """Return only items belonging to the principal's organization."""
        if self.principal.role == "platform_admin":
            return list(items)
        return [
            item
            for item in items
            if item.get(org_field) == self.principal.organization_id
        ]

    def assert_owned(self, resource: dict, org_field: str = "organization_id") -> None:
        """Assert the principal owns the given resource."""
        self.require_same_organization(resource.get(org_field, ""))


def scoped_organization_id(principal: Principal) -> str:
    """Return the organization id the principal is scoped to."""
    return principal.organization_id
