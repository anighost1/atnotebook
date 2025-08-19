from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path("ws/notebook-collab/", consumers.MyWebSocketConsumer.as_asgi()),
]