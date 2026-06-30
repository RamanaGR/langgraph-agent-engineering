from arq import create_pool
from arq.connections import RedisSettings

from talentscreen.config import get_settings
from talentscreen.db.session import get_session_factory
from talentscreen.ingestion.pipeline import process_document_ingestion


async def ingest_document_task(ctx, document_id: str) -> dict:
    factory = get_session_factory()
    async with factory() as session:
        return await process_document_ingestion(session, document_id)


class WorkerSettings:
    functions = [ingest_document_task]
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url)
    max_jobs = 4


async def enqueue_ingestion(document_id: str) -> str:
    redis = await create_pool(RedisSettings.from_dsn(get_settings().redis_url))
    job = await redis.enqueue_job("ingest_document_task", document_id)
    return job.job_id if job else ""


def run_worker_cli() -> None:
    import asyncio

    from arq import run_worker

    asyncio.run(run_worker(WorkerSettings))
