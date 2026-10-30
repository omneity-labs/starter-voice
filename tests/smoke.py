"""End-to-end starter checks against a local API fixture. No paid requests."""

import io, json, os, subprocess, threading, wave, tempfile, sys, shutil
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

repo_root = Path(__file__).resolve().parents[1]
r = repo_root.parent
node = shutil.which("node")
assert node, "Install Node.js 24 or newer"
python = sys.executable
seen = []


class API(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def reply(self, body, status=200, kind="application/json"):
        self.send_response(status)
        self.send_header("Content-Type", kind)
        self.end_headers()
        self.wfile.write(
            json.dumps(body).encode() if kind == "application/json" else body
        )

    def do_POST(self):
        assert self.headers["Authorization"] == "Bearer fixture-key"
        body = self.rfile.read(int(self.headers["Content-Length"]))
        seen.append(self.path)
        if self.path.endswith("/chat/completions"):
            data = json.loads(body)
            messages = data["messages"]
            user = messages[1]["content"]
            if isinstance(user, list):
                assert (
                    user[1]["type"] == "input_audio"
                    and user[1]["input_audio"]["format"] == "wav"
                )
            if messages[-1]["role"] == "tool":
                assert messages[-1]["tool_call_id"] == "clock1"
                assert json.loads(messages[-1]["content"])["utc"]
                self.reply({"choices": [{"message": {"content": "Fixture answer"}}]})
            else:
                self.reply(
                    {
                        "choices": [
                            {
                                "message": {
                                    "content": None,
                                    "tool_calls": [
                                        {
                                            "id": "clock1",
                                            "type": "function",
                                            "function": {
                                                "name": "current_time",
                                                "arguments": "{}",
                                            },
                                        }
                                    ],
                                }
                            }
                        ]
                    }
                )
        elif self.path.endswith("/audio/speech"):
            assert json.loads(body)["input"] == "Fixture answer"
            self.reply(b"RIFFfixture", kind="audio/wav")
        else:
            self.reply({"error": "unexpected path"}, 404)

    def do_GET(self):
        seen.append(self.path)
        if self.path.endswith("/srt"):
            self.reply(b"1\n00:00:00,000 --> 00:00:01,000\nHello\n", kind="text/plain")
        else:
            self.reply({"status": "done"})


server = ThreadingHTTPServer(("127.0.0.1", 0), API)
threading.Thread(target=server.serve_forever, daemon=True).start()
env = {
    **os.environ,
    "SAWALNI_API_KEY": "fixture-key",
    "SAWALNI_BASE_URL": f"http://127.0.0.1:{server.server_port}/v1",
}
with tempfile.TemporaryDirectory() as folder:
    folder = Path(folder)
    audio = folder / "recording.wav"
    text = folder / "transcript.txt"
    text.write_text("Reviewed script")
    with wave.open(str(audio), "wb") as w:
        w.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
        w.writeframes(b"\0\0" * 3200)
    for repo in ["starter-voice"]:
        for lang in ["python", "typescript"]:
            cwd = repo_root / lang

            def run(args):
                cmd = (
                    [python, "src/main.py"]
                    if lang == "python"
                    else [node, "src/main.ts"]
                )
                result = subprocess.run(
                    cmd + args,
                    cwd=cwd,
                    env=env,
                    text=True,
                    capture_output=True,
                    timeout=30,
                )
                assert result.returncode == 0, (repo, lang, result.stderr)
                return result.stdout

            if repo == "starter-agent":
                assert "Fixture answer" in run(["Time?"])
            elif repo == "starter-voice":
                output = folder / f"{lang}.wav"
                before = len(seen)
                args = (
                    [str(audio), "--speak", str(output)]
                    if lang == "python"
                    else [str(audio), str(output)]
                )
                assert "Fixture answer" in run(args)
                assert output.read_bytes() == b"RIFFfixture"
                assert not any("transcribe" in x for x in seen[before:])
            print("PASS", repo, lang)
server.shutdown()
print("PASS HTTP fixture workflows for", repo_root.name)
