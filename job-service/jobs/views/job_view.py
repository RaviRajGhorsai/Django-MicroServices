from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.response import Response

from jobs.models import Job
from jobs.serializers.job_serializer import JobSerializer


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
        serializer.save()
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
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, pk=None):
        instance = get_object_or_404(Job, pk=pk)
        instance.delete()
        return Response({"message": "Job deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
