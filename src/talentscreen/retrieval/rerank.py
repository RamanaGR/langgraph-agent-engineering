"""Cross-encoder reranking over dense retrieval candidates."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from talentscreen.config import get_settings


@lru_cache(maxsize=1)
def _get_cross_encoder():
    from sentence_transformers import CrossEncoder

    model_name = get_settings().rerank_model
    return CrossEncoder(model_name)


def rerank_hits(
    query: str,
    hits: list[dict[str, Any]],
    *,
    top_k: int | None = None,
) -> list[dict[str, Any]]:
    """Rerank hits that include a ``text`` field; preserve metadata."""
    if not hits:
        return []

    texts = [hit.get("text") or "" for hit in hits]
    if not any(texts):
        return hits[: top_k or len(hits)]

    model = _get_cross_encoder()
    pairs = [(query, text) for text in texts]
    scores = model.predict(pairs)

    reranked: list[dict[str, Any]] = []
    for hit, score in sorted(zip(hits, scores, strict=True), key=lambda x: x[1], reverse=True):
        updated = {**hit, "dense_score": hit.get("score"), "score": float(score)}
        reranked.append(updated)

    limit = top_k or len(reranked)
    return reranked[:limit]
