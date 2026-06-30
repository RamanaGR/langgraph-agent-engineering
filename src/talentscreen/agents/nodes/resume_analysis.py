"""ResumeAnalysisAgent — normalize skills and compare candidates from context."""

from __future__ import annotations

import re

from talentscreen.agents.nodes._helpers import mark_subgoal_done, merge_task_result
from talentscreen.agents.state import AgentState


def _extract_candidate_blocks(text: str) -> list[dict]:
    candidates: list[dict] = []
    name_match = re.match(r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", text.strip())
    skills_match = re.search(r"Skills?:\s*(.+)", text, re.IGNORECASE)
    yoe_match = re.search(r"Years of Experience:\s*(\d+)", text, re.IGNORECASE)
    if name_match:
        skills = []
        if skills_match:
            skills = [s.strip() for s in re.split(r",|;", skills_match.group(1)) if s.strip()]
        candidates.append(
            {
                "name": name_match.group(1),
                "skills": skills,
                "years_experience": int(yoe_match.group(1)) if yoe_match else None,
            }
        )
    return candidates


def resume_analysis_node(state: AgentState) -> dict:
    all_candidates: list[dict] = []
    for chunk in state.get("retrieved_context") or []:
        if chunk.get("doc_type") in ("resume", "unknown", None) or "resume" in (
            chunk.get("filename") or ""
        ):
            all_candidates.extend(_extract_candidate_blocks(chunk.get("text") or ""))

    seen: set[str] = set()
    unique: list[dict] = []
    for c in all_candidates:
        if c["name"] not in seen:
            seen.add(c["name"])
            unique.append(c)

    comparison = sorted(
        unique,
        key=lambda c: (c.get("years_experience") or 0, len(c.get("skills") or [])),
        reverse=True,
    )
    result = {"candidates": comparison, "count": len(comparison)}
    return {
        "execution_plan": mark_subgoal_done(state, "resume_analysis"),
        "task_results": merge_task_result(state, "resume_analysis", result),
    }
