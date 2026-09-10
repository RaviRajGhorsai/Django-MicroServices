from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def send_websocket_notification(candidate_id, data):
    channel_layer = get_channel_layer()

    async_to_sync(channel_layer.group_send)(
        f"candidate_{candidate_id}",
        {
            "type": "notification",
            "data": data,
        },
    )
