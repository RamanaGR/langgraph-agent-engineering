"""HITL gate — dynamic interrupt for recruiter approval."""

from __future__ import annotations

from langchain_core.messages import AIMessage
from langgraph.types import interrupt

from talentscreen.agents.state import AgentState


def hitl_gate_node(state: AgentState) -> dict:
    if state.get("requires_hitl") and state.get("pending_approval"):
        decision = interrupt(
            {
                "action": "review_required",
                "pending_approval": state.get("pending_approval"),
            }
        )
        if isinstance(decision, dict) and decision.get("action") == "reject":
            msg = "Recommendation rejected by recruiter."
            return {"final_response": msg, "messages": [AIMessage(content=msg)]}

    final = state.get("final_response") or ""
    return {"messages": [AIMessage(content=final)]}
