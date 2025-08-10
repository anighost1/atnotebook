from channels.generic.websocket import AsyncJsonWebsocketConsumer
import json
from urllib.parse import parse_qs
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async
from .redis_client import set_notebook_content, get_notebook_content, delete_notebook_content

connected_users = {}


class MyWebSocketConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        query_string = self.scope["query_string"].decode()
        token = parse_qs(query_string).get("token", [None])[0]
        notebook_id = parse_qs(query_string).get("id", [None])[0]

        self.room_name = f"notebook_{notebook_id}"
        self.room_group_name = f"collab_{self.room_name}"
        self.notebook_id = notebook_id

        if token and notebook_id:
            try:
                validated_token = UntypedToken(token)
                user_id = validated_token.get("user_id")
                user = await self.get_user(user_id)
                self.scope["user"] = user

                # Add user to global tracker
                connected_users.setdefault(
                    self.room_group_name, set()).add(user.username)

                # Join room group
                await self.channel_layer.group_add(
                    self.room_group_name,
                    self.channel_name
                )

                await self.accept()

                notebook_data = await self.get_notebook_data(notebook_id)
                await self.send_json({
                    "type": "notebook_data",
                    "notebook": notebook_data
                })

                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "user_list_update",
                        "users": list(connected_users[self.room_group_name]),
                    }
                )

            except (InvalidToken, TokenError):
                await self.close()
        else:
            await self.close()

    @database_sync_to_async
    def get_user(self, user_id):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        return User.objects.get(id=user_id)

    @database_sync_to_async
    def get_notebook_data(self, notebook_id):
        from notebook.models import Notebook
        from notebook.serializers import NotebookSerializer
        try:
            notebook = Notebook.objects.get(pk=notebook_id)
            return NotebookSerializer(notebook).data
        except Notebook.DoesNotExist:
            return None

    async def receive(self, text_data):
        data = json.loads(text_data)
        if data.get("type") == "update_notebook":
            content = data.get("content")
            await sync_to_async(set_notebook_content)(self.notebook_id, content)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "broadcast_notebook_update",
                    "content": content,
                    "user": self.scope["user"].username,
                }
            )

        # async def broadcast_message(self, event):
        #     await self.send_json({
        #         "message": event["message"],
        #         "from": event["user"]
        #     })

    # @sync_to_async
    # def get_content_from_redis(notebook_id):
    #     from django_redis import get_redis_connection
    #     redis = get_redis_connection("default")
    #     key = f"notebook:{notebook_id}:content"
    #     return redis.get(key)

    @staticmethod
    @sync_to_async
    def save_content_to_db(notebook_id, content):
        from notebook.models import Notebook 
        try:
            notebook = Notebook.objects.get(pk=notebook_id)
            notebook.content = content
            notebook.save()
        except Notebook.DoesNotExist:
            pass

    async def disconnect(self, close_code):
        username = getattr(self.scope["user"], "username", None)

        content = await sync_to_async(get_notebook_content)(self.notebook_id)
        if content:
            await self.save_content_to_db(self.notebook_id, content)

            await sync_to_async(delete_notebook_content)(self.notebook_id)

        if username and self.room_group_name in connected_users:
            connected_users[self.room_group_name].discard(username)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "user_list_update",
                    "users": list(connected_users[self.room_group_name]),
                }
            )

            if not connected_users[self.room_group_name]:
                del connected_users[self.room_group_name]

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def user_list_update(self, event):
        await self.send_json({
            "type": "user_list",
            "users": event["users"]
        })

    async def broadcast_notebook_update(self, event):
        await self.send_json({
            "type": "notebook_update",
            "user": event["user"],
            "content": event["content"]
        })
