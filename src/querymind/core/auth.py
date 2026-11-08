"""Authentication service.

Provider-independent authentication: registration, login, logout,
access-token validation, refresh-token rotation, token expiration,
password hashing (bcrypt), and session invalidation.

No plaintext passwords are ever stored. All token state is held in
memory for the default implementation; production deployments should
back this with Redis or the internal database.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt

from querymind.core.config import settings
from querymind.core.exceptions import (
    AuthenticationError,
    NotFoundError,
    SecurityError,
    ValidationError,
)
from querymind.core.rbac import Principal, principal_from_claims

_USER_NOT_FOUND = "User not found"
_INVALID_CREDENTIALS = "Invalid credentials"
_TOKEN_EXPIRED = "Token has expired"
_TOKEN_INVALID = "Token is invalid or malformed"
_TOKEN_REVOKED = "Token has been revoked"
_REGISTRATION_DISABLED = "User registration is disabled"
_USERNAME_TAKEN = "Username is already taken"
_EMAIL_TAKEN = "Email is already taken"


@dataclass
class User:
    """Application user account."""

    user_id: str
    username: str
    email: str
    password_hash: str
    organization_id: str
    is_active: bool = True
    is_verified: bool = False
    role: str = "viewer"
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    last_login_at: Optional[str] = None


@dataclass
class TokenPair:
    """Access and refresh token pair."""

    access_token: str
    refresh_token: str
    access_token_expires_at: str
    refresh_token_expires_at: str
    token_type: str = "Bearer"


@dataclass
class RefreshTokenRecord:
    """Stored refresh token metadata."""

    token_hash: str
    user_id: str
    expires_at: str
    revoked: bool = False


class AuthService:
    """Authenticates users and manages JWT access/refresh tokens."""

    def __init__(self) -> None:
        self._users: dict[str, User] = {}
        self._users_by_username: dict[str, str] = {}
        self._users_by_email: dict[str, str] = {}
        self._access_blocklist: set[str] = set()  # jti of revoked access tokens
        self._refresh_tokens: dict[str, RefreshTokenRecord] = {}  # jti -> record

    # ---------- user management ----------

    def hash_password(self, password: str) -> str:
        return bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt(settings.bcrypt_rounds)
        ).decode("utf-8")

    def verify_password(self, password: str, password_hash: str) -> bool:
        try:
            return bcrypt.checkpw(
                password.encode("utf-8"), password_hash.encode("utf-8")
            )
        except (ValueError, TypeError):
            return False

    def register(
        self,
        *,
        username: str,
        email: str,
        password: str,
        organization_id: str,
        role: str = "viewer",
    ) -> User:
        if not settings.registration_enabled:
            raise SecurityError(_REGISTRATION_DISABLED, code="registration_disabled")
        if not username or not email or not password:
            raise ValidationError("Username, email and password are required")
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters")
        if username in self._users_by_username:
            raise SecurityError(_USERNAME_TAKEN, code="username_taken")
        if email in self._users_by_email:
            raise SecurityError(_EMAIL_TAKEN, code="email_taken")

        user_id = secrets.token_urlsafe(16)
        user = User(
            user_id=user_id,
            username=username,
            email=email,
            password_hash=self.hash_password(password),
            organization_id=organization_id,
            role=role,
        )
        self._users[user_id] = user
        self._users_by_username[username] = user_id
        self._users_by_email[email] = user_id
        return user

    def get_user(self, user_id: str) -> Optional[User]:
        return self._users.get(user_id)

    def get_user_by_username(self, username: str) -> Optional[User]:
        uid = self._users_by_username.get(username)
        return self._users.get(uid) if uid else None

    def deactivate_user(self, user_id: str) -> None:
        user = self._users.get(user_id)
        if user is None:
            raise NotFoundError(_USER_NOT_FOUND, code="user_not_found")
        user.is_active = False
        user.updated_at = datetime.now(timezone.utc).isoformat()
        # Revoke all refresh tokens and blocklist access tokens on deactivation.
        self.revoke_all_user_sessions(user_id)

    # ---------- tokens ----------

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    def _make_access_token(self, user: User) -> tuple[str, str, str]:
        now = self._now()
        expires = now + timedelta(minutes=settings.access_token_expire_minutes)
        jti = secrets.token_urlsafe(16)
        payload = {
            "sub": user.user_id,
            "username": user.username,
            "organization_id": user.organization_id,
            "role": user.role,
            "jti": jti,
            "iat": int(now.timestamp()),
            "exp": int(expires.timestamp()),
            "typ": "access",
        }
        token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        return token, jti, expires.isoformat()

    def _make_refresh_token(self, user: User) -> tuple[str, str, str]:
        now = self._now()
        expires = now + timedelta(days=settings.refresh_token_expire_days)
        jti = secrets.token_urlsafe(16)
        payload = {
            "sub": user.user_id,
            "jti": jti,
            "iat": int(now.timestamp()),
            "exp": int(expires.timestamp()),
            "typ": "refresh",
        }
        token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        return token, jti, expires.isoformat()

    def login(self, *, username: str, password: str) -> TokenPair:
        user = self.get_user_by_username(username)
        if user is None or not user.is_active:
            raise AuthenticationError(_INVALID_CREDENTIALS, code="invalid_credentials")
        if not self.verify_password(password, user.password_hash):
            raise AuthenticationError(_INVALID_CREDENTIALS, code="invalid_credentials")

        access_token, access_jti, access_expires = self._make_access_token(user)
        refresh_token, refresh_jti, refresh_expires = self._make_refresh_token(user)

        self._refresh_tokens[refresh_jti] = RefreshTokenRecord(
            token_hash=refresh_jti,  # jti doubles as lookup key; hash stored for clarity
            user_id=user.user_id,
            expires_at=refresh_expires,
        )
        user.last_login_at = self._now().isoformat()
        user.updated_at = user.last_login_at

        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            access_token_expires_at=access_expires,
            refresh_token_expires_at=refresh_expires,
        )

    def logout(self, *, access_token_jti: Optional[str] = None, refresh_token_jti: Optional[str] = None) -> None:
        if access_token_jti:
            self._access_blocklist.add(access_token_jti)
        if refresh_token_jti:
            record = self._refresh_tokens.get(refresh_token_jti)
            if record is not None:
                record.revoked = True

    def revoke_all_user_sessions(self, user_id: str) -> None:
        for record in self._refresh_tokens.values():
            if record.user_id == user_id:
                record.revoked = True

    def refresh(self, *, refresh_token: str) -> TokenPair:
        """Rotate a refresh token into a new access/refresh token pair."""
        payload = self._decode_token(refresh_token, expected_type="refresh")
        user_id = payload["sub"]
        jti = payload["jti"]

        record = self._refresh_tokens.get(jti)
        if record is None or record.revoked:
            raise AuthenticationError(_TOKEN_REVOKED, code="refresh_token_revoked")
        if record.user_id != user_id:
            raise AuthenticationError(_INVALID_CREDENTIALS, code="invalid_credentials")

        user = self._users.get(user_id)
        if user is None or not user.is_active:
            raise AuthenticationError(_INVALID_CREDENTIALS, code="user_inactive")

        # Rotate: revoke old refresh token, issue a new pair.
        record.revoked = True

        access_token, access_jti, access_expires = self._make_access_token(user)
        refresh_token_new, refresh_jti, refresh_expires = self._make_refresh_token(user)
        self._refresh_tokens[refresh_jti] = RefreshTokenRecord(
            token_hash=refresh_jti,
            user_id=user.user_id,
            expires_at=refresh_expires,
        )
        user.last_login_at = self._now().isoformat()
        user.updated_at = user.last_login_at

        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token_new,
            access_token_expires_at=access_expires,
            refresh_token_expires_at=refresh_expires,
        )

    def validate_access_token(self, access_token: str) -> dict:
        """Validate an access token and return its claims.

        Raises AuthenticationError on expiry, revocation, or invalid token.
        """
        payload = self._decode_token(access_token, expected_type="access")
        jti = payload["jti"]
        if jti in self._access_blocklist:
            raise AuthenticationError(_TOKEN_REVOKED, code="access_token_revoked")
        user = self._users.get(payload["sub"])
        if user is None or not user.is_active:
            raise AuthenticationError(_INVALID_CREDENTIALS, code="user_inactive")
        return payload

    # ---------- internals ----------

    def _decode_token(self, token: str, *, expected_type: str) -> dict:
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm],
                options={"require": ["exp", "iat", "sub", "jti", "typ"]},
            )
        except jwt.ExpiredSignatureError as exc:
            raise AuthenticationError(_TOKEN_EXPIRED, code="token_expired") from exc
        except jwt.InvalidTokenError as exc:
            raise AuthenticationError(_TOKEN_INVALID, code="token_invalid") from exc
        if payload.get("typ") != expected_type:
            raise AuthenticationError(_TOKEN_INVALID, code="token_type_mismatch")
        return payload


auth_service = AuthService()


def resolve_principal(access_token: Optional[str]) -> Optional[Principal]:
    """Resolve an access token to a Principal.

    Returns None when no token is provided (unauthenticated). Raises
    AuthenticationError when a token is provided but is invalid, expired,
    or revoked.
    """
    if not access_token:
        return None
    claims = auth_service.validate_access_token(access_token)
    return principal_from_claims(claims)
