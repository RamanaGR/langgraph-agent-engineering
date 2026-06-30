"""Semantic query cache — Redis vector similarity (Phase 1b)."""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any

import redis

from talentscreen.config import get_settings

SEMANTIC_PREFIX = "ts:cache:semantic:"


def _tenant_key(tenant_id: str) -> str:
    return f"{SEMANTIC_PREFIX}{tenant_id}"


def _entry_key(query: str) -> str:
    return hashlib.sha256(query.strip().lower().encode()).hexdigest()[:16]


def get_redis_client() -> redis.Redis:
    return redis.from_url(get_settings().redis_url, decode_responses=True)


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def get_semantic_cached_result(
    *,
    tenant_id: str,
    query_vector: list[float],
    top_k: int,
    doc_type: str | None,
    generate_answer: bool,
) -> dict[str, Any] | None:
    client = get_redis_client()
    raw_entries = client.hgetall(_tenant_key(tenant_id))
    if not raw_entries:
        return None

    threshold = get_settings().semantic_cache_threshold
    best_sim = 0.0
    best_payload: dict[str, Any] | None = None

    for value in raw_entries.values():
        entry = json.loads(value)
        if entry.get("top_k") != top_k:
            continue
        if entry.get("doc_type") != doc_type:
            continue
        if entry.get("generate_answer") != generate_answer:
            continue
        sim = _cosine(query_vector, entry.get("vector", []))
        if sim >= threshold and sim > best_sim:
            best_sim = sim
            best_payload = entry.get("result")

    if best_payload:
        best_payload = dict(best_payload)
        best_payload["cache_hit"] = True
        best_payload["semantic_cache_similarity"] = best_sim
    return best_payload


def set_semantic_cached_result(
    *,
    tenant_id: str,
    query: str,
    query_vector: list[float],
    top_k: int,
    doc_type: str | None,
    generate_answer: bool,
    result: dict[str, Any],
) -> None:
    client = get_redis_client()
    key = _tenant_key(tenant_id)
    entry = {
        "query": query.strip().lower(),
        "vector": query_vector,
        "top_k": top_k,
        "doc_type": doc_type,
        "generate_answer": generate_answer,
        "result": result,
    }
    ttl = get_settings().semantic_cache_ttl_seconds
    client.hset(key, _entry_key(query), json.dumps(entry))
    client.expire(key, ttl)
