"""Dispatch — route to next pending agent in execution plan."""

from __future__ import annotations

from talentscreen.agents.state import AgentState


def dispatch_route(state: AgentState) -> str:
    intent = state.get("intent")
    if intent == "out_of_scope":
        return "reject"

    for goal in state.get("execution_plan") or []:
        if goal.get("status") == "pending":
            return goal["agent"]
    return "aggregate"


def reject_node(state: AgentState) -> dict:
    msg = (
        "I can help with hiring, policy, and scheduling questions about candidates and roles. "
        "Please rephrase your request."
    )
    return {
        "final_response": msg,
        "messages": [{"role": "assistant", "content": msg}],
        "requires_hitl": False,
    }
