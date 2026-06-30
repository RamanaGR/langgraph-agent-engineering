"""MCP postgres-server — wraps agents.tools.postgres.postgres_query."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from talentscreen.mcp.wrappers import mcp_postgres_query

mcp = FastMCP(
    "talentscreen-postgres",
    instructions="Read-only, tenant-scoped SQL over hiring tables (RBAC enforced).",
)


@mcp.tool()
def postgres_query(
    sql: str,
    tenant_id: str = "demo-tenant",
    limit: int = 20,
) -> dict:
    """Run a read-only SELECT against candidates, jobs, documents, or chunks."""
    return mcp_postgres_query(sql=sql, tenant_id=tenant_id, limit=limit)


def main() -> None:
    mcp.run()
