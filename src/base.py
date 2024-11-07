import asyncio
from abc import ABC, abstractmethod

from websockets.asyncio.server import ServerConnection, serve
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK

from logger import Logger


class BaseServer(ABC):
    host: str
    port: int

    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self.logger = Logger(self.__class__.__name__)

    @property
    def url(self) -> str:
        return f"ws://{self.host}:{self.port}"

    async def handler(self, ws: ServerConnection, *args, **kwargs) -> None:
        try:
            await self._handler(ws, *args, **kwargs)
        except (ConnectionClosedError, ConnectionClosedOK):
            pass
        finally:
            await self.handle_client_disconnection(ws, *args, **kwargs)

    @abstractmethod
    async def _handler(self, ws: ServerConnection, *args, **kwargs) -> None:
        raise NotImplementedError

    @abstractmethod
    async def handle_client_disconnection(self, ws: ServerConnection, *args, **kwargs) -> None:
        raise NotImplementedError

    async def start(self) -> None:
        async with serve(self.handler, self.host, self.port):
            await asyncio.get_running_loop().create_future()  # Keeps the server running indefinitely
