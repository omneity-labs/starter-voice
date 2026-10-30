import argparse
import os
from pathlib import Path
from client import Sawalni
from voice import respond

parser = argparse.ArgumentParser(description="Sawalni native audio voice backend")
parser.add_argument("audio", type=Path)
parser.add_argument("--speak", type=Path, help="Save an ASAT spoken answer as WAV")
args = parser.parse_args()
client = Sawalni()
reply = respond(args.audio.read_bytes(), client)
print(reply)
if args.speak:
    audio = client.request(
        "POST",
        "audio/speech",
        json={
            "model": "asat",
            "input": reply,
            "voice": os.getenv("ASAT_VOICE", "male-1"),
            "response_format": "wav",
            "stream": False,
        },
    )
    if not audio.headers.get("content-type", "").startswith("audio/"):
        raise ValueError("ASAT returned no audio")
    args.speak.write_bytes(audio.content)
