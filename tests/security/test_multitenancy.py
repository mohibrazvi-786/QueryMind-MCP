"""Unit tests for multi-tenancy (organization scoping)."""

from __future__ import annotations

import pytest

from querymind.core.multitenancy import TenantIsolationError, TenantScope
from querymind.core.rbac import Principal


def _principal(role: str, organization_id: str = "org-a") -> Principal:
    return Principal(
        user_id="u1", username="alice", organization_id=organization_id, role=role
    )


def test_same_organization_allowed():
    scope = TenantScope(_principal("viewer", "org-a"))
    assert scope.may_access("org-a") is True


def test_cross_organization_blocked():
    scope = TenantScope(_principal("viewer", "org-a"))
    assert scope.may_access("org-b") is False


def test_platform_admin_accesses_any_org():
    scope = TenantScope(_principal("platform_admin", "org-a"))
    assert scope.may_access("org-b") is True
    assert scope.may_access("org-c") is True


def test_require_same_organization_raises():
    scope = TenantScope(_principal("viewer", "org-a"))
    with pytest.raises(TenantIsolationError):
        scope.require_same_organization("org-b")


def test_filter_by_organization():
    scope = TenantScope(_principal("viewer", "org-a"))
    items = [
        {"id": 1, "organization_id": "org-a", "name": "A"},
        {"id": 2, "organization_id": "org-b", "name": "B"},
        {"id": 3, "organization_id": "org-a", "name": "C"},
    ]
    filtered = scope.filter_by_organization(items)
    assert len(filtered) == 2
    assert all(i["organization_id"] == "org-a" for i in filtered)


def test_filter_by_organization_platform_admin_sees_all():
    scope = TenantScope(_principal("platform_admin", "org-a"))
    items = [
        {"id": 1, "organization_id": "org-a"},
        {"id": 2, "organization_id": "org-b"},
    ]
    assert len(scope.filter_by_organization(items)) == 2


def test_assert_owned_raises_on_other_org():
    scope = TenantScope(_principal("viewer", "org-a"))
    with pytest.raises(TenantIsolationError):
        scope.assert_owned({"organization_id": "org-b"})
