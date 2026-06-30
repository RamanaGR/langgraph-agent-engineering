"""Shared helpers for agent nodes."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from talentscreen.agents.state import AgentState, SubGoal


def last_user_message(state: AgentState) -> str:
    messages = state.get("messages") or []
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            return str(msg.content)
        if isinstance(msg, dict) and msg.get("role") == "user":
            return str(msg.get("content", ""))
    return state.get("user_query") or ""


def mark_subgoal_done(state: AgentState, agent_name: str) -> list[SubGoal]:
    plan: list[SubGoal] = []
    for goal in state.get("execution_plan") or []:
        updated = dict(goal)
        if goal["agent"] == agent_name:
            updated["status"] = "done"
        plan.append(updated)  # type: ignore[arg-type]
    return plan


def merge_task_result(state: AgentState, agent_name: str, result: dict[str, Any]) -> dict[str, Any]:
    task_results = dict(state.get("task_results") or {})
    task_results[agent_name] = result
    return task_results


HIRING_KEYWORDS = (
    "candidate",
    "resume",
    "hire",
    "job",
    "interview",
    "skill",
    "java",
    "aws",
    "fit",
    "match",
    "recruit",
)

POLICY_KEYWORDS = ("policy", "compliance", "gdpr", "eeo", "diversity")
SCHEDULING_KEYWORDS = ("schedule", "calendar", "meeting", "interview time", "slot")


def classify_intent_rules(text: str) -> str:
    lowered = text.lower()
    if any(k in lowered for k in SCHEDULING_KEYWORDS):
        return "scheduling"
    if any(k in lowered for k in POLICY_KEYWORDS):
        return "policy"
    if any(k in lowered for k in HIRING_KEYWORDS):
        return "hiring"
    if len(lowered.split()) < 3:
        return "out_of_scope"
    return "hiring"


def message_count(state: AgentState) -> int:
    return len(state.get("messages") or [])


def append_ai_message(content: str) -> dict[str, list[BaseMessage]]:
    return {"messages": [AIMessage(content=content)]}
