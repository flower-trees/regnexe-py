"""Example 11 — User-triggered stop: cancel() for an in-flight run

Demonstrates RegnexeAgent.cancel()/acancel(): unlike with_interrupt_on() (a
pre-configured pause before a specific tool, for approval), cancel() lets a caller
stop a run at an arbitrary point -- e.g. a "Stop" button in a chat UI.

Flow:
  1. ainvoke() is launched as a background asyncio.Task (required: cancel() must be
     called concurrently, from a different task, to actually interrupt it).
  2. A custom listener flips an asyncio.Event the moment the slow tool starts, so the
     demo cancels deterministically mid-tool-call instead of guessing a sleep delay.
  3. acancel() is called on the same session -- the background task is stopped and
     reports AgentResult(status="cancelled") instead of raising.
  4. A later plain ainvoke() on the same session_id continues normally: LangGraph
     checkpoints after every completed step, and there was no pending interrupt to
     fulfil, so this is a normal call (not aresume(), which is only for
     with_interrupt_on() approval gates).
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

    session_id = "reports-1"

    print("=" * 60)
    print("Phase 1: Launch a slow task, then stop it mid-flight")
    print("=" * 60)

    run = asyncio.create_task(
        agent.ainvoke(
            "Generate a financial report on Q2 sales.",
            app_id="reports-app", user_id="analyst1", session_id=session_id,
        )
    )

    await tool_started.wait()   # let the tool actually start before stopping it
    print("\n[STOP] Tool call detected in flight -- requesting cancellation now...")
    cancelled = await agent.acancel(app_id="reports-app", user_id="analyst1", session_id=session_id)
    print(f"[STOP] acancel() returned: {cancelled}")

    result1 = await run

    print("\n=== Phase 1 result ===")
    print("Status :", result1.status)
    print("Output :", result1.final_text or "(stopped before producing a final answer)")

    # ── Phase 2: a plain follow-up call on the same session continues the task ─────
    print("\nPhase 2: Asking it to finish the report on the same session...")

    result2 = await agent.ainvoke(
        "Please go ahead and finish generating that report.",
        app_id="reports-app", user_id="analyst1", session_id=session_id,  # same session
    )

    print("\n=== Phase 2 result ===")
    print("Status :", result2.status)
    print("Output :\n", result2.final_text)


if __name__ == "__main__":
    asyncio.run(main())
