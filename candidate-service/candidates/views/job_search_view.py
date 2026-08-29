from rest_framework import viewsets, status
from rest_framework.response import Response
from opensearchpy.exceptions import NotFoundError
from candidates.search import search_jobs_from_opensearch, get_job_by_id

class JobSearchViewSet(viewsets.ViewSet):
    """Read-only — queries OpenSearch jobs index directly, no job-service HTTP call"""

    def list(self, request):
        try:
            results = search_jobs_from_opensearch(
                query=request.query_params.get('q'),
                location=request.query_params.get('location'),
                skills=request.query_params.getlist('skills'),
                salary_min=request.query_params.get('salary_min'),
            )

            return Response(
                {
                    'count': len(results),
                    'results': results,
                },
                status=status.HTTP_200_OK,
            )

        except NotFoundError as exc:
        # OpenSearch index does not exist
            if 'index_not_found_exception' in str(exc):
             return Response(
                {
                    'count': 0,
                    'results': [],
                    'message': 'Search index is not available yet.',
                },
                status=status.HTTP_200_OK,
            )

            raise  

    def retrieve(self, request, pk=None):
        """GET /api/search/jobs/{id}"""
        job = get_job_by_id(pk)
        if not job:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(job)
