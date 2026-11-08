# Authentication — QueryMind MCP

## Overview

QueryMind provides provider-independent authentication for its application
and network-accessible MCP/API interfaces. Passwords are never stored in
plaintext; all credentials are hashed with bcrypt.

## Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/register` | POST | Register a new user (open when enabled; otherwise platform-admin only) |
| `/auth/login` | POST | Authenticate and return an access + refresh token pair |
| `/auth/logout` | POST | Revoke a refresh token (session logout) |
| `/auth/refresh` | POST | Rotate a refresh token into a new token pair |
| `/auth/me` | GET | Return the authenticated principal's profile and permissions |

## Token model

- **Access token**: short-lived JWT (default 30 min), carries `sub`,
  `username`, `organization_id`, `role`, `jti`, `typ`.
- **Refresh token**: longer-lived JWT (default 7 days), stored server-side
  and rotated on each use. Rotating revokes the previous token.
- **Revocation**: access tokens can be blocklisted; refresh tokens are marked
  revoked on logout, rotation, password change, or user deactivation.
- **Session invalidation**: deactivating a user revokes all their sessions.

## Passwords

- Hashed with bcrypt (configurable rounds, default 12).
- Never stored, logged, or returned in plaintext.
- Minimum length enforced (8 characters).

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `JWT_SECRET_KEY` | `change-me-in-production-32-bytes-min` | HS256 signing key (change in production) |
| `JWT_ALGORITHM` | `HS256` | Token signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token lifetime |
| `BCRYPT_ROUNDS` | `12` | bcrypt cost factor |
| `REGISTRATION_ENABLED` | `true` | Allow open self-registration |

## Security notes

- Use HTTPS in production; never transmit tokens over plaintext.
- Rotate `JWT_SECRET_KEY` on suspected compromise (invalidates all tokens).
- Service accounts use the same token flow with explicitly scoped roles.
- Password-reset via email is not implemented unless an email provider is
  configured; do not invent email delivery.
