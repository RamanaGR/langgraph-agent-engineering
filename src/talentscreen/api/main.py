import uuid

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from talentscreen.api.agents import router as agents_router
from talentscreen.api.auth import AuthContext, require_recruiter
from talentscreen.api.jobs import router as jobs_router
from talentscreen.api.mcp_routes import router as mcp_router
from talentscreen.config import get_settings
from talentscreen.db.session import get_db_session
from talentscreen.guardrails.injection import assert_safe_prompt
from talentscreen.ingestion.pipeline import register_upload
from talentscreen.ingestion.storage import upload_bytes
from talentscreen.ingestion.worker import enqueue_ingestion
from talentscreen.retrieval.pipeline import (
    GenerationUnavailableError,
    RetrievalUnavailableError,
    run_query_pipeline,
)

app = FastAPI(title="TalentScreen API", version="0.6.0")

_settings = get_settings()
_origins = [origin.strip() for origin in _settings.cors_origins.split(",") if origin.strip()]
if _origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(agents_router)
app.include_router(jobs_router)
app.include_router(mcp_router)


class HealthResponse(BaseModel):
    status: str
    services: dict[str, str]


class IngestResponse(BaseModel):
    document_id: str
    job_id: str
    status: str
    idempotent_skip: bool = False


class Citation(BaseModel):
    chunk_id: str
    quote: str


class CitationValidation(BaseModel):
    valid_count: int
    invalid_chunk_ids: list[str]
    all_valid: bool


class AnswerPayload(BaseModel):
    answer: str
    citations: list[Citation]
    confidence: float
    citation_validation: CitationValidation
    model: str | None = None
    llm_cached: bool | None = None
    skipped: bool | None = None


class QueryHit(BaseModel):
    chunk_id: str
    document_id: str
    doc_type: str
    filename: str | None = None
    text: str | None = None
    score: float
    dense_score: float | None = None


class QueryRequest(BaseModel):
    query: str
    tenant_id: str = Field(default_factory=lambda: get_settings().default_tenant_id)
    top_k: int = 5
    doc_type: str | None = None
    generate_answer: bool = True
    use_cache: bool = True
    retrieval_mode: str = Field(default_factory=lambda: get_settings().retrieval_mode)


class QueryResponse(BaseModel):
    query: str
    sanitized_query: str
    rewritten_queries: list[str]
    expanded_query: str
    expansion_terms: list[str]
    pii_entities: list[str]
    pii_engine: str
    retrieval_mode: str
    cache_hit: bool
    cache_type: str | None = None
    dense_hit_count: int
    fused_hit_count: int | None = None
    hits: list[QueryHit]
    answer: AnswerPayload | None = None
    generation_error: str | None = None
    trace_id: str | None = None
    semantic_cache_similarity: float | None = None


class DegradedResponse(BaseModel):
    milvus: str
    postgres: str
    redis: str
    minio: str


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", services={"api": "up"})


@app.get("/degraded", response_model=DegradedResponse)
async def degraded(session: AsyncSession = Depends(get_db_session)) -> DegradedResponse:
    statuses: dict[str, str] = {
        "postgres": "unknown",
        "milvus": "unknown",
        "redis": "unknown",
        "minio": "unknown",
    }

    try:
        await session.execute(__import__("sqlalchemy").text("SELECT 1"))
        statuses["postgres"] = "up"
    except Exception as exc:
        statuses["postgres"] = f"down: {exc}"

    try:
        from talentscreen.retrieval.milvus.client import connect_milvus

        connect_milvus()
        statuses["milvus"] = "up"
    except Exception as exc:
        statuses["milvus"] = f"down: {exc}"

    try:
        import redis

        client = redis.from_url(get_settings().redis_url)
        client.ping()
        statuses["redis"] = "up"
    except Exception as exc:
        statuses["redis"] = f"down: {exc}"

    try:
        from talentscreen.ingestion.storage import ensure_bucket

        ensure_bucket()
        statuses["minio"] = "up"
    except Exception as exc:
        statuses["minio"] = f"down: {exc}"

    return DegradedResponse(**statuses)


