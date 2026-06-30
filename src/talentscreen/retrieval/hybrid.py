"""Reciprocal Rank Fusion for dense + BM25 + multi-query variants."""

from __future__ import annotations

from typing import Any

from talentscreen.config import get_settings


def reciprocal_rank_fusion(
    rankings: list[list[dict[str, Any]]],
    *,
    k: int | None = None,
) -> list[dict[str, Any]]:
    """Merge ranked hit lists; preserve metadata from first occurrence."""
    rrf_k = k or get_settings().rrf_k
    scores: dict[str, float] = {}
    meta: dict[str, dict[str, Any]] = {}

    for ranking in rankings:
        for rank, hit in enumerate(ranking, start=1):
            chunk_id = hit["chunk_id"]
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (rrf_k + rank)
            if chunk_id not in meta:
                meta[chunk_id] = dict(hit)

    fused: list[dict[str, Any]] = []
    for chunk_id, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
        hit = {**meta[chunk_id], "score": score, "fusion": "rrf"}
        fused.append(hit)
    return fused
