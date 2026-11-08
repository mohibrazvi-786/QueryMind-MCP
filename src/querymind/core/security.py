"""Security helpers (placeholder, expanded in Stage 8)."""

from __future__ import annotations

import re

_ALLOWED_HOSTS = {"localhost", "127.0.0.1", "::1"}
_DISALLOWED_HOST_PATTERNS = [
    r"169\.254\.",          # cloud metadata
    r"10\.",                # private ranges (dev allowlist only)
    r"172\.(1[6-9]|2[0-9]|3[01])\.",  # private
    r"192\.168\.",          # private
]


def is_allowed_host(host: str) -> bool:
    """Return True if the host is an explicitly allowed local dev target."""
    if not host:
        return False
    host = host.lower()
    for pattern in _DISALLOWED_HOST_PATTERNS:
        if re.search(pattern, host):
            return False
    return host in _ALLOWED_HOSTS or host.endswith(".local")


def redact(value: str) -> str:
    """Redact a sensitive value for logging."""
    if not value:
        return value
    return "***"
