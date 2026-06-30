"""Postgres chunk lookups — canonical text for retrieval hits."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from talentscreen.db.models import Chunk, Document


async def fetch_chunks_by_ids(
    session: AsyncSession,
    chunk_ids: list[str],
) -> dict[str, dict]:
    if not chunk_ids:
        return {}

    uuids = [uuid.UUID(cid) for cid in chunk_ids]
    rows = (
        await session.execute(
            select(Chunk, Document.filename)
            .join(Document, Chunk.document_id == Document.document_id)
            .where(Chunk.chunk_id.in_(uuids))
        )
    ).all()

    out: dict[str, dict] = {}
    for chunk, filename in rows:
        meta = chunk.metadata_ or {}
        out[str(chunk.chunk_id)] = {
            "chunk_id": str(chunk.chunk_id),
            "document_id": str(chunk.document_id),
            "doc_type": meta.get("doc_type", "unknown"),
            "filename": filename,
            "text": chunk.text,
            "chunk_index": chunk.chunk_index,
        }
    return out


def enrich_hits_with_text(hits: list[dict], chunk_map: dict[str, dict]) -> list[dict]:
    enriched: list[dict] = []
    for hit in hits:
        chunk = chunk_map.get(hit["chunk_id"])
        if not chunk:
            continue
        enriched.append({**hit, **chunk})
    return enriched
