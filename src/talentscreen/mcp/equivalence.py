"""MCP equivalence checks — native @tool vs MCP wrapper."""

from __future__ import annotations

from typing import Any

from talentscreen.agents.tools.postgres import postgres_query
from talentscreen.agents.tools.rag import rag_retrieve
from talentscreen.mcp.wrappers import mcp_postgres_query, mcp_rag_retrieve


def _compare(label: str, native: dict[str, Any], wrapped: dict[str, Any]) -> dict[str, Any]:
    match = native == wrapped
    return {
        "tool": label,
        "equivalent": match,
        "native_keys": sorted(native.keys()),
        "wrapped_keys": sorted(wrapped.keys()),
    }


def run_equivalence_checks(
    *,
    rag_query: str = "Who has Java experience?",
    tenant_id: str = "demo-tenant",
) -> dict[str, Any]:
    """Compare in-process @tool output to MCP wrapper output (same code path as MCP servers)."""
    results: list[dict[str, Any]] = []

    pg_sql = f"SELECT filename, doc_type FROM documents WHERE tenant_id = '{tenant_id}' LIMIT 3"
    native_pg = postgres_query.invoke({"sql": pg_sql, "tenant_id": tenant_id, "limit": 3})
    wrapped_pg = mcp_postgres_query(sql=pg_sql, tenant_id=tenant_id, limit=3)
    results.append(_compare("postgres_query", native_pg, wrapped_pg))

    blocked_sql = "DELETE FROM candidates WHERE tenant_id = 'demo-tenant'"
    native_block = postgres_query.invoke({"sql": blocked_sql, "tenant_id": tenant_id})
    wrapped_block = mcp_postgres_query(sql=blocked_sql, tenant_id=tenant_id)
    results.append(_compare("postgres_query_blocked", native_block, wrapped_block))

    try:
        native_rag = rag_retrieve.invoke(
            {
                "query": rag_query,
                "tenant_id": tenant_id,
                "top_k": 3,
                "retrieval_mode": "hybrid",
            }
        )
        wrapped_rag = mcp_rag_retrieve(
            query=rag_query,
            tenant_id=tenant_id,
            top_k=3,
            retrieval_mode="hybrid",
        )
        native_trimmed = {
            "query": native_rag.get("query"),
            "hit_count": len(native_rag.get("hits") or []),
            "rewritten_queries": native_rag.get("rewritten_queries"),
            "retrieval_mode": native_rag.get("retrieval_mode"),
        }
        wrapped_trimmed = {
            "query": wrapped_rag.get("query"),
            "hit_count": len(wrapped_rag.get("hits") or []),
            "rewritten_queries": wrapped_rag.get("rewritten_queries"),
            "retrieval_mode": wrapped_rag.get("retrieval_mode"),
        }
        rag_equiv = native_trimmed == wrapped_trimmed
        results.append(
            {
                "tool": "rag_retrieve",
                "equivalent": rag_equiv,
                "native": native_trimmed,
                "wrapped": wrapped_trimmed,
            }
        )
    except Exception as exc:
        results.append(
            {
                "tool": "rag_retrieve",
                "equivalent": None,
                "skipped": True,
                "reason": str(exc),
            }
        )

    passed = all(r.get("equivalent") is True for r in results if not r.get("skipped"))
    return {"passed": passed, "checks": results}
