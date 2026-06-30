"""BiasFairnessAgent — PII, bias, and toxicity checks on query + context."""

from __future__ import annotations

from talentscreen.agents.nodes._helpers import (
    last_user_message,
    mark_subgoal_done,
    merge_task_result,
)
from talentscreen.agents.state import AgentState
from talentscreen.agents.tools.guardrails import guardrails_check


def bias_fairness_node(state: AgentState) -> dict:
    query = last_user_message(state)
    checks: list[dict] = [guardrails_check.invoke({"text": query})]

    for chunk in (state.get("retrieved_context") or [])[:3]:
        text = chunk.get("text") or ""
        if text:
            checks.append(guardrails_check.invoke({"text": text[:1000]}))

    issues = [c for c in checks if not c.get("passed")]
    result = {
        "all_passed": len(issues) == 0,
        "issue_count": len(issues),
        "checks": checks,
    }
    return {
        "execution_plan": mark_subgoal_done(state, "bias_fairness"),
        "task_results": merge_task_result(state, "bias_fairness", result),
    }
