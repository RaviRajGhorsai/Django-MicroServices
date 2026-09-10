from django.shortcuts import get_object_or_404
import logging
from django.db import transaction
from django.utils import timezone

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from opensearchpy.exceptions import NotFoundError

from jobs.models import Application, OutBoxEvent
from jobs.serializers.application_serializer import ApplicationSerializer
from jobs.kafka_producer import publish_event
from jobs.search import (
    update_application_status_in_os,
    list_applications,
    get_application,
)
from jobs.services.minio import generate_download_url


logger = logging.getLogger(__name__)


class ApplicationViewSet(viewsets.ViewSet):
    """
    HR-facing application management.
    All actions are scoped to applications belonging to the HR's own jobs.

    GET   /api/applications/        list
    GET   /api/applications/{id}/   retrieve
    PATCH /api/applications/{id}/   partial_update  (accept / reject)
    """

    def _get_own_application(self, pk, request):
        """
        Returns the application only if it belongs to a job posted by this HR.
        Raises 404 otherwise.
        """
        return get_object_or_404(
            Application,
            pk=pk,
            job__posted_by=request.user,  # ← double underscore: follows FK to Job
        )

    def list(self, request: Request):
        # Only applications for this HR's jobs
        logger.info(
            "HR requested application list",
            extra={
                "user_id": request.user.id,
                "page": request.query_params.get("page", 1),
                "page_size": request.query_params.get("page_size", 20),
                "status_filter": request.query_params.get("status"),
            },
        )

        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))
        status_filter = request.query_params.get("status")

        try:
            result = list_applications(
                posted_by=request.user.id,
                status=status_filter,
                page=page,
                page_size=page_size,
            )

            logger.info(
                f"Applications retrieved  successfully -- {request.user.username}",
                extra={
                    "user_id": request.user.id,
                    "page": page,
                    "page_size": page_size,
                },
            )

            # serializer = ApplicationSerializer(queryset, many=True)
            return Response(
                {
                    "data": result,
                    "message": "Applications retrieved successfully.",
                },
                status=status.HTTP_200_OK,
            )

        except NotFoundError as exc:
            logger.warning(
                "Application search index is not available",
                extra={
                    "user_id": request.user.id,
                },
            )

            return Response(
                {
                    "count": 0,
                    "results": [],
                    "message": "Application search index is not available yet.",
                },
                status=status.HTTP_200_OK,
            )

    def retrieve(self, request: Request, pk=None):

        logger.info(
            "HR requested application details",
            extra={
                "user_id": request.user.id,
                "application_id": pk,
            },
        )
        try:
            result = get_application(pk)

            logger.info(
                "Application retrieved successfully",
                extra={
                    "user_id": request.user.id,
                    "application_id": pk,
                },
            )

            return Response(
                {
                    "data": result,
                    "message": "Application retrieved successfully.",
                },
                status=status.HTTP_200_OK,
            )
        except Exception:
            logger.exception(
                "Failed to retrieve application",
                extra={
                    "user_id": request.user.id,
                    "application_id": pk,
                },
            )
            raise

    def partial_update(self, request: Request, pk=None):

        logger.info(
            "HR requested application status update",
            extra={
                "user_id": request.user.id,
                "application_id": pk,
                "requested_status": request.data.get("status"),
            },
        )

        instance = self._get_own_application(pk, request)
        old_status = instance.status
        new_status = request.data.get("status")

        serializer = ApplicationSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            serializer.save()

            event = OutBoxEvent.objects.create(
                topic="application.status_updated",
                key=str(instance.job_id),
                payload={
                    "event_type": "application.status_updated",
                    "job_id": instance.job_id,
                    "candidate_id": instance.candidate_id,
                    "job_title": instance.job.title,
                    "application_id": instance.id,
                    "new_status": new_status,
                },
            )

            logger.info(
                "Application updated in database",
                extra={
                    "user_id": request.user.id,
                    "application_id": instance.id,
                    "old_status": old_status,
                    "new_status": new_status,
                },
            )

        if new_status and new_status != old_status:
            try:
                # Keep OpenSearch in sync
                update_application_status_in_os(instance.id, new_status)

                logger.info(
                    "Application status updated in OpenSearch",
                    extra={
                        "application_id": instance.id,
                        "old_status": old_status,
                        "new_status": new_status,
                    },
                )

                # Notify candidate-service via Kafka
                publish_event(
                    "application.status_updated",
                    str(instance.job_id),
                    {
                        "event_type": "application.status_updated",
                        "job_id": instance.job_id,
                        "candidate_id": instance.candidate_id,
                        "application_id": instance.id,
                        "job_title": instance.job.title,
                        "new_status": new_status,
                    },
                )
                
                # update the outbox event after successful kafka event push
                event.status = OutBoxEvent.Status.PUBLISHED
                event.published_at = timezone.now()

                event.save(
                    update_fields=[
                        "status",
                        "published_at",
                    ]
                )
            except Exception:
                logger.exception(
                    "Failed to update application status in OpenSearch",
                    extra={
                        "application_id": instance.id,
                        "new_status": new_status,
                    },
                )
                raise

        return Response(
            {
                "data": serializer.data,
                "message": "Application updated successfully.",
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"], url_path="resume/download")
    def download(self, request):
        resume_object_key = request.query_params.get("resume_object_key")

        if not resume_object_key:
            return Response(
                {"detail": "resume_object_key is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            download_url = generate_download_url(resume_object_key)
        except Exception:
            return Response(
                {"detail": "Failed to generate download URL."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {
                "download_url": download_url,
            },
            status=status.HTTP_200_OK,
        )
