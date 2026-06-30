"""Citation validation for RAG answers."""

from __future__ import annotations

import json
import re
from typing import Any


def parse_llm_json(content: str) -> dict[str, Any]:
    """Parse JSON from LLM output, tolerating markdown fences."""
    stripped = content.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", stripped, re.DOTALL)
    if fence:
        stripped = fence.group(1)
    return json.loads(stripped)


def validate_citations(
    answer_payload: dict[str, Any],
    allowed_chunk_ids: set[str],
) -> dict[str, Any]:
    """Drop invalid citations; flag validation status."""
    citations = answer_payload.get("citations") or []
    valid: list[dict[str, str]] = []
    invalid: list[str] = []

    for cite in citations:
        chunk_id = str(cite.get("chunk_id", ""))
        if chunk_id in allowed_chunk_ids:
            valid.append(
                {
                    "chunk_id": chunk_id,
                    "quote": str(cite.get("quote", ""))[:500],
                }
            )
        elif chunk_id:
            invalid.append(chunk_id)

    return {
        "answer": str(answer_payload.get("answer", "")),
        "citations": valid,
        "confidence": float(answer_payload.get("confidence", 0.0)),
        "citation_validation": {
            "valid_count": len(valid),
            "invalid_chunk_ids": invalid,
            "all_valid": len(invalid) == 0,
        },
    }
