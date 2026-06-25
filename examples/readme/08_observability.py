"""README example 8 — Observability: ConsoleEventListener and its filtering flags.

ConsoleEventListener -- used as the default throughout this README -- prints every
AGENT_STARTED / LLM_START / LLM_END / TOOL_CALLED / TOOL_RESULT / AGENT_COMPLETED event
to stdout. AbstractEventListener (its base class) suppresses LLM_START/LLM_END by
default via should_handle(); pass show_llm_events=True to see them, plus
show_token_usage=True for the tokens= line inside LLM_END.

For a production-grade listener (structured JSON logs, token accounting, SSE
streaming) instead of stdout, see 06_custom_event_listener.py / 07_streaming_api.py --
write your own AgentEventListener/AbstractEventListener subclass the same way.
"""

import asyncio

from regnexe import ConsoleEventListener, RegnexeAgentBuilder, Vendor, agent_tool, plugin


@plugin(id="weather", name="Weather Plugin")
class WeatherPlugin:
    @agent_tool("Get today's weather for a city.", tags=["weather"])
    def get_weather(self, city: str) -> str:
        return "Beijing: sunny, 22 C, excellent air quality."


async def run_with_listener(listener: ConsoleEventListener, session_id: str) -> None:
    agent = (
        RegnexeAgentBuilder()
        .with_default_model(Vendor.DEEPSEEK, "deepseek-v4-flash")
        .with_plugin(WeatherPlugin())
        .with_event_listener(listener)
        .build()
    )
    result = await agent.ainvoke(
        "Check today's weather in Beijing. Is it good for running?",
        app_id="readme", user_id="reader", session_id=session_id,
    )
    print("\nStatus :", result.status)
    print("Output :", result.final_text)


async def main() -> None:
    print("=" * 60)
    print("Default ConsoleEventListener() -- LLM_START/LLM_END suppressed")
    print("=" * 60)
    await run_with_listener(ConsoleEventListener(), "08-observability-default")

    print("\n" + "=" * 60)
    print("Verbose: show_llm_events=True, show_token_usage=True")
    print("=" * 60)
    await run_with_listener(
        ConsoleEventListener(show_llm_events=True, show_token_usage=True),
        "08-observability-verbose",
    )

    print("\n" + "=" * 60)
    print("Filtering flags, checked directly (no LLM call)")
    print("=" * 60)
    quiet = ConsoleEventListener()
    verbose = ConsoleEventListener(show_llm_events=True)
    print("quiet.should_handle('AGENT_STARTED')  ->", quiet.should_handle("AGENT_STARTED"))
    print("quiet.should_handle('LLM_START')       ->", quiet.should_handle("LLM_START"))
    print("verbose.should_handle('LLM_START')     ->", verbose.should_handle("LLM_START"))


if __name__ == "__main__":
    asyncio.run(main())
