import asyncio
import json

from websockets.asyncio.client import ClientConnection, connect
from websockets.asyncio.server import ServerConnection, serve
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK

from base import BaseServer
from enums import MessageType
from errors import ValidationError
from models import Message


class ProxyServer(BaseServer):
    def __init__(self, host: str, port: int, main_server_url: str) -> None:
        super().__init__(host, port)
        self.main_server_url = main_server_url
        self.users: dict[str, ServerConnection] = {}
        self.logger.info(f"ProxyServer initialized with host: {host}, port: {port}")

    async def _handler(self, ws: ServerConnection, main_server: ClientConnection, *args, **kwargs) -> None:
        """Forward messages from the user to the main server."""
        async for event in ws:
            try:
                message = Message.from_json(event)  # type: ignore

                if message.user not in self.users and message.type != MessageType.USER_REGISTER:
                    self.logger.error(f"User not registered: {message.user}")
                    response = Message(type=MessageType.SERVER_ERROR, body={"message": "User not registered"})
                    await ws.send(json.dumps(response))
                    continue

                if message.type == MessageType.USER_REGISTER:
                    self.users[message.user] = ws
                    message.proxy = self.url
                    await main_server.send(message.to_json())
                    continue

                elif message.type == MessageType.CHAT:
                    message.proxy = self.url
                    await main_server.send(message.to_json())
                    continue
                else:
                    self.logger.error(f"Invalid message type: {message.type}")
                    response = Message(type=MessageType.SERVER_ERROR, body={"message": "Invalid message type"})
                    await ws.send(response.to_json())

            except ValidationError as e:
                response = Message(type=MessageType.SERVER_ERROR, body={"message": e.message})
                continue

    async def consume_main_server(self, main_server: ClientConnection) -> None:
        """Consume messages from the main server and forward them to the appropriate user."""

        async for event in main_server:
            try:
                message = Message.from_json(event)  # type: ignore
                if message.type == MessageType.CHAT:
                    sender_user = message.user
                    recipient_user = message.recipient

                    if recipient_user in self.users:
                        ws = self.users[recipient_user]
                        await ws.send(message.to_json())

                    if sender_user in self.users:
                        ws = self.users[sender_user]
                        await ws.send(message.to_json())

                elif message.type in (MessageType.SERVER_RESPONSE, MessageType.SERVER_ERROR):
                    user = message.user
                    if user in self.users:
                        ws = self.users[user]
                        await ws.send(message.to_json())

            except ValidationError as e:
                self.logger.error(f"Error: {e.message}, Message: {event}")  # type: ignore
                continue

            except (ConnectionClosedError, ConnectionClosedOK) as e:
                self.logger.error(f"Connection error: {e}")
                continue

    async def handle_client_disconnection(self, ws: ServerConnection, *args, **kwargs) -> None:
        for user, user_ws in self.users.items():
            if user_ws == ws:
                self.users.pop(user)
                self.logger.info(f"User disconnected: {user}")
                break
        await ws.close()

    async def register_proxy(self, main_server: ClientConnection) -> None:
        """Register the proxy server with the main server."""
        message = Message(type=MessageType.REGISTER_PROXY)
        message.proxy = self.url
        await main_server.send(message.to_json())
        response = await main_server.recv()
        self.logger.info(response)  # type: ignore
        self.logger.info(f"ProxyServer registered with main server: {self.port}")  # type: ignore

    async def start(self) -> None:
        """Override the start method to connect to the main server, register the proxy server,
        and consume messages from the main server."""
        main_server = await connect(self.main_server_url)
        await self.register_proxy(main_server)
        asyncio.create_task(self.consume_main_server(main_server))

        async with serve(lambda ws: self.handler(ws, main_server), self.host, self.port):
            await asyncio.get_running_loop().create_future()


async def main():
    proxy_8081 = ProxyServer("localhost", 8081, "ws://localhost:8080")
    proxy_8082 = ProxyServer("localhost", 8082, "ws://localhost:8080")
    await asyncio.gather(proxy_8081.start(), proxy_8082.start())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except OSError as e:
        print(f"Error: {e}")
    except KeyboardInterrupt:
        print("Shutting down...")
