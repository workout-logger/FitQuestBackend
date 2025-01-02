import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from boto3.dynamodb.conditions import Key
import boto3
from datetime import datetime
from django.conf import settings
from django.contrib.auth import get_user_model


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
        try:
            self.user = self.scope["user"]

            if self.user.is_authenticated:
                self.room_group_name = "global_chat"

                # Add user to WebSocket group
                await self.channel_layer.group_add(
                    self.room_group_name,
                    self.channel_name
                )
                await self.accept()

                # Send connection success message
                await self.send(text_data=json.dumps({
                    "type": "connection_established",
                    "message": "Connected successfully"
                }))

                # Load chat history after connection is established
                await self.fetch_and_send_messages()
            else:
                await self.close(code=4001)  # Custom code for authentication failure
        except Exception as e:
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": f"Connection error: {str(e)}"
            }))
            await self.close(code=4002)  # Custom code for general error

    async def disconnect(self, close_code):
        try:
            if hasattr(self, "room_group_name") and self.room_group_name:
                await self.channel_layer.group_discard(
                    self.room_group_name,
                    self.channel_name
                )
        except Exception as e:
            print(f"Error during disconnect: {str(e)}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            action = data.get("action")
            message = data.get("message")

            if action == "send" and message:
                if not message.strip():  # Check for empty or whitespace-only messages
                    return

                timestamp = datetime.utcnow().isoformat()

                # Store message first
                await self.store_message_in_dynamodb(message, timestamp)

                # Then broadcast to group
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "chat_message",
                        "message_data": {
                            "type": "chat_message",
                            "sender_id": str(self.user.id),
                            "username": self.user.username,
                            "message": message,
                            "timestamp": timestamp,
                        }
                    }
                )
            elif action == "fetch":
                await self.fetch_and_send_messages()
            else:
                await self.send(text_data=json.dumps({
                    "type": "error",
                    "message": "Invalid action"
                }))

        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": "Invalid JSON format"
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": f"Error processing message: {str(e)}"
            }))

    async def chat_message(self, event):
        try:
            message_data = event["message_data"]
            message_data["is_current_user"] = message_data["sender_id"] == str(self.user.id)
            await self.send(text_data=json.dumps(message_data))
        except Exception as e:
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": f"Error sending message: {str(e)}"
            }))

    @sync_to_async
    def store_message_in_dynamodb(self, message, timestamp):
        try:
            table.put_item(
                Item={
                    "chat_id": "global_chat",
                    "timestamp": timestamp,
                    "sender_id": str(self.user.id),
                    "username": self.user.username,
                    "message": message,
                }
            )
        except Exception as e:
            print(f"Error storing message in DynamoDB: {str(e)}")
            raise

    async def fetch_and_send_messages(self):
        try:
            # Query DynamoDB for all messages in the global chat
            messages = await self.fetch_messages_from_dynamodb()

            # Send messages to the WebSocket client
            await self.send(text_data=json.dumps({
                "type": "chat_history",
                "messages": messages
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": f"Failed to fetch messages: {str(e)}"
            }))

    @sync_to_async
    def fetch_messages_from_dynamodb(self):
        try:
            response = table.query(
                KeyConditionExpression=Key("chat_id").eq("global_chat"),
                ScanIndexForward=True,  # Retrieve messages in ascending order
                Limit=100  # Limit the number of messages to prevent overwhelming the client
            )

            return [
                {
                    "sender_id": message["sender_id"],
                    "username": message["username"],
                    "message": message["message"],
                    "timestamp": message["timestamp"],
                    "is_current_user": message["sender_id"] == str(self.user.id),
                }
                for message in response.get("Items", [])
            ]
        except Exception as e:
            print(f"Error fetching messages from DynamoDB: {str(e)}")
            raise

