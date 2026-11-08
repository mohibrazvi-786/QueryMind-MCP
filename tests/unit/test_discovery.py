"""Offline unit tests for the Database Discovery Engine.

These tests do not require a live PostgreSQL. They validate that every
discovery SQL statement parses (PostgreSQL dialect via SQLGlot) and that
the catalogue assembly logic produces the correct JSON structure from
synthetic rows. A live PostgreSQL is required for an end-to-end run
(see docs/REPOSITORY_AUDIT.md — environment constraints).
"""

from __future__ import annotations

from types import SimpleNamespace

import sqlglot

from querymind.services.discovery_service import (
    DiscoveryService,
    _DATABASE_VERSION,
    _DISCOVER_COLUMNS,
    _DISCOVER_SCHEMAS,
    _DISCOVER_TABLES,
    _FOREIGN_KEYS,
    _INDEXES,
    _PRIMARY_KEYS,
    _TABLE_STATS,
)


class FakeConnection:
    """Stand-in for TargetConnection returning synthetic catalogue rows."""

    def __init__(self, tables: dict[str, list[dict]]) -> None:
        self._tables = tables
        self.calls = []

    def execute(self, sql: str, params: dict | None = None):
        self.calls.append((sql, params))
        if sql.strip() == _DATABASE_VERSION.strip():
            return [{"version": "PostgreSQL 17.11 on x86_64-pc-linux-gnu"}]
        if sql.strip() == _DISCOVER_SCHEMAS.strip():
            return [{"schema_name": "public"}, {"schema_name": "sales"}]
        if sql.strip() == _DISCOVER_TABLES.strip():
            return self._tables["tables"]
        if sql.strip() == _DISCOVER_COLUMNS.strip():
            return self._tables["columns"]
        if sql.strip() == _PRIMARY_KEYS.strip():
            return self._tables["pks"]
        if sql.strip() == _FOREIGN_KEYS.strip():
            return self._tables["fks"]
        if sql.strip() == _INDEXES.strip():
            return self._tables["indexes"]
        if sql.strip() == _TABLE_STATS.strip():
            return self._tables["stats"]
        return []


def _parse(sql: str) -> None:
    """Assert the statement parses as PostgreSQL SQL."""
    ast = sqlglot.parse_one(sql, read="postgres")
    assert ast is not None


SYNTHETIC = {
    "tables": [
        {"table_schema": "public", "table_name": "customers", "table_type": "BASE TABLE"},
        {"table_schema": "public", "table_name": "orders", "table_type": "BASE TABLE"},
        {"table_schema": "sales", "table_name": "monthly_report", "table_type": "VIEW"},
    ],
    "columns": [
        {"table_schema": "public", "table_name": "customers", "column_name": "id", "data_type": "integer", "udt_name": "int4", "character_maximum_length": None, "numeric_precision": 32, "numeric_scale": 0, "is_nullable": "NO", "column_default": None, "ordinal_position": 1},
        {"table_schema": "public", "table_name": "customers", "column_name": "email", "data_type": "character varying", "udt_name": "varchar", "character_maximum_length": 255, "numeric_precision": None, "numeric_scale": None, "is_nullable": "YES", "column_default": None, "ordinal_position": 2},
        {"table_schema": "public", "table_name": "orders", "column_name": "id", "data_type": "integer", "udt_name": "int4", "character_maximum_length": None, "numeric_precision": 32, "numeric_scale": 0, "is_nullable": "NO", "column_default": None, "ordinal_position": 1},
        {"table_schema": "public", "table_name": "orders", "column_name": "customer_id", "data_type": "integer", "udt_name": "int4", "character_maximum_length": None, "numeric_precision": 32, "numeric_scale": 0, "is_nullable": "NO", "column_default": None, "ordinal_position": 2},
    ],
    "pks": [
        {"table_schema": "public", "table_name": "customers", "column_name": "id"},
        {"table_schema": "public", "table_name": "orders", "column_name": "id"},
    ],
    "fks": [
        {
            "source_schema": "public",
            "source_table": "orders",
            "source_column": "customer_id",
            "target_schema": "public",
            "target_table": "customers",
            "target_column": "id",
            "constraint_name": "orders_customer_id_fkey",
        }
    ],
    "indexes": [
        {
            "table_schema": "public",
            "table_name": "orders",
            "index_name": "idx_orders_customer_id",
            "index_definition": "CREATE INDEX idx_orders_customer_id ON public.orders USING btree (customer_id)",
        }
    ],
    "stats": [
        {
            "table_schema": "public",
            "table_name": "customers",
            "relkind": "r",
            "total_bytes": 123456,
            "table_bytes": 98765,
            "row_estimate": 100000,
            "last_analyze": None,
            "last_autoanalyze": None,
        }
    ],
}


def test_discovery_sql_parses_postgres():
    for sql in [
        _DISCOVER_SCHEMAS,
        _DISCOVER_TABLES,
        _DISCOVER_COLUMNS,
        _PRIMARY_KEYS,
        _FOREIGN_KEYS,
        _INDEXES,
        _TABLE_STATS,
        _DATABASE_VERSION,
    ]:
        _parse(sql)


def test_discover_all_structure():
    conn = FakeConnection(SYNTHETIC)
    service = DiscoveryService(conn)
    catalogue = service.discover_all()

    assert catalogue["database_version"].startswith("PostgreSQL")
    assert "public" in catalogue["schemas"]
    assert "sales" in catalogue["schemas"]

    table_names = {(t["schema"], t["name"]) for t in catalogue["tables"]}
    assert ("public", "customers") in table_names
    assert ("public", "orders") in table_names
    assert ("sales", "monthly_report") in table_names

    customers = next(t for t in catalogue["tables"] if t["name"] == "customers")
    assert {c["column_name"] for c in customers["columns"]} == {"id", "email"}
    assert customers["primary_keys"] == ["id"]
    assert customers["foreign_keys"] == []
    assert len(customers["indexes"]) == 0
    assert customers["stats"]["row_estimate"] == 100000

    orders = next(t for t in catalogue["tables"] if t["name"] == "orders")
    assert orders["primary_keys"] == ["id"]
    assert len(orders["foreign_keys"]) == 1
    assert orders["foreign_keys"][0]["target_table"] == "customers"
    assert len(orders["indexes"]) == 1
    assert orders["indexes"][0]["index_name"] == "idx_orders_customer_id"

    relationships = catalogue["relationships"]
    assert len(relationships) == 1
    assert relationships[0]["source_table"] == "orders"
    assert relationships[0]["target_table"] == "customers"

    assert len(catalogue["indexes"]) == 1
    assert len(catalogue["table_stats"]) == 1


def test_discover_all_calls_each_discovery_query_once():
    conn = FakeConnection(SYNTHETIC)
    service = DiscoveryService(conn)
    service.discover_all()
    sqls = {call[0].strip() for call in conn.calls}
    expected = {
        _DATABASE_VERSION.strip(),
        _DISCOVER_SCHEMAS.strip(),
        _DISCOVER_TABLES.strip(),
        _DISCOVER_COLUMNS.strip(),
        _PRIMARY_KEYS.strip(),
        _FOREIGN_KEYS.strip(),
        _INDEXES.strip(),
        _TABLE_STATS.strip(),
    }
    assert sqls == expected
