"""OrchestratorAgent — build execution plan and aggregate agent outputs."""

from __future__ import annotations

import json

from talentscreen.agents.nodes._helpers import last_user_message
from talentscreen.agents.state import AgentState, SubGoal
from talentscreen.generation.llm.provider import get_llm_provider

_PLANS: dict[str, list[tuple[str, str]]] = {
    "hiring": [
        ("retrieval", "Retrieve relevant resumes, JDs, and interview notes"),
        ("resume_analysis", "Normalize skills and compare candidates"),
        ("candidate_fit", "Score fit vs job requirements and identify gaps"),
        ("bias_fairness", "Check outputs for bias and PII"),
        ("conversation_manager", "Ensure answer addresses recruiter question"),
    ],
    "policy": [
        ("conversation_manager", "Answer policy/compliance question"),
        ("bias_fairness", "Apply fairness guardrails"),
    ],
    "scheduling": [
        ("conversation_manager", "Clarify scheduling intent and next steps"),
    ],
}


def orchestrator_plan_node(state: AgentState) -> dict:
    intent = state.get("intent") or "hiring"
    steps = _PLANS.get(intent, _PLANS["hiring"])
    plan: list[SubGoal] = [
        {"agent": agent, "status": "pending", "description": desc} for agent, desc in steps
    ]
    return {"execution_plan": plan, "task_results": {}}


def _format_no_match(query: str, fit: dict) -> str:
    reason = fit.get("no_match_reason") or "No matching candidates were found."
    criteria = []
    if fit.get("query_skills"):
        criteria.append(f"**Skills requested:** {', '.join(fit['query_skills'])}")
    if fit.get("min_years") is not None:
        criteria.append(f"**Minimum experience:** {fit['min_years']} years")
    criteria_block = "\n".join(criteria)
    return (
        f"## No strong matches\n\n"
        f"For your question: *{query}*\n\n"
        f"{reason}\n\n"
        f"{criteria_block}\n\n"
        f"**Suggestion:** Try broadening skills, lowering experience requirements, "
        f"or upload resumes that mention the skills you need."
    )


def _format_ranked_response(query: str, fit: dict) -> str:
    lines = [f"## Results for: *{query}*\n"]
    if fit.get("query_skills"):
        lines.append(f"**Skills filter:** {', '.join(fit['query_skills'])}  ")
    if fit.get("min_years") is not None:
        lines.append(f"**Min experience:** {fit['min_years']}+ years  ")
    lines.append("")

    for i, cand in enumerate(fit.get("ranked_candidates") or [], start=1):
        gaps = ", ".join(cand.get("gaps") or []) or "none"
        matched = ", ".join(cand.get("matched_skills") or []) or "none"
        yoe = cand.get("years_experience")
        yoe_str = f"{yoe} years" if yoe is not None else "unknown"
        skills = ", ".join(cand.get("skills") or []) or "—"
        lines.append(f"### {i}. {cand.get('name')} — fit {cand.get('fit_score', 0):.0%}")
        lines.append(f"- **Experience:** {yoe_str}")
        lines.append(f"- **Skills:** {skills}")
        lines.append(f"- **Matched:** {matched}")
        lines.append(f"- **Gaps:** {gaps}")
        questions = cand.get("interview_questions") or []
        if questions:
            lines.append(f"- **Interview questions:** {'; '.join(questions)}")
        lines.append("")

    top = fit.get("top_candidate")
    if top:
        lines.append(
            f"## Recommendation\n**{top['name']}** is the strongest match "
            f"({top.get('fit_score', 0):.0%} fit) for your criteria."
        )
    return "\n".join(lines)


def orchestrator_aggregate_node(state: AgentState) -> dict:
    query = last_user_message(state)
    task_results = state.get("task_results") or {}
    fit = task_results.get("candidate_fit") or {}
    intent = state.get("intent") or "hiring"

    if fit.get("no_strong_matches"):
        final = _format_no_match(query, fit)
        return {
            "final_response": final,
            "requires_hitl": False,
            "pending_approval": None,
            "messages": [{"role": "assistant", "content": final}],
        }

    ranked = fit.get("ranked_candidates") or []
    if intent == "hiring" and ranked:
        final = _format_ranked_response(query, fit)
        requires_hitl = bool(fit.get("requires_approval")) or bool(fit.get("high_impact"))
        pending_approval = None
        if requires_hitl:
            pending_approval = {
                "action": "review_candidate_recommendation",
                "summary": final[:500],
                "fit_score": (fit.get("top_candidate") or {}).get("fit_score"),
            }
        return {
            "final_response": final,
            "requires_hitl": requires_hitl,
            "pending_approval": pending_approval,
            "messages": [{"role": "assistant", "content": final}],
        }

    context = state.get("retrieved_context") or []
    llm_payload = {
        "query": query,
        "intent": intent,
        "task_results": {k: v for k, v in task_results.items() if k != "conversation_manager"},
        "retrieved_chunk_count": len(context),
    }

    llm = get_llm_provider()
    response = llm.invoke(
        [
            {
                "role": "system",
                "content": (
                    "You are TalentScreen Orchestrator. Write a concise recruiter-facing answer. "
                    "Use markdown. Do NOT mention internal agents or thread context. Max 200 words."
                ),
            },
            {"role": "user", "content": json.dumps(llm_payload, default=str)[:6000]},
        ]
    )
    final = response.content.strip()

    requires_hitl = bool(fit.get("requires_approval")) or bool(fit.get("high_impact"))
    pending_approval = None
    if requires_hitl:
        pending_approval = {
            "action": "review_candidate_recommendation",
            "summary": final[:500],
            "fit_score": (fit.get("top_candidate") or {}).get("fit_score"),
        }

    return {
        "final_response": final,
        "requires_hitl": requires_hitl,
        "pending_approval": pending_approval,
        "messages": [{"role": "assistant", "content": final}],
    }
