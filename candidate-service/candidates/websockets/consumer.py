from channels.generic.websocket import AsyncJsonWebsocketConsumer


class CandidateNotificationConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        self.candidate_id = self.scope["url_route"]["kwargs"]["candidate_id"]
        self.group_name = f"candidate_{self.candidate_id}"

        print(f"WS CONNECT: candidate={self.candidate_id}")
        print(f"WS CHANNEL: {self.channel_name}")
        print(f"WS GROUP: {self.group_name}")

        await self.accept()

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name,
        )

        print("WS GROUP ADD: OK")

    async def disconnect(self, close_code):
        print(f"WS DISCONNECT: {self.candidate_id}, code={close_code}")

        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name,
        )

    async def notification(self, event):
        print(f"WS NOTIFICATION: {event}")

        await self.send_json(event["data"])
