from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/chats/<str:username>/', consumers.ChatConsumer.as_asgi()),
]