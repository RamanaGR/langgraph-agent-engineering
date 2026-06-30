"""Native @tool — guardrails: PII, bias language, basic toxicity heuristics."""

from __future__ import annotations

import re
from typing import Any

from langchain_core.tools import tool

from talentscreen.guardrails.pii import redact_pii

_BIAS_PATTERNS = [
    r"\brock\s*star\b",
    r"\bninja\b",
    r"\bguru\b",
    r"\byoung\b",
    r"\benergetic\b",
    r"\bguys\b",
    r"\bhe/she\b",
    r"\bfemale\b",
    r"\bmale\b",
    r"\bage\s*\d+",
]

_TOXIC_PATTERNS = [
    r"\bidiot\b",
    r"\bstupid\b",
    r"\bhate\b",
]


@tool
def guardrails_check(text: str) -> dict[str, Any]:
    """Check text for PII, biased hiring language, and toxic terms."""
    pii = redact_pii(text)
    lowered = text.lower()
    bias_flags = [p for p in _BIAS_PATTERNS if re.search(p, lowered)]
    toxic_flags = [p for p in _TOXIC_PATTERNS if re.search(p, lowered)]

    issues: list[str] = []
    if pii.entities_found:
        issues.append(f"pii:{','.join(pii.entities_found)}")
    if bias_flags:
        issues.append("biased_language")
    if toxic_flags:
        issues.append("toxic_language")

    return {
        "passed": len(issues) == 0,
        "issues": issues,
        "pii_entities": pii.entities_found,
        "redacted_text": pii.redacted_text,
        "bias_matches": bias_flags,
        "toxic_matches": toxic_flags,
    }
