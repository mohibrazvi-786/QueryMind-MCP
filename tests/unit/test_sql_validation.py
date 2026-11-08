"""Unit tests for SQL validation service (SQLGlot AST-based)."""

from __future__ import annotations

import pytest

from querymind.services.sql_validation_service import (
    DISALLOWED_STATEMENT_TYPES,
    SQLValidationService,
    validate_readonly_sql,
)


def test_valid_select_passes():
    service = SQLValidationService()
    result = service.validate("SELECT id, email FROM customers WHERE id = 1")
    assert result.valid is True
    assert result.statement_type == "select"
    assert "customers" in result.tables


def test_insert_rejected():
    service = SQLValidationService()
    with pytest.raises(Exception):
        service.validate("INSERT INTO customers (email) VALUES ('a@b.c')")


def test_delete_rejected():
    service = SQLValidationService()
    with pytest.raises(Exception):
        service.validate("DELETE FROM customers WHERE id = 1")


def test_update_rejected():
    service = SQLValidationService()
    with pytest.raises(Exception):
        service.validate("UPDATE customers SET email = 'x' WHERE id = 1")


def test_drop_rejected():
    service = SQLValidationService()
    with pytest.raises(Exception):
        service.validate("DROP TABLE customers")


def test_alter_rejected():
    service = SQLValidationService()
    with pytest.raises(Exception):
        service.validate("ALTER TABLE customers ADD COLUMN x int")


def test_truncate_rejected():
    service = SQLValidationService()
    with pytest.raises(Exception):
        service.validate("TRUNCATE customers")


def test_create_rejected():
    service = SQLValidationService()
    with pytest.raises(Exception):
        service.validate("CREATE TABLE t (id int)")


def test_multi_statement_rejected():
    service = SQLValidationService()
    with pytest.raises(Exception):
        service.validate("SELECT 1; SELECT 2")


def test_empty_sql_rejected():
    service = SQLValidationService()
    with pytest.raises(Exception):
        service.validate("")


def test_disallowed_function_rejected():
    service = SQLValidationService()
    with pytest.raises(Exception):
        service.validate("SELECT pg_sleep(10) FROM customers")


def test_allowlist_table_rejected():
    service = SQLValidationService(allowed_tables={"customers"})
    with pytest.raises(Exception):
        service.validate("SELECT * FROM orders")


def test_allowlist_schema_rejected():
    service = SQLValidationService(allowed_schemas={"public"})
    with pytest.raises(Exception):
        service.validate("SELECT * FROM pg_catalog.pg_class")


def test_convenience_wrapper():
    result = validate_readonly_sql("SELECT id FROM customers")
    assert result.valid is True


def test_disallowed_statement_types_nonempty():
    assert "insert" in DISALLOWED_STATEMENT_TYPES
    assert "delete" in DISALLOWED_STATEMENT_TYPES
    assert "drop" in DISALLOWED_STATEMENT_TYPES
