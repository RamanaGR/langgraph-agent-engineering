"""Native @tool — read-only Postgres queries with tenant RBAC."""

from __future__ import annotations

import re
from typing import Any

from langchain_core.tools import tool
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from talentscreen.config import get_settings
from talentscreen.db.session import get_session_factory
from talentscreen.utils.async_bridge import run_sync

_ALLOWED_TABLES = frozenset({"candidates", "jobs", "documents", "chunks"})
_FORBIDDEN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE|GRANT|REVOKE)\b",
    re.IGNORECASE,
)


async def _query_async(sql: str, tenant_id: str, limit: int) -> dict[str, Any]:
    cleaned = sql.strip().rstrip(";")
    if not cleaned.lower().startswith("select"):
        return {"error": "Only SELECT statements are allowed", "rows": []}
    if _FORBIDDEN.search(cleaned):
        return {"error": "Forbidden SQL keyword detected", "rows": []}

    table_match = re.search(r"\bfrom\s+([a-z_]+)", cleaned, re.IGNORECASE)
    if table_match and table_match.group(1).lower() not in _ALLOWED_TABLES:
        return {"error": f"Table not allowed: {table_match.group(1)}", "rows": []}

    if "tenant_id" not in cleaned.lower():
        return {"error": "Query must filter by tenant_id", "rows": []}
    if tenant_id not in cleaned:
        return {"error": "Query tenant_id must match session tenant", "rows": []}

    wrapped = f"SELECT * FROM ({cleaned}) AS q LIMIT {limit}"
    factory = get_session_factory()
    async with factory() as session:
        rows = await _execute_select(session, wrapped)
    return {"rows": rows, "count": len(rows)}


async def _execute_select(session: AsyncSession, sql: str) -> list[dict[str, Any]]:
    result = await session.execute(text(sql))
    columns = list(result.keys())
    return [dict(zip(columns, row, strict=True)) for row in result.fetchall()]


@tool
def postgres_query(sql: str, tenant_id: str | None = None, limit: int = 20) -> dict[str, Any]:
    """Run a read-only SQL SELECT against hiring tables (tenant-scoped)."""
    tid = tenant_id or get_settings().default_tenant_id
    return run_sync(_query_async(sql, tid, min(limit, 50)))
