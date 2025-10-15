import asyncio
import cobalt_sdk
import cobalt_sdk.illumiere
import time
import websockets


async def main():
    ADDRESS = "localhost"
    MAX_FRAMES = 100

    # Modules related to Koito Illumiere in Cobalt Helius
    # are not activated by default.
    # Activate them before subscribing to Illumiere objects.
    #
    # Cobaltのイルミエル関連モジュールはデフォルトでは有効になっていません。
    # Illumiereオブジェクトを購読する前に有効化してください。
    cobalt_sdk.illumiere.activate_illumiere_modules(ADDRESS)
    time.sleep(3)
    print("connected to cobalt")

    async with cobalt_sdk.data_connect(ADDRESS) as h3:
        await cobalt_sdk.illumiere.subscribe_illumiere_objects(h3)

        frame_count = 0
        while frame_count < MAX_FRAMES:
            try:
                data = await h3.recv()
            except TimeoutError:
                print("TimeoutError")
                continue
            except websockets.exceptions.ConnectionClosedError:
                print("ConnectionClosedError")
                break
            objects = cobalt_sdk.illumiere.IllumiereObjects.from_bytes(data)
            print(f"--- Got {objects.i_num_objects} objects ---")
            print(f"Header: code={objects.b_e_code}, lidar={objects.b_e_lidar}")
            for obj in objects.objects:
                print(
                    f"  Object: id={obj.i_cu_mobj_id}, type={obj.i_class}, position=({obj.f_pos_x_m},{obj.f_pos_y_m})"
                )
            frame_count += 1
    print("done")


asyncio.run(main())
