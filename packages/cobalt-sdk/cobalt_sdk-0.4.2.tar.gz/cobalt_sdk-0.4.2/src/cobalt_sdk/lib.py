import json

from websockets.asyncio.client import ClientConnection, connect


def proto_connect(address: str = "localhost") -> ClientConnection:
    """
    Connect to the protocol WebSocket server.

    プロトコルWebSocketサーバーに接続します。
    """
    return connect("ws://" + address + ":23787")


def data_connect(address: str = "localhost") -> ClientConnection:
    """
    Connect to the data WebSocket server.

    データWebSocketサーバーに接続します。
    """
    # Set max_size to 10MB to handle large point cloud data
    return connect(
        "ws://" + address + ":9030", max_size=10 * 1024 * 1024, ping_interval=None
    )


async def subscribe_objects(ws: ClientConnection):
    """
    Subscribe to object detection data on a WebSocket connection.

    WebSocket接続でオブジェクト検出データを購読します。
    """
    msg = json.dumps([{"token": "COBJ", "subscribed": True}])
    await ws.send(msg)


async def subscribe_foreground_cloud(ws: ClientConnection):
    """Subscribe to foreground cloud data on a WebSocket connection."""
    msg = json.dumps([{"token": "FGCL", "subscribed": True}])
    await ws.send(msg)


async def subscribe_background_cloud(ws: ClientConnection):
    """Subscribe to background cloud data on a WebSocket connection."""
    msg = json.dumps([{"token": "BGCL", "subscribed": True}])
    await ws.send(msg)


async def subscribe_ground_cloud(ws: ClientConnection):
    """Subscribe to ground cloud data on a WebSocket connection."""
    msg = json.dumps([{"token": "GRCL", "subscribed": True}])
    await ws.send(msg)


async def subscribe_base_cloud(ws: ClientConnection):
    """Subscribe to base cloud data on a WebSocket connection."""
    msg = json.dumps([{"token": "HCLD", "subscribed": True}])
    await ws.send(msg)


async def subscribe_zones(ws: ClientConnection):
    """Subscribe to zone data on a WebSocket connection."""
    msg = json.dumps([{"token": "ZONE", "subscribed": True}])
    await ws.send(msg)
