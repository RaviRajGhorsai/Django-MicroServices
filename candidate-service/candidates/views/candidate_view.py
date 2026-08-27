from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from candidates.models import Candidate
from candidates.serializers.candidate_serializer import CandidateDetailSerializer

from candidates.tasks import index_candidate_in_opensearch
from candidates.search import delete_candidate

class CandidateViewSet(viewsets.ViewSet):
    """
    ViewSet for handling candidate registration, viewing profile, partial updates, and deletion.
    """

    # def create(self, request):
    #     """
    #     POST /api/candidates/ - Register a new candidate.
    #     """
    #     serializer = CandidateDetailSerializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)
    #     candidate = serializer.save()

    #     index_candidate_in_opensearch.delay(candidate.id)

    #     return Response(serializer.data, status=status.HTTP_201_CREATED)
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request: Request):
        
        try:
            candidate_profile = request.user.candidate_profile
        except User.candidate_profile.RelatedObjectDoesNotExist:
            
            return Response(
            {
                'message': 'No candidate profile found.',
            },
            status=status.HTTP_404_NOT_FOUND,
        )


        return Response({
            'data':    CandidateDetailSerializer(candidate_profile).data,
            'message': 'Profile retrieved successfully.',
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['patch'], url_path='me/update')
    def edit(self, request):
        try:
            candidate = get_object_or_404(Candidate, pk=request.user.candidate_profile.id)
        except User.candidate_profile.RelatedObjectDoesNotExist:
            
            return Response(
            {
                'message': 'No candidate profile found.',
            },
            status=status.HTTP_404_NOT_FOUND,
        )

        serializer = CandidateDetailSerializer(candidate, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        candidate = serializer.save()

        index_candidate_in_opensearch.delay(candidate.id)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['delete'], url_path='me/delete')
    def delete(self, request):
        try:
            candidate = get_object_or_404(Candidate, pk=request.user.candidate_profile.id)
        except User.candidate_profile.RelatedObjectDoesNotExist:
            
            return Response(
            {
                'message': 'No candidate profile found.',
            },
            status=status.HTTP_404_NOT_FOUND,
        )

        delete_candidate(candidate.id)
        candidate.delete()
        return Response({"message": "Candidate deleted successfully."}, status=status.HTTP_200_OK)
