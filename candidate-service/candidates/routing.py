from django.urls import path
from candidates.websockets.consumer import CandidateNotificationConsumer

websocket_urlpatterns = [
    path(
        "ws/notifications/<int:candidate_id>",
        CandidateNotificationConsumer.as_asgi(),
    ),
]
