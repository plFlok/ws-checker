import asyncio
import json
import time

import websockets

proceed_search = True

async def receive_messages(websocket):
    global proceed_search
    async for message in websocket:
        data = json.loads(message)
        if data["status"] == "SUCCESS" and data["found"] == True:
            proceed_search = False
        print(f"Got message: {message}")

async def send_adts_frames(uri: str, frames: list[bytes], frame_duration_ms: float = 23.2):
    global proceed_search
    frame_duration = frame_duration_ms / 1000.0
    try:
        async with websockets.connect(uri) as websocket:
            receiver = asyncio.create_task(receive_messages(websocket))

            for i, frame in enumerate(frames):
                if not proceed_search:
                    break
                start_time = time.perf_counter()
                print(f"Sending frame {i}, size={len(frame)} bytes")
                await websocket.send(frame)
                time_taken = time.perf_counter() - start_time
                time_sleep = max(frame_duration - time_taken, 0.0)
                await asyncio.sleep(time_sleep)

            await receiver
    except Exception as e:
        print(f"error while sending frames: {e}")