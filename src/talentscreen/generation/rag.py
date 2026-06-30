"""RAG answer generation with few-shot JSON citations."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from talentscreen.generation.citations import parse_llm_json, validate_citations
from talentscreen.generation.llm.provider import get_llm_provider

_FEW_SHOT = (
    "You are TalentScreen, a hiring assistant. "
    "Answer ONLY from the provided context chunks.\n"
    "Return valid JSON with keys: answer (string), "
    "citations (array of {chunk_id, quote}), confidence (0-1).\n\n"
    "Example:\n"
    "Question: Who has AWS experience?\n"
    "Context:\n"
    "[chunk_id=abc] Carol Singh — Skills: Java, AWS (EC2, S3, Lambda)\n"
    "Answer JSON:\n"
    '{"answer": "Carol Singh has AWS experience.", '
    '"citations": [{"chunk_id": "abc", "quote": "Skills: Java, AWS"}], '
    '"confidence": 0.9}'
)


def _build_context_block(chunks: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for chunk in chunks:
        lines.append(
            f"[chunk_id={chunk['chunk_id']} doc_type={chunk.get('doc_type', '')} "
            f"file={chunk.get('filename', '')}]\n{chunk.get('text', '')}"
        )
    return "\n\n".join(lines)


def _generate_sync(query: str, chunks: list[dict[str, Any]]) -> dict[str, Any]:
    allowed_ids = {c["chunk_id"] for c in chunks}
    if not chunks:
        return {
            "answer": "No relevant documents were found in the knowledge base for this question.",
            "citations": [],
            "confidence": 0.0,
            "citation_validation": {
                "valid_count": 0,
                "invalid_chunk_ids": [],
                "all_valid": True,
            },
            "skipped": True,
        }

    context = _build_context_block(chunks)
    messages = [
        {"role": "system", "content": _FEW_SHOT},
        {
            "role": "user",
            "content": f"Question: {query}\n\nContext:\n{context}\n\nAnswer JSON:",
        },
    ]

    llm = get_llm_provider()
    response = llm.invoke(messages, response_format={"type": "json_object"})
    try:
        payload = parse_llm_json(response.content)
    except (json.JSONDecodeError, TypeError):
        payload = {
            "answer": response.content,
            "citations": [],
            "confidence": 0.5,
        }

    validated = validate_citations(payload, allowed_ids)
    validated["model"] = response.model
    validated["llm_cached"] = response.cached
    return validated


async def generate_answer(query: str, chunks: list[dict[str, Any]]) -> dict[str, Any]:
    return await asyncio.to_thread(_generate_sync, query, chunks)
