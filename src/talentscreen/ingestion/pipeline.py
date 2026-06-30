import asyncio
import hashlib
import uuid
from datetime import UTC, datetime

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from talentscreen.config import get_settings
from talentscreen.db.models import Chunk, Document
from talentscreen.generation.embeddings.local import get_embedding_provider
from talentscreen.ingestion.chunking import semantic_chunk
from talentscreen.ingestion.parsers import parse_with_docling, parse_with_unstructured
from talentscreen.ingestion.router import ParserChoice, choose_parser
from talentscreen.ingestion.storage import download_bytes
from talentscreen.retrieval.milvus.client import upsert_vectors


def content_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _parse_document(
    raw: bytes, filename: str, mime_type: str | None
) -> tuple[str, str, list[dict]]:
    """CPU/sync parsing — run in a thread from async worker."""
    parser_choice = choose_parser(filename, mime_type)
    if parser_choice == ParserChoice.DOCLING:
        try:
            parsed = parse_with_docling(raw, filename)
        except ImportError:
            parsed = parse_with_unstructured(raw, filename)
    else:
        parsed = parse_with_unstructured(raw, filename)

    chunk_payloads = semantic_chunk(
        parsed.text,
        metadata={"filename": filename, **parsed.metadata},
    )
    return parsed.parser_used, parsed.text, chunk_payloads


def _embed_and_index(
    chunk_ids: list[str],
    tenant_ids: list[str],
    document_ids: list[str],
    doc_types: list[str],
    texts: list[str],
) -> None:
    if not texts:
        return
    embedder = get_embedding_provider()
    vectors = embedder.embed(texts).vectors
    upsert_vectors(chunk_ids, tenant_ids, document_ids, doc_types, vectors)


async def process_document_ingestion(session: AsyncSession, document_id: str) -> dict:
    """Full ingestion: parse → chunk → Postgres (canonical) → Milvus (vectors)."""
    doc_uuid = uuid.UUID(document_id)
    result = await session.execute(select(Document).where(Document.document_id == doc_uuid))
    document = result.scalar_one()

    if document.status == "completed":
        return {"status": "skipped", "reason": "already_completed", "document_id": document_id}

    document.status = "processing"
    document.updated_at = datetime.now(UTC)
    await session.commit()

    filename = document.filename
    mime_type = document.mime_type
    minio_key = document.minio_key
    doc_type = document.doc_type
    tenant_id = document.tenant_id
    document_uuid = document.document_id

    try:
        raw = await asyncio.to_thread(download_bytes, minio_key)
        parser_used, _text, chunk_payloads = await asyncio.to_thread(
            _parse_document, raw, filename, mime_type
        )

        # Avoid lazy-loading document.chunks in async session (causes greenlet_spawn error)
        await session.execute(delete(Chunk).where(Chunk.document_id == document_uuid))
        await session.flush()

        chunk_ids: list[str] = []
        tenant_ids: list[str] = []
        document_ids: list[str] = []
        doc_types: list[str] = []
        texts: list[str] = []

        for index, payload in enumerate(chunk_payloads):
            chunk = Chunk(
                document_id=document_uuid,
                tenant_id=tenant_id,
                chunk_index=index,
                text=payload["text"],
                token_count=payload["token_count"],
                metadata_={**payload["metadata"], "doc_type": doc_type},
            )
            session.add(chunk)
            texts.append(payload["text"])

        await session.flush()

        for chunk in (
            await session.execute(
                select(Chunk)
                .where(Chunk.document_id == document_uuid)
                .order_by(Chunk.chunk_index)
            )
        ).scalars():
            chunk_ids.append(str(chunk.chunk_id))
            tenant_ids.append(tenant_id)
            document_ids.append(str(document_uuid))
            doc_types.append(doc_type)

        await asyncio.to_thread(
            _embed_and_index, chunk_ids, tenant_ids, document_ids, doc_types, texts
        )

        await session.execute(
            update(Document)
            .where(Document.document_id == document_uuid)
            .values(
                parser_used=parser_used,
                status="completed",
                error_message=None,
                updated_at=datetime.now(UTC),
            )
        )
        await session.commit()

        return {
            "status": "completed",
            "document_id": document_id,
            "parser_used": parser_used,
            "chunk_count": len(chunk_ids),
        }
    except Exception as exc:
        await session.rollback()
        await session.execute(
            update(Document)
            .where(Document.document_id == doc_uuid)
            .values(
                status="failed",
                error_message=str(exc)[:2000],
                updated_at=datetime.now(UTC),
            )
        )
        await session.commit()
        raise


async def register_upload(
    session: AsyncSession,
    *,
    tenant_id: str,
    filename: str,
    file_bytes: bytes,
    doc_type: str,
    minio_key: str,
    mime_type: str | None = None,
    candidate_id: uuid.UUID | None = None,
    job_id: uuid.UUID | None = None,
) -> tuple[Document, bool]:
    """Register document; returns (document, is_new). Re-upload same hash → idempotent skip."""
    digest = content_hash(file_bytes)
    existing = await session.execute(
        select(Document).where(Document.tenant_id == tenant_id, Document.content_hash == digest)
    )
    found = existing.scalar_one_or_none()
    if found:
        return found, False

    document = Document(
        tenant_id=tenant_id or get_settings().default_tenant_id,
        candidate_id=candidate_id,
        job_id=job_id,
        doc_type=doc_type,
        filename=filename,
        content_hash=digest,
        minio_key=minio_key,
        mime_type=mime_type,
        status="pending",
    )
    session.add(document)
    await session.flush()
    return document, True
