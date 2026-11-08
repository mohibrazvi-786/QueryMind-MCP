"""MCP Prompts — 6 structured analysis prompts.

Each prompt defines arguments, references the appropriate QueryMind
tools/resources, and gives evidence-oriented instructions.
"""

from __future__ import annotations

from querymind.mcp.app import mcp


@mcp.prompt()
def database_health_audit(connection_id: str = "default") -> str:
    """Audit database health and produce a prioritized findings list.

    Arguments:
    - connection_id: the registered target database connection.
    """
    return f"""
You are performing a database health audit for connection '{connection_id}'.

Steps:
1. Call get_database_health with connection_id='{connection_id}'.
2. Read the querymind://database/health resource for current metrics.
3. For each metric marked warn or critical, record the value, threshold, and warning.
4. Check querymind://database/metrics for table sizes and row estimates.
5. Produce a report with: overall status, per-metric status, warnings, and recommended actions.
6. Clearly mark any metrics that are unavailable (do not invent values).

Output format: Markdown with sections — Overall Status, Metrics, Warnings, Recommendations, Limitations.
"""


@mcp.prompt()
def sql_query_optimization(connection_id: str = "default", sql: str = "") -> str:
    """Optimize a SQL query using plan analysis and index recommendations.

    Arguments:
    - connection_id: the registered target database connection.
    - sql: the SELECT statement to optimize.
    """
    return f"""
You are optimizing a SQL query on connection '{connection_id}'.

SQL to optimize:
{{sql}}

Steps:
1. Call validate_sql with connection_id='{connection_id}' and sql='{{sql}}'. If invalid, stop and report the rejection reason.
2. Call explain_sql with connection_id='{connection_id}' and sql='{{sql}}'. Review the plan tree, costs, and findings.
3. Call detect_query_inefficiencies with connection_id='{connection_id}' and sql='{{sql}}'.
4. Based on plan findings (sequential scans, sorts, nested loops), call recommend_indexes for the relevant tables.
5. Produce a Markdown report: original SQL, plan evidence, bottlenecks, index recommendations (proposed SQL only — no DDL executed), trade-offs, and confidence levels.
6. Never claim an optimization improves performance unless measured.
"""


@mcp.prompt()
def database_schema_explanation(connection_id: str = "default", table: str = "") -> str:
    """Explain a database schema in plain language.

    Arguments:
    - connection_id: the registered target database connection.
    - table: optional table name to focus on.
    """
    return f"""
You are explaining a database schema on connection '{connection_id}'.

Steps:
1. Call list_tables with connection_id='{connection_id}' to inventory tables.
2. {'Call describe_table with connection_id=\'{connection_id}\', schema=\'public\', table=\'{table}\'.' if table else 'For each table, call describe_table to get columns, keys, and indexes.'}
3. Call get_relationships with connection_id='{connection_id}' to understand foreign-key relationships.
4. Read the querymind://database/schema resource for the full catalogue.
5. Produce a plain-language explanation: what each table represents, key columns, relationships, and indexes.
6. Clearly distinguish verified metadata (from the database) from any inferred descriptions.
"""


@mcp.prompt()
def database_security_review(connection_id: str = "default") -> str:
    """Review database access security and configuration.

    Arguments:
    - connection_id: the registered target database connection.
    """
    return f"""
You are performing a security review of connection '{connection_id}'.

Steps:
1. Confirm the connection is read-only (connect_database result shows read_only: true).
2. Review get_database_health for high connection counts or warnings.
3. Verify no DDL/DML tools are available — only SELECT is permitted.
4. Confirm statement timeouts and result limits are enforced.
5. Review audit logs for rejected operations (cross-tenant, disallowed statements).
6. Produce a report: access mode, timeout/limit configuration, rejected operations, and remaining risks.
"""


@mcp.prompt()
def slow_query_investigation(connection_id: str = "default", query: str = "") -> str:
    """Investigate a slow query using execution-plan evidence.

    Arguments:
    - connection_id: the registered target database connection.
    - query: the slow query to investigate.
    """
    return f"""
You are investigating a slow query on connection '{connection_id}'.

Query:
{{query}}

Steps:
1. Call validate_sql to confirm the query is read-only and single-statement.
2. Call explain_sql to retrieve the EXPLAIN (FORMAT JSON) plan. Do NOT use EXPLAIN ANALYZE unless explicitly authorized on a controlled target.
3. Call detect_query_inefficiencies to find static issues (SELECT *, missing LIMIT, leading wildcards, etc.).
4. Call analyze_slow_queries to see if the query appears in pg_stat_statements (if available).
5. Based on plan findings, call recommend_indexes for the relevant tables.
6. Produce an evidence-based report: execution time evidence (if available), bottlenecks, existing indexes, recommendations, and confidence levels.
7. Do not claim improvement without measured evidence.
"""


@mcp.prompt()
def database_performance_report(connection_id: str = "default") -> str:
    """Generate a complete database performance report.

    Arguments:
    - connection_id: the registered target database connection.
    """
    return f"""
You are generating a database performance report for connection '{connection_id}'.

Steps:
1. Call get_database_health with connection_id='{connection_id}'.
2. Call analyze_slow_queries with connection_id='{connection_id}' to rank expensive queries.
3. For the top slow queries, call explain_sql and detect_query_inefficiencies.
4. Call recommend_indexes for tables involved in the slowest queries.
5. Read querymind://database/metrics for table sizes and row estimates.
6. Compile a Markdown report: database overview, slow-query summary, plan findings, index recommendations, inefficiencies, risk/trade-off analysis, prioritized action list, and data limitations.
7. Mark unavailable statistics clearly; do not fabricate measurements.
"""
