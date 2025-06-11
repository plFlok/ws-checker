import asyncio
import os
from pathlib import Path
from typing import List

from ws_client import send_adts_frames

SHAZAM_WS_URL = os.getenv("SHAZAM_WS_URL")
if not SHAZAM_WS_URL:
    print("SHAZAM_WS_URL not set")
    exit(1)


def load_frames_from_resources() -> List[bytes]:
    resources_path = Path('resources/websocket_data')
    frames: list[bytes] = []

    for file_path in sorted(resources_path.iterdir()):
        if file_path.is_file():
            with file_path.open('rb') as f:
                frame = f.read()
                frames.append(frame)
    return frames


def main() -> None:
    frames = load_frames_from_resources()
    asyncio.run(send_adts_frames(
        uri=SHAZAM_WS_URL,
        frames=frames
    ))

if __name__ == "__main__":
    main()
