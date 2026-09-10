from django.urls import path
from jobs.websockets.consumer import CandidateNotificationConsumer

websocket_urlpatterns = [
    path(
        "ws/notifications/<int:user_id>",
        CandidateNotificationConsumer.as_asgi(),
    ),
]
