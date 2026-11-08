"""Database discovery engine.

Queries PostgreSQL system catalogues (information_schema, pg_catalog,
pg_class, pg_attribute, pg_constraint, pg_indexes, pg_stat_user_tables)
to produce a complete, searchable schema catalogue without hardcoding any
table names.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import text

from querymind.database.connection import TargetConnection
from querymind.core.exceptions import DatabaseError

_SYSTEM_SCHEMAS = {
    "pg_catalog",
    "information_schema",
    "pg_toast",
}

_DISCOVER_SCHEMAS = """
SELECT schema_name
FROM information_schema.schemata
WHERE schema_name NOT IN :system_schemas
ORDER BY schema_name
"""

_DISCOVER_TABLES = """
SELECT table_schema,
       table_name,
       table_type
FROM information_schema.tables
WHERE table_schema NOT IN :system_schemas
ORDER BY table_schema, table_name
"""

_DISCOVER_COLUMNS = """
SELECT table_schema,
       table_name,
       column_name,
       data_type,
       udt_name,
       character_maximum_length,
       numeric_precision,
       numeric_scale,
       is_nullable,
       column_default,
       ordinal_position
FROM information_schema.columns
WHERE table_schema NOT IN :system_schemas
ORDER BY table_schema, table_name, ordinal_position
"""

_PRIMARY_KEYS = """
SELECT kcu.table_schema,
       kcu.table_name,
       kcu.column_name
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
  ON tc.constraint_name = kcu.constraint_name
 AND tc.table_schema = kcu.table_schema
 AND tc.table_name = kcu.table_name
WHERE tc.constraint_type = 'PRIMARY KEY'
  AND tc.table_schema NOT IN :system_schemas
ORDER BY kcu.table_schema, kcu.table_name, kcu.ordinal_position
"""

_FOREIGN_KEYS = """
SELECT
    kcu.table_schema AS source_schema,
    kcu.table_name AS source_table,
    kcu.column_name AS source_column,
    ccu.table_schema AS target_schema,
    ccu.table_name AS target_table,
    ccu.column_name AS target_column,
    tc.constraint_name
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
  ON tc.constraint_name = kcu.constraint_name
 AND tc.table_schema = kcu.table_schema
 AND tc.table_name = kcu.table_name
JOIN information_schema.referential_constraints rc
  ON tc.constraint_name = rc.constraint_name
 AND tc.constraint_schema = rc.constraint_schema
JOIN information_schema.key_column_usage ccu
  ON rc.unique_constraint_name = ccu.constraint_name
 AND ccu.table_schema = rc.unique_constraint_schema
 AND ccu.ordinal_position = kcu.ordinal_position
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_schema NOT IN :system_schemas
ORDER BY tc.table_schema, tc.table_name, tc.constraint_name
"""

_INDEXES = """
SELECT
    schemaname AS table_schema,
    tablename AS table_name,
    indexname AS index_name,
    indexdef AS index_definition
FROM pg_indexes
WHERE schemaname NOT IN :system_schemas
ORDER BY schemaname, tablename, indexname
"""

_TABLE_STATS = """
SELECT
    c.relnamespace::regnamespace::text AS table_schema,
    c.relname AS table_name,
    c.relkind AS relkind,
    pg_total_relation_size(c.oid) AS total_bytes,
    pg_relation_size(c.oid) AS table_bytes,
    s.n_live_tup AS row_estimate,
    s.last_analyze,
    s.last_autoanalyze
FROM pg_class c
LEFT JOIN pg_namespace n ON n.oid = c.relnamespace
LEFT JOIN pg_stat_user_tables s
  ON s.schemaname = n.nspname AND s.relname = c.relname
WHERE n.nspname NOT IN :system_schemas
  AND c.relkind IN ('r', 'p', 'v', 'm')
