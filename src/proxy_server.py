import asyncio
import json

from websockets.asyncio.client import ClientConnection, connect
from websockets.asyncio.server import ServerConnection, serve
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK


class ProxyServer:
    def __init__(self, host: str, port: int, main_server_url: str) -> None:
        self.host = host
        self.port = port
        self.main_server_url = main_server_url
        self.users: dict[str, ServerConnection] = {}

    @property
    def url(self) -> str:
        return f"ws://{self.host}:{self.port}"

    async def handler(
        self, user_ws: ServerConnection, main_server: ClientConnection
    ) -> None:
        """
        Handle incoming messages from users.
        Forward messages to the main server.
        """
        try:
            async for message in user_ws:
                event = json.loads(message)
                username = event["username"]
                if username not in self.users:
                    self.users[username] = user_ws

                event["url"] = self.url
                await main_server.send(json.dumps(event))

                # Send the message back to the user if it's a chat message
                if event["type"] == "chat":
                    await user_ws.send(message)
        finally:
            for username, ws in self.users.items():
                if ws == user_ws:
                    self.users.pop(username)
                    print(f"User disconnected: {username}")
                    break
            await user_ws.close()

    async def consume_main_server(self, main_server: ClientConnection) -> None:
        """
        Consume messages from the main server.
        Forward messages to the appropriate user.
        """
        async for message in main_server:
            try:
                event = json.loads(message)
                event_type = event["type"]

                if event_type == "chat":
                    event.pop("url")
                    recipient = event["recipient"]
                    if recipient in self.users:
                        user_ws = self.users[recipient]
                        await user_ws.send(json.dumps(event))

                elif event_type == "response":
                    username = event["username"]
                    if username in self.users:
                        user_ws = self.users[username]
                        await user_ws.send(json.dumps(event))
            except (ConnectionClosedError, ConnectionClosedOK) as e:
                print(f"Error: {e}")
                print(message)
                continue

    async def register(self, main_server: ClientConnection) -> None:
        """
        Register the proxy server with the main server.
        """
        registration_msg = json.dumps({"type": "proxy_reg", "url": self.url})
        await main_server.send(registration_msg)
        response: str = await main_server.recv()  # type: ignore
        print(f"Registration response: {response}")

    async def start(self) -> None:
        """
        Start the proxy server.
        """
        main_server = await connect(self.main_server_url)
        await self.register(main_server)
        asyncio.create_task(self.consume_main_server(main_server))

        async with serve(
            lambda ws: self.handler(ws, main_server), self.host, self.port
        ):
            print(f"ProxyServer started at {self.url}")
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
