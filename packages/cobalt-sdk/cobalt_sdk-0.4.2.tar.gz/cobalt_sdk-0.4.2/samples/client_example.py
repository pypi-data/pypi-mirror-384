"""
A sample code of using ``CobaltClient``.

When you would like to subscribe to multiple data types,
it might take time to use several subscribe_xxx() functions and
write a parser for received data by yourself.

In that case, you can use ``CobaltClient`` instead.
This class provides an event driven API.

You can register a handler function on a specific data type,
and it will be called on receiving that data type from Cobalt.
"""

import asyncio
import cobalt_sdk
from cobalt_sdk.client import CobaltClient


# define handlers on specific data type
def objects_handler(objs: cobalt_sdk.Objects) -> None:
    print("Got Objects")
    print(f"n: {objs.num_objects}, sequence_id: {objs.sequence_id}")


def zone_handler(zone_settings: cobalt_sdk.ZoneSettings) -> None:
    print("GOT Zones")
    print(f"n: {len(zone_settings.zones)}")


async def main():
    # build a client with event handlers
    client = (
        CobaltClient("localhost")
        .on_event(cobalt_sdk.Objects, objects_handler)
        .on_event(cobalt_sdk.ZoneSettings, zone_handler)
    )

    # open connection, subscribe to data, and start event loop
    async with cobalt_sdk.data_connect() as ws:
        await client.send_subscription(ws)
        await client.start_listening(ws)
        print("Start listening!")

        await asyncio.sleep(10)

        await client.stop_listening(ws)
        print("Closing connection...")


if __name__ == "__main__":
    asyncio.run(main())
