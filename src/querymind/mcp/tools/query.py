"""MCP tools — SQL intelligence (5 tools).

Group B: generate_sql, validate_sql, explain_sql, execute_readonly_query,
analyze_query_plan.
"""

from __future__ import annotations

from typing import Optional

from querymind.core.exceptions import DatabaseError, NotFoundError, ValidationError
from querymind.core.rbac import (
    PERMISSION_SQL_EXECUTE_READONLY,
    PERMISSION_SQL_EXPLAIN,
    PERMISSION_SQL_GENERATE,
    PERMISSION_SQL_VALIDATE,
)
from querymind.database.connection import TargetConnection
from querymind.intelligence.llm.provider import MockLLMProvider
from querymind.mcp.app import connection_registry, mcp
from querymind.mcp.authz import authorize
from querymind.services.discovery_service import DiscoveryService
from querymind.services.performance_service import PerformanceService
from querymind.services.sql_generation_service import SQLGenerationService
from querymind.services.sql_validation_service import SQLValidationService, validate_readonly_sql

# Service instances wired per connection. Created lazily.
_validation_service = SQLValidationService()
_generation_service: Optional[SQLGenerationService] = None


def _get_connection(connection_id: str) -> TargetConnection:
    conn = connection_registry.get(connection_id)
    if conn is None:
        raise NotFoundError(f"Connection '{connection_id}' not registered", code="connection_not_found")
    return conn


def _generation_service(connection_id: str) -> SQLGenerationService:
    global _generation_service
    if _generation_service is None:
        conn = _get_connection(connection_id)
        discovery = DiscoveryService(conn)
        _generation_service = SQLGenerationService(
            llm_provider=MockLLMProvider(),
            discovery_service=discovery,
            validation_service=_validation_service,
        )
    return _generation_service


@mcp.tool()
def generate_sql(
    connection_id: str,
    question: str,
    *,
    allowed_schema: Optional[str] = None,
    access_token: Optional[str] = None,
) -> dict:
    """Generate PostgreSQL SQL from a natural-language question.

    The generated SQL is NOT executed. It is returned for validation and,
    optionally, read-only execution via execute_readonly_query.
    """
    authorize(
        access_token=access_token,
        permission=PERMISSION_SQL_GENERATE,
        connection_id=connection_id,
    )
    svc = _generation_service(connection_id)
    allowed_schemas = {allowed_schema} if allowed_schema else None
    try:
        result = svc.generate(question, allowed_schemas=allowed_schemas, validate=False)
    except Exception as exc:  # noqa: BLE001
        raise DatabaseError(f"SQL generation failed: {exc}", code="generation_failed") from exc

    return {
        "connection_id": connection_id,
        "question": result.question,
        "sql": result.sql,
        "explanation": result.explanation,
        "referenced_tables": result.referenced_tables,
        "referenced_columns": result.referenced_columns,
        "assumptions": result.assumptions,
        "confidence": result.confidence,
        "executed": False,
    }


@mcp.tool()
def validate_sql(
    connection_id: str,
    sql: str,
    *,
    allowed_schema: Optional[str] = None,
    access_token: Optional[str] = None,
) -> dict:
    """Validate SQL syntax and security using SQLGlot AST parsing.

    Rejects INSERT/UPDATE/DELETE/DROP/ALTER/TRUNCATE/CREATE/GRANT/REVOKE,
    multi-statement, disallowed functions, and non-allowlisted relations.
    """
    authorize(
        access_token=access_token,
        permission=PERMISSION_SQL_VALIDATE,
        connection_id=connection_id,
    )
    allowed_schemas = {allowed_schema} if allowed_schema else None
    try:
        result = _validation_service.validate(
            sql, allowed_schemas=allowed_schemas
        )
    except Exception as exc:
        # Validation failures (SecurityError/ValidationError) are expected
        # outcomes — return them as invalid rather than crashing.
        from querymind.core.exceptions import QueryMindError

        if isinstance(exc, QueryMindError):
            return {
                "connection_id": connection_id,
                "sql": sql,
                "valid": False,
                "error": exc.message,
                "code": exc.code,
            }
        raise DatabaseError(f"Validation error: {exc}", code="validation_error") from exc

    return {
        "connection_id": connection_id,
        "sql": sql,
        "valid": True,
        "statement_type": result.statement_type,
        "tables": result.tables,
        "schemas": result.schemas,
        "columns": result.columns,
        "function_calls": result.function_calls,
    }


@mcp.tool()
def explain_sql(
    connection_id: str,
    sql: str,
    *,
    access_token: Optional[str] = None,
) -> dict:
    """Return a safe EXPLAIN (FORMAT JSON) plan for a read-only statement.

    Does NOT use EXPLAIN ANALYZE (which executes the query).
    """
    authorize(
        access_token=access_token,
        permission=PERMISSION_SQL_EXPLAIN,
        connection_id=connection_id,
    )
    conn = _get_connection(connection_id)
    svc = PerformanceService(connection=conn, discovery_service=DiscoveryService(conn))
    try:
        return svc.analyze_query_plan(sql)
    except Exception as exc:  # noqa: BLE001
        raise DatabaseError(f"EXPLAIN failed: {exc}", code="explain_failed") from exc


@mcp.tool()
def execute_readonly_query(
    connection_id: str,
    sql: str,
    *,
    max_rows: Optional[int] = None,
    access_token: Optional[str] = None,
) -> dict:
    """Execute a single validated read-only SELECT statement.

    The SQL must already pass validate_sql. Enforces statement timeout,
    result row limit, and read-only transaction. Audit-logged.
    """
    authorize(
        access_token=access_token,
        permission=PERMISSION_SQL_EXECUTE_READONLY,
        connection_id=connection_id,
    )
    conn = _get_connection(connection_id)

    # Re-validate at execution time — never trust caller.
    try:
        validate_readonly_sql(sql)
    except Exception as exc:
        from querymind.core.exceptions import QueryMindError

        if isinstance(exc, QueryMindError):
            return {
                "connection_id": connection_id,
                "sql": sql,
                "executed": False,
                "rejected": True,
                "error": exc.message,
                "code": exc.code,
            }
        raise DatabaseError(f"Execution validation failed: {exc}", code="execution_validation_failed") from exc

    try:
        rows = conn.execute(sql)
    except Exception as exc:  # noqa: BLE001
        raise DatabaseError(f"Query execution failed: {exc}", code="execution_failed") from exc

    limit = max_rows if max_rows is not None else conn.max_result_rows
    truncated = len(rows) > limit
    rows = rows[:limit]

    return {
        "connection_id": connection_id,
        "sql": sql,
        "executed": True,
        "row_count": len(rows),
        "truncated": truncated,
        "limit": limit,
        "rows": rows,
    }


@mcp.tool()
def analyze_query_plan(
    connection_id: str,
    sql: str,
    *,
    access_token: Optional[str] = None,
) -> dict:
    """Analyze an EXPLAIN plan for a statement and return evidence-based findings."""
    authorize(
        access_token=access_token,
        permission=PERMISSION_SQL_EXPLAIN,
        connection_id=connection_id,
    )
    conn = _get_connection(connection_id)
    svc = PerformanceService(connection=conn, discovery_service=DiscoveryService(conn))
    try:
        return svc.analyze_query_plan(sql)
    except Exception as exc:  # noqa: BLE001
        raise DatabaseError(f"Plan analysis failed: {exc}", code="plan_analysis_failed") from exc
