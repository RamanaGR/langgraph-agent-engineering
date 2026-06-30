"""CandidateFitAgent — JD fit scoring, gaps, interview questions."""

from __future__ import annotations

from talentscreen.agents.nodes._helpers import (
    last_user_message,
    mark_subgoal_done,
    merge_task_result,
)
from talentscreen.agents.query_parsing import (
    candidate_has_skill,
    extract_min_years,
    extract_query_skills,
)
from talentscreen.agents.state import AgentState
from talentscreen.agents.tools.postgres import postgres_query

_JD_FALLBACK_SKILLS = ("java", "aws", "kubernetes", "spring", "postgresql", "microservices")


def _jd_skills_from_context(state: AgentState) -> list[str]:
    skills: list[str] = []
    for chunk in state.get("retrieved_context") or []:
        if chunk.get("doc_type") == "job_description" or "job" in (chunk.get("filename") or ""):
            text = (chunk.get("text") or "").lower()
            for skill in _JD_FALLBACK_SKILLS:
                if skill in text and skill not in skills:
                    skills.append(skill)
    return skills or list(_JD_FALLBACK_SKILLS[:4])


def _resolve_required_skills(
    query: str, state: AgentState
) -> tuple[list[str], list[str], int | None]:
    query_skills = extract_query_skills(query)
    jd_skills = _jd_skills_from_context(state)
    min_years = extract_min_years(query)
    if query_skills:
        required = query_skills
    else:
        required = jd_skills
    return required, query_skills, min_years


def candidate_fit_node(state: AgentState) -> dict:
    query = last_user_message(state)
    tenant_id = state.get("tenant_id") or "demo-tenant"
    resume_data = (state.get("task_results") or {}).get("resume_analysis") or {}
    candidates = resume_data.get("candidates") or []
    required, query_skills, min_years = _resolve_required_skills(query, state)

    scored: list[dict] = []
    for cand in candidates:
        cand_skills = [s.lower() for s in cand.get("skills") or []]
        yoe = cand.get("years_experience")

        if min_years is not None and (yoe is None or yoe < min_years):
            continue

        matched = [r for r in required if candidate_has_skill(cand_skills, r)]
        gaps = [r for r in required if r not in matched]
        score = len(matched) / max(len(required), 1)

        if query_skills and not matched:
            continue

        scored.append(
            {
                "name": cand.get("name"),
                "years_experience": yoe,
                "skills": cand.get("skills") or [],
                "fit_score": round(score, 2),
                "matched_skills": matched,
                "gaps": gaps,
                "interview_questions": [
                    f"Describe your experience with {g}." for g in gaps[:2]
                ],
            }
        )

    scored.sort(key=lambda x: x["fit_score"], reverse=True)
    top = scored[0] if scored else None
    requires_approval = bool(top and top["fit_score"] >= 0.75)

    no_strong_matches = not scored and bool(candidates)
    no_match_reason: str | None = None
    if no_strong_matches:
        parts = []
        if query_skills:
            parts.append(f"skills: {', '.join(query_skills)}")
        if min_years is not None:
            parts.append(f"minimum {min_years} years experience")
        no_match_reason = (
            f"No candidates in the retrieved pool matched your criteria ({'; '.join(parts)})."
            if parts
            else "No candidates matched the required skills."
        )

    pg_result = {}
    try:
        pg_result = postgres_query.invoke(
            {
                "sql": (
                    f"SELECT full_name, years_experience, skills FROM candidates "
                    f"WHERE tenant_id = '{tenant_id}' LIMIT 5"
                ),
                "tenant_id": tenant_id,
            }
        )
    except Exception as exc:
        pg_result = {"error": str(exc)}

    result = {
        "ranked_candidates": scored,
        "top_candidate": top,
        "required_skills": required,
        "query_skills": query_skills,
        "min_years": min_years,
        "no_strong_matches": no_strong_matches,
        "no_match_reason": no_match_reason,
        "requires_approval": requires_approval,
        "high_impact": "recommend" in query.lower() and "reject" in query.lower(),
        "postgres_rows": pg_result.get("rows", []),
    }
    return {
        "execution_plan": mark_subgoal_done(state, "candidate_fit"),
        "task_results": merge_task_result(state, "candidate_fit", result),
    }
