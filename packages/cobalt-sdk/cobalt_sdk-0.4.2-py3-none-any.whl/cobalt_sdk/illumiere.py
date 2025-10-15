"""
Functions for sending data to Koito Illumiere.

イルミエル向けにデータを送信するための関数セット。
"""

import ctypes
import json
import http.client
from websockets.asyncio.client import ClientConnection


def activate_illumiere_modules(address: str = "localhost") -> None:
    """
    Activate modules in Cobalt to send data to Koito Illumiere.

    Cobalt内のイルミエル関連モジュールを起動します。
    """

    conn = http.client.HTTPConnection(address, 23789)
    conn.request("POST", "/start-sending-to-illumiere")
    response = conn.getresponse()
    if response.status == 404:
        conn.close()
        raise ConnectionError("Failed to connect to Cobalt.")
    conn.close()


async def subscribe_illumiere_objects(ws: ClientConnection) -> None:
    """
    Subscribe to object detection data for Illumiere on a WebSocket connection.

    WebSocket接続でイルミエル物体データを購読します。
    """
    msg = json.dumps([{"token": "IOBJ", "subscribed": True}])
    await ws.send(msg)


class IllumiereObject(ctypes.LittleEndianStructure):
    """
    An object detected by Cobalt, formatted for Illumiere.

    Cobaltで検出された物体をイルミエル向けにフォーマットしたもの。
    """

    _pack_ = 1
    _fields_ = [
        ("i_cu_mobj_id", ctypes.c_uint32),
        ("f_timestamp", ctypes.c_double),
        ("f_pos_x_m", ctypes.c_float),
        ("f_pos_y_m", ctypes.c_float),
        ("f_vel_x_mps", ctypes.c_float),
        ("f_vel_y_mps", ctypes.c_float),
        ("f_direction_deg", ctypes.c_float),
        ("f_timelived_s", ctypes.c_float),
        ("i_class", ctypes.c_char),
        ("i_class_attr", ctypes.c_uint32),
        ("f_width_m", ctypes.c_float),
        ("f_depth_m", ctypes.c_float),
        ("f_height_m", ctypes.c_float),
    ]


class IllumiereObjectsHeader(ctypes.LittleEndianStructure):
    """
    Header for Illumiere objects data frame.

    イルミエル物体データフレームのヘッダー。
    """

    _fields_ = [
        ("magic", ctypes.c_char * 4),  # "IOBJ"
        ("i_num_objects", ctypes.c_uint16),
        ("b_e_code", ctypes.c_char),
        ("b_e_lidar", ctypes.c_char),
    ]


class IllumiereObjects(ctypes.LittleEndianStructure):
    """
    Complete Illumiere objects data frame.

    イルミエル物体データフレーム全体。
    """

    _fields_ = [
        ("magic", ctypes.c_char * 4),  # "IOBJ"
        ("i_num_objects", ctypes.c_uint16),
        ("b_e_code", ctypes.c_char),
        ("b_e_lidar", ctypes.c_char),
        # Note: objects array needs to be handled separately due to dynamic size
    ]

    def __init__(self, num_objects: int = 0):
        super().__init__()
        self.magic = b"IOBJ"
        self.i_num_objects = num_objects
        self.b_e_code = 0
        self.b_e_lidar = 0

    @classmethod
    def from_bytes(cls, data: bytes) -> "IllumiereObjects":
        """
        Parse IllumiereObjects from binary data.

        バイナリデータからIllumiereObjectsをパースします。
        """
        header_size = ctypes.sizeof(IllumiereObjectsHeader)
        object_size = ctypes.sizeof(IllumiereObject)

        header = IllumiereObjectsHeader.from_buffer_copy(data[:header_size])

        if header.magic != b"IOBJ":
            raise ValueError(f"Invalid magic: {header.magic}")

        # Create IllumiereObjects instance
        objects_frame = cls(header.i_num_objects)
        objects_frame.b_e_code = header.b_e_code
        objects_frame.b_e_lidar = header.b_e_lidar

        # Parse object data
        objects = []
        for i in range(header.i_num_objects):
            offset = header_size + (i * object_size)
            obj_bytes = data[offset : offset + object_size]
            obj = IllumiereObject.from_buffer_copy(obj_bytes)
            objects.append(obj)

        objects_frame.objects = objects
        return objects_frame
