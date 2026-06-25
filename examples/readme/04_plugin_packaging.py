"""README example 4 — Plugin packaging: PluginDescriptor + CapabilityDescriptor.

Every loading channel in this README (with_tool, with_skill, with_subagent,
with_plugin, with_directory) ultimately builds the same thing: a PluginDescriptor
holding one or more CapabilityDescriptors, installed into a Marketplace. This example
builds one by hand -- a tool, a skill, and a sub-agent, sharing one plugin_id
("trip-plugin") -- instead of going through the with_*() shortcuts.

A Skill's "tools" list must reference the *fully-qualified* capability id. Since the
tool and the skill share the plugin_id "trip-plugin" here, that id is
"trip-plugin.get_weather", not bare "get_weather".
"""

import asyncio

from langchain_core.tools import tool

from regnexe import ConsoleEventListener, RegnexeAgentBuilder, Vendor
from regnexe.llm.model_provider import ModelProvider
from regnexe.market.simple_marketplace import SimpleMarketplace
from regnexe.plugin.descriptor import CapabilityDescriptor, PluginDescriptor
from regnexe.plugin.enums import CapabilityType


@tool
def get_weather(city: str) -> str:
    """Get today's weather for a city."""
    return "Beijing: sunny, 22 C, excellent air quality."


@tool
def estimate_trip_cost(days: int, city: str) -> str:
    """Estimate total cost for a multi-day business trip."""
    return f"{days}-day {city} trip estimate: 3600 CNY total."


trip_plugin = PluginDescriptor(
    plugin_id="trip-plugin",
    name="Trip Plugin",
    capabilities=[
        CapabilityDescriptor(
            capability_id="trip-plugin.get_weather",
            plugin_id="trip-plugin",
            type=CapabilityType.MCP_TOOL,
            name="get_weather",
            description="Get today's weather for a city.",
            tool=get_weather,
        ),
        CapabilityDescriptor(
            capability_id="trip-plugin.travel_advisor",
            plugin_id="trip-plugin",
            type=CapabilityType.SKILL,
            name="travel_advisor",
            description=(
                "Calls get_weather for the city, then gives outdoor-activity advice. "
                "TRIGGER: Use when the user asks whether the weather suits an outdoor activity."
            ),
            sub_agent={
                "name": "travel_advisor",
                "description": "Outdoor-activity advisor based on current weather.",
                "system_prompt": "Call get_weather for the city, then give a short go/no-go running recommendation.",
                "tools": ["trip-plugin.get_weather"],   # fully-qualified capability id, not owned
            },
        ),
        CapabilityDescriptor(
            capability_id="trip-plugin.expense_estimator",
            plugin_id="trip-plugin",
            type=CapabilityType.SUB_AGENT,
            name="expense_estimator",
            description="Estimates business trip cost. TRIGGER: Use when the user asks for a trip budget.",
            sub_agent={
                "name": "expense_estimator",
                "description": "Travel expense estimator.",
                "model": ModelProvider().resolve(Vendor.ALIYUN, "qwen-plus"),   # own model
                "system_prompt": "Call estimate_trip_cost, then report the total.",
                "tools": [estimate_trip_cost],   # private -- never exposed to the outer agent
            },
        ),
    ],
)


async def main() -> None:
    marketplace = SimpleMarketplace()
    marketplace.install(trip_plugin)

    for cap_id in ("trip-plugin.get_weather", "trip-plugin.travel_advisor", "trip-plugin.expense_estimator"):
        cap = marketplace.resolve(cap_id)
        print(f"{cap_id:32s} -> {cap.type.value}")

    agent = (
        RegnexeAgentBuilder()
        .with_default_model(Vendor.DEEPSEEK, "deepseek-v4-flash")
        .with_marketplace(marketplace)       # installs the hand-built PluginDescriptor's capabilities
        .with_event_listener(ConsoleEventListener())
        .build()
    )

    result = await agent.ainvoke(
        "Use your travel advisor skill to tell me if it's a good day for an outdoor run in Beijing.",
        app_id="readme", user_id="reader", session_id="04-plugin-packaging",
    )

    print("\n=== Result ===")
    print("Status :", result.status)
    print("Output :", result.final_text)


if __name__ == "__main__":
    asyncio.run(main())
