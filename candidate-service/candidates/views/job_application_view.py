from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated

from candidates.models import JobApplication
from candidates.serializers import JobApplicationSerializer
from candidates.kafka_producer import publish_event

from candidates.search import list_applications


class JobApplicationViewSet(viewsets.ViewSet):
    """
    ViewSet handling JobApplication:

    GET  /applications/       -> list
    GET  /applications/{id}/  -> retrieve
    POST /applications/       -> create
    """

    permission_classes = [IsAuthenticated]

    def list(self, request):
        candidate_id = request.user.candidate_profile.id

        applications = list_applications(candidate_id)

        return Response(
            applications,
            status=status.HTTP_200_OK
        )

    def retrieve(self, request, pk=None):
        application = get_object_or_404(
            JobApplication,
            pk=pk,
            candidate_id = request.user.candidate_profile.id
        )

        serializer = JobApplicationSerializer(application)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    def create(self, request):
        serializer = JobApplicationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        application = serializer.save()

        candidate = application.candidate

        publish_event('application.submitted', str(application.job_id), {
                'event_type':   'application.submitted',
                'job_id':       application.job_id,
                'job_title':    application.job_title,
                'candidate_id': candidate.id,
                'candidate_data': {              # ← everything in one block
                    'name':             candidate.name,
                    'email':            candidate.email,
                    'phone':            candidate.phone,
                    'skills':           candidate.skills,
                    'location':         candidate.location,
                    'experience_years': candidate.experience_years,
                    'resume_text':      candidate.resume_text,
                },
                'cover_letter': application.cover_letter,
            })

        return Response(
            JobApplicationSerializer(application).data,
            status=status.HTTP_201_CREATED
        )