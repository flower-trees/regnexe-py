"""README example 3 — Plugin packaging: PluginDescriptor.builder().

Every loading channel in this README (with_tool, with_skill, with_subagent,
with_plugin, with_directory) ultimately builds the same thing: a PluginDescriptor
holding one or more CapabilityDescriptors. The most direct way to build one by hand
is PluginDescriptor.builder(), which has tool(...), skill_config(...), and
sub_agent_config(...) -- each wraps the raw tool/config dict into a
CapabilityDescriptor automatically, id'd as "<plugin_id>.<name>". with_plugin(...)
can register that descriptor directly, so one call bundles a whole mixed-type plugin
instead of hand-building each CapabilityDescriptor separately (mirrors regnexe-agent's
PluginDescriptor.builder().tool().skillConfig().subAgentConfig()).

A Skill's "tools" list must reference the *fully-qualified* capability id. Since the
tool and the skill share the plugin_id "trip-plugin" here, that id is
"trip-plugin.get_weather", not bare "get_weather".

model in sub_agent_config() accepts a plain "vendor:model_name" string (regnexe's own
Vendor namespace, resolved the same way with_default_model() is) -- no need to
pre-build a BaseChatModel yourself.
"""

import asyncio

from langchain_core.tools import tool

from regnexe import ConsoleEventListener, RegnexeAgentBuilder, Vendor
from regnexe.plugin.descriptor import PluginDescriptor


@tool
def get_weather(city: str) -> str:
    """Get today's weather for a city."""
    return "Beijing: sunny, 22 C, excellent air quality."


@tool
def estimate_trip_cost(days: int, city: str) -> str:
    """Estimate total cost for a multi-day business trip."""
    return f"{days}-day {city} trip estimate: 3600 CNY total."


travel_advisor = {
    "name": "travel_advisor",
    "description": (
        "Calls get_weather for the city, then gives outdoor-activity advice. "
        "TRIGGER: Use when the user asks whether the weather suits an outdoor activity."
    ),
    "system_prompt": "Call get_weather for the city, then give a short go/no-go running recommendation.",
    "tools": ["trip-plugin.get_weather"],   # fully-qualified capability id, not owned
}

expense_estimator = {
    "name": "expense_estimator",
    "description": "Estimates business trip cost. TRIGGER: Use when the user asks for a trip budget.",
    "system_prompt": "Call estimate_trip_cost, then report the total.",
    "model": "aliyun:qwen-plus",            # own model -- resolved via regnexe's Vendor namespace
    "tools": [estimate_trip_cost],          # private -- never exposed to the outer agent
}

trip_plugin = (
    PluginDescriptor.builder()
    .plugin_id("trip-plugin")
    .version("1.0")
    .name("Trip Plugin")
    .description("Bundles a tool, a skill, and a sub-agent for trip planning")
    .tool(get_weather)                                    # -> trip-plugin.get_weather
    .skill_config(travel_advisor)                         # -> trip-plugin.travel_advisor
    .sub_agent_config(expense_estimator)                  # -> trip-plugin.expense_estimator
    .build()
)


async def main() -> None:
    for cap in trip_plugin.capabilities:
        print(f"{cap.capability_id:32s} -> {cap.type.value}")

    agent = (
        RegnexeAgentBuilder()
        .with_default_model(Vendor.DEEPSEEK, "deepseek-v4-flash")
        .with_plugin(trip_plugin)            # PluginDescriptor can be registered directly
        .with_event_listener(ConsoleEventListener())
        .build()
    )

    result = await agent.ainvoke(
        "Use your travel advisor skill to tell me if it's a good day for an outdoor run in Beijing.",
        app_id="readme", user_id="reader", session_id="03-plugin-packaging",
    )

    print("\n=== Travel Advisor Result ===")
    print("Status :", result.status)
    print("Output :", result.final_text)

    result = await agent.ainvoke(
        "Use your expense estimator sub-agent to estimate a 3-day business trip budget in Shanghai.",
        app_id="readme", user_id="reader", session_id="03-plugin-packaging-expense",
    )

    print("\n=== Expense Estimator Result ===")
    print("Status :", result.status)
    print("Output :", result.final_text)


if __name__ == "__main__":
    asyncio.run(main())
