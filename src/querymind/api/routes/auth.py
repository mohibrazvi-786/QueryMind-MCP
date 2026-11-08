"""FastAPI authentication routes.

Endpoints:
- POST /auth/register
- POST /auth/login
- POST /auth/logout
- POST /auth/refresh
- GET /auth/me
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, status

from querymind.core.auth import TokenPair, auth_service
from querymind.core.config import settings
from querymind.core.rbac import Principal
from querymind.api.dependencies import get_current_principal, require_principal

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    username: str = Body(..., embed=True),
    email: str = Body(..., embed=True),
    password: str = Body(..., embed=True),
    organization_id: str = Body(..., embed=True),
    role: str = Body("viewer", embed=True),
    principal: Optional[Principal] = Depends(get_current_principal),
) -> dict:
    """Register a new user. Open when registration_enabled; otherwise
    restricted to platform administrators."""
    if not settings.registration_enabled and (
        principal is None or principal.role != "platform_admin"
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Registration is disabled",
        )
    try:
        user = auth_service.register(
            username=username,
            email=email,
            password=password,
            organization_id=organization_id,
            role=role,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return {
        "user_id": user.user_id,
        "username": user.username,
        "email": user.email,
        "organization_id": user.organization_id,
        "role": user.role,
        "is_active": user.is_active,
    }


@router.post("/login", response_model=TokenPair)
def login(
    username: str = Body(..., embed=True),
    password: str = Body(..., embed=True),
) -> TokenPair:
    try:
        return auth_service.login(username=username, password=password)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    refresh_token: Optional[str] = Body(None, embed=True),
    principal: Optional[Principal] = Depends(get_current_principal),
) -> None:
    if principal is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    auth_service.logout(refresh_token_jti=refresh_token)


@router.post("/refresh", response_model=TokenPair)
def refresh(
    refresh_token: str = Body(..., embed=True),
) -> TokenPair:
    try:
        return auth_service.refresh(refresh_token=refresh_token)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))


@router.get("/me")
def me(principal: Principal = Depends(require_principal)) -> dict:
    return {
        "user_id": principal.user_id,
        "username": principal.username,
        "organization_id": principal.organization_id,
        "role": principal.role,
        "permissions": sorted(principal.permissions),
        "is_service_account": principal.is_service_account,
    }
