"""Retrieval evaluation metrics (F1@K and keyword proxy)."""

from __future__ import annotations


def precision_at_k(retrieved: list[str], expected: set[str], k: int) -> float:
    top = retrieved[:k]
    if not top:
        return 0.0
    hits = sum(1 for item in top if item in expected)
    return hits / len(top)


def recall_at_k(retrieved: list[str], expected: set[str], k: int) -> float:
    if not expected:
        return 1.0
    top = retrieved[:k]
    hits = sum(1 for item in expected if item in top)
    return hits / len(expected)


def f1_at_k(retrieved: list[str], expected: list[str], k: int = 5) -> float:
    expected_set = set(expected)
    if not expected_set:
        return 0.0
    p = precision_at_k(retrieved, expected_set, k)
    r = recall_at_k(retrieved, expected_set, k)
    if p + r == 0:
        return 0.0
    return 2 * p * r / (p + r)


def keyword_recall_at_k(
    chunk_texts: list[str],
    keywords: list[str],
    k: int = 5,
) -> float:
    """Proxy metric when golden chunk_ids are not populated."""
    if not keywords:
        return 1.0
    top = chunk_texts[:k]
    if not top:
        return 0.0
    joined = " ".join(top).lower()
    found = sum(1 for kw in keywords if kw.lower() in joined)
    return found / len(keywords)
