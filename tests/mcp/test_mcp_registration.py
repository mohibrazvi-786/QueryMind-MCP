"""MCP registration tests: 19 tools, 6 resources, 6 prompts."""

from __future__ import annotations

import asyncio

import pytest

# Import the server module to trigger @mcp.tool / @mcp.resource / @mcp.prompt registration.
from querymind.mcp import server  # noqa: F401
from querymind.mcp.app import mcp


@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


async def _list(kind):
    if kind == "tools":
        return await mcp.list_tools()
    if kind == "resources":
        return await mcp.list_resources()
    return await mcp.list_prompts()


def test_all_19_tools_registered(event_loop):
    tools = event_loop.run_until_complete(_list("tools"))
    names = {t.name for t in tools}
    expected = {
        "connect_database",
        "list_databases",
        "list_tables",
        "describe_table",
        "get_relationships",
        "get_database_stats",
        "generate_sql",
        "validate_sql",
        "explain_sql",
        "execute_readonly_query",
        "analyze_query_plan",
        "recommend_indexes",
        "analyze_slow_queries",
        "compare_query_performance",
        "detect_query_inefficiencies",
        "get_database_health",
        "detect_database_anomalies",
        "generate_schema_documentation",
        "search_database_knowledge",
    }
    assert names == expected, f"missing: {expected - names}, extra: {names - expected}"
    assert len(tools) == 19


def test_all_6_resources_registered(event_loop):
    resources = event_loop.run_until_complete(_list("resources"))
    names = {r.name for r in resources}
    expected = {
        "database_schema",
        "database_tables",
        "database_relationships",
        "database_health",
        "database_documentation",
        "database_metrics",
    }
    assert names == expected
    assert len(resources) == 6


def test_all_6_prompts_registered(event_loop):
    prompts = event_loop.run_until_complete(_list("prompts"))
    names = {p.name for p in prompts}
    expected = {
        "database_health_audit",
        "sql_query_optimization",
        "database_schema_explanation",
        "database_security_review",
        "slow_query_investigation",
        "database_performance_report",
    }
    assert names == expected
    assert len(prompts) == 6
