import asyncio
import os
import subprocess

from ws_client import send_adts_frames

SHAZAM_WS_URL = os.getenv("SHAZAM_WS_URL")
ADTS_HEADER_SIZE = 7

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

def main_mp3():
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
    main_mp3()
