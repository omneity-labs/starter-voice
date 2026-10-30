import { readFile, writeFile } from "node:fs/promises";
import { Sawalni } from "./client.ts";
import { respond } from "./voice.ts";
const [path, output] = process.argv.slice(2);
if (!path) throw new Error("Usage: npm start -- recording.wav [reply.wav]");
const client = new Sawalni();
const reply = await respond(await readFile(path), client);
console.log(reply);
if (output) {
  const response = await client.request("audio/speech", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: "asat",
      input: reply,
      voice: process.env.ASAT_VOICE || "male-1",
      response_format: "wav",
      stream: false,
    }),
  });
  if (!response.headers.get("content-type")?.startsWith("audio/"))
    throw new Error("ASAT returned no audio");
  await writeFile(output, Buffer.from(await response.arrayBuffer()));
}
