"""Phase 1b query pipeline: PII → LLM rewrite → semantic cache → hybrid RRF → rerank → generate."""

from __future__ import annotations

import asyncio
from typing import Any, Literal

from sqlalchemy.ext.asyncio import AsyncSession

from talentscreen.config import get_settings
from talentscreen.generation.embeddings.local import get_embedding_provider
from talentscreen.generation.rag import generate_answer
from talentscreen.guardrails.pii import redact_pii
from talentscreen.observability.langfuse_tracer import trace_query
from talentscreen.retrieval.bm25 import bm25_search
from talentscreen.retrieval.cache import get_cached_query_result, set_cached_query_result
from talentscreen.retrieval.chunks import enrich_hits_with_text, fetch_chunks_by_ids
from talentscreen.retrieval.hybrid import reciprocal_rank_fusion
from talentscreen.retrieval.milvus.client import connect_milvus, dense_search
from talentscreen.retrieval.query_expansion import expand_query
from talentscreen.retrieval.query_rewrite import llm_rewrite_queries
from talentscreen.retrieval.rerank import rerank_hits
from talentscreen.retrieval.semantic_cache import (
    get_semantic_cached_result,
    set_semantic_cached_result,
)

RetrievalMode = Literal["hybrid", "dense"]


class RetrievalUnavailableError(Exception):
    """Milvus or embedding service unavailable."""


class GenerationUnavailableError(Exception):
    """LLM generation failed after successful retrieval."""


async def _dense_retrieve(
    query: str,
    *,
    tenant_id: str,
    retrieval_k: int,
    doc_type: str | None,
) -> list[dict[str, Any]]:
    def _search() -> list[dict[str, Any]]:
        connect_milvus()
        embedder = get_embedding_provider()
        vector = embedder.embed([query]).vectors[0]
        hits = dense_search(vector, tenant_id=tenant_id, top_k=retrieval_k, doc_type=doc_type)
        for hit in hits:
            hit["source"] = "dense"
        return hits

    return await asyncio.to_thread(_search)


def _embed_query(query: str) -> list[float]:
    embedder = get_embedding_provider()
    return embedder.embed([query]).vectors[0]


