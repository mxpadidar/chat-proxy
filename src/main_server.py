import asyncio
import json

from websockets.asyncio.server import ServerConnection, serve
from websockets.exceptions import ConnectionClosedError


class MainServer:
    def __init__(self, host: str = "localhost", port: int = 8080):
        self.host = host
        self.port = port
        self.proxies: dict[str, ServerConnection] = {}  # {url: ws}
        self.user_proxy: dict[str, str] = {}  # {username: url}

    @property
    def url(self) -> str:
        return f"ws://{self.host}:{self.port}"

    async def handle_proxy_register(
        self, event: dict, proxy_ws: ServerConnection
    ) -> None:
        """
        Register a proxy server.
        """
        url = event["url"]
        self.proxies[url] = proxy_ws
        print(f"Registered proxy: {url}")
        await proxy_ws.send(
            json.dumps({"type": "response", "message": "Proxy registered"})
        )

    async def handle_user_register(
        self, event: dict, proxy_ws: ServerConnection
    ) -> None:
        """
        Register a user.
        """
        username = event["username"]
        url = event["url"]
        self.user_proxy[username] = url
        print(f"Registered user: {username}: {url}")
        await proxy_ws.send(
            json.dumps(
                {"type": "response", "message": "User registered", "username": username}
            )
        )

    async def handle_chat(self, event: dict, ws: ServerConnection) -> None:
        """
        Handle chat messages.
        """
        recipient = event["recipient"]
        username = event["username"]

        recipient_proxy_url = self.user_proxy.get(recipient)
        user_proxy_url = self.user_proxy.get(username)

        if not recipient_proxy_url or not user_proxy_url:
            response = {"type": "error", "message": "Recipient or user not found"}
            print(f"Response: {response}")
            await ws.send(json.dumps(response))
            return

        if recipient_proxy_url == user_proxy_url:
            user_proxy = self.proxies[user_proxy_url]
            await user_proxy.send(json.dumps(event))
            return

        recipient_proxy = self.proxies[recipient_proxy_url]
        user_proxy = self.proxies[user_proxy_url]

        await recipient_proxy.send(json.dumps(event))
        await user_proxy.send(json.dumps(event))

    async def handler(self, ws: ServerConnection) -> None:
        """Handle incoming messages from proxy servers."""

        try:
            async for message in ws:
                event = json.loads(message)
                event_type = event["type"]
                if event_type == "proxy_reg":
                    await self.handle_proxy_register(event, ws)
                elif event_type == "user_reg":
                    await self.handle_user_register(event, ws)
                elif event_type == "chat":
                    await self.handle_chat(event, ws)
                else:
                    print(f"Invalid message: {event}")
        except ConnectionClosedError:
            for url, proxy in self.proxies.items():
                if proxy == ws:
                    del self.proxies[url]
                    print(f"Proxy disconnected: {url}")
                    break

        finally:
            await ws.close()

    async def start(self) -> None:
        async with serve(self.handler, self.host, self.port):
            print(f"MainServer started at {self.url}")
            await asyncio.get_running_loop().create_future()  # Keeps the server running indefinitely


async def main():
    main_server = MainServer()
    await main_server.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down...")
