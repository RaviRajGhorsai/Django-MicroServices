from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action

from jobs.models import Job, Application
from jobs.serializers.job_serializer import JobSerializer
from jobs.serializers.application_serializer import ApplicationSerializer

from jobs.kafka_producer import publish_event
from jobs.tasks import index_job_in_opensearch
from jobs.search import search_applicants, delete_job

class JobViewSet(viewsets.ViewSet):
    """
    ViewSet handling CRUD actions for Job:
    - POST   /jobs/     -> create
    - GET    /jobs/     -> list
    - GET    /jobs/{id} -> retrieve
    - PATCH  /jobs/{id} -> partial_update
    - DELETE /jobs/{id} -> destroy
    """

    def create(self, request):
        serializer = JobSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        job = serializer.save()

        print("Job created successfully")
        index_job_in_opensearch.delay(job.id)
        publish_event('job.created', str(job.id), {
            'event_type':      'job.created',
            'job_id':          job.id,
            'title':           job.title,
            'company':         job.company,
            'location':        job.location,
            'skills_required': job.skills_required,
        })

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def list(self, request):
        queryset = Job.objects.all()
        serializer = JobSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        instance = get_object_or_404(Job, pk=pk)
        serializer = JobSerializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def partial_update(self, request, pk=None):
        instance = get_object_or_404(Job, pk=pk)
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

        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, pk=None):
        instance = get_object_or_404(Job, pk=pk)
        instance.delete()
        delete_job(instance.id)

        return Response({"message": "Job deleted successfully."}, status=status.HTTP_204_NO_CONTENT)

    action(detail=True, methods=['get'], url_path='applicants')
    def applicants(self, request, pk=None):
        """GET /api/jobs/{id}/applicants/ — DB list"""
        qs = Application.objects.filter(job_id=pk).order_by('-applied_at')
        
        serializer = ApplicationSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='applicants/search')
    def applicants_search(self, request, pk=None):
        """GET /api/jobs/{id}/applicants/search/ — OpenSearch"""
        results = search_applicants(
            job_id=int(pk),
            query=request.query_params.get('q'),
            skills=request.query_params.getlist('skills'),
            location=request.query_params.get('location'),
            min_experience=request.query_params.get('min_experience'),
            status=request.query_params.get('status'),
        )
        return Response({'count': len(results), 'results': results})
