"""Mandatory LLM query rewrite — generate 2–3 optimized retrieval variants."""

from __future__ import annotations

import asyncio
import json
import re

from talentscreen.generation.citations import parse_llm_json
from talentscreen.generation.llm.provider import get_llm_provider

_SYSTEM = (
    "You rewrite recruiter search queries for a hiring knowledge base (resumes, "
    "job descriptions, interview notes). Fix terminology, expand synonyms, and "
    "produce 2-3 DISTINCT optimized search queries.\n"
    'Return JSON only: {"variants": ["query1", "query2", "query3"]}'
)


def _rewrite_sync(query: str) -> list[str]:
    llm = get_llm_provider()
    response = llm.invoke(
        [
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": f"Recruiter query: {query}"},
        ],
        response_format={"type": "json_object"},
    )
    variants: list[str] = []
    try:
        payload = parse_llm_json(response.content)
        raw = payload.get("variants") or payload.get("queries") or []
        if isinstance(raw, list):
            variants = [str(v).strip() for v in raw if str(v).strip()]
    except (json.JSONDecodeError, TypeError, ValueError):
        pass

    if not variants:
        # Regex fallback: split on punctuation and rebuild focused queries
        tokens = re.findall(r"[A-Za-z0-9+#.]+", query)
        if len(tokens) > 3:
            variants = [
                query,
                " ".join(tokens[: max(3, len(tokens) // 2)]),
                " ".join(tokens),
            ]
        else:
            variants = [query]

    seen: set[str] = set()
    ordered: list[str] = []
    for candidate in [query, *variants]:
        key = candidate.strip().lower()
        if key and key not in seen:
            seen.add(key)
            ordered.append(candidate.strip())
    return ordered[:3]


async def llm_rewrite_queries(query: str) -> list[str]:
    return await asyncio.to_thread(_rewrite_sync, query)
