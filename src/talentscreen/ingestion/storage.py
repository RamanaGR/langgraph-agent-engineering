from io import BytesIO

from minio import Minio
from minio.error import S3Error

from talentscreen.config import get_settings


def get_minio_client() -> Minio:
    settings = get_settings()
    return Minio(
        settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure,
    )


def ensure_bucket() -> None:
    client = get_minio_client()
    settings = get_settings()
    if not client.bucket_exists(settings.minio_bucket):
        client.make_bucket(settings.minio_bucket)


def upload_bytes(key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
    ensure_bucket()
    client = get_minio_client()
    settings = get_settings()
    client.put_object(
        settings.minio_bucket,
        key,
        BytesIO(data),
        length=len(data),
        content_type=content_type,
    )
    return key


def download_bytes(key: str) -> bytes:
    client = get_minio_client()
    settings = get_settings()
    response = client.get_object(settings.minio_bucket, key)
    try:
        return response.read()
    finally:
        response.close()
        response.release_conn()


def object_exists(key: str) -> bool:
    client = get_minio_client()
    settings = get_settings()
    try:
        client.stat_object(settings.minio_bucket, key)
        return True
    except S3Error:
        return False
