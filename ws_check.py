import asyncio
import json
import os
import subprocess
import time
import websockets


ADTS_HEADER_SIZE = 7
proceed_search = True

def transcode_to_adts(input_file: str, output_file: str) -> None:
    subprocess.run([
        "ffmpeg", "-y", "-i", input_file,
        "-c:a", "aac", "-b:a", "128k",
        "-f", "adts", output_file
    ], check=True)

def extract_adts_frames(adts_data: bytes) -> list[bytes]:
    frames = []
    i = 0
    while i + ADTS_HEADER_SIZE <= len(adts_data):
        if adts_data[i] != 0xFF or (adts_data[i+1] & 0xF0) != 0xF0:
            raise ValueError(f"Invalid ADTS syncword at position {i}")

        frame_length = ((adts_data[i+3] & 0x03) << 11) | (adts_data[i+4] << 3) | ((adts_data[i+5] & 0xE0) >> 5)
        frames.append(adts_data[i:i+frame_length])
        i += frame_length
    return frames

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



def main():
    input_file = "demo.mp3"
    adts_file = "output.aac"

    transcode_to_adts(input_file, adts_file)

    with open(adts_file, "rb") as f:
        adts_data = f.read()

    frames = extract_adts_frames(adts_data)
    print(f"Extracted {len(frames)} ADTS frames.")
    shazam_ws_url=os.getenv("SHAZAM_WS_URL")

    asyncio.run(send_adts_frames(
        uri=shazam_ws_url,
        frames=frames
    ))

if __name__ == "__main__":
    main()
