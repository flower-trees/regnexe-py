"""README example 4 — Plugin concept: @plugin, @agent_tool, @agent_skill, @agent_subagent.

The two getting-started tools from 01_multi_tool.py become @agent_tool methods on one
@plugin-decorated class. @agent_skill and @agent_subagent -- the same Skill and
Sub-Agent from 02_skill_vs_subagent.py, as decorators instead of raw dicts -- nest as
inner classes of that same @plugin class, bundling everything under one plugin_id
("weather"): one with_plugin(WeatherPlugin()) call registers two tools, a skill, and
a sub-agent at once.

@agent_skill is a pure marker -- a Skill never owns tools, so no @agent_tool methods
are needed on it. @agent_subagent reuses @agent_tool for its private tools, exactly
like the outer @plugin does for MCP_TOOL -- the only difference is the resulting
capability type.

@agent_skill/@agent_subagent also work standalone (not nested): with_plugin(MySkill())
on its own registers it as its own single-capability plugin, the same way the
code-first with_skill()/with_subagent() from 02_skill_vs_subagent.py do.
"""

import asyncio

from regnexe import (
    ConsoleEventListener,
    RegnexeAgentBuilder,
    Vendor,
    agent_skill,
    agent_subagent,
    agent_tool,
    plugin,
)


@plugin(id="weather", name="Weather Plugin", description="Weather, advice, and trip cost estimation")
class WeatherPlugin:
    @agent_tool("Get today's weather for a city.", tags=["weather"])
    def get_weather(self, city: str) -> str:
        return "Beijing: sunny, 22 C."

    @agent_tool("Get today's air quality index (AQI) for a city.", tags=["weather"])
    def get_air_quality(self, city: str) -> str:
        return "Beijing: AQI 35, excellent air quality."

    @agent_skill(
        id="travel_advisor",
        description=(
            "Gives outdoor-activity advice based on the current weather for a city. "
            "TRIGGER: Use when the user asks whether the weather is suitable for an outdoor activity."
        ),
        system_prompt=(
            "You are an outdoor-activity advisor.\n"
            "1. Call get_weather for the city the user mentions.\n"
            "2. Based on the result, give a short, direct go/no-go recommendation."
        ),
        allowed_tools=["weather.get_weather"],   # full capability id within this plugin
    )
    class TravelAdvisorSkill:
        pass   # No @agent_tool methods -- a Skill can't own private tools.

    @agent_subagent(
        id="expense_estimator",
        description=(
            "Estimates the total cost of a business trip. "
            "TRIGGER: Use when the user asks for a trip budget or cost estimate."
        ),
        system_prompt=(
            "You are a travel expense estimator.\n"
            "1. Call estimate_trip_cost with the trip length and destination.\n"
            "2. Report the total and a one-line breakdown."
        ),
        model="aliyun:qwen-plus",   # own model, independent of the parent's default model
    )
    class ExpenseEstimatorSubAgent:
        @agent_tool("Estimates total cost for a multi-day business trip.")
        def estimate_trip_cost(self, days: int, city: str) -> str:
            return f"{days}-day {city} trip estimate: 3600 CNY total."


async def main() -> None:
    agent = (
        RegnexeAgentBuilder()
        .with_default_model(Vendor.DEEPSEEK, "deepseek-v4-flash")
        .with_plugin(WeatherPlugin())   # one call: two tools, a skill, and a sub-agent
        .with_event_listener(ConsoleEventListener())
        .build()
    )

    print("=" * 60)
    print("@agent_tool x2 (weather.get_weather, weather.get_air_quality)")
    print("=" * 60)
    result1 = await agent.ainvoke(
        "Check today's weather and air quality in Beijing, then tell me if it's good for outdoor running.",
        app_id="readme", user_id="reader", session_id="04-plugin-tools",
    )
    print("\nStatus :", result1.status)
    print("Output :", result1.final_text)

    print("\n" + "=" * 60)
    print("Nested @agent_skill (weather.travel_advisor)")
    print("=" * 60)
    result2 = await agent.ainvoke(
        "Use your travel advisor skill to tell me if it's a good day for an outdoor run in Beijing.",
        app_id="readme", user_id="reader", session_id="04-plugin-skill",
    )
    print("\nStatus :", result2.status)
    print("Output :", result2.final_text)

    print("\n" + "=" * 60)
    print("Nested @agent_subagent (weather.expense_estimator)")
    print("=" * 60)
    result3 = await agent.ainvoke(
        "What would a 3-day business trip to Chengdu cost?",
        app_id="readme", user_id="reader", session_id="04-plugin-subagent",
    )
    print("\nStatus :", result3.status)
    print("Output :", result3.final_text)


if __name__ == "__main__":
    asyncio.run(main())