async def run_query_pipeline(
    session: AsyncSession,
    *,
    query: str,
    tenant_id: str,
    top_k: int = 5,
    doc_type: str | None = None,
    generate_answer_flag: bool = True,
    use_cache: bool = True,
    retrieval_mode: RetrievalMode = "hybrid",
) -> dict[str, Any]:
    settings = get_settings()
    retrieval_k = max(top_k * 4, settings.retrieval_top_k)

    with trace_query(
        name="query_pipeline",
        input_data={
            "query": query,
            "tenant_id": tenant_id,
            "top_k": top_k,
            "doc_type": doc_type,
            "retrieval_mode": retrieval_mode,
        },
    ) as trace:
        if use_cache:
            exact = get_cached_query_result(
                tenant_id=tenant_id,
                query=query,
                top_k=top_k,
                doc_type=doc_type,
                generate_answer=generate_answer_flag,
            )
            if exact:
                exact["cache_hit"] = True
                exact["cache_type"] = "exact"
                trace.update(output={"cache_hit": True, "cache_type": "exact"})
                return exact

        pii = redact_pii(query)
        rewritten_queries = await llm_rewrite_queries(pii.redacted_text)
        expanded_query, expansion_terms = expand_query(pii.redacted_text)

        trace.event(
            name="pii_scan",
            metadata={"engine": pii.engine, "entities": pii.entities_found},
        )
        trace.event(name="llm_query_rewrite", metadata={"variants": rewritten_queries})
        trace.event(name="query_expansion", metadata={"terms_added": expansion_terms})

        query_vector: list[float] | None = None
        if use_cache:
            try:
                query_vector = await asyncio.to_thread(_embed_query, pii.redacted_text)
                semantic = get_semantic_cached_result(
                    tenant_id=tenant_id,
                    query_vector=query_vector,
                    top_k=top_k,
                    doc_type=doc_type,
                    generate_answer=generate_answer_flag,
                )
                if semantic:
                    semantic["cache_type"] = "semantic"
                    trace.update(
                        output={
                            "cache_hit": True,
                            "cache_type": "semantic",
                            "similarity": semantic.get("semantic_cache_similarity"),
                        }
                    )
                    return semantic
            except Exception:
                query_vector = None

        try:
            dense_rankings: list[list[dict[str, Any]]] = []
            for variant in rewritten_queries:
                hits = await _dense_retrieve(
                    variant,
                    tenant_id=tenant_id,
                    retrieval_k=retrieval_k,
                    doc_type=doc_type,
                )
                dense_rankings.append(hits)

            if retrieval_mode == "hybrid":
                bm25_hits = await bm25_search(
                    session,
                    pii.redacted_text,
                    tenant_id=tenant_id,
                    top_k=retrieval_k,
                    doc_type=doc_type,
                )
                fused_hits = reciprocal_rank_fusion([*dense_rankings, bm25_hits])
            else:
                fused_hits = reciprocal_rank_fusion(dense_rankings)

        except Exception as exc:
            raise RetrievalUnavailableError(str(exc)) from exc

        chunk_map = await fetch_chunks_by_ids(
            session, [h["chunk_id"] for h in fused_hits[:retrieval_k]]
        )
        enriched = enrich_hits_with_text(fused_hits[:retrieval_k], chunk_map)

        def _rerank() -> list[dict[str, Any]]:
            return rerank_hits(pii.redacted_text, enriched, top_k=top_k)

        reranked = await asyncio.to_thread(_rerank)

        answer_payload: dict[str, Any] | None = None
        generation_error: str | None = None
        if generate_answer_flag:
            try:
                answer_payload = await generate_answer(pii.redacted_text, reranked)
            except Exception as exc:
                generation_error = str(exc)[:500]
                if not reranked:
                    raise GenerationUnavailableError(generation_error) from exc

        hits = [
            {
                "chunk_id": h["chunk_id"],
                "document_id": h["document_id"],
                "doc_type": h.get("doc_type", "unknown"),
                "filename": h.get("filename"),
                "text": h.get("text", "")[:500],
                "score": h.get("score", 0.0),
                "dense_score": h.get("dense_score"),
                "fusion": h.get("fusion"),
                "source": h.get("source"),
            }
            for h in reranked
        ]

        result: dict[str, Any] = {
            "query": query,
            "sanitized_query": pii.redacted_text,
            "rewritten_queries": rewritten_queries,
            "expanded_query": expanded_query,
            "expansion_terms": expansion_terms,
            "pii_entities": pii.entities_found,
            "pii_engine": pii.engine,
            "retrieval_mode": retrieval_mode,
            "cache_hit": False,
            "cache_type": None,
            "dense_hit_count": sum(len(r) for r in dense_rankings),
            "fused_hit_count": len(enriched),
            "hits": hits,
            "answer": answer_payload,
            "generation_error": generation_error,
            "trace_id": getattr(trace, "id", None) or None,
        }

        if use_cache and hits:
            set_cached_query_result(
                tenant_id=tenant_id,
                query=query,
                top_k=top_k,
                doc_type=doc_type,
                generate_answer=generate_answer_flag,
                result=result,
            )
            if query_vector is None:
                try:
                    query_vector = await asyncio.to_thread(_embed_query, pii.redacted_text)
                except Exception:
                    query_vector = None
            if query_vector is not None:
                set_semantic_cached_result(
                    tenant_id=tenant_id,
                    query=query,
                    query_vector=query_vector,
                    top_k=top_k,
                    doc_type=doc_type,
                    generate_answer=generate_answer_flag,
                    result=result,
                )

        trace.update(
            output={
                "hit_count": len(hits),
                "fused_hit_count": len(enriched),
                "retrieval_mode": retrieval_mode,
                "rewrite_variants": len(rewritten_queries),
            }
        )
        return result
