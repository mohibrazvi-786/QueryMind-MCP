"""MCP authorization helpers.

Resolves a bearer token to a Principal and enforces the permission and
organization scope required by each MCP tool. Unauthenticated calls are
permitted only when no token is supplied (default dev mode); when a token
is supplied it must be valid and the principal authorized.
"""

from __future__ import annotations

from typing import Optional

from fastmcp import Context

from querymind.core.auth import resolve_principal
from querymind.core.rbac import Principal, PermissionChecker
from querymind.core.exceptions import AuthenticationError, UnauthorizedError
from querymind.core.multitenancy import TenantScope
from querymind.mcp.app import connection_registry


def _connection_org_id(connection_id: str) -> Optional[str]:
    conn = connection_registry.get(connection_id)
    if conn is None:
        return None
    return getattr(conn, "organization_id", None)


def authorize(
    *,
    access_token: Optional[str],
    permission: str,
    connection_id: Optional[str] = None,
    ctx: Optional[Context] = None,
) -> Optional[Principal]:
    """Authorize an MCP tool call.

    Returns the resolved Principal (or None when no token was supplied).
    Raises AuthenticationError/UnauthorizedError on failure.
    """
    principal = resolve_principal(access_token)
    if principal is None:
        return None

    # Permission check.
    PermissionChecker(principal).require(permission)

    # Tenant scope: if the connection belongs to an organization, the
    # principal must be in that organization (or a platform admin).
    if connection_id:
        org_id = _connection_org_id(connection_id)
        if org_id is not None:
            TenantScope(principal).require_same_organization(org_id)

    return principal


def require_auth(
    *, access_token: Optional[str], ctx: Optional[Context] = None
) -> Principal:
    """Require a valid authenticated principal (no permission check)."""
    principal = resolve_principal(access_token)
    if principal is None:
        raise AuthenticationError(
            "Authentication required", code="authentication_required"
        )
    return principal
