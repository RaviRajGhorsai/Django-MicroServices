import logging

from django.shortcuts import get_object_or_404

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from jobs.models import Job
from jobs.serializers.job_serializer import JobSerializer
from jobs.kafka_producer import publish_event
from jobs.tasks import index_job_in_opensearch
from jobs.search import search_applicants, delete_job

logger = logging.getLogger(__name__)


class JobViewSet(viewsets.ViewSet):
    """
    HR-facing job management.
    All actions are scoped to jobs posted by the authenticated HR.

    POST   /api/jobs/                        create
    GET    /api/jobs/                        list
    GET    /api/jobs/{id}/                   retrieve
    PATCH  /api/jobs/{id}/                   partial_update
    DELETE /api/jobs/{id}/                   destroy
    GET    /api/jobs/{id}/applicants/        applicants  (DB list)
    GET    /api/jobs/{id}/applicants/search/ applicants_search (OpenSearch)
    """

    # ── helpers ───────────────────────────────────────────

    def _get_own_job(self, pk, request):
        """
        Returns the job only if it belongs to the authenticated HR.
        Raises 404 otherwise — intentionally vague to avoid leaking existence.
        """
        return get_object_or_404(Job, pk=pk, posted_by=request.user)


    def create(self, request: Request):
        serializer = JobSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        job = serializer.save(posted_by=request.user)  # ← link job to HR

        index_job_in_opensearch.delay(job.id)
        publish_event('job.created', str(job.id), {
            'event_type':      'job.created',
            'job_id':          job.id,
            'title':           job.title,
            'company':         job.company,
            'location':        job.location,
            'skills_required': job.skills_required,
        })

        return Response({
            'data':    serializer.data,
            'message': 'Job created successfully.',
        }, status=status.HTTP_201_CREATED)

    def list(self, request: Request):
        # HR only sees their own jobs
        queryset   = Job.objects.filter(posted_by=request.user).order_by('-created_at')
        serializer = JobSerializer(queryset, many=True)
        return Response({
            'data':    serializer.data,
            'message': 'Jobs retrieved successfully.',
        }, status=status.HTTP_200_OK)

    def retrieve(self, request: Request, pk=None):
        instance   = self._get_own_job(pk, request)
        serializer = JobSerializer(instance)
        return Response({
            'data':    serializer.data,
            'message': 'Job retrieved successfully.',
        }, status=status.HTTP_200_OK)

    def partial_update(self, request: Request, pk=None):
        instance   = self._get_own_job(pk, request)
        serializer = JobSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        job = serializer.save()

        index_job_in_opensearch.delay(job.id)
        publish_event('job.updated', str(job.id), {
            'event_type': 'job.updated',
            'job_id':     job.id,
            'title':      job.title,
            'status':     job.status,
        })

        return Response({
            'data':    serializer.data,
            'message': 'Job updated successfully.',
        }, status=status.HTTP_200_OK)

    def destroy(self, request: Request, pk=None):
        instance = self._get_own_job(pk, request)

        delete_job(instance.id)   # remove from OpenSearch
        instance.delete()          # remove from DB

        return Response({
            'message': 'Job deleted successfully.',
        }, status=status.HTTP_204_NO_CONTENT)
