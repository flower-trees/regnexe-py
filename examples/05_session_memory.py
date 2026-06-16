"""Example 05 — Multi-turn session memory (Layer 2 + Layer 3)

Scenario: two ainvoke calls share the same session_id.
  Turn 1: query Beijing weather and decide whether to go running
  Turn 2: get running tips based on Turn 1's result without re-calling the weather tool

Demonstrates three-layer memory:
  Layer 2 (task layer):   same session_id + checkpointer preserves conversation history;
                          Turn 2 can directly reference Turn 1's LLM output.
  Layer 3 (cross-session): TaskResultStore saves Turn 1's task summary;
                           injected into the system prompt of a brand-new session in Turn 3.

Mirrors: SessionMemoryTest in regnexe-agent (Java)
"""

import asyncio

from regnexe import ConsoleEventListener, RegnexeAgentBuilder, Vendor, agent_tool, plugin


@plugin(id="weather", name="Weather Plugin")
class WeatherPlugin:
    @agent_tool("Get today's weather for a city, including temperature and activity advice.", tags=["weather"])
    def get_weather(self, city: str) -> str:
        if "beijing" in city.lower():
            return "Beijing today: sunny, 22 degrees C, air quality excellent -- great for outdoor running."
        return f"{city}: cloudy, 18 degrees C, reduce outdoor activities."


async def main() -> None:
    agent = (
        RegnexeAgentBuilder()
        .with_default_model(Vendor.DEEPSEEK, "deepseek-v4-flash")
        .with_plugin(WeatherPlugin())
        .with_event_listener(ConsoleEventListener())
        .build()
    )

    # Turn 1: query weather
    print("=" * 60)
    print("Turn 1: Query Beijing weather")
    print("=" * 60)

    result1 = await agent.ainvoke(
        "Check today's weather in Beijing and tell me if it is good for outdoor running.",
        app_id="demo", user_id="user1", session_id="session-weather",
    )
    print("\n=== Turn 1 Result ===")
    print("Status:", result1.status)
    print("Answer:\n", result1.final_text)

    # Turn 2: follow-up in the same session -- should NOT re-call the weather tool
    print("\n" + "=" * 60)
    print("Turn 2: Running tips (no weather tool call expected)")
    print("=" * 60)

    result2 = await agent.ainvoke(
        "Based on the Beijing weather you just looked up, what should I keep in mind "
        "when running outdoors today? No need to check the weather again.",
        app_id="demo", user_id="user1", session_id="session-weather",  # same session_id
    )
    print("\n=== Turn 2 Result (follow-up) ===")
    print("Status:", result2.status)
    print("Answer:\n", result2.final_text)

    # Turn 3: new session_id -- cross-session memory (Layer 3)
    # TaskResultStore injects the previous task summaries into the new session's system prompt
    print("\n" + "=" * 60)
    print("Turn 3: New session -- verify Layer 3 cross-session memory")
    print("=" * 60)

    result3 = await agent.ainvoke(
        "I previously asked about Beijing weather. Do you remember the conclusion?",
        app_id="demo", user_id="user1", session_id="session-new",  # new session_id
    )
    print("\n=== Turn 3 Result (new session, Layer 3) ===")
    print("Status:", result3.status)
    print("Answer:\n", result3.final_text)


if __name__ == "__main__":
    asyncio.run(main())
