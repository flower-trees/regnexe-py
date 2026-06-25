"""README example 6 — Marketplace: the capability index behind every with_*() method.

Part 1 (no LLM): the default SimpleMarketplace -- install + search + resolve.

Part 2 (LLM): a custom marketplace standing in for a DB-backed store (a real one would
back `table` with an ORM/SQL query instead of a dict). Subclassing SimpleMarketplace
keeps split_by_type() (used internally by RegnexeAgent's graph construction, and not
part of the Marketplace protocol) for free -- only install()/search()/resolve() need
overriding. with_marketplace(...) plugs it into the agent with no other code changes.
"""

import asyncio

from langchain_core.tools import tool

from regnexe import ConsoleEventListener, RegnexeAgentBuilder, Vendor
from regnexe.market.simple_marketplace import SimpleMarketplace
from regnexe.plugin.descriptor import CapabilityDescriptor, PluginDescriptor
from regnexe.plugin.enums import CapabilityType


@tool
def get_weather(city: str) -> str:
    """Get today's weather for a city."""
    return "Beijing: sunny, 22 C."


weather_plugin = PluginDescriptor(
    plugin_id="weather-plugin",
    name="Weather Plugin",
    capabilities=[
        CapabilityDescriptor(
            capability_id="weather-plugin.get_weather",
            plugin_id="weather-plugin",
            type=CapabilityType.MCP_TOOL,
            name="get_weather",
            description="Get today's weather for a city.",
            tags=["weather"],
            tool=get_weather,
        ),
    ],
)


def default_marketplace_demo() -> None:
    marketplace = SimpleMarketplace()
    marketplace.install(weather_plugin)

    candidates = marketplace.search("Check today's weather in Beijing")   # v1: query ignored, returns all
    print("Search candidates:", [c.capability_id for c in candidates])

    resolved = marketplace.resolve("weather-plugin.get_weather")
    print("Resolved tool     :", resolved.tool is get_weather)


class InMemoryDbMarketplace(SimpleMarketplace):
    """Minimal custom marketplace, e.g. backed by a database table in a real deployment.

    `table` here is an in-memory stand-in for that table; everything else (resolve(),
    split_by_type()) is inherited from SimpleMarketplace unchanged.
    """

    def __init__(self) -> None:
        super().__init__()
        self.table: dict[str, PluginDescriptor] = {}

    def install(self, plugin: PluginDescriptor) -> None:
        self.table[plugin.plugin_id] = plugin
        super().install(plugin)

    def find_by_tag(self, tag: str) -> list[PluginDescriptor]:
        """Custom query beyond the Marketplace protocol -- e.g. an ops/admin screen."""
        return [
            p for p in self.table.values()
            if any(tag in cap.tags for cap in p.capabilities)
        ]


async def custom_marketplace_demo() -> None:
    marketplace = InMemoryDbMarketplace()
    marketplace.install(weather_plugin)

    weather_plugins = marketplace.find_by_tag("weather")
    print("Plugins tagged 'weather':", [p.plugin_id for p in weather_plugins])

    agent = (
        RegnexeAgentBuilder()
        .with_default_model(Vendor.DEEPSEEK, "deepseek-v4-flash")
        .with_marketplace(marketplace)   # any Marketplace implementation plugs in here
        .with_event_listener(ConsoleEventListener())
        .build()
    )

    result = await agent.ainvoke(
        "Check today's Beijing weather. Is it good for running?",
        app_id="readme", user_id="reader", session_id="06-marketplace",
    )

    print("\n=== Result ===")
    print("Status :", result.status)
    print("Output :", result.final_text)


async def main() -> None:
    print("=" * 60)
    print("Part 1: default SimpleMarketplace")
    print("=" * 60)
    default_marketplace_demo()

    print("\n" + "=" * 60)
    print("Part 2: custom Marketplace (DB-backed stand-in)")
    print("=" * 60)
    await custom_marketplace_demo()


if __name__ == "__main__":
    asyncio.run(main())
