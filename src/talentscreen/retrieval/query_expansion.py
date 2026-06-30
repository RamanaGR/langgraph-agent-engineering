"""Rule-based query expansion — baseline before Phase 1b LLM rewrite."""

from __future__ import annotations

# Recruitment synonym groups: if any term in a group appears, append siblings.
_SYNONYM_GROUPS: tuple[tuple[str, ...], ...] = (
    ("java", "spring boot", "jvm", "spring"),
    ("aws", "amazon web services", "ec2", "s3", "lambda", "cloud"),
    ("kubernetes", "k8s", "eks", "container orchestration"),
    ("python", "django", "flask", "fastapi"),
    ("devops", "ci/cd", "cicd", "terraform", "infrastructure as code"),
    ("microservices", "distributed systems", "service mesh"),
    ("postgres", "postgresql", "sql database"),
    ("senior", "lead", "staff", "principal"),
    ("years experience", "yoe", "years of experience"),
    ("candidate", "applicant", "resume", "cv"),
)


def expand_query(query: str) -> tuple[str, list[str]]:
    """Return (expanded_query, terms_added)."""
    lowered = query.lower()
    added: list[str] = []
    for group in _SYNONYM_GROUPS:
        if any(term in lowered for term in group):
            for term in group:
                if term not in lowered and term not in added:
                    added.append(term)
    if not added:
        return query, []
    expanded = f"{query} {' '.join(added)}"
    return expanded, added
