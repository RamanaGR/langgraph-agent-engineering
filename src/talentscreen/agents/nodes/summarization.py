"""SummarizationNode — compress dialogue when history exceeds threshold."""

from __future__ import annotations

from langchain_core.messages import HumanMessage

from talentscreen.agents.nodes._helpers import last_user_message
from talentscreen.agents.state import AgentState
from talentscreen.config import get_settings
from talentscreen.generation.llm.provider import get_llm_provider


def _format_history(state: AgentState) -> str:
    lines: list[str] = []
    for msg in state.get("messages") or []:
        if isinstance(msg, HumanMessage):
            lines.append(f"User: {msg.content}")
        elif hasattr(msg, "content"):
            role = getattr(msg, "type", "ai")
            lines.append(f"{role}: {msg.content}")
    return "\n".join(lines[-20:])


def summarization_node(state: AgentState) -> dict:
    history = _format_history(state)
    llm = get_llm_provider()
    response = llm.invoke(
        [
            {
                "role": "system",
                "content": "Summarize this recruiter conversation in 3-5 bullet points.",
            },
            {"role": "user", "content": history},
        ]
    )
    summary = response.content.strip()
    return {
        "summary": summary,
        "user_query": last_user_message(state),
    }


def should_summarize(state: AgentState) -> str:
    threshold = get_settings().summarization_message_threshold
    if len(state.get("messages") or []) > threshold:
        return "summarize"
    return "skip"
