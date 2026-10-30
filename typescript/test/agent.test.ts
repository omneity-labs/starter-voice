import { test } from "node:test";
import assert from "node:assert/strict";
import { Sawalni } from "../src/client.ts";
import { runAgent } from "../src/agent.ts";
test("tool round trip preserves call IDs and results", async () => {
  class Fixture extends Sawalni {
    count = 0;
    constructor() {
      super("fixture");
    }
    override async json(_path: string, body: any): Promise<any> {
      this.count++;
      if (this.count === 1)
        return {
          choices: [
            {
              message: {
                content: null,
                tool_calls: [
                  {
                    id: "clock-1",
                    type: "function",
                    function: { name: "current_time", arguments: "{}" },
                  },
                ],
              },
            },
          ],
        };
      assert.equal(body.messages.at(-1).tool_call_id, "clock-1");
      assert.ok(JSON.parse(body.messages.at(-1).content).utc);
      return { choices: [{ message: { content: "The time is available." } }] };
    }
  }
  const client = new Fixture();
  assert.equal(await runAgent("Time?", client), "The time is available.");
  assert.equal(client.count, 2);
});
test("tool loop has a bounded number of rounds", async () => {
  class Fixture extends Sawalni {
    constructor() {
      super("fixture");
    }
    override async json(): Promise<any> {
      return {
        choices: [
          {
            message: {
              tool_calls: [
                { id: "x", function: { name: "unknown", arguments: "{}" } },
              ],
            },
          },
        ],
      };
    }
  }
  await assert.rejects(runAgent("Loop", new Fixture()), /limit/);
});
