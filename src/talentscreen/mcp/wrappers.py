"""Thin MCP delegates — zero logic duplication over native @tool functions."""

from __future__ import annotations

from typing import Any

from talentscreen.agents.tools.postgres import postgres_query
from talentscreen.agents.tools.rag import rag_retrieve


def mcp_rag_retrieve(
    query: str,
    tenant_id: str | None = None,
    top_k: int = 5,
    retrieval_mode: str = "hybrid",
) -> dict[str, Any]:
    """MCP-exposed RAG retrieve — delegates to native rag_retrieve @tool."""
    return rag_retrieve.invoke(
        {
            "query": query,
            "tenant_id": tenant_id,
            "top_k": top_k,
            "retrieval_mode": retrieval_mode,
        }
    )


def mcp_postgres_query(
    sql: str,
    tenant_id: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """MCP-exposed Postgres query — delegates to native postgres_query @tool."""
    return postgres_query.invoke(
        {
            "sql": sql,
            "tenant_id": tenant_id,
            "limit": limit,
        }
    )
