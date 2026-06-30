"""Job listings and candidate application routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from talentscreen.api.auth import AuthContext, require_any_auth, require_candidate
from talentscreen.db.models import Application, Job
from talentscreen.db.session import get_db_session
from talentscreen.ingestion.pipeline import register_upload
from talentscreen.ingestion.storage import upload_bytes
from talentscreen.ingestion.worker import enqueue_ingestion

router = APIRouter(tags=["jobs"])


class JobSummary(BaseModel):
    job_id: str
    title: str
    location: str | None
    required_skills: list[str]
    created_at: str | None = None


class JobDetail(JobSummary):
    description: str | None


class ApplicationResponse(BaseModel):
    application_id: str
    job_id: str
    job_title: str | None = None
    full_name: str
    email: str
    status: str
    resume_document_id: str | None = None
    notes: str | None = None
    created_at: str | None = None


class ApplicationCreateResponse(BaseModel):
    application_id: str
    status: str
    resume_document_id: str | None = None
    resume_status: str | None = None


@router.get("/jobs", response_model=list[JobSummary])
async def list_jobs(
    session: AsyncSession = Depends(get_db_session),
    auth: AuthContext = Depends(require_any_auth),
) -> list[JobSummary]:
    tenant_id = auth.tenant_id
    result = await session.execute(
        select(Job).where(Job.tenant_id == tenant_id).order_by(Job.created_at.desc())
    )
    jobs = result.scalars().all()
    return [
        JobSummary(
            job_id=str(job.job_id),
            title=job.title,
            location=job.location,
            required_skills=list(job.required_skills or []),
            created_at=job.created_at.isoformat() if job.created_at else None,
        )
        for job in jobs
    ]


@router.get("/jobs/{job_id}", response_model=JobDetail)
async def get_job(
    job_id: str,
    session: AsyncSession = Depends(get_db_session),
    auth: AuthContext = Depends(require_any_auth),
) -> JobDetail:
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid job_id") from exc

    result = await session.execute(
        select(Job).where(Job.job_id == job_uuid, Job.tenant_id == auth.tenant_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobDetail(
        job_id=str(job.job_id),
        title=job.title,
        location=job.location,
        required_skills=list(job.required_skills or []),
        description=job.description,
        created_at=job.created_at.isoformat() if job.created_at else None,
    )


@router.post("/applications", response_model=ApplicationCreateResponse)
async def create_application(
    job_id: str = Form(...),
    full_name: str = Form(...),
    email: str = Form(...),
    notes: str = Form(""),
    resume: UploadFile | None = File(None),
    session: AsyncSession = Depends(get_db_session),
    auth: AuthContext = Depends(require_candidate),
) -> ApplicationCreateResponse:
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid job_id") from exc

    result = await session.execute(
        select(Job).where(Job.job_id == job_uuid, Job.tenant_id == auth.tenant_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    resume_doc_id: uuid.UUID | None = None
    resume_status: str | None = None

    if resume and resume.filename:
        file_bytes = await resume.read()
        if file_bytes:
            tenant_id = auth.tenant_id
            object_key = f"{tenant_id}/{uuid.uuid4()}/{resume.filename}"
            upload_bytes(
                object_key,
                file_bytes,
                content_type=resume.content_type or "application/octet-stream",
            )
            document, _is_new = await register_upload(
                session,
                tenant_id=tenant_id,
                filename=resume.filename,
                file_bytes=file_bytes,
                doc_type="resume",
                minio_key=object_key,
                mime_type=resume.content_type,
            )
            resume_doc_id = document.document_id
            resume_status = "queued"
            await enqueue_ingestion(str(document.document_id))

    application = Application(
        tenant_id=auth.tenant_id,
        job_id=job_uuid,
        full_name=full_name.strip(),
        email=email.strip().lower(),
        resume_document_id=resume_doc_id,
        status="submitted",
        notes=notes.strip() or None,
    )
    session.add(application)
    await session.commit()
    await session.refresh(application)

    return ApplicationCreateResponse(
        application_id=str(application.application_id),
        status=application.status,
        resume_document_id=str(resume_doc_id) if resume_doc_id else None,
        resume_status=resume_status,
    )


@router.get("/applications/{application_id}", response_model=ApplicationResponse)
async def get_application(
    application_id: str,
    session: AsyncSession = Depends(get_db_session),
    auth: AuthContext = Depends(require_any_auth),
) -> ApplicationResponse:
    try:
        app_uuid = uuid.UUID(application_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid application_id") from exc

    result = await session.execute(
        select(Application, Job)
        .join(Job, Application.job_id == Job.job_id)
        .where(Application.application_id == app_uuid, Application.tenant_id == auth.tenant_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Application not found")

    application, job = row
    return ApplicationResponse(
        application_id=str(application.application_id),
        job_id=str(application.job_id),
        job_title=job.title,
        full_name=application.full_name,
        email=application.email,
        status=application.status,
        resume_document_id=str(application.resume_document_id)
        if application.resume_document_id
        else None,
        notes=application.notes,
        created_at=application.created_at.isoformat() if application.created_at else None,
    )


@router.get("/applications", response_model=list[ApplicationResponse])
async def list_applications(
    email: EmailStr | None = None,
    session: AsyncSession = Depends(get_db_session),
    auth: AuthContext = Depends(require_any_auth),
) -> list[ApplicationResponse]:
    tenant_id = auth.tenant_id
    stmt = (
        select(Application, Job)
        .join(Job, Application.job_id == Job.job_id)
        .where(Application.tenant_id == tenant_id)
        .order_by(Application.created_at.desc())
    )
    if email:
        stmt = stmt.where(Application.email == email.lower())

    result = await session.execute(stmt)
    rows = result.all()
    return [
        ApplicationResponse(
            application_id=str(app.application_id),
            job_id=str(app.job_id),
            job_title=job.title,
            full_name=app.full_name,
            email=app.email,
            status=app.status,
            resume_document_id=str(app.resume_document_id) if app.resume_document_id else None,
            notes=app.notes,
            created_at=app.created_at.isoformat() if app.created_at else None,
        )
        for app, job in rows
    ]
