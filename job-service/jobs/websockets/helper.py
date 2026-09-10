from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def send_websocket_notification(user_id, data):
    channel_layer = get_channel_layer()
    
    group_name = f"HR_user_{user_id}"

    print(f"WS SEND GROUP: {group_name}")
    print(f"WS SEND DATA: {data}")

    try:
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "notification",
                "data": data,
            },
        )

        print("WS GROUP SEND: OK")

    except Exception as exc:
        print(f"WS GROUP SEND ERROR: {type(exc).__name__}: {exc}")
        raise
