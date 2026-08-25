from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.response import Response

from candidates.models import Candidate
from candidates.serializers.candidate_serializer import CandidateSerializer

from candidates.tasks import index_candidate_in_opensearch
from candidates.search import delete_candidate

class CandidateViewSet(viewsets.ViewSet):
    """
    ViewSet for handling candidate registration, viewing profile, partial updates, and deletion.
    """

    def create(self, request):
        """
        POST /api/candidates/ - Register a new candidate.
        """
        serializer = CandidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        candidate = serializer.save()

        index_candidate_in_opensearch.delay(candidate.id)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None):
        """
        GET /api/candidates/{id}/ - View profile by candidate ID.
        """
        candidate = get_object_or_404(Candidate, pk=pk)
        serializer = CandidateSerializer(candidate)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def partial_update(self, request, pk=None):
        """
        PATCH /api/candidates/{id}/ - Partial update candidate profile.
        """
        candidate = get_object_or_404(Candidate, pk=pk)
        serializer = CandidateSerializer(candidate, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        candidate = serializer.save()

        index_candidate_in_opensearch.delay(candidate.id)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, pk=None):
        """
        DELETE /api/candidates/{id}/ - Delete candidate profile.
        """
        candidate = get_object_or_404(Candidate, pk=pk)

        delete_candidate(candidate.id)
        candidate.delete()
        return Response({"message": "Candidate deleted successfully."}, status=status.HTTP_200_OK)
