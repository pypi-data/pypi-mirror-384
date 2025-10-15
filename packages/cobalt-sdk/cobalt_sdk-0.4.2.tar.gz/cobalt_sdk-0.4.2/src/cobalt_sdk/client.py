import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Callable, Dict, Optional, Type, Union

from websockets.asyncio.client import ClientConnection

import cobalt_sdk.illumiere
from cobalt_sdk import (
    BackgroundCloud,
    BaseCloud,
    ForegroundCloud,
    GroundCloud,
    Objects,
    ZoneSettings,
)

logger = logging.getLogger("cobalt-sdk")


_TOKEN_MAP = {
    Objects.__name__: "COBJ",
    ForegroundCloud.__name__: ForegroundCloud._token.decode(),
    BackgroundCloud.__name__: BackgroundCloud._token.decode(),
    GroundCloud.__name__: GroundCloud._token.decode(),
    BaseCloud.__name__: BaseCloud._token.decode(),
    ZoneSettings.__name__: ZoneSettings._token,  # text message has token as string
    cobalt_sdk.illumiere.IllumiereObjects.__name__: "IOBJ",
}


class _DataParser:
    BINARY_PARSERS = {
        b"COBJ": lambda data: Objects.from_bytes(data),
        ForegroundCloud._token: lambda data: ForegroundCloud(data),
        BackgroundCloud._token: lambda data: BackgroundCloud(data),
        GroundCloud._token: lambda data: GroundCloud(data),
        BaseCloud._token: lambda data: BaseCloud(data),
        b"IOBJ": lambda data: cobalt_sdk.illumiere.IllumiereObjects.from_bytes(data),
    }

    TEXT_PARSERS = {ZoneSettings._token: lambda data: ZoneSettings.from_str(data)}

    @classmethod
    def parse(cls, data: Union[bytes, str]):
        if isinstance(data, bytes):
            if len(data) < 4:
                raise ValueError("Data too short to contain magic number")
            magic = data[:4]
            if magic in cls.BINARY_PARSERS:
                return cls.BINARY_PARSERS[magic](data)
            else:
                raise ValueError(f"Unknown binary data type: {magic!r}")

        elif isinstance(data, str):
            json_data = json.loads(data)

            token = json_data["token"]
            data = json_data["text"]

            if token in cls.TEXT_PARSERS:
                return cls.TEXT_PARSERS[token](data)
            else:
                raise ValueError(f"Unknown text data type: {token}")


@dataclass
class _Subscription:
    token: str
    handler: Callable


class _EventLoop:
    """Handles the WebSocket event loop and data parsing."""

    def __init__(self):
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(
        self, ws: ClientConnection, subscriptions: Dict[str, _Subscription]
    ):
        """Start the event loop as a background task"""
        if self._task is not None:
            return

        self._running = True
        self._task = asyncio.create_task(self._run_loop(ws, subscriptions))

    async def stop(self) -> None:
        """Stop the event loop"""
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None

    async def _run_loop(
        self, ws: ClientConnection, subscriptions: Dict[str, _Subscription]
    ) -> None:
        while self._running:
            try:
                raw_data = await asyncio.wait_for(ws.recv(), timeout=10)

                parsed_data = _DataParser.parse(raw_data)

                type_name = type(parsed_data).__name__
                token = _TOKEN_MAP[type_name]

                if token in subscriptions:
                    subscription = subscriptions[token]
                    if asyncio.iscoroutinefunction(subscription.handler):
                        await subscription.handler(parsed_data)
                    else:
                        subscription.handler(parsed_data)
            except asyncio.TimeoutError:
                continue  # Timeout is expected, just continue the loop

            except asyncio.CancelledError:
                break  # Task was cancelled, exit the loop

            except Exception as e:
                logging.error(f"Error in listening loop: {e}")
                break

        self._running = False


class CobaltClient:
    """
    Event driven API,
    which parse and handle data within an event loop.
    """

    def __init__(self, address: str = "localhost"):
        self.address = address
        self.subscriptions: Dict[str, _Subscription] = {}  # token and subscription info
        self._event_loop = _EventLoop()

    def on_event(self, data_type: Type, handler: Callable) -> "CobaltClient":
        """
        Register a handler function which will be called
        on receiving specific data type.

        ``handler`` can be an async function.

        This method can be called within a method chain.
        """
        token = _TOKEN_MAP.get(data_type.__name__)
        if token:
            self.subscriptions[token] = _Subscription(token, handler)
        else:
            logging.warning(f"Unexpected data_type: {data_type}")
        return self

    async def send_subscription(self, ws: ClientConnection) -> None:
        """Send subscription message to cobalt."""
        msgs = []

        for subscription in self.subscriptions.values():
            msgs.append({"token": subscription.token, "subscribed": True})

        if msgs:
            await ws.send(json.dumps(msgs))
        else:
            logging.warning("No subscription registered")

    async def start_listening(self, ws: ClientConnection) -> None:
        """Start a loop to receive and handle data."""
        await self._event_loop.start(ws, self.subscriptions)

    async def stop_listening(self, ws: ClientConnection) -> None:
        """Stop the event loop."""
        await self._event_loop.stop()

        msgs = []
        for subscription in self.subscriptions.values():
            msgs.append({"token": subscription.token, "subscribed": False})

        if msgs:
            try:
                await ws.send(json.dumps(msgs))
                await asyncio.sleep(0.1)  # Give some time for the message to be sent
            except Exception as e:
                logging.error(f"Error sending unsubscription message: {e}")
