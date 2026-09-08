from rest_framework import viewsets

from config.database import logs_collection
from logs.serializers.log_serializer import LogSerializer

from rest_framework.pagination import PageNumberPagination


class LogPagination(PageNumberPagination):
    page_size = 15
    page_size_query_param = "page_size"
    max_page_size = 100


class LogViewSet(viewsets.ViewSet):
    pagination_class = LogPagination

    def list(self, request):
        query = {}

        service = request.query_params.get("service")
        level = request.query_params.get("level")
        logger = request.query_params.get("logger")
        search = request.query_params.get("search")

        if service:
            query["service"] = service

        if level:
            query["level"] = level

        if logger:
            query["logger"] = logger

        if search:
            query["message"] = {
                "$regex": search,
                "$options": "i",
            }

        logs = logs_collection.find(query).sort("timestamp", -1).limit(100)

        result = []

        for log in logs:
            result.append(
                {
                    "id": str(log["_id"]),
                    "service": log.get("service"),
                    "level": log.get("level"),
                    "logger": log.get("logger"),
                    "message": log.get("message"),
                    "timestamp": log.get("timestamp"),
                }
            )

        paginator = self.pagination_class()

        page = paginator.paginate_queryset(
            result,
            request,
            view=self,
        )


        serializer = LogSerializer(page, many=True)

        return paginator.get_paginated_response(
            serializer.data
        )
