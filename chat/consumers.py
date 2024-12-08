import json
from channels.generic.websocket import AsyncWebsocketConsumer
from boto3.dynamodb.conditions import Key
import boto3
from datetime import datetime
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()

# Initialize DynamoDB
dynamodb = boto3.resource(
    'dynamodb',
    region_name=settings.DYNAMODB['AWS_REGION'],
    aws_access_key_id=settings.DYNAMODB['AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=settings.DYNAMODB['AWS_SECRET_ACCESS_KEY']
)
table = dynamodb.Table(settings.DYNAMODB['TABLE_NAME'])

class ChatConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_group_name = None
        self.user = None

    async def connect(self):
        # Get the authenticated user
        self.user = self.scope["user"]

        # Check if the user is authenticated
        self.room_group_name = "global_chat"

        # Check if the user is authenticated
        if not self.scope["user"].is_authenticated:
            await self.close()  # Reject connection if the user is not authenticated
            return

        # Accept the WebSocket connection
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Ensure the room group name exists before trying to remove the group
        if hasattr(self, "room_group_name") and self.room_group_name:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        # Parse incoming data
        data = json.loads(text_data)
        message = data.get('message')

        # Ensure message content exists
        if not message:
            await self.send(text_data=json.dumps({
                'error': 'Message content cannot be empty.'
            }))
            return

        # Store message in DynamoDB
        timestamp = datetime.utcnow().isoformat()
        table.put_item(
            Item={
                'chat_id': 'global_chat',
                'timestamp': timestamp,
                'sender_id': str(self.user.id),  # Use authenticated user's ID
                'username': self.user.username,  # Optionally store the username
                'message': message,
            }
        )

        # Send message to the group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'sender_id': str(self.user.id),  # Include sender's ID
                'username': self.user.username,  # Include sender's username
                'message': message,
                'timestamp': timestamp,
            }
        )

    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'sender_id': event['sender_id'],
            'username': event['username'],  # Include the username in the message
            'message': event['message'],
            'timestamp': event['timestamp'],
        }))
