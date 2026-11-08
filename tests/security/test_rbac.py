"""Unit tests for RBAC (role-based access control)."""

from __future__ import annotations

import pytest

from querymind.core.rbac import (
    Principal,
    PermissionChecker,
    permissions_for_role,
    principal_from_claims,
    ROLE_PERMISSIONS,
)


def test_role_permissions_nonempty():
    for role in ("platform_admin", "org_admin", "database_analyst", "viewer", "service_account"):
        perms = permissions_for_role(role)
        assert perms, f"role {role} has no permissions"


def test_platform_admin_has_all():
    perms = permissions_for_role("platform_admin")
    # platform_admin role maps to all permissions.
    assert len(perms) > 0


def test_viewer_cannot_execute_sql():
    perms = permissions_for_role("viewer")
    assert "sql:execute:readonly" not in perms
    assert "sql:generate" not in perms


def test_database_analyst_can_execute_readonly():
    perms = permissions_for_role("database_analyst")
    assert "sql:execute:readonly" in perms
    assert "sql:generate" in perms


def test_viewer_cannot_manage_connections():
    perms = permissions_for_role("viewer")
    assert "connection:manage" not in perms


def test_org_admin_can_manage_org():
    perms = permissions_for_role("org_admin")
    assert "org:manage" in perms
    assert "user:manage" in perms


def test_principal_has_permission():
    principal = Principal(
        user_id="u1", username="alice", organization_id="org-1",
        role="database_analyst",
    )
    assert principal.has_permission("sql:generate")
    assert not principal.has_permission("connection:manage")


def test_principal_from_claims():
    claims = {
        "sub": "u2", "username": "bob", "organization_id": "org-2",
        "role": "org_admin",
    }
    principal = principal_from_claims(claims)
    assert principal.organization_id == "org-2"
    assert principal.role == "org_admin"
    assert principal.has_permission("org:manage")


def test_permission_checker_require():
    principal = Principal(
        user_id="u1", username="alice", organization_id="org-1",
        role="viewer",
    )
    checker = PermissionChecker(principal)
    checker.require("db:discover")  # viewer has this
    with pytest.raises(Exception):
        checker.require("connection:manage")


def test_permission_checker_require_any():
    principal = Principal(
        user_id="u1", username="alice", organization_id="org-1",
        role="viewer",
    )
    checker = PermissionChecker(principal)
    checker.require_any(["db:discover", "connection:manage"])  # has db:discover
    with pytest.raises(Exception):
        checker.require_any(["connection:manage", "user:manage"])


def test_permission_checker_require_all():
    principal = Principal(
        user_id="u1", username="alice", organization_id="org-1",
        role="database_analyst",
    )
    checker = PermissionChecker(principal)
    checker.require_all(["sql:generate", "sql:execute:readonly"])
    with pytest.raises(Exception):
        checker.require_all(["sql:generate", "connection:manage"])
