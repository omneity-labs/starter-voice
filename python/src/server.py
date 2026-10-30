"""Local HTTP adapter. Import the agent/voice module in your own application."""

import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from voice import respond


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/api/voice":
            self.send_error(404)
            return
        if self.headers.get("Origin") and self.headers[
            "Origin"
        ] != "http://" + self.headers.get("Host", ""):
            self.send_error(403)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 3000000:
                self.send_error(413)
                return
            raw = self.rfile.read(length)
            reply = respond(raw)
            body = json.dumps({"reply": reply}).encode()
            self.send_response(200)
        except (ValueError, KeyError):
            body = b'{"error":"Invalid input"}'
            self.send_response(400)
        except Exception:
            body = (
                b'{"error":"Upstream request failed. Check key, access and credits."}'
            )
            self.send_response(502)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    print("Listening on http://127.0.0.1:3000")
    HTTPServer(("127.0.0.1", int(os.getenv("PORT", "3000"))), Handler).serve_forever()
