"""Native @tool — hybrid RAG retrieval (wraps Phase 1b pipeline)."""

from __future__ import annotations

from typing import Any

from langchain_core.tools import tool

from talentscreen.config import get_settings
from talentscreen.db.session import get_session_factory
from talentscreen.retrieval.pipeline import run_query_pipeline
from talentscreen.utils.async_bridge import run_sync


async def _retrieve_async(
    query: str,
    tenant_id: str,
    top_k: int,
    retrieval_mode: str,
) -> dict[str, Any]:
    factory = get_session_factory()
    async with factory() as session:
        return await run_query_pipeline(
            session,
            query=query,
            tenant_id=tenant_id,
            top_k=top_k,
            generate_answer_flag=False,
            use_cache=True,
            retrieval_mode=retrieval_mode if retrieval_mode in ("hybrid", "dense") else "hybrid",
        )


@tool
def rag_retrieve(
    query: str,
    tenant_id: str | None = None,
    top_k: int = 5,
    retrieval_mode: str = "hybrid",
) -> dict[str, Any]:
    """Retrieve relevant resume, JD, and interview-note chunks via hybrid RAG."""
    tid = tenant_id or get_settings().default_tenant_id
    return run_sync(_retrieve_async(query, tid, top_k, retrieval_mode))
