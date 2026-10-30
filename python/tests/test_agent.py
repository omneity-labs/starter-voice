import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from agent import run_agent


class Client:
    def __init__(self):
        self.count = 0

    def request(self, method, path, **kwargs):
        self.count += 1
        messages = kwargs["json"]["messages"]
        if self.count == 1:
            message = {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "clock-1",
                        "type": "function",
                        "function": {"name": "current_time", "arguments": "{}"},
                    }
                ],
            }
        else:
            assert messages[-1]["tool_call_id"] == "clock-1"
            assert "utc" in messages[-1]["content"]
            message = {"content": "The time is available."}
        self.result = {"choices": [{"message": message}]}
        return self

    def json(self):
        return self.result


class AgentTests(unittest.TestCase):
    def test_tool_round_trip(self):
        client = Client()
        self.assertEqual(run_agent("Time?", client), "The time is available.")
        self.assertEqual(client.count, 2)


if __name__ == "__main__":
    unittest.main()
