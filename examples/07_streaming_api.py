"""Example 07 — Real-time streaming output via a custom event listener

Scenario: simulates a web / SSE (Server-Sent Events) endpoint that streams the
agent's progress as events arrive.

Key technique: implement AgentEventListener and emit SSE-formatted lines for each
TOOL_CALLED, TOOL_RESULT, and LLM_END event. A web framework (FastAPI, Starlette)
can forward these directly to the browser.

In a real deployment, replace print_sse() with `yield` inside an async generator
that feeds a StreamingResponse.
"""

import asyncio
from typing import Any

from regnexe import RegnexeAgentBuilder, Vendor, agent_tool, plugin


def print_sse(event: str, data: str) -> None:
    """Simulate SSE output (replace with `yield` in a real FastAPI/Starlette handler)."""
    print(f"event: {event}")
    print(f"data: {data}")
    print()  # blank line terminates an SSE message


class SseEventListener:
    """Translates agent events into SSE-formatted lines."""

    async def on_event(self, event_type: str, name: str, data: dict[str, Any]) -> None:
        match event_type:
            case "AGENT_STARTED":
                print_sse("agent_started", f"Processing: {data.get('goal', '')[:80]}")

            case "TOOL_CALLED":
                import json
                try:
                    input_str = json.dumps(data.get("input", {}), ensure_ascii=False)
                except (TypeError, ValueError):
                    input_str = str(data.get("input", ""))
                print_sse("tool_called", f"{name}: {input_str}")

            case "TOOL_RESULT":
                output = str(data.get("output", ""))
                print_sse("tool_result", output[:200])

            case "LLM_END":
                # Chunk the final text into 80-character SSE delta events
                text = data.get("text", "")
                if text:
                    chunk_size = 80
                    for i in range(0, len(text), chunk_size):
                        print_sse("delta", text[i:i + chunk_size])

            case "AGENT_COMPLETED":
                print_sse("done", data.get("status", "completed"))


@plugin(id="weather", name="Weather Plugin")
class WeatherPlugin:
    @agent_tool("Get today's weather for a city.", tags=["weather"])
    def get_weather(self, city: str) -> str:
        return "Beijing: sunny, 22 degrees C, air quality excellent -- perfect for outdoor activities."


async def main() -> None:
    agent = (
        RegnexeAgentBuilder()
        .with_default_model(Vendor.DEEPSEEK, "deepseek-v4-flash")
        .with_plugin(WeatherPlugin())
        .with_event_listener(SseEventListener())
        .build()
    )

    print("=== SSE stream start ===\n")
    result = await agent.ainvoke(
        "What is the weather like in Beijing today and is it suitable for cycling?",
        app_id="web", user_id="visitor1", session_id="stream-1",
    )
    print("=== SSE stream end ===")
    print("\nFull result:", result.final_text[:200])


if __name__ == "__main__":
    asyncio.run(main())
