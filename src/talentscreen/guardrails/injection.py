"""Prompt-injection heuristics at the API layer (Phase 3)."""

from __future__ import annotations

import re

_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
    r"disregard\s+(the\s+)?(system|above)",
    r"you\s+are\s+now\s+",
    r"reveal\s+(the\s+)?(system\s+)?prompt",
    r"jailbreak",
    r"<\s*script",
    r"```\s*system",
]


def detect_prompt_injection(text: str) -> list[str]:
    lowered = text.lower()
    return [p for p in _INJECTION_PATTERNS if re.search(p, lowered)]


def assert_safe_prompt(text: str) -> None:
    matches = detect_prompt_injection(text)
    if matches:
        raise ValueError(f"Potential prompt injection detected: {matches[0]}")
