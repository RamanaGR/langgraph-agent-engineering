"""FastAPI routes for LangGraph multi-agent chat."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from talentscreen.agents.pending_store import list_pending, register_pending, remove_pending
from talentscreen.agents.service import resume_agent_thread, run_agent_chat
from talentscreen.api.auth import AuthContext, require_recruiter
from talentscreen.config import get_settings
from talentscreen.guardrails.injection import assert_safe_prompt

router = APIRouter(prefix="/agents", tags=["agents"])


class AgentChatRequest(BaseModel):
    message: str
    thread_id: str | None = None
    tenant_id: str = Field(default_factory=lambda: get_settings().default_tenant_id)


class AgentChatResponse(BaseModel):
    thread_id: str
    response: str | None
    intent: str | None
    rewritten_queries: list[str] | None = None
    retrieved_context: list[dict] | None = None
    task_results: dict | None = None
    requires_hitl: bool = False
    pending_approval: dict | None = None
    interrupted: bool = False


class AgentResumeRequest(BaseModel):
    action: str = "approve"


class AgentResumeResponse(BaseModel):
    thread_id: str
    status: str
    response: str | None = None
    interrupted: bool = False


class PendingApproval(BaseModel):
    thread_id: str
    tenant_id: str
    pending_approval: dict
    preview: str | None = None
    created_at: str | None = None


@router.post("/chat", response_model=AgentChatResponse)
async def agent_chat(
    body: AgentChatRequest,
    auth: AuthContext = Depends(require_recruiter),
) -> AgentChatResponse:
    if not body.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    try:
        assert_safe_prompt(body.message)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    try:
        result = await asyncio.to_thread(
            run_agent_chat,
            message=body.message,
            thread_id=body.thread_id,
            tenant_id=body.tenant_id or auth.tenant_id,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={"error": "agent_unavailable", "message": str(exc)},
        ) from exc
    if result.get("interrupted") and result.get("pending_approval"):
        register_pending(
            thread_id=result["thread_id"],
            pending_approval=result["pending_approval"],
            tenant_id=body.tenant_id or auth.tenant_id,
            preview=result.get("response"),
        )
    return AgentChatResponse(**result)


@router.get("/pending", response_model=list[PendingApproval])
async def list_pending_approvals(
    auth: AuthContext = Depends(require_recruiter),
) -> list[PendingApproval]:
    items = list_pending(tenant_id=auth.tenant_id)
    return [PendingApproval(**item) for item in items]


@router.post("/resume/{thread_id}", response_model=AgentResumeResponse)
async def agent_resume(
    thread_id: str,
    body: AgentResumeRequest,
    auth: AuthContext = Depends(require_recruiter),
) -> AgentResumeResponse:
    if body.action not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail="action must be approve or reject")
    try:
        result = await asyncio.to_thread(
            resume_agent_thread,
            thread_id=thread_id,
            action=body.action,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={"error": "resume_failed", "message": str(exc)},
        ) from exc
    remove_pending(thread_id)
    return AgentResumeResponse(**result)
