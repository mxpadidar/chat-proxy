import asyncio
import json

from websockets import connect, serve
from websockets.server import WebSocketServerProtocol as ServerConnection


class ProxyServer:
    def __init__(
        self,
        host: str = "localhost",
        port: int = 8081,
        main_server_url: str = "ws://localhost:8080",
    ):
        self.host = host
        self.port = port
        self.ms_url = main_server_url
        self.to_ms_queue: asyncio.Queue[dict[str, str]] = asyncio.Queue()
        self.to_clients_queue: asyncio.Queue[dict[str, str]] = asyncio.Queue()
        self.users: dict[str, ServerConnection] = {}

    @property
    def url(self) -> str:
        return f"ws://{self.host}:{self.port}"

    async def handle_ms_messages(self) -> None:
        while True:
            async with connect(self.ms_url) as ms_ws:
                msg = await self.to_ms_queue.get()
                msg["url"] = self.url
                await ms_ws.send(json.dumps(msg))
                print(f"Sent message to MainServer: {msg}")

    async def handle_clients_messages(self) -> None:
        while True:
            msg = await self.to_clients_queue.get()
            user_ws = self.users.get(msg["username"])
            if user_ws:
                await user_ws.send(json.dumps(msg))
                print(f"Sent message to {msg['username']} client: {msg}")

    async def handle_ms(self) -> None:
        async with connect(self.ms_url) as ms_ws:
            async for message in ms_ws:
                data = json.loads(message)
                await self.to_clients_queue.put(data)

    async def handler(self, ws: ServerConnection):
        async for message in ws:
            msg_data = json.loads(message)
            msg_type = msg_data.get("type")
            username = msg_data.get("username")

            if not msg_type or not username:
                await ws.send(json.dumps({"msg": "Invalid message"}))
                continue

            if username not in self.users and msg_type != "registration":
                await ws.send(json.dumps({"msg": "User not registered"}))
                continue

            if msg_type == "registration":
                if username in self.users:
                    await ws.send(json.dumps({"msg": "User already registered"}))
                else:
                    self.users[username] = ws
                    await self.to_ms_queue.put(msg_data)
                    await ws.send(json.dumps({"msg": "User registered successfully"}))

            elif msg_type == "chat":
                await self.to_ms_queue.put(msg_data)
            else:
                print(f"Unknown message type: {msg_type}")

    async def start(self) -> None:
        # Register with MainServer
        async with connect(self.ms_url) as ms_ws:
            await ms_ws.send(json.dumps({"type": "registration", "url": self.url}))
            print(f"Registered with MainServer: {self.url}")

            msg = await ms_ws.recv()
            print(f"Received message from MainServer: {msg}")

        # Start the ProxyServer
        async with serve(self.handler, self.host, self.port):
            print(f"ProxyServer running on {self.url}")

            await asyncio.gather(
                self.handle_ms(),
                self.handle_ms_messages(),
                self.handle_clients_messages(),
            )

            await asyncio.get_running_loop().create_future()  # Keeps the server running indefinitely


if __name__ == "__main__":
    proxy_server = ProxyServer(
        host="localhost", port=8081, main_server_url="ws://localhost:8080"
    )
    asyncio.run(proxy_server.start())
