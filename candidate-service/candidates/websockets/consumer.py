from channels.generic.websocket import AsyncJsonWebsocketConsumer


class CandidateNotificationConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        self.candidate_id = self.scope["url_route"]["kwargs"]["candidate_id"]

        self.group_name = f"candidate_{self.candidate_id}"

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name,
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name,
        )

    async def notification(self, event):
        await self.send_json(event["data"])
