import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from .models import Message
from asgiref.sync import async_to_sync
from users.models import Profile
from django.http import HttpResponseForbidden

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.username = self.scope['url_route']['kwargs']['username']
        self.user = self.scope['user']

        # Check if the user is authenticated (similar to @login_required)
        if not self.user.is_authenticated:
            await self.close()
            return

        # Fetch the other user (patient or therapist)
        other_user = await async_to_sync(get_user_model().objects.get)(username=self.username)

        # Authorization: Check if the user has access to this chat (match logic)
        if self.user.role == 'patient':
            if self.user.profile.assigned_therapist != other_user:
                await self.close()
                return
        elif self.user.role == 'therapist':
            patient_profiles = await async_to_sync(Profile.objects.filter)(assigned_therapist=self.user)
            if not any(profile.user == other_user for profile in patient_profiles):
                await self.close()
                return

        # Create a unique room name based on the two users
        self.room_name = f"{self.user.username}_{self.username}"
        self.room_group_name = f"chat_{self.room_name}"

        # Join the chat group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # Accept the WebSocket connection
        await self.accept()

    async def disconnect(self, close_code):
        # Leave the chat group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        sender = self.user.username

        # Save the message to the database
        recipient = await async_to_sync(get_user_model().objects.get)(username=self.username)
        msg = Message.objects.create(sender=self.user, recipient=recipient, content=message)

        # Send message to the chat group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender': sender,
                'timestamp': msg.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            }
        )

    # Receive message from the chat group
    async def chat_message(self, event):
        message = event['message']
        sender = event['sender']
        timestamp = event['timestamp']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'sender': sender,
            'timestamp': timestamp
        }))
