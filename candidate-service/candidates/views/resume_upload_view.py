import uuid

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from candidates.services.minio import generate_upload_url


class ResumeUploadURLView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def create(self, request):

        candidate = request.user.candidate_profile

        filename = request.data.get("filename")

        if not filename:
            return Response(
                {"error": "filename is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Generate unique object name
        object_name = f"resumes/{candidate.id}/{uuid.uuid4()}-{filename}"

        upload_url = generate_upload_url(object_name)

        return Response(
            {
                "upload_url": upload_url,
                "object_key": object_name,
            },
            status=status.HTTP_200_OK,
        )
