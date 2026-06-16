"""Example 01 — Basic MCP_TOOL: @plugin + @agent_tool

Scenario: query city weather and get outdoor running advice.
Capability type: MCP_TOOL — direct tool call registered via @plugin / @agent_tool.

Mirrors: WeatherPluginTest in regnexe-agent (Java)
"""

import asyncio

from regnexe import (
    ConsoleEventListener,
    RegnexeAgentBuilder,
    Vendor,
    agent_tool,
    plugin,
)


@plugin(id="weather", name="Weather Plugin", description="Provides weather information")
class WeatherPlugin:
    @agent_tool("Get today's weather for a given city", tags=["weather", "forecast"])
    def get_weather(self, city: str) -> str:
        data = {
            "Beijing":   "sunny, 22°C, humidity 40%, great for outdoor activities",
            "Shanghai":  "cloudy, 18°C, humidity 65%, light jacket recommended",
            "Guangzhou": "rainy, 26°C, humidity 85%, bring an umbrella",
        }
        return data.get(city, f"No weather data available for {city}")

    @agent_tool("Get the 3-day weather forecast for a given city", tags=["weather", "forecast"])
    def get_forecast(self, city: str) -> str:
        return f"{city}: Mon sunny 22°C, Tue cloudy 19°C, Wed rainy 16°C"


async def main() -> None:
    agent = (
        RegnexeAgentBuilder()
        .with_default_model(Vendor.DEEPSEEK, "deepseek-v4-flash")
        .with_plugin(WeatherPlugin())
        .with_event_listener(ConsoleEventListener(show_system_prompt=True))
        .build()
    )

    result = await agent.ainvoke(
        "Check the weather in Beijing. Is it a good day for running outdoors?",
        app_id="demo",
        user_id="user1",
        session_id="sess1",
    )

    print("Final answer:", result.final_text)
    print("Status:      ", result.status)
    print("Task ID:     ", result.task_id)

    # Second turn in the same session — conversation history is retained
    result2 = await agent.ainvoke(
        "What about Shanghai?",
        app_id="demo",
        user_id="user1",
        session_id="sess1",
    )
    print("\nFollow-up:", result2.final_text)


if __name__ == "__main__":
    asyncio.run(main())
