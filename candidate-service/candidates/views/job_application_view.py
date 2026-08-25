from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404

from candidates.models import JobApplication
from candidates.serializers import JobApplicationSerializer
from candidates.kafka_producer import publish_event


class JobApplicationViewSet(viewsets.ViewSet):
    """
    ViewSet handling JobApplication:

    GET  /applications/       -> list
    GET  /applications/{id}/  -> retrieve
    POST /applications/       -> create
    """

    def list(self, request):
        candidate_id = request.query_params.get('candidate_id')

        queryset = JobApplication.objects.all().order_by('-applied_at')

        if candidate_id:
            queryset = queryset.filter(candidate_id=candidate_id)

        serializer = JobApplicationSerializer(queryset, many=True)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    def retrieve(self, request, pk=None):
        application = get_object_or_404(
            JobApplication,
            pk=pk
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

        publish_event(
            'application.submitted',
            str(application.job_id),
            {
                'event_type': 'application.submitted',
                'job_id': application.job_id,
                'job_title': application.job_title,
                'candidate_id': candidate.id,
                'candidate_name': candidate.name,
                'candidate_email': candidate.email,
                'candidate_skills': candidate.skills,
                'candidate_location': candidate.location,
                'experience_years': candidate.experience_years,
                'cover_letter': application.cover_letter,
            }
        )

        return Response(
            JobApplicationSerializer(application).data,
            status=status.HTTP_201_CREATED
        )