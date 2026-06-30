"""BM25 lexical retrieval over Postgres canonical chunks (hybrid leg)."""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Any

from rank_bm25 import BM25Okapi
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from talentscreen.db.models import Chunk, Document


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9+#.]+", text.lower())


@lru_cache(maxsize=32)
def _build_bm25(corpus_key: str, corpus_json: str) -> tuple[BM25Okapi, list[str]]:
    """corpus_json is a stable serialized list of (chunk_id, text) for cache keying."""
    import json

    pairs: list[list[str]] = json.loads(corpus_json)
    chunk_ids = [p[0] for p in pairs]
    tokenized = [_tokenize(p[1]) for p in pairs]
    return BM25Okapi(tokenized), chunk_ids


async def fetch_tenant_corpus(
    session: AsyncSession,
    tenant_id: str,
    doc_type: str | None = None,
) -> list[tuple[str, str, str, str]]:
    stmt = (
        select(Chunk.chunk_id, Chunk.text, Chunk.document_id, Document.doc_type)
        .join(Document, Chunk.document_id == Document.document_id)
        .where(Chunk.tenant_id == tenant_id)
    )
    if doc_type:
        stmt = stmt.where(Document.doc_type == doc_type)

    rows = (await session.execute(stmt)).all()
    return [
        (str(chunk_id), text, str(document_id), doc_type_val)
        for chunk_id, text, document_id, doc_type_val in rows
    ]


async def bm25_search(
    session: AsyncSession,
    query: str,
    *,
    tenant_id: str,
    top_k: int = 20,
    doc_type: str | None = None,
) -> list[dict[str, Any]]:
    corpus = await fetch_tenant_corpus(session, tenant_id, doc_type)
    if not corpus:
        return []

    import json

    corpus_key = f"{tenant_id}:{doc_type or 'all'}:{len(corpus)}"
    corpus_json = json.dumps([(c[0], c[1]) for c in corpus], sort_keys=True)
    bm25, chunk_ids = _build_bm25(corpus_key, corpus_json)

    scores = bm25.get_scores(_tokenize(query))
    ranked = sorted(zip(chunk_ids, scores, strict=True), key=lambda x: x[1], reverse=True)

    meta = {c[0]: c for c in corpus}
    hits: list[dict[str, Any]] = []
    for chunk_id, score in ranked[:top_k]:
        if score <= 0:
            continue
        _cid, _text, document_id, dtype = meta[chunk_id]
        hits.append(
            {
                "chunk_id": chunk_id,
                "document_id": document_id,
                "doc_type": dtype,
                "tenant_id": tenant_id,
                "score": float(score),
                "source": "bm25",
            }
        )
    return hits
