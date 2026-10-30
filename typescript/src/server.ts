import { createServer } from "node:http";
import { respond } from "./voice.ts";

createServer(async (req, res) => {
  const send = (status: number, data: unknown) => {
    res.writeHead(status, {
      "Content-Type": "application/json",
      "Cache-Control": "no-store",
    });
    res.end(JSON.stringify(data));
  };
  if (req.method !== "POST" || req.url !== "/api/voice") {
    send(404, { error: "Not found" });
    return;
  }

  if (
    req.headers.origin &&
    req.headers.origin !== `http://${req.headers.host}`
  ) {
    send(403, { error: "Origin not allowed" });
    return;
  }
  try {
    const chunks: Buffer[] = [];
    let size = 0;
    for await (const chunk of req) {
      size += chunk.length;
      if (size > 3000000) {
        send(413, { error: "Input too large" });
        return;
      }
      chunks.push(chunk);
    }
    const raw = Buffer.concat(chunks);
    const reply = await respond(raw);
    send(200, { reply });
  } catch {
    send(502, {
      error: "Request failed. Check input, API key, access and credits.",
    });
  }
}).listen(Number(process.env.PORT || 3000), "127.0.0.1", () =>
  console.log("Listening on http://127.0.0.1:3000"),
);
