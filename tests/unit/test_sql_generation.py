"""Unit tests for SQL generation service (NL-to-SQL)."""

from __future__ import annotations

from types import SimpleNamespace

from querymind.intelligence.llm.provider import MockLLMProvider
from querymind.services.discovery_service import DiscoveryService
from querymind.services.sql_generation_service import SQLGenerationService
from querymind.services.sql_validation_service import SQLValidationService


class FakeConnection:
    def __init__(self, tables: dict) -> None:
        self._tables = tables

    def execute(self, sql: str, params: dict | None = None):
        if sql.strip() == "SELECT version() AS v":
            return [{"v": "PostgreSQL 17.11"}]
        return []


def test_sql_generation_top_customers():
    catalogue = {
        "database_version": "PostgreSQL 17.11",
        "schemas": ["public"],
        "tables": [
            {
                "schema": "public",
                "name": "customers",
                "type": "BASE TABLE",
                "columns": [
                    {"column_name": "id", "data_type": "integer", "is_nullable": "NO"},
                    {"column_name": "email", "data_type": "varchar", "is_nullable": "YES"},
                ],
                "primary_keys": ["id"],
                "foreign_keys": [],
                "indexes": [],
                "stats": {},
            },
            {
                "schema": "public",
                "name": "orders",
                "type": "BASE TABLE",
                "columns": [
                    {"column_name": "id", "data_type": "integer", "is_nullable": "NO"},
                    {"column_name": "customer_id", "data_type": "integer", "is_nullable": "NO"},
                    {"column_name": "total_amount", "data_type": "numeric", "is_nullable": "YES"},
                ],
                "primary_keys": ["id"],
                "foreign_keys": [],
                "indexes": [],
                "stats": {},
            },
        ],
        "relationships": [],
        "indexes": [],
        "table_stats": [],
    }

    conn = FakeConnection({})
    discovery = DiscoveryService(conn)
    discovery.discover_all = lambda: catalogue  # type: ignore[method-assign]

    svc = SQLGenerationService(
        llm_provider=MockLLMProvider(),
        discovery_service=discovery,
        validation_service=SQLValidationService(),
    )
    result = svc.generate("Find my top 10 customers by spending")

    assert result.sql
    assert "customers" in result.sql.lower() or "orders" in result.sql.lower()
    assert result.confidence in {"low", "medium", "high"}
    assert result.question == "Find my top 10 customers by spending"

    # Validate the generated SQL — mock should produce valid SELECT.
    validation = svc.validation.validate(result.sql)
    assert validation.valid is True
    assert validation.statement_type == "select"
