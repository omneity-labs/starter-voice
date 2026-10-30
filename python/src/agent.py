import json
import secrets
import os
from datetime import datetime, timezone
from client import Sawalni

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "current_time",
            "description": "Get the current UTC time.",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        },
    }
]

TOOLS.append(
    {
        "type": "function",
        "function": {
            "name": "roll_dice",
            "description": "Roll one six-sided die.",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        },
    }
)


def run_agent(content, client=None):
    client = client or Sawalni()
    messages = [
        {
            "role": "system",
            "content": "Be helpful and concise. Use current_time for the time and roll_dice for dice. Reply in the user's language.",
        },
        {"role": "user", "content": content},
    ]
    for _ in range(6):
        result = client.request(
            "POST",
            "chat/completions",
            json={
                "model": os.getenv("SAWALNI_MODEL", "sawalni-beta"),
                "messages": messages,
                "tools": TOOLS,
                "max_tokens": 768,
                "stream": False,
            },
        ).json()
        message = result["choices"][0]["message"]
        calls = message.get("tool_calls") or []
        if not calls:
            if not message.get("content"):
                raise ValueError("Model returned no answer")
            return message["content"]
        if len(calls) > 8:
            raise ValueError("Too many tool calls")
        messages.append(
            {
                "role": "assistant",
                "content": message.get("content"),
                "tool_calls": calls,
            }
        )
        for call in calls:
            try:
                args = json.loads(call["function"]["arguments"])
                if (
                    call["function"]["name"] not in ["current_time", "roll_dice"]
                    or args != {}
                ):
                    raise ValueError("Unknown tool or invalid arguments")
                value = (
                    {"utc": datetime.now(timezone.utc).isoformat()}
                    if call["function"]["name"] == "current_time"
                    else {"roll": secrets.randbelow(6) + 1}
                )
            except (ValueError, KeyError, TypeError):
                value = {"error": "Unknown tool or invalid arguments"}
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call["id"],
                    "content": json.dumps(value),
                }
            )
    raise RuntimeError("Tool round limit reached")
