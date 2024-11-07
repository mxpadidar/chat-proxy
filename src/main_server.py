import asyncio

from websockets.asyncio.server import ServerConnection

from base import BaseServer
from enums import MessageType
from errors import MissingHeaderError, ValidationError
from models import Message


class MainServer(BaseServer):
    def __init__(self, host: str = "localhost", port: int = 8080) -> None:
        super().__init__(host, port)
        self.proxies: dict[str, ServerConnection] = {}  # {proxy: ws}
        self.user_proxy: dict[str, str] = {}  # {user: proxy}
        self.logger.info(f"MainServer initialized on {host}:{port}")

    async def _handler(self, ws: ServerConnection, *args, **kwargs) -> None:
        async for event in ws:
            try:
                message = Message.from_json(event)  # type: ignore
            except ValidationError as e:
                await ws.send(e.json())
                continue

            if message.type == MessageType.REGISTER_PROXY:
                await self._handle_proxy_register(message, ws)
                continue

            elif message.type == MessageType.USER_REGISTER:
                await self._handle_user_register(message, ws)
                continue

            elif message.type == MessageType.CHAT:
                await self._handle_chat(message, ws)
                continue

    async def handle_client_disconnection(self, ws: ServerConnection, *args, **kwargs) -> None:
        """Remove the proxy and user from the list of proxies and users when the connection is closed."""
        for proxy, client in self.proxies.items():
            if client == ws:
                self.logger.info(f"Proxy {proxy} disconnected")
                await self._proxy_disconnect(proxy)
                break

    async def _proxy_disconnect(self, proxy: str) -> None:
        """Remove the proxy and user from the list of proxies and users when the connection is closed."""
        ws = self.proxies.get(proxy)

        if ws:
            self.proxies.pop(proxy)
            self.user_proxy = {user: p for user, p in self.user_proxy.items() if p != proxy}

    async def _handle_user_register(self, message: Message, ws: ServerConnection) -> None:
        """Validate the user registration message and add the user to the list of users."""

        try:
            user = message.user
            proxy = message.proxy
        except (ValidationError, MissingHeaderError) as e:
            await ws.send(e.json())
            return

        self.user_proxy[user] = proxy
        self.logger.info(f"Registered user: {user}, proxy: {proxy}")
        response = Message(
            type=MessageType.SERVER_RESPONSE,
            body={"message": "User registered", "user": user},
        )
        await ws.send(response.to_json())

    async def _handle_proxy_register(self, message: Message, ws: ServerConnection) -> None:
        """Validate the proxy registration message and add the proxy to the list of proxies."""
        try:
            proxy = message.proxy
        except MissingHeaderError as e:
            self.logger.error(e.message)
            await ws.send(e.json())
            return

        self.proxies[proxy] = ws
        self.logger.info(f"Registered proxy: {proxy}")
        response = Message(
            type=MessageType.SERVER_RESPONSE,
            body={"message": "Proxy registered"},
        )
        response.proxy = proxy
        await ws.send(response.to_json())

    async def _handle_chat(self, message: Message, ws: ServerConnection) -> None:
        """Validate the chat message and send it to the recipient."""
        try:
            recipient = message.recipient
            user = message.user
            proxy = message.proxy
            chat_message = message.message
        except (ValidationError, MissingHeaderError) as e:
            self.logger.error(e.message)
            await ws.send(e.json())
            return

        if not proxy:
            self.logger.error("Proxy not found")
            response = Message(
                type=MessageType.SERVER_ERROR,
                body={"message": "Proxy not found"},
            )
            await ws.send(response.to_json())
            return

        if not chat_message:
            self.logger.error("Message cannot be empty")
            response = Message(
                type=MessageType.SERVER_ERROR,
                body={"message": "Message cannot be empty"},
            )
            await ws.send(response.to_json())
            return

        recipient_proxy = self.user_proxy.get(recipient)
        user_proxy = self.user_proxy.get(user)

        if not recipient_proxy or not user_proxy:
            response = Message(
                type=MessageType.SERVER_ERROR,
                body={"message": "Recipient or user not registered"},
            )
            await ws.send(response.to_json())
            return

        if recipient_proxy == user_proxy:
            proxy_ws = self.proxies[user_proxy]
            await proxy_ws.send(message.to_json())

        else:
            recipient_ws = self.proxies[recipient_proxy]
            user_ws = self.proxies[user_proxy]

            await recipient_ws.send(message.to_json())
            await user_ws.send(message.to_json())


async def main():
    main_server = MainServer()
    await main_server.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down...")
