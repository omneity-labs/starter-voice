import { randomInt } from "node:crypto";
import { Sawalni } from "./client.ts";
export const tools = [
  {
    type: "function",
    function: {
      name: "current_time",
      description: "Get the current UTC time.",
      parameters: {
        type: "object",
        properties: {},
        additionalProperties: false,
      },
    },
  },
];
tools.push({
  type: "function",
  function: {
    name: "roll_dice",
    description: "Roll one six-sided die.",
    parameters: { type: "object", properties: {}, additionalProperties: false },
  },
});
export async function runAgent(
  content: unknown,
  client = new Sawalni(),
): Promise<string> {
  const messages: any[] = [
    {
      role: "system",
      content:
        "Be helpful and concise. Use current_time for the time and roll_dice for dice. Reply in the user's language.",
    },
    { role: "user", content },
  ];
  for (let round = 0; round < 6; round++) {
    const result = await client.json("chat/completions", {
      model: process.env.SAWALNI_MODEL || "sawalni-beta",
      messages,
      tools,
      max_tokens: 768,
      stream: false,
    });
    const message = result.choices?.[0]?.message;
    if (!message) throw new Error("Model returned no message");
    const calls = message.tool_calls || [];
    if (!calls.length) {
      if (typeof message.content !== "string" || !message.content.trim())
        throw new Error("Model returned no answer");
      return message.content;
    }
    if (calls.length > 8) throw new Error("Too many tool calls");
    messages.push({
      role: "assistant",
      content: message.content ?? null,
      tool_calls: calls,
    });
    for (const call of calls) {
      let value;
      try {
        const args = JSON.parse(call.function.arguments);
        if (
          !["current_time", "roll_dice"].includes(call.function.name) ||
          !args ||
          typeof args !== "object" ||
          Array.isArray(args) ||
          Object.keys(args).length
        )
          throw new Error();
        value =
          call.function.name === "current_time"
            ? { utc: new Date().toISOString() }
            : { roll: randomInt(1, 7) };
      } catch {
        value = { error: "Unknown tool or invalid arguments" };
      }
      messages.push({
        role: "tool",
        tool_call_id: call.id,
        content: JSON.stringify(value),
      });
    }
  }
  throw new Error("Tool round limit reached");
}
