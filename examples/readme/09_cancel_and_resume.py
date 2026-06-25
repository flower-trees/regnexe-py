"""README example 9 — Cancel & Resume.

acancel()/cancel() is the user-triggered counterpart to with_interrupt_on(): instead of
a pre-configured pause before a specific tool, a caller can stop an in-flight run at
any point -- e.g. a "Stop" button in a chat UI.

ainvoke()/aresume() must run as a separate asyncio.Task for acancel() to reach it
concurrently. An asyncio.Event -- set the moment the slow tool starts -- makes the
cancellation point deterministic instead of guessing a sleep delay.

The cancelled run reports AgentResult(status="cancelled") rather than raising.
LangGraph checkpoints after every completed step, so a later plain ainvoke() on the
same session_id just continues -- no special resume call needed, since there was no
pending approval gate to fulfil (that's aresume()'s job; see 10_interrupt_example.py
in the top-level examples/ directory).
"""

import asyncio
import time
from typing import Any

from regnexe import ConsoleEventListener, RegnexeAgentBuilder, Vendor, agent_tool, plugin


@plugin(id="reports", name="Reports Plugin")
class ReportsPlugin:
    @agent_tool("Generate a financial report for a topic. Takes a while to run.", tags=["reports"])
    def generate_report(self, topic: str) -> str:
        time.sleep(6)
        return f"Report on {topic}: revenue up 12% quarter-over-quarter."


class ToolStartListener(ConsoleEventListener):
    """ConsoleEventListener that also signals an asyncio.Event when a tool starts."""

    def __init__(self, tool_started: asyncio.Event) -> None:
        super().__init__()
        self._tool_started = tool_started

    async def on_event(self, event_type: str, name: str, data: dict[str, Any]) -> None:
        await super().on_event(event_type, name, data)
        if event_type == "TOOL_CALLED":
            self._tool_started.set()


async def main() -> None:
    tool_started = asyncio.Event()

    agent = (
        RegnexeAgentBuilder()
        .with_default_model(Vendor.DEEPSEEK, "deepseek-v4-flash")
        .with_plugin(ReportsPlugin())
        .with_event_listener(ToolStartListener(tool_started))
        .build()
    )

    session_id = "09-cancel-resume"

    print("=" * 60)
    print("Phase 1: launch a slow task, then stop it mid-flight")
    print("=" * 60)

    run = asyncio.create_task(
        agent.ainvoke(
            "Generate a financial report on Q2 sales.",
            app_id="readme", user_id="reader", session_id=session_id,
        )
    )

    await tool_started.wait()   # let the tool actually start before stopping it
    print("\n[STOP] Tool call detected in flight -- requesting cancellation now...")
    cancelled = await agent.acancel(app_id="readme", user_id="reader", session_id=session_id)
    print(f"[STOP] acancel() returned: {cancelled}")

    result1 = await run
    print("\nStatus :", result1.status)
    print("Output :", result1.final_text or "(stopped before producing a final answer)")

    print("\n" + "=" * 60)
    print("Phase 2: a plain follow-up call on the same session continues the task")
    print("=" * 60)

    result2 = await agent.ainvoke(
        "Please go ahead and finish generating that report.",
        app_id="readme", user_id="reader", session_id=session_id,   # same session
    )
    print("\nStatus :", result2.status)
    print("Output :", result2.final_text)


if __name__ == "__main__":
    asyncio.run(main())
