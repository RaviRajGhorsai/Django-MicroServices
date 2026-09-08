from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from opensearchpy.exceptions import NotFoundError
import logging
from django.db import transaction
from django.utils import timezone

from candidates.models import JobApplication, OutBoxEvent
from candidates.serializers import JobApplicationSerializer
from candidates.kafka_producer import publish_event

from candidates.search import list_applications

logger = logging.getLogger(__name__)


class JobApplicationViewSet(viewsets.ViewSet):
    """
    ViewSet handling JobApplication:

    GET  /applications/       -> list
    GET  /applications/{id}/  -> retrieve
    POST /applications/       -> create
    """

    permission_classes = [IsAuthenticated]

    def list(self, request):
        try:
            candidate_id = request.user.candidate_profile.id
            print("candidate id: ", candidate_id)
            # applications = list_applications(candidate_id)
            applications = JobApplication.objects.filter(candidate=candidate_id)
            serializer = JobApplicationSerializer(applications, many=True)

            return Response(serializer.data, status=status.HTTP_200_OK)
        except NotFoundError as exc:
            if "index_not_found_exception" in str(exc):
                return Response(
                    {
                        "count": 0,
                        "results": [],
                        "message": "Search index is not available yet.",
                    },
                    status=status.HTTP_200_OK,
                )

            raise

    def retrieve(self, request, pk=None):
        application = get_object_or_404(
            JobApplication, pk=pk, candidate_id=request.user.candidate_profile.id
        )

        serializer = JobApplicationSerializer(application)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request):

        serializer = JobApplicationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            application = serializer.save()

            candidate = application.candidate
            event = OutBoxEvent.objects.create(
                topic="application.submitted",
                key=str(application.job_id),
                payload={
                    "event_type": "application.submitted",
                    "job_id": application.job_id,
                    "job_title": application.job_title,
                    "candidate_id": candidate.id,
                    "candidate_data": {  # ← everything in one block
                        "name": candidate.name,
                        "email": candidate.email,
                        "phone": candidate.phone,
                        "skills": candidate.skills,
                        "location": candidate.location,
                        "experience_years": candidate.experience_years,
                        "resume_text": candidate.resume_text,
                    },
                    "cover_letter": application.cover_letter,
                },
            )
        try:
            publish_event(
                "application.submitted",
                str(application.job_id),
                {
                    "event_type": "application.submitted",
                    "job_id": application.job_id,
                    "job_title": application.job_title,
                    "candidate_id": candidate.id,
                    "candidate_data": {  # ← everything in one block
                        "name": candidate.name,
                        "email": candidate.email,
                        "phone": candidate.phone,
                        "skills": candidate.skills,
                        "location": candidate.location,
                        "experience_years": candidate.experience_years,
                        "resume_text": candidate.resume_text,
                    },
                    "cover_letter": application.cover_letter,
                },
            )

            event.status = OutBoxEvent.Status.PUBLISHED
            event.published_at = timezone.now()

            event.save(
                update_fields=[
                    "status",
                    "published_at",
                ]
            )

            logger.info(
                "Application submitted successfully | application_id=%s | job_id=%s | candidate_id=%s",
                application.id,
                application.job_id,
                candidate.id,
            )
            return Response(
                JobApplicationSerializer(application).data,
                status=status.HTTP_201_CREATED,
            )
        except Exception:
            logger.error("Application submitted event error.")
            return Response("Kafka push event failed", status=status.HTTP_200_OK)
