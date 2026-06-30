"""Agent graph runtime — checkpointer setup and invoke helpers."""

from __future__ import annotations

import uuid
from functools import lru_cache
from typing import Any

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from talentscreen.agents.graph import build_agent_graph
from talentscreen.config import get_settings

_graph = None
_checkpointer_ctx = None


def _sync_postgres_url() -> str:
    url = get_settings().database_url
    return url.replace("postgresql+asyncpg://", "postgresql://")


@lru_cache(maxsize=1)
def get_agent_graph():
    global _graph, _checkpointer_ctx
    if _graph is not None:
        return _graph

    settings = get_settings()
    if settings.agent_checkpointer == "postgres":
        try:
            from langgraph.checkpoint.postgres import PostgresSaver

            _checkpointer_ctx = PostgresSaver.from_conn_string(_sync_postgres_url())
            checkpointer = _checkpointer_ctx.__enter__()
            checkpointer.setup()
            _graph = build_agent_graph(checkpointer=checkpointer)
            return _graph
        except Exception:
            pass

    _graph = build_agent_graph(checkpointer=MemorySaver())
    return _graph


def run_agent_chat(
    *,
    message: str,
    thread_id: str | None = None,
    tenant_id: str | None = None,
) -> dict[str, Any]:
    graph = get_agent_graph()
    tid = thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": tid}}
    tenant = tenant_id or get_settings().default_tenant_id

    result = graph.invoke(
        {
            "messages": [HumanMessage(content=message)],
            "tenant_id": tenant,
            "user_query": message,
        },
        config=config,
    )

    interrupted = bool(graph.get_state(config).next)
    return {
        "thread_id": tid,
        "response": result.get("final_response"),
        "intent": result.get("intent"),
        "rewritten_queries": result.get("rewritten_queries"),
        "retrieved_context": result.get("retrieved_context"),
        "task_results": result.get("task_results"),
        "requires_hitl": result.get("requires_hitl"),
        "pending_approval": result.get("pending_approval"),
        "interrupted": interrupted,
    }


def resume_agent_thread(
    *,
    thread_id: str,
    action: str = "approve",
) -> dict[str, Any]:
    graph = get_agent_graph()
    config = {"configurable": {"thread_id": thread_id}}

    if action == "reject":
        graph.invoke(
            Command(resume={"action": "reject", "approved": False}),
            config=config,
        )
        return {
            "thread_id": thread_id,
            "status": "rejected",
            "response": "Recommendation rejected by recruiter.",
        }

    result = graph.invoke(Command(resume={"action": "approve", "approved": True}), config=config)
    return {
        "thread_id": thread_id,
        "status": "approved",
        "response": result.get("final_response"),
        "interrupted": bool(graph.get_state(config).next),
    }
