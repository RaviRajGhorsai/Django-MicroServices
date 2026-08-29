from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from jobs.search import search_applicants


class CandidateView(viewsets.ViewSet):

    @action(
        detail=False,
        methods=["get"],
        url_path="list",
    )
    def applicants(self, request: Request):
        """
        GET /api/applicants/

        HR searches applicants who applied to jobs posted by them.

        Supports:
        ?q=python
        ?skills=Python
        ?skills=Django
        ?location=Kathmandu
        ?min_experience=2
        ?status=pending
        """

        results = search_applicants(
            posted_by=request.user.id,
            query=request.query_params.get("q"),
            skills=request.query_params.getlist("skills"),
            location=request.query_params.get("location"),
            min_experience=request.query_params.get("min_experience"),
            status=request.query_params.get("status"),
        )

        return Response(
            {
                "data": results,
                "count": len(results),
                "message": "Applicants retrieved successfully.",
            },
            status=status.HTTP_200_OK,
        )     
