"""Exact-match Redis query cache (Phase 1a)."""

from __future__ import annotations

import hashlib
import json
from typing import Any

import redis

from talentscreen.config import get_settings

CACHE_PREFIX = "ts:cache:query:"


def _cache_key(
    *,
    tenant_id: str,
    query: str,
    top_k: int,
    doc_type: str | None,
    generate_answer: bool,
) -> str:
    raw = json.dumps(
        {
            "tenant_id": tenant_id,
            "query": query.strip().lower(),
            "top_k": top_k,
            "doc_type": doc_type,
            "generate_answer": generate_answer,
        },
        sort_keys=True,
    )
    digest = hashlib.sha256(raw.encode()).hexdigest()
    return f"{CACHE_PREFIX}{digest}"


def get_redis_client() -> redis.Redis:
    return redis.from_url(get_settings().redis_url, decode_responses=True)


def get_cached_query_result(
    *,
    tenant_id: str,
    query: str,
    top_k: int,
    doc_type: str | None,
    generate_answer: bool,
) -> dict[str, Any] | None:
    client = get_redis_client()
    key = _cache_key(
        tenant_id=tenant_id,
        query=query,
        top_k=top_k,
        doc_type=doc_type,
        generate_answer=generate_answer,
    )
    payload = client.get(key)
    if not payload:
        return None
    return json.loads(payload)


def set_cached_query_result(
    *,
    tenant_id: str,
    query: str,
    top_k: int,
    doc_type: str | None,
    generate_answer: bool,
    result: dict[str, Any],
) -> None:
    client = get_redis_client()
    key = _cache_key(
        tenant_id=tenant_id,
        query=query,
        top_k=top_k,
        doc_type=doc_type,
        generate_answer=generate_answer,
    )
    ttl = get_settings().query_cache_ttl_seconds
    client.setex(key, ttl, json.dumps(result))
