"""ConversationManagerAgent — clarifying questions and dialogue continuity."""

from __future__ import annotations

from talentscreen.agents.nodes._helpers import (
    last_user_message,
    mark_subgoal_done,
    merge_task_result,
)
from talentscreen.agents.state import AgentState


def conversation_manager_node(state: AgentState) -> dict:
    query = last_user_message(state)
    clarifying: list[str] = []

    if len(query.split()) < 6:
        clarifying.append("Which role or job title are you hiring for?")
    if "candidate" not in query.lower() and "who" not in query.lower():
        clarifying.append("Are you comparing specific candidates or searching the full pool?")
    if state.get("summary"):
        clarifying.append("Should I factor in the conversation summary above?")

    result = {
        "clarifying_questions": clarifying[:2],
        "thread_context": {
            "summary": state.get("summary"),
            "intent": state.get("intent"),
            "message_count": len(state.get("messages") or []),
        },
    }
    return {
        "execution_plan": mark_subgoal_done(state, "conversation_manager"),
        "task_results": merge_task_result(state, "conversation_manager", result),
    }
