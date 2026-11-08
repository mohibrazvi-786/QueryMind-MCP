"""SQL security validation using SQLGlot AST parsing.

Validates that LLM-generated or user-supplied SQL is safe for read-only
execution against a target PostgreSQL database. Never relies on keyword
matching alone — uses AST validation combined with allowlist policies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import sqlglot
from sqlglot import exp

from querymind.core.exceptions import ValidationError, SecurityError

# Statement types that are explicitly rejected for read-only execution.
DISALLOWED_STATEMENT_TYPES = {
    "insert",
    "update",
    "delete",
    "drop",
    "alter",
    "truncate",
    "create",
    "grant",
    "revoke",
    "call",
    "execute",
    "merge",
    "replace",
}

# Functions considered dangerous or disallowed in read-only analytical queries.
DISALLOWED_FUNCTIONS = {
    "pg_sleep",
    "pg_exec",
    "system",
    "execute",
    "unsafe",
    "dblink",
    "pg_read_file",
    "pg_write_file",
    "pg_ls_dir",
    "copy",
    "lo_import",
    "lo_export",
}

# System catalogs / information_schema that should not be directly queried
# through arbitrary SQL without an explicit schema allowlist.
DISALLOWED_SCHEMAS = {"pg_catalog", "information_schema", "pg_toast"}


@dataclass
class SQLValidationResult:
    """Result of SQL validation."""

    valid: bool
    statement_type: Optional[str] = None
    tables: list[str] = field(default_factory=list)
    schemas: list[str] = field(default_factory=list)
    columns: list[str] = field(default_factory=list)
    function_calls: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    ast: object = None  # sqlglot AST node


class SQLValidationService:
    """Validates SQL statements for read-only execution safety."""

    def __init__(
        self,
        *,
        allowed_schemas: Optional[set[str]] = None,
        allowed_tables: Optional[set[str]] = None,
        max_statements: int = 1,
        max_result_rows: int = 1000,
    ) -> None:
        self.allowed_schemas = allowed_schemas or set()
        self.allowed_tables = allowed_tables or set()
        self.max_statements = max_statements
        self.max_result_rows = max_result_rows

    def validate(self, sql: str) -> SQLValidationResult:
        """Validate a SQL string and return a structured result.

        Raises:
            ValidationError: if SQL cannot be parsed or fails policy.
            SecurityError: if a hard security boundary is crossed.
        """
        if not sql or not sql.strip():
            raise ValidationError("SQL statement is empty", code="empty_sql")

        result = SQLValidationResult(valid=True)

        # Parse into one or more statements.
        try:
            statements = sqlglot.parse(sql, read="postgres")
        except Exception as exc:  # noqa: BLE001
            raise ValidationError(f"SQL parse error: {exc}", code="parse_error") from exc

        if not statements:
            raise ValidationError("No SQL statements found", code="no_statements")

        if len(statements) > self.max_statements:
            raise SecurityError(
                f"Multiple statements not allowed ({len(statements)} found, max {self.max_statements})",
                code="multi_statement",
            )

        statement = statements[0]
        result.ast = statement

        # Only SELECT statements are allowed; reject everything else (including
        # unknown statement types) so we never accidentally permit DDL/DML.
        if not isinstance(statement, exp.Select):
            stmt_type = self._statement_type(statement)
            result.statement_type = stmt_type
            raise SecurityError(
                f"Only SELECT statements are allowed, got: {stmt_type or 'unknown'}",
                code="non_select",
            )

        result.statement_type = "select"

        # Collect referenced tables, schemas, columns, functions.
        self._collect_references(statement, result)

        # Validate schemas against allowlist.
        for schema in result.schemas:
            if schema in DISALLOWED_SCHEMAS:
                raise SecurityError(
                    f"Access to system schema '{schema}' is disallowed",
                    code="disallowed_schema",
                )
            if self.allowed_schemas and schema not in self.allowed_schemas:
                raise SecurityError(
                    f"Schema '{schema}' is not in the allowlist",
                    code="schema_not_allowed",
                )

        # Validate tables against allowlist.
        for table in result.tables:
            if self.allowed_tables and table not in self.allowed_tables:
                raise SecurityError(
                    f"Table '{table}' is not in the allowlist", code="table_not_allowed"
                )

        # Validate functions.
        for func in result.function_calls:
            if func.lower() in DISALLOWED_FUNCTIONS:
                raise SecurityError(
                    f"Disallowed function: {func}", code="disallowed_function"
                )

        # Reject LIMIT-less exploratory queries? (policy decision — warn only)
        # Keep as observation, not hard rejection, to avoid false positives.

        return result

    @staticmethod
    def _statement_type(statement: exp.Expression) -> Optional[str]:
        # sqlglot represents statements as Select, Insert, etc.
        type_map = {
            exp.Select: "select",
            exp.Insert: "insert",
            exp.Update: "update",
            exp.Delete: "delete",
            exp.Drop: "drop",
            exp.Alter: "alter",
            exp.Create: "create",
            exp.Merge: "merge",
        }
        # Truncate may not exist in all sqlglot versions; handle defensively.
        truncate_cls = getattr(exp, "Truncate", None)
        if truncate_cls is not None:
            type_map[truncate_cls] = "truncate"
        for klass, name in type_map.items():
            if isinstance(statement, klass):
                return name
        return None

    def _collect_references(
        self, statement: exp.Expression, result: SQLValidationResult
    ) -> None:
        # Tables.
        for table in statement.find_all(exp.Table):
            result.tables.append(table.name)
            if table.db:
                result.schemas.append(table.db)

        # Columns.
        for column in statement.find_all(exp.Column):
            result.columns.append(column.name)
            if column.table:
                # table-qualified column
                pass

        # Functions.
        for func in statement.find_all(exp.Func):
            result.function_calls.append(func.name)


def validate_readonly_sql(
    sql: str,
    *,
    allowed_schemas: Optional[set[str]] = None,
    allowed_tables: Optional[set[str]] = None,
) -> SQLValidationResult:
    """Convenience: validate SQL as read-only with default policies."""
    service = SQLValidationService(
        allowed_schemas=allowed_schemas,
        allowed_tables=allowed_tables,
        max_statements=1,
    )
    return service.validate(sql)
