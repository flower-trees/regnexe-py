"""README example 5 — File-system directory loading: with_directory().

Best for ops-managed, hot-pluggable capabilities -- no Python classes or decorators,
just files on disk:

  weather-plugin/
    plugin.yaml          <- metadata catalogue entry (MCP_TOOL descriptor)
    SKILL.md              <- skill content, with YAML frontmatter

with_directory() scans for SKILL.md and plugin.yaml/plugin.yml and registers both as
CapabilityDescriptors -- searchable and resolvable through the marketplace, same as
any other loading channel.

No LLM call here, by design (mirrors regnexe-agent's own directory-loading example):
deepagents only reads a SKILL.md's *content* off real disk when the graph is built
with a FilesystemBackend(root_dir=...); regnexe-py's RegnexeAgent does not configure
one yet, so a directory-loaded skill_path is currently registered, searchable, and
resolvable, but not yet wired into a live agent run the way with_skill()'s in-process
sub_agent dict is. Add or remove plugin folders -- no code changes required either way.
"""

import shutil
import tempfile
from pathlib import Path

from regnexe.market.simple_marketplace import SimpleMarketplace

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
description: "Outdoor activity advisor. TRIGGER: when the user asks about outdoor plans."
tags: [weather]
---
You are a weather advisor. Given the user's question about an outdoor activity,
recommend whether to go, plus one practical tip (clothing, timing, hydration).
"""


def main() -> None:
    base_dir = Path(tempfile.mkdtemp(prefix="regnexe-readme-plugin-"))
    plugin_dir = base_dir / "weather-plugin"
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "plugin.yaml").write_text(PLUGIN_YAML)
    (plugin_dir / "SKILL.md").write_text(SKILL_MD)

    try:
        marketplace = SimpleMarketplace()
        marketplace.install_from_file(str(base_dir))

        tool_cap = marketplace.resolve("weather-plugin.get_weather")
        print(f"weather-plugin.get_weather -> type={tool_cap.type.value}, tags={tool_cap.tags}")

        skill_cap = marketplace.resolve("weather-plugin.advisor")
        print(f"weather-plugin.advisor    -> type={skill_cap.type.value}, skill_path={skill_cap.skill_path}")
    finally:
        shutil.rmtree(base_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
