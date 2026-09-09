from datetime import timedelta

from minio import Minio
from django.conf import settings


# Django → MinIO
internal_client = Minio(
    settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=settings.MINIO_SECURE,
)


# Browser-facing presigned URLs
public_client = Minio(
    settings.MINIO_PUBLIC_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=settings.MINIO_PUBLIC_SECURE,
    region="us-east-1",
    secure=True,
)


def ensure_bucket_exists():
    bucket = settings.MINIO_BUCKET

    if not internal_client.bucket_exists(bucket):
        internal_client.make_bucket(bucket)


def generate_upload_url(object_name):
    ensure_bucket_exists()

    return public_client.presigned_put_object(
        settings.MINIO_BUCKET,
        object_name,
        expires=timedelta(minutes=10),
    )


def generate_download_url(object_name):
    return public_client.presigned_get_object(
        settings.MINIO_BUCKET,
        object_name,
        expires=timedelta(minutes=10),
    )
