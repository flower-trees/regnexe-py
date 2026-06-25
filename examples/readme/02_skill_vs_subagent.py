"""README example 2 — Going deeper: Skill vs Sub-Agent.

Two richer capability types compose multi-step behavior, with opposite tradeoffs:

  Skill (with_skill)       -- always inherits the parent's model; tools are borrowed
                               by capability id from the marketplace (must already be
                               registered via with_tool()), never owned.
  Sub-Agent (with_subagent) -- can own a different model from the parent, and its
                               tools are private: built directly, never registered in
                               the marketplace, so the outer agent can never call them.

install_skill_agent() (used by with_skill) raises if you try to pass a "model" key --
a Skill has no model field at all, by design.
"""

import asyncio

from langchain_core.tools import tool

from regnexe import ConsoleEventListener, RegnexeAgentBuilder, Vendor
from regnexe.llm.model_provider import ModelProvider


# ── Skill: shares the parent's model and a borrowed, already-registered tool ───────

@tool
def get_weather(city: str) -> str:
    """Get today's weather for a city."""
    return "Beijing: sunny, 22 C, excellent air quality."


travel_advisor = {
    "name": "travel_advisor",
    "description": (
        "Calls get_weather for the city the user mentions and gives outdoor-activity "
        "advice based on the current weather. TRIGGER: Use when the user asks whether "
        "the weather is suitable for an outdoor activity."
    ),
    "system_prompt": (
        "You are an outdoor-activity advisor.\n"
        "1. Call get_weather for the city the user mentions.\n"
        "2. Based on the result, give a short, direct go/no-go recommendation."
    ),
    "tools": ["get_weather"],   # borrowed by capability id, not owned
}


# ── Sub-Agent: owns a different model and a private tool ───────────────────────────

@tool
def estimate_trip_cost(days: int, city: str) -> str:
    """Estimate total cost for a multi-day business trip."""
    return f"{days}-day {city} trip estimate: flights 1800 CNY, hotel 1200 CNY, meals 600 CNY. Total: 3600 CNY."


expense_estimator = {
    "name": "expense_estimator",
    "description": (
        "Estimates the total cost of a business trip. "
        "TRIGGER: Use when the user asks for a trip budget or cost estimate."
    ),
    "model": ModelProvider().resolve(Vendor.ALIYUN, "qwen-plus"),   # own model, independent of the parent
    "system_prompt": (
        "You are a travel expense estimator.\n"
        "1. Call estimate_trip_cost with the trip length and destination.\n"
        "2. Report the total and a one-line breakdown."
    ),
    "tools": [estimate_trip_cost],   # private -- invisible to the outer agent
}


async def main() -> None:
    agent = (
        RegnexeAgentBuilder()
        .with_default_model(Vendor.DEEPSEEK, "deepseek-v4-flash")   # outer model: DeepSeek
        .with_tool(get_weather)                                     # the Skill borrows this
        .with_skill("travel.travel_advisor", travel_advisor)
        .with_subagent("travel.expense_estimator", expense_estimator)
        .with_event_listener(ConsoleEventListener())
        .build()
    )

    print("=" * 60)
    print("Skill: inherits the parent's DeepSeek model, shares get_weather")
    print("=" * 60)
    result1 = await agent.ainvoke(
        "Use your travel advisor skill to tell me if it's a good day for an outdoor run in Beijing.",
        app_id="readme", user_id="reader", session_id="02-skill",
    )
    print("\nStatus :", result1.status)
    print("Output :", result1.final_text)

    print("\n" + "=" * 60)
    print("Sub-Agent: own Aliyun Qwen-Plus model, private estimate_trip_cost tool")
    print("=" * 60)
    result2 = await agent.ainvoke(
        "What would a 3-day business trip to Chengdu cost?",
        app_id="readme", user_id="reader", session_id="02-subagent",
    )
    print("\nStatus :", result2.status)
    print("Output :", result2.final_text)


if __name__ == "__main__":
    asyncio.run(main())
