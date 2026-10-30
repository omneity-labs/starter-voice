import base64
import io
import wave
from agent import run_agent
from client import Sawalni


def respond(audio, client=None):
    with wave.open(io.BytesIO(audio)) as wav:
        if (
            wav.getnchannels() != 1
            or wav.getsampwidth() != 2
            or wav.getframerate() != 16000
            or not 1600 <= wav.getnframes() <= 1440000
        ):
            raise ValueError("Use a 0.1–90 second mono 16 kHz PCM16 WAV")
    client = client or Sawalni()
    reply = run_agent(
        [
            {
                "type": "text",
                "text": "Answer the spoken request. Use tools when needed.",
            },
            {
                "type": "input_audio",
                "input_audio": {
                    "format": "wav",
                    "data": base64.b64encode(audio).decode(),
                },
            },
        ],
        client,
    )
    return reply
