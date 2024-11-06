import asyncio
import json

import websockets
from websockets.asyncio.client import ClientConnection, connect
from websockets.asyncio.server import ServerConnection, serve

MAIN_SERVER_URL = "ws://localhost:8080"
PROXY_SERVER_URL = "ws://localhost:8081"
PROXY_REGISTERED = False

clients: set[ServerConnection] = set()


users: dict[str, ServerConnection] = {}


async def proxy_handler(client_ws, ms_client):
    try:
        await froward_to_ms(client_ws, ms_client)
    except websockets.ConnectionClosedOK:
        print("Connection closed")


async def forward_to_user(ms_client):
    async for message in ms_client:
        print(f"Received message from main server: {message}")
        event = json.loads(message)
        event_type = event["type"]
        try:
            event.pop("url")
        except KeyError:
            pass
        if event_type == "chat":
            username = event["recipient"]
            if username in users:
                client_ws = users[username]
                await client_ws.send(json.dumps(event))
        elif event_type == "response":
            username = event["username"]
            if username in users:
                client_ws = users[username]
                await client_ws.send(json.dumps(event))


async def froward_to_ms(client_ws, ms_client):
    global users
    async for message in client_ws:
        print(f"Received message from client: {message}")
        event = json.loads(message)
        username = event["username"]
        if username not in users:
            users[username] = client_ws
        event["url"] = PROXY_SERVER_URL
        await ms_client.send(json.dumps(event))
        if event["type"] == "chat":
            await client_ws.send(message)


async def register_proxy(main_ws):
    event = {"type": "proxy_reg", "url": PROXY_SERVER_URL}
    await main_ws.send(json.dumps(event))
    response = await main_ws.recv()
    print(f"Main server response: {response}")


async def proxy1():
    ms = await connect(MAIN_SERVER_URL)
    await register_proxy(ms)
    asyncio.create_task(forward_to_user(ms))
    async with serve(lambda ws: proxy_handler(ws, ms), "localhost", 8081):
        await asyncio.get_running_loop().create_future()  # Keeps the proxy server running indefinitely


async def proxy2():
    ms = await connect(MAIN_SERVER_URL)
    await register_proxy(ms)
    asyncio.create_task(forward_to_user(ms))
    async with serve(lambda ws: proxy_handler(ws, ms), "localhost", 8082):
        await asyncio.get_running_loop().create_future()  # Keeps the proxy server running indefinitely


async def main():
    await asyncio.gather(proxy1(), proxy2())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Proxy server stopped")
