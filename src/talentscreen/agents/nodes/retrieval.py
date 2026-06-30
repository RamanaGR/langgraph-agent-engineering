"""RetrievalAgent — LLM rewrite + hybrid RAG + context packaging."""

from __future__ import annotations

from talentscreen.agents.nodes._helpers import (
    last_user_message,
    mark_subgoal_done,
    merge_task_result,
)
from talentscreen.agents.state import AgentState, ChunkRef
from talentscreen.agents.tools.rag import rag_retrieve


def retrieval_node(state: AgentState) -> dict:
    query = last_user_message(state)
    tenant_id = state.get("tenant_id") or "demo-tenant"
    raw = rag_retrieve.invoke(
        {
            "query": query,
            "tenant_id": tenant_id,
            "top_k": 5,
            "retrieval_mode": "hybrid",
        }
    )

    chunks: list[ChunkRef] = []
    for hit in raw.get("hits") or []:
        chunks.append(
            ChunkRef(
                chunk_id=hit.get("chunk_id", ""),
                document_id=hit.get("document_id", ""),
                doc_type=hit.get("doc_type", ""),
                filename=hit.get("filename"),
                text=hit.get("text", ""),
                score=float(hit.get("score", 0)),
            )
        )

    result = {
        "hit_count": len(chunks),
        "rewritten_queries": raw.get("rewritten_queries") or [],
        "retrieval_mode": raw.get("retrieval_mode"),
    }
    return {
        "retrieved_context": chunks,
        "rewritten_queries": raw.get("rewritten_queries") or [],
        "execution_plan": mark_subgoal_done(state, "retrieval"),
        "task_results": merge_task_result(state, "retrieval", result),
    }
