"""Extract skill and experience requirements from recruiter natural-language queries."""

from __future__ import annotations

import re

# Longer phrases first so "machine learning" wins over "learning"
_SKILL_PATTERNS: list[tuple[str, str]] = [
    ("machine learning", r"\bmachine\s+learning\b"),
    ("artificial intelligence", r"\bartificial\s+intelligence\b"),
    ("spring boot", r"\bspring\s+boot\b"),
    ("deep learning", r"\bdeep\s+learning\b"),
    ("kubernetes", r"\bkubernetes\b|\bk8s\b"),
    ("microservices", r"\bmicroservices?\b"),
    ("postgresql", r"\bpostgresql\b|\bpostgres\b"),
    ("terraform", r"\bterraform\b"),
    ("javascript", r"\bjavascript\b|\bjs\b"),
    ("typescript", r"\btypescript\b|\bts\b"),
    ("python", r"\bpython\b"),
    ("tensorflow", r"\btensorflow\b"),
    ("pytorch", r"\bpytorch\b"),
    ("java", r"\bjava\b"),
    ("spring", r"\bspring\b"),
    ("docker", r"\bdocker\b"),
    ("kafka", r"\bkafka\b"),
    ("ml", r"\bml\b"),
    ("ai", r"\bai\b"),
    ("aws", r"\baws\b"),
    ("gcp", r"\bgcp\b|\bgoogle\s+cloud\b"),
    ("azure", r"\azure\b"),
    ("react", r"\breact\b"),
    ("node", r"\bnode\.?js\b"),
]

_MIN_YEARS_RE = re.compile(
    r"(?:min(?:imum)?|at\s+least|>=?)\s*(\d+)\s*(?:\+?\s*)?(?:years?|yrs?|y)\b"
    r"|\b(\d+)\s*\+\s*years?\b"
    r"|\b(\d+)\s*years?\s+(?:of\s+)?experience\b",
    re.IGNORECASE,
)


def extract_query_skills(query: str) -> list[str]:
    lowered = query.lower()
    found: list[str] = []
    seen: set[str] = set()
    for skill, pattern in _SKILL_PATTERNS:
        if re.search(pattern, lowered, re.IGNORECASE) and skill not in seen:
            seen.add(skill)
            found.append(skill)
    return found


def extract_min_years(query: str) -> int | None:
    match = _MIN_YEARS_RE.search(query)
    if not match:
        return None
    for group in match.groups():
        if group:
            return int(group)
    return None


def skill_matches(candidate_skill: str, required: str) -> bool:
    cs = candidate_skill.lower().strip()
    rs = required.lower().strip()
    if not cs or not rs:
        return False
    return rs in cs or cs in rs


def candidate_has_skill(candidate_skills: list[str], required: str) -> bool:
    return any(skill_matches(s, required) for s in candidate_skills)
