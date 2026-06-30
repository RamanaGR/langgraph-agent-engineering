"""LangGraph AgentState — single blackboard for multi-agent hiring workflow."""

from __future__ import annotations

from typing import Annotated, Any, TypedDict

from langgraph.graph.message import add_messages


class SubGoal(TypedDict):
    agent: str
    status: str
    description: str


class ChunkRef(TypedDict, total=False):
    chunk_id: str
    document_id: str
    doc_type: str
    filename: str
    text: str
    score: float


class AgentState(TypedDict, total=False):
    messages: Annotated[list, add_messages]
    intent: str
    execution_plan: list[SubGoal]
    task_results: dict[str, Any]
    retrieved_context: list[ChunkRef]
    rewritten_queries: list[str]
    summary: str | None
    candidate_id: str | None
    job_id: str | None
    pending_approval: dict[str, Any] | None
    tenant_id: str
    final_response: str | None
    requires_hitl: bool
    user_query: str