@app.post("/ingest", response_model=IngestResponse)
async def ingest(
    file: UploadFile = File(...),
    doc_type: str = Form("resume"),
    tenant_id: str = Form("demo-tenant"),
    session: AsyncSession = Depends(get_db_session),
    auth: AuthContext = Depends(require_recruiter),
) -> IngestResponse:
    tenant_id = auth.tenant_id
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Empty file")

    object_key = f"{tenant_id}/{uuid.uuid4()}/{file.filename}"
    content_type = file.content_type or "application/octet-stream"
    upload_bytes(object_key, file_bytes, content_type=content_type)

    document, is_new = await register_upload(
        session,
        tenant_id=tenant_id,
        filename=file.filename or "upload.bin",
        file_bytes=file_bytes,
        doc_type=doc_type,
        minio_key=object_key,
        mime_type=file.content_type,
    )
    await session.commit()

    if not is_new and document.status == "completed":
        return IngestResponse(
            document_id=str(document.document_id),
            job_id="",
            status="skipped",
            idempotent_skip=True,
        )

    job_id = await enqueue_ingestion(str(document.document_id))
    return IngestResponse(
        document_id=str(document.document_id),
        job_id=job_id,
        status="queued",
        idempotent_skip=not is_new,
    )


@app.post("/query", response_model=QueryResponse)
async def query(
    body: QueryRequest,
    session: AsyncSession = Depends(get_db_session),
    auth: AuthContext = Depends(require_recruiter),
) -> QueryResponse:
    if not body.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    try:
        assert_safe_prompt(body.query)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    tenant_id = auth.tenant_id
    mode = body.retrieval_mode if body.retrieval_mode in ("hybrid", "dense") else "hybrid"
    try:
        result = await run_query_pipeline(
            session,
            query=body.query,
            tenant_id=tenant_id,
            top_k=body.top_k,
            doc_type=body.doc_type,
            generate_answer_flag=body.generate_answer,
            use_cache=body.use_cache,
            retrieval_mode=mode,
        )
    except RetrievalUnavailableError as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "retrieval_unavailable",
                "message": "Milvus or embedding service is unavailable.",
                "detail": str(exc),
            },
        ) from exc
    except GenerationUnavailableError as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "generation_unavailable",
                "message": "LLM generation failed and no retrieval context was available.",
                "detail": str(exc),
            },
        ) from exc

    if not result["hits"] and not result.get("answer"):
        return QueryResponse(
            query=result["query"],
            sanitized_query=result["sanitized_query"],
            rewritten_queries=result.get("rewritten_queries", []),
            expanded_query=result["expanded_query"],
            expansion_terms=result["expansion_terms"],
            pii_entities=result["pii_entities"],
            pii_engine=result["pii_engine"],
            retrieval_mode=result.get("retrieval_mode", "hybrid"),
            cache_hit=result["cache_hit"],
            cache_type=result.get("cache_type"),
            dense_hit_count=result["dense_hit_count"],
            fused_hit_count=result.get("fused_hit_count"),
            hits=[],
            answer=AnswerPayload(
                answer=(
                    "No matching documents found. "
                    "Try uploading resumes or interview notes first."
                ),
                citations=[],
                confidence=0.0,
                citation_validation=CitationValidation(
                    valid_count=0,
                    invalid_chunk_ids=[],
                    all_valid=True,
                ),
                skipped=True,
            )
            if body.generate_answer
            else None,
            generation_error=result.get("generation_error"),
            trace_id=result.get("trace_id"),
        )

    answer = None
    if result.get("answer"):
        answer = AnswerPayload(**result["answer"])

    return QueryResponse(
        query=result["query"],
        sanitized_query=result["sanitized_query"],
        rewritten_queries=result.get("rewritten_queries", []),
        expanded_query=result["expanded_query"],
        expansion_terms=result["expansion_terms"],
        pii_entities=result["pii_entities"],
        pii_engine=result["pii_engine"],
        retrieval_mode=result.get("retrieval_mode", "hybrid"),
        cache_hit=result["cache_hit"],
        cache_type=result.get("cache_type"),
        dense_hit_count=result["dense_hit_count"],
        fused_hit_count=result.get("fused_hit_count"),
        hits=[QueryHit(**hit) for hit in result["hits"]],
        answer=answer,
        generation_error=result.get("generation_error"),
        trace_id=result.get("trace_id"),
        semantic_cache_similarity=result.get("semantic_cache_similarity"),
    )


def run_server() -> None:
    import uvicorn

    uvicorn.run("talentscreen.api.main:app", host="0.0.0.0", port=8000, reload=True)
