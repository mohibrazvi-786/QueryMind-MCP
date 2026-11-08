"""Unit tests for secrets management."""

from __future__ import annotations

import pytest
from cryptography.fernet import Fernet

from querymind.core.secrets import SecretManager, secret_manager


def _valid_key() -> str:
    return Fernet.generate_key().decode()


def test_encrypt_decrypt_roundtrip():
    key = _valid_key()
    mgr = SecretManager(encryption_key=key)
    plaintext = "super-secret-db-password"
    ciphertext = mgr.encrypt(plaintext)
    assert ciphertext != plaintext
    assert mgr.decrypt(ciphertext) == plaintext


def test_decrypt_invalid_raises():
    key = _valid_key()
    mgr = SecretManager(encryption_key=key)
    with pytest.raises(Exception):
        mgr.decrypt("not-a-valid-token!!!")


def test_empty_string_passthrough():
    key = _valid_key()
    mgr = SecretManager(encryption_key=key)
    assert mgr.encrypt("") == ""
    assert mgr.decrypt("") == ""


def test_invalid_encryption_key_rejected():
    with pytest.raises(Exception):
        SecretManager(encryption_key="not-a-valid-key")


def test_rotation_can_decrypt_with_new_key():
    mgr = SecretManager(encryption_key=_valid_key())
    ciphertext = mgr.encrypt("my-secret")
    new_key = _valid_key()
    new_mgr = mgr.rotate(new_encryption_key=new_key)
    # New manager cannot decrypt old ciphertext (different key).
    with pytest.raises(Exception):
        new_mgr.decrypt(ciphertext)
    # But can encrypt/decrypt fresh secrets.
    fresh = new_mgr.encrypt("new-secret")
    assert new_mgr.decrypt(fresh) == "new-secret"


def test_global_secret_manager():
    assert secret_manager is not None
