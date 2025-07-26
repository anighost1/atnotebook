from channels.generic.websocket import AsyncJsonWebsocketConsumer
import json
from urllib.parse import parse_qs
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from channels.db import database_sync_to_async

connected_users = {}


class MyWebSocketConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        query_string = self.scope["query_string"].decode()
        token = parse_qs(query_string).get("token", [None])[0]
        notebook_id = parse_qs(query_string).get("id", [None])[0]

        self.room_name = f"notebook_{notebook_id}"
        self.room_group_name = f"collab_{self.room_name}"

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

    async def receive(self, text_data):
        # Broadcast to group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "broadcast_message",
                "message": text_data,
                "user": self.scope["user"].username,
            }
        )

    async def broadcast_message(self, event):
        await self.send_json({
            "message": event["message"],
            "from": event["user"]
        })

    async def disconnect(self, close_code):
        username = getattr(self.scope["user"], "username", None)

        if username and self.room_group_name in connected_users:
            connected_users[self.room_group_name].discard(username)

            # Broadcast updated user list
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "user_list_update",
                    "users": list(connected_users[self.room_group_name]),
                }
            )

            # Clean up empty groups
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
