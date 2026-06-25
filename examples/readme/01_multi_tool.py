"""README example 1 — Quick start: multiple tools, one loop.

with_tool(...) registers pre-built LangChain tools directly -- no class, no decorator,
the fastest path to a running agent.
"""

import asyncio

from langchain_core.tools import tool

from regnexe import ConsoleEventListener, RegnexeAgentBuilder, Vendor


@tool
def get_weather(city: str) -> str:
    """Get today's weather for a city."""
    return "Beijing: sunny, 22 C."


@tool
def get_air_quality(city: str) -> str:
    """Get today's air quality index (AQI) for a city."""
    return "Beijing: AQI 35, excellent air quality."


async def main() -> None:
    agent = (
        RegnexeAgentBuilder()
        .with_default_model(Vendor.DEEPSEEK, "deepseek-v4-flash")
        .with_tool(get_weather, get_air_quality)   # as many as you need, one call
        .with_event_listener(ConsoleEventListener())
        .build()
    )

    result = await agent.ainvoke(
        "Check today's weather and air quality in Beijing, then tell me if it's good for outdoor running.",
        app_id="readme", user_id="reader", session_id="01-multi-tool",
    )

    print("\n=== Result ===")
    print("Status :", result.status)
    print("Output :", result.final_text)


if __name__ == "__main__":
    asyncio.run(main())
