"""README example 5 — File-system directory loading: with_directory().

Best for ops-managed, hot-pluggable capabilities -- no Python classes or decorators,
just files on disk:

  weather-plugin/
    plugin.yaml          <- metadata catalogue entry (MCP_TOOL descriptor)
    SKILL.md              <- skill content, with YAML frontmatter

with_directory() scans for SKILL.md and plugin.yaml/plugin.yml, registers them as
CapabilityDescriptors in the marketplace, and the agent picks them up at build time --
same as any other loading channel.  Add or remove plugin folders -- no code changes
required either way.
"""

import asyncio
import shutil
import tempfile
from pathlib import Path

from langchain_core.tools import tool

from regnexe import ConsoleEventListener, RegnexeAgentBuilder, Vendor

PLUGIN_YAML = """\
plugin_id: weather-plugin
capabilities:
  - capability_id: weather-plugin.get_weather
    type: mcp_tool
    name: get_weather
    description: "Get today's weather for a city"
    tags: [weather]
"""

SKILL_MD = """\
---
name: advisor
plugin_id: weather-plugin
capability_id: weather-plugin.advisor
description: "Outdoor activity advisor: checks weather then gives a go/no-go verdict with practical tips. TRIGGER: whenever the user asks whether to do an outdoor activity."
tags: [weather]
allowed_tools: [get_weather]
---
You are an outdoor activity advisor.
1. Call get_weather for the city the user mentions.
2. Based on the result, give a short go/no-go recommendation and one practical tip
   (clothing, timing, or hydration).
"""


@tool
def get_weather(city: str) -> str:
    """Get today's weather for a city."""
    return "Beijing: sunny, 22 C, excellent air quality."


async def main() -> None:
    base_dir = Path(tempfile.mkdtemp(prefix="regnexe-readme-plugin-"))
    plugin_dir = base_dir / "weather-plugin"
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "plugin.yaml").write_text(PLUGIN_YAML)
    (plugin_dir / "SKILL.md").write_text(SKILL_MD)

    try:
        agent = (
            RegnexeAgentBuilder()
            .with_default_model(Vendor.DEEPSEEK, "deepseek-v4-flash")
            .with_tool(get_weather)
            .with_directory(str(plugin_dir))
            .with_event_listener(ConsoleEventListener())
            .build()
        )

        result = await agent.ainvoke(
            "Should I go for an outdoor run in Beijing today?",
            app_id="readme", user_id="reader", session_id="05-directory",
        )

        print("\nStatus :", result.status)
        print("Output :", result.final_text)
    finally:
        shutil.rmtree(base_dir, ignore_errors=True)


if __name__ == "__main__":
    asyncio.run(main())
