from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.response import Response

from jobs.models import Application
from jobs.serializers.application_serializer import ApplicationSerializer

from jobs.kafka_producer import publish_event
from jobs.search import update_application_status_in_os

class ApplicationViewSet(viewsets.ViewSet):
    """
    ViewSet handling CRUD actions for Application:
  
    - GET    /applications/     -> list
    - GET    /applications/{id} -> retrieve
   
    - PATCH  /applications/{id} -> partial_update
   
    """

    def list(self, request):
        queryset = Application.objects.all()
        serializer = ApplicationSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        instance = get_object_or_404(Application, pk=pk)
        serializer = ApplicationSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    

    def partial_update(self, request, pk=None):
        instance = get_object_or_404(Application, pk=pk)

        old_status = instance.status
        new_status = request.data.get('status')

        serializer = ApplicationSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        if new_status and new_status != old_status:

            # Update OpenSearch
            update_application_status_in_os(
                instance.id,
                new_status
            )

            # Notify candidate-service through Kafka
            publish_event(
                'application.status_updated',
                str(instance.job_id),
                {
                    'event_type': 'application.status_updated',
                    'job_id': instance.job_id,
                    'candidate_id': instance.candidate_id,
                    'new_status': new_status,
                }
            )

        return Response(serializer.data, status=status.HTTP_200_OK)