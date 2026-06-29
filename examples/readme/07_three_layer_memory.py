"""README example 7 — Session memory: how regnexe-py persists conversation context.

How it works
------------
Every ainvoke() call is mapped to a LangGraph thread via:

    thread_id = "{app_id}:{user_id}:{session_id}"

The checkpointer (default: MemorySaver) stores the full message list for that
thread between calls. All messages -- HumanMessage, AIMessage, ToolMessage --
accumulate as a flat list in DeepAgentState["messages"]; the next ainvoke()
restores the thread and the model sees the entire conversation history.

Context management
------------------
deepagents bundles SummarizationMiddleware by default. When the message list
approaches the model's context limit (85% of the window), it:
  1. Summarises old messages via an LLM call.
  2. Offloads the raw transcript to /conversation_history/{thread_id}.md.
  3. Stores a _summarization_event (cutoff + summary) in private state.

Critically, state["messages"] is never truncated -- only the view the model
receives is shortened. This keeps the full log available for replay and evals.

Customisation
-------------
Pass a custom SummarizationMiddleware via with_middleware() to control when
compaction triggers and how much history to keep.
"""

import asyncio

from regnexe import ConsoleEventListener, RegnexeAgentBuilder, Vendor, agent_tool, plugin


@plugin(id="weather", name="Weather Plugin")
class WeatherPlugin:
    @agent_tool("Get today's weather for a city.", tags=["weather"])
    def get_weather(self, city: str) -> str:
        return "Beijing: sunny, 22 C, excellent air quality -- great for outdoor running."


async def main() -> None:
    # ── Default setup: MemorySaver checkpointer, built-in SummarizationMiddleware ─
    agent = (
        RegnexeAgentBuilder()
        .with_default_model(Vendor.DEEPSEEK, "deepseek-v4-flash")
        .with_plugin(WeatherPlugin())
        .with_event_listener(ConsoleEventListener())
        .build()
    )

    # ── Session memory demo ───────────────────────────────────────────────────
    # Turn 1 and Turn 2 share the same session_id.
    # The checkpointer restores the full thread state before Turn 2, so the
    # model already knows the weather result without calling the tool again.

    print("=" * 60)
    print("Turn 1 — tool is called to fetch weather")
    print("=" * 60)
    result1 = await agent.ainvoke(
        "Check today's weather in Beijing and tell me if it's good for outdoor running.",
        app_id="readme", user_id="reader", session_id="07-memory-a",
    )
    print("\nStatus :", result1.status)
    print("Output :", result1.final_text)

    print("\n" + "=" * 60)
    print("Turn 2 — same session_id, model recalls from checkpointer")
    print("=" * 60)
    result2 = await agent.ainvoke(
        "Based on the weather you just looked up, what should I keep in mind while running? "
        "No need to check the weather again.",
        app_id="readme", user_id="reader", session_id="07-memory-a",
    )
    print("\nStatus :", result2.status)
    print("Output :", result2.final_text)

    # ── New session: no prior context ─────────────────────────────────────────
    # Changing session_id creates a fresh thread -- the checkpointer has no
    # state for "07-memory-b", so the model starts from scratch.

    print("\n" + "=" * 60)
    print("Turn 3 — new session_id, starts fresh")
    print("=" * 60)
    result3 = await agent.ainvoke(
        "What is the capital of France?",
        app_id="readme", user_id="reader", session_id="07-memory-b",
    )
    print("\nStatus :", result3.status)
    print("Output :", result3.final_text)

    # ── Custom SummarizationMiddleware via with_middleware() ──────────────────
    # The default trigger is 85% of the model's context window.
    # Override it here to compact earlier (60 000 tokens) and keep 10 messages.
    #
    # from deepagents.middleware.summarization import SummarizationMiddleware
    # from deepagents.backends import StateBackend
    #
    # summ = SummarizationMiddleware(
    #     model=my_model,
    #     backend=StateBackend(),
    #     trigger=("tokens", 60_000),
    #     keep=("messages", 10),
    # )
    # agent2 = (
    #     RegnexeAgentBuilder()
    #     .with_default_model(Vendor.DEEPSEEK, "deepseek-v4-flash")
    #     .with_plugin(WeatherPlugin())
    #     .with_middleware(summ)
    #     .build()
    # )


if __name__ == "__main__":
    asyncio.run(main())
