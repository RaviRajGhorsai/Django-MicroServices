from datetime import timedelta
from minio import Minio
from django.conf import settings


client = Minio(
    settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=settings.MINIO_SECURE,
)


def generate_upload_url(object_name):
    return client.presigned_put_object(
        settings.MINIO_BUCKET,
        object_name,
        expires=timedelta(minutes=10),
    )


def generate_download_url(object_name):
    return client.presigned_get_object(
        settings.MINIO_BUCKET,
        object_name,
        expires=timedelta(minutes=10),
    )
