"""Example 09 — File-based capability loading: SKILL.md + plugin.yaml

Demonstrates how to load capabilities from a directory using with_directory().
The loader scans for:
  SKILL.md files   -> registered as SKILL knowledge capabilities (passed to deepagents as skill_paths)
  plugin.yaml files -> registered as MCP_TOOL descriptors (metadata catalogue)

Directory layout used here:
  examples/skills/
    translation/
      SKILL.md          <- translation skill with YAML frontmatter

How SKILL.md files work:
  deepagents reads the SKILL.md at runtime and injects its content as knowledge
  context into the agent's system prompt, so no Python code is needed for the
  skill itself -- domain experts can author it as plain Markdown.

Run this example from the repo root or any directory; the skills path is
resolved relative to this file's location.
"""

import asyncio
import os

from regnexe import ConsoleEventListener, RegnexeAgentBuilder, Vendor


SKILLS_DIR = os.path.join(os.path.dirname(__file__), "skills")


async def main() -> None:
    agent = (
        RegnexeAgentBuilder()
        .with_default_model(Vendor.DEEPSEEK, "deepseek-v4-flash")
        .with_directory(SKILLS_DIR)   # scan all SKILL.md and plugin.yaml under this dir
        .with_event_listener(ConsoleEventListener(show_system_prompt=True))
        .build()
    )

    print(f"Loading capabilities from: {SKILLS_DIR}\n")

    result = await agent.ainvoke(
        "Translate the following text to French: "
        "'Artificial intelligence is transforming the world.'",
        app_id="demo", user_id="user1", session_id="file-load-1",
    )

    print("\n========== File Plugin Loading Result ==========")
    print("Status:", result.status)
    print("Result:\n", result.final_text)
    print("================================================\n")


if __name__ == "__main__":
    asyncio.run(main())
