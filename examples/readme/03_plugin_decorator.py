"""README example 3 — Plugin concept: @plugin and @agent_tool.

The two getting-started tools from 01_multi_tool.py become @agent_tool methods on one
@plugin-decorated class -- Python's annotation-driven equivalent of constructing raw
tools by hand. One with_plugin(WeatherPlugin()) call registers both, sharing one
plugin_id ("weather"): the resulting capability ids are "weather.get_weather" and
"weather.get_air_quality".

Note: unlike regnexe-agent's @Plugin (which can also nest @AgentSkill/@AgentSubAgent
inner classes under the same plugin_id), @plugin in regnexe-py only scans @agent_tool
methods today. Bundling a Skill and a Sub-Agent under one plugin_id is done by hand-
building a PluginDescriptor instead -- see 04_plugin_packaging.py.
"""

import asyncio

from regnexe import ConsoleEventListener, RegnexeAgentBuilder, Vendor, agent_tool, plugin


@plugin(id="weather", name="Weather Plugin", description="Weather and air quality queries")
class WeatherPlugin:
    @agent_tool("Get today's weather for a city.", tags=["weather"])
    def get_weather(self, city: str) -> str:
        return "Beijing: sunny, 22 C."

    @agent_tool("Get today's air quality index (AQI) for a city.", tags=["weather"])
    def get_air_quality(self, city: str) -> str:
        return "Beijing: AQI 35, excellent air quality."


async def main() -> None:
    agent = (
        RegnexeAgentBuilder()
        .with_default_model(Vendor.DEEPSEEK, "deepseek-v4-flash")
        .with_plugin(WeatherPlugin())   # one call registers both @agent_tool methods
        .with_event_listener(ConsoleEventListener())
        .build()
    )

    result = await agent.ainvoke(
        "Check today's weather and air quality in Beijing, then tell me if it's good for outdoor running.",
        app_id="readme", user_id="reader", session_id="03-plugin-decorator",
    )

    print("\n=== Result ===")
    print("Status :", result.status)
    print("Output :", result.final_text)


if __name__ == "__main__":
    asyncio.run(main())
