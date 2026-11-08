"""FastAPI dependencies for authenticated access."""

from __future__ import annotations

from typing import Optional, Sequence

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from querymind.core.auth import resolve_principal
from querymind.core.rbac import Principal, PermissionChecker

_bearer = HTTPBearer(auto_error=False)


def get_bearer_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> Optional[str]:
    return credentials.credentials if credentials else None


def get_current_principal(
    token: Optional[str] = Depends(get_bearer_token),
) -> Optional[Principal]:
    return resolve_principal(token)


def require_principal(principal: Optional[Principal]) -> Principal:
    if principal is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return principal


def require_permissions(
    permissions: Sequence[str],
):
    """Dependency factory: require the authenticated principal to hold all permissions."""

    def checker(principal: Principal = Depends(require_principal)) -> Principal:
        PermissionChecker(principal).require_all(list(permissions))
        return principal

    return checker


def require_any_permission(
    permissions: Sequence[str],
):
    """Dependency factory: require the authenticated principal to hold any permission."""

    def checker(principal: Principal = Depends(require_principal)) -> Principal:
        PermissionChecker(principal).require_any(list(permissions))
        return principal

    return checker
