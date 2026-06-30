"""PII detection and redaction on recruiter queries (Presidio with regex fallback)."""

from __future__ import annotations

import re
from dataclasses import dataclass

_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
_PHONE_RE = re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
_SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")


@dataclass
class PIIScanResult:
    redacted_text: str
    entities_found: list[str]
    engine: str


_analyzer = None
_anonymizer = None
_presidio_available: bool | None = None


def _init_presidio() -> bool:
    global _analyzer, _anonymizer, _presidio_available
    if _presidio_available is not None:
        return _presidio_available
    try:
        from presidio_analyzer import AnalyzerEngine
        from presidio_anonymizer import AnonymizerEngine

        _analyzer = AnalyzerEngine()
        _anonymizer = AnonymizerEngine()
        _presidio_available = True
    except Exception:
        _presidio_available = False
    return _presidio_available


def _regex_redact(text: str) -> PIIScanResult:
    entities: list[str] = []
    redacted = text
    for label, pattern in (
        ("EMAIL", _EMAIL_RE),
        ("PHONE", _PHONE_RE),
        ("US_SSN", _SSN_RE),
    ):
        if pattern.search(redacted):
            entities.append(label)
            redacted = pattern.sub(f"<{label}>", redacted)
    return PIIScanResult(redacted_text=redacted, entities_found=entities, engine="regex")


def redact_pii(text: str) -> PIIScanResult:
    if not text.strip():
        return PIIScanResult(redacted_text=text, entities_found=[], engine="none")

    if _init_presidio() and _analyzer is not None and _anonymizer is not None:
        try:
            results = _analyzer.analyze(text=text, language="en")
            if not results:
                return PIIScanResult(redacted_text=text, entities_found=[], engine="presidio")
            anonymized = _anonymizer.anonymize(text=text, analyzer_results=results)
            entities = sorted({r.entity_type for r in results})
            return PIIScanResult(
                redacted_text=anonymized.text,
                entities_found=entities,
                engine="presidio",
            )
        except Exception:
            pass

    return _regex_redact(text)
