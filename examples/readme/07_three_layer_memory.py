"""README example 7 — Three layers of memory, each solving a different problem.

  Layer 1 (current turn)   "What's in this one LLM/tool turn?"
                            Messages and tool results in the active deepagents graph
                            state -- always on, no config knob.
  Layer 2 (same session)   "What did we say earlier in this session_id?"
                            with_checkpointer(...) -- LangGraph checkpointer, MemorySaver by default.
  Layer 3 (cross-session)  "What did this user accomplish in past sessions?"
                            with_store(...) -- backs TaskResultStore, injected into the
                            system prompt of future sessions for the same (app_id, user_id).
"""

import asyncio

from regnexe import ConsoleEventListener, RegnexeAgentBuilder, Vendor, agent_tool, plugin


@plugin(id="weather", name="Weather Plugin")
class WeatherPlugin:
    @agent_tool("Get today's weather for a city.", tags=["weather"])
    def get_weather(self, city: str) -> str:
        return "Beijing: sunny, 22 C, excellent air quality -- great for outdoor running."


async def main() -> None:
    agent = (
        RegnexeAgentBuilder()
        .with_default_model(Vendor.DEEPSEEK, "deepseek-v4-flash")
        .with_plugin(WeatherPlugin())
        .with_event_listener(ConsoleEventListener())
        .build()
    )

    print("=" * 60)
    print("Layer 1: current turn -- messages and tool results live in graph state")
    print("=" * 60)
    result1 = await agent.ainvoke(
        "Check today's weather in Beijing and tell me if it's good for outdoor running.",
        app_id="readme", user_id="reader", session_id="07-memory-a",
    )
    print("\nStatus :", result1.status)
    print("Output :", result1.final_text)

    print("\n" + "=" * 60)
    print("Layer 2: same session -- the checkpointer recalls Turn 1 without re-querying")
    print("=" * 60)
    result2 = await agent.ainvoke(
        "Based on the weather you just looked up, what should I keep in mind while running? "
        "No need to check the weather again.",
        app_id="readme", user_id="reader", session_id="07-memory-a",   # same session_id
    )
    print("\nStatus :", result2.status)
    print("Output :", result2.final_text)

    print("\n" + "=" * 60)
    print("Layer 3: cross-session -- a brand-new session recalls the prior task summary")
    print("=" * 60)
    result3 = await agent.ainvoke(
        "I previously asked about Beijing weather. Do you remember the conclusion?",
        app_id="readme", user_id="reader", session_id="07-memory-b",   # new session_id, same user_id
    )
    print("\nStatus :", result3.status)
    print("Output :", result3.final_text)

    # No public accessor for the builder's internal TaskResultStore today --
    # this reaches into the same instance RegnexeAgent already holds, just to show
    # what Layer 3 actually persisted.
    recent = await agent._task_store.load_recent("readme", "reader")
    print("\nPersisted task records for (readme, reader):")
    for r in recent:
        print(f"  [{r.status}] {r.goal!r} -> {r.summary[:60]!r}")


if __name__ == "__main__":
    asyncio.run(main())
