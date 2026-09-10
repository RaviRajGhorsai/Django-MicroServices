from datetime import timedelta

from minio import Minio
from django.conf import settings

# Browser-facing presigned URLs
public_client = Minio(
    settings.MINIO_PUBLIC_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=settings.MINIO_PUBLIC_SECURE,
    region="us-east-1",
)


def generate_download_url(object_name):
    return public_client.presigned_get_object(
        settings.MINIO_BUCKET,
        object_name,
        expires=timedelta(minutes=10),
    )
