from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.response import Response

from jobs.models import Application
from jobs.serializers.application_serializer import ApplicationSerializer


class ApplicationViewSet(viewsets.ViewSet):
    """
    ViewSet handling partial update action for Application:
    - PATCH  /applications/{id} -> partial_update
    """

    def partial_update(self, request, pk=None):
        instance = get_object_or_404(Application, pk=pk)
        serializer = ApplicationSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
