from django.shortcuts import get_object_or_404

from rest_framework import viewsets, status
from rest_framework.request import Request
from rest_framework.response import Response

from jobs.models import Application
from jobs.serializers.application_serializer import ApplicationSerializer
from jobs.kafka_producer import publish_event
from jobs.search import update_application_status_in_os, list_applications


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
        # queryset = Application.objects.filter(
        #     job__posted_by=request.user
        # ).order_by('-applied_at')

        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))
        status_filter = request.query_params.get("status")

        result = list_applications(
            posted_by=request.user.id,
            status=status_filter,
            page=page,
            page_size=page_size,
        )

        # serializer = ApplicationSerializer(queryset, many=True)
        return Response({
            'data':    result,
            'message': 'Applications retrieved successfully.',
        }, status=status.HTTP_200_OK)

    def retrieve(self, request: Request, pk=None):
        instance   = self._get_own_application(pk, request)
        serializer = ApplicationSerializer(instance)
        return Response({
            'data':    serializer.data,
            'message': 'Application retrieved successfully.',
        }, status=status.HTTP_200_OK)

    def partial_update(self, request: Request, pk=None):
        instance   = self._get_own_application(pk, request)
        old_status = instance.status
        new_status = request.data.get('status')

        serializer = ApplicationSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        if new_status and new_status != old_status:
            # Keep OpenSearch in sync
            update_application_status_in_os(instance.id, new_status)

            # Notify candidate-service via Kafka
            publish_event(
                'application.status_updated',
                str(instance.job_id),
                {
                    'event_type':   'application.status_updated',
                    'job_id':       instance.job_id,
                    'candidate_id': instance.candidate_id,
                    'application_id': instance.id,
                    'new_status':   new_status,
                }
            )

        return Response({
            'data':    serializer.data,
            'message': 'Application updated successfully.',
        }, status=status.HTTP_200_OK)