ORDER BY n.nspname, c.relname
"""

_DATABASE_VERSION = "SELECT version() AS version"


class DiscoveryService:
    """Discovers and catalogues a PostgreSQL database schema."""

    def __init__(self, connection: TargetConnection) -> None:
        self.connection = connection

    def _run(self, sql: str, params: dict | None = None) -> list[dict[str, Any]]:
        try:
            return self.connection.execute(sql, params or {})
        except Exception as exc:  # noqa: BLE001
            raise DatabaseError(f"Discovery query failed: {exc}") from exc

    def version(self) -> str:
        rows = self._run(_DATABASE_VERSION)
        return rows[0]["version"] if rows else "unknown"

    def discover_schemas(self) -> list[dict[str, Any]]:
        return self._run(_DISCOVER_SCHEMAS, {"system_schemas": tuple(_SYSTEM_SCHEMAS)})

    def discover_tables(self) -> list[dict[str, Any]]:
        return self._run(_DISCOVER_TABLES, {"system_schemas": tuple(_SYSTEM_SCHEMAS)})

    def discover_columns(self) -> list[dict[str, Any]]:
        return self._run(_DISCOVER_COLUMNS, {"system_schemas": tuple(_SYSTEM_SCHEMAS)})

    def discover_primary_keys(self) -> list[dict[str, Any]]:
        return self._run(_PRIMARY_KEYS, {"system_schemas": tuple(_SYSTEM_SCHEMAS)})

    def discover_foreign_keys(self) -> list[dict[str, Any]]:
        return self._run(_FOREIGN_KEYS, {"system_schemas": tuple(_SYSTEM_SCHEMAS)})

    def discover_indexes(self) -> list[dict[str, Any]]:
        return self._run(_INDEXES, {"system_schemas": tuple(_SYSTEM_SCHEMAS)})

    def discover_table_stats(self) -> list[dict[str, Any]]:
        return self._run(_TABLE_STATS, {"system_schemas": tuple(_SYSTEM_SCHEMAS)})

    def discover_all(self) -> dict[str, Any]:
        """Return a complete schema catalogue as JSON-serializable dict."""
        version = self.version()
        schemas = [row["schema_name"] for row in self.discover_schemas()]
        tables = self.discover_tables()
        columns = self.discover_columns()
        pks = self.discover_primary_keys()
        fks = self.discover_foreign_keys()
        indexes = self.discover_indexes()
        stats = self.discover_table_stats()

        # Index columns by table for fast assembly.
        columns_by_table: dict[tuple[str, str], list[dict[str, Any]]] = {}
        for col in columns:
            columns_by_table.setdefault((col["table_schema"], col["table_name"]), []).append(col)

        pks_by_table: dict[tuple[str, str], list[dict[str, Any]]] = {}
        for pk in pks:
            pks_by_table.setdefault((pk["table_schema"], pk["table_name"]), []).append(pk)

        fks_by_table: dict[tuple[str, str], list[dict[str, Any]]] = {}
        for fk in fks:
            fks_by_table.setdefault((fk["source_schema"], fk["source_table"]), []).append(fk)

        indexes_by_table: dict[tuple[str, str], list[dict[str, Any]]] = {}
        for idx in indexes:
            indexes_by_table.setdefault((idx["table_schema"], idx["table_name"]), []).append(idx)

        stats_by_table: dict[tuple[str, str], dict[str, Any]] = {}
        for stat in stats:
            stats_by_table[(stat["table_schema"], stat["table_name"])] = stat

        catalogue_tables = []
        for table in tables:
            key = (table["table_schema"], table["table_name"])
            catalogue_tables.append(
                {
                    "schema": table["table_schema"],
                    "name": table["table_name"],
                    "type": table["table_type"],
                    "columns": columns_by_table.get(key, []),
                    "primary_keys": [pk["column_name"] for pk in pks_by_table.get(key, [])],
                    "foreign_keys": fks_by_table.get(key, []),
                    "indexes": indexes_by_table.get(key, []),
                    "stats": stats_by_table.get(key, {}),
                }
            )

        schemas = sorted({t["schema"] for t in catalogue_tables})

        return {
            "database_version": version,
            "schemas": schemas,
            "tables": catalogue_tables,
            "relationships": fks,
            "indexes": indexes,
            "table_stats": stats,
        }
