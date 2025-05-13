from channels.generic.websocket import AsyncWebsocketConsumer
import json

class VendingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Extract vending machine serial number from the URL route
        self.serial_number = self.scope['url_route']['kwargs']['serial_number']
        self.group_name = f"vending_{self.serial_number}"

        # Join the WebSocket group for this vending machine
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()  # Accept the WebSocket connection

    async def disconnect(self, close_code):
        # Leave the WebSocket group on disconnect
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def vending_update(self, event):
        # Send vending machine data to the front end
        await self.send(text_data=json.dumps(event['machine']))
