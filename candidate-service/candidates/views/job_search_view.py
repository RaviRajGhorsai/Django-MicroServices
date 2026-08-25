from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.response import Response
from candidates.search import search_jobs_from_opensearch, get_job_by_id

class JobSearchViewSet(viewsets.ViewSet):
    """Read-only — queries OpenSearch jobs index directly, no job-service HTTP call"""

    def list(self, request):
        """GET /api/jobs/search/"""
        results = search_jobs_from_opensearch(
            query=request.query_params.get('q'),
            location=request.query_params.get('location'),
            skills=request.query_params.getlist('skills'),
            salary_min=request.query_params.get('salary_min'),
        )
        return Response({'count': len(results), 'results': results})

    def retrieve(self, request, pk=None):
        """GET /api/jobs/{id}/"""
        job = get_job_by_id(pk)
        if not job:
            return Response({'detail': 'Not found.'}, status=404)
        return Response(job)
