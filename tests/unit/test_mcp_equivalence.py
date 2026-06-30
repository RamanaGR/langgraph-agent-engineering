"""MCP equivalence — native @tool vs thin MCP wrappers."""

from talentscreen.agents.tools.postgres import postgres_query
from talentscreen.mcp.equivalence import run_equivalence_checks
from talentscreen.mcp.wrappers import mcp_postgres_query


def test_postgres_wrapper_matches_native_block() -> None:
    sql = "INSERT INTO candidates (full_name) VALUES ('bad')"
    native = postgres_query.invoke({"sql": sql, "tenant_id": "demo-tenant"})
    wrapped = mcp_postgres_query(sql=sql, tenant_id="demo-tenant")
    assert native == wrapped
    assert "error" in native


def test_postgres_wrapper_matches_native_select() -> None:
    import pytest

    sql = "SELECT filename FROM documents WHERE tenant_id = 'demo-tenant' LIMIT 1"
    try:
        native = postgres_query.invoke({"sql": sql, "tenant_id": "demo-tenant", "limit": 1})
        wrapped = mcp_postgres_query(sql=sql, tenant_id="demo-tenant", limit=1)
    except Exception as exc:
        pytest.skip(f"Postgres not available: {exc}")
    assert native == wrapped


def test_equivalence_report_structure() -> None:
    report = run_equivalence_checks()
    assert "passed" in report
    assert "checks" in report
    assert len(report["checks"]) >= 2
