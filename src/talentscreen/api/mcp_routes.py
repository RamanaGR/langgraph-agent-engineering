"""MCP demo and equivalence API routes."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter

from talentscreen.mcp.equivalence import run_equivalence_checks

router = APIRouter(prefix="/mcp", tags=["mcp"])


@router.get("/equivalence")
async def mcp_equivalence() -> dict:
    """Compare native @tool output vs MCP wrapper (Phase 2b demo)."""
    return await asyncio.to_thread(run_equivalence_checks)
