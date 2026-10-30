import { Sawalni } from "./client.ts";
import { runAgent } from "./agent.ts";
export async function respond(
  audio: Buffer,
  client = new Sawalni(),
): Promise<string> {
  // Reject containers that are not PCM16 mono 16 kHz. Use ffmpeg for conversion.
  if (
    audio.length < 44 ||
    audio.toString("ascii", 0, 4) !== "RIFF" ||
    audio.toString("ascii", 8, 12) !== "WAVE"
  )
    throw new Error("Use a WAV file");
  let valid = false,
    samples = 0;
  for (let offset = 12; offset + 8 <= audio.length; ) {
    const size = audio.readUInt32LE(offset + 4),
      start = offset + 8;
    if (start + size > audio.length) throw new Error("Truncated WAV");
    const tag = audio.toString("ascii", offset, offset + 4);
    if (tag === "fmt " && size >= 16)
      valid =
        audio.readUInt16LE(start) === 1 &&
        audio.readUInt16LE(start + 2) === 1 &&
        audio.readUInt32LE(start + 4) === 16000 &&
        audio.readUInt16LE(start + 14) === 16;
    if (tag === "data") samples += size / 2;
    offset = start + size + (size % 2);
  }
  if (!valid || samples < 1600 || samples > 1440000)
    throw new Error("Use a 0.1–90 second mono 16 kHz PCM16 WAV");
  const reply = await runAgent(
    [
      {
        type: "text",
        text: "Answer the spoken request. Use tools when needed.",
      },
      {
        type: "input_audio",
        input_audio: { format: "wav", data: audio.toString("base64") },
      },
    ],
    client,
  );
  return reply;
}
