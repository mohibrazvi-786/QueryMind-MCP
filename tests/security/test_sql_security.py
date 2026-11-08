"""Security tests: unsafe SQL rejection and credential redaction."""

from __future__ import annotations

import pytest

from querymind.core.security import is_allowed_host, redact
from querymind.services.sql_validation_service import SQLValidationService


def test_redact_never_exposes_secret():
    assert redact("super-secret-password") == "***"
    assert redact("") == ""
    assert redact(None) is None


def test_metadata_ip_blocked():
    assert is_allowed_host("169.254.169.254") is False
    assert is_allowed_host("localhost") is True
    assert is_allowed_host("127.0.0.1") is True


@pytest.mark.parametrize(
    "bad_sql",
    [
        "DROP TABLE customers",
        "DELETE FROM customers",
        "UPDATE customers SET x=1",
        "INSERT INTO customers VALUES (1)",
        "ALTER TABLE customers ADD COLUMN x int",
        "TRUNCATE customers",
        "CREATE TABLE t (id int)",
        "GRANT ALL ON customers TO public",
        "REVOKE ALL ON customers FROM public",
        "SELECT 1; SELECT 2",
        "SELECT pg_sleep(10)",
    ],
)
def test_unsafe_sql_rejected(bad_sql):
    service = SQLValidationService()
    with pytest.raises(Exception):
        service.validate(bad_sql)


def test_safe_select_allowed():
    service = SQLValidationService()
    result = service.validate("SELECT id, email FROM customers WHERE id = 1 LIMIT 10")
    assert result.valid is True
