"""Secrets management.

Encrypts sensitive credentials (e.g. database passwords) at rest using
Fernet (AES-128-CBC + HMAC-SHA256) backed by a configurable encryption
key. Never stores or logs plaintext secrets.
"""

from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken

from querymind.core.config import settings
from querymind.core.exceptions import SecurityError


class SecretManager:
    """Encrypts and decrypts secrets at rest."""

    def __init__(self, encryption_key: Optional[str] = None) -> None:
        key = encryption_key or settings.encryption_key
        try:
            self._fernet = Fernet(key.encode("utf-8"))
        except (ValueError, TypeError) as exc:
            raise SecurityError(
                "Invalid ENCRYPTION_KEY: must be a URL-safe base64-encoded 32-byte key",
                code="invalid_encryption_key",
            ) from exc

    def encrypt(self, plaintext: str) -> str:
        """Encrypt a plaintext secret and return a base64 ciphertext token."""
        if not plaintext:
            return plaintext
        token = self._fernet.encrypt(plaintext.encode("utf-8"))
        return token.decode("utf-8")

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt a ciphertext token back to plaintext."""
        if not ciphertext:
            return ciphertext
        try:
            return self._fernet.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
        except InvalidToken as exc:
            raise SecurityError("Failed to decrypt secret", code="decryption_failed") from exc

    def rotate(self, new_encryption_key: str) -> "SecretManager":
        """Return a new SecretManager using the new key.

        Re-encrypting existing secrets requires decrypting with the old
        manager and encrypting with the new one (key rotation strategy).
        """
        return SecretManager(encryption_key=new_encryption_key)


secret_manager = SecretManager()
