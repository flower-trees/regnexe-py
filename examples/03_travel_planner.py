"""Example 03 — SUB_AGENT capability: fully autonomous nested agent

Scenario: 3-day Chengdu travel itinerary planning.
Capability type: SUB_AGENT — context-isolated, fully autonomous nested agent.

The outer agent delegates the task to travel_planner.
travel_planner autonomously calls get_attractions and get_restaurants,
then returns the complete itinerary to the outer agent.

Mirrors: TravelPlannerTest in regnexe-agent (Java)
"""

import asyncio

from langchain_core.tools import tool

from regnexe import ConsoleEventListener, RegnexeAgentBuilder, Vendor


@tool
def get_attractions(city: str, theme: str) -> str:
    """Get popular attractions for a city.

    Args:
        city: City name
        theme: Attraction theme -- cultural / nature / general
    """
    if "cultural" in theme.lower():
        return (
            "Chengdu cultural attractions:\n"
            "1. Wuhou Shrine (Three Kingdoms culture, ~2 h)\n"
            "2. Jinli Ancient Street (folk culture, ~1.5 h)\n"
            "3. Du Fu Thatched Cottage (poet's former residence, ~1 h)"
        )
    if "nature" in theme.lower():
        return (
            "Chengdu nature attractions:\n"
            "1. Qingcheng Mountain (Taoist mountain, half-day)\n"
            "2. Dujiangyan Irrigation System (UNESCO World Heritage, ~3 h)\n"
            "3. Longquan Mountain City Forest Park (flowers & scenery, ~2 h)"
        )
    return (
        "Chengdu top attractions:\n"
        "1. Giant Panda Breeding Research Base (arrive before 9 AM, ~3 h)\n"
        "2. Jinli Street (folk crafts & snacks, ~1.5 h)\n"
        "3. Tianfu Square (city centre landmark, ~1 h)"
    )


@tool
def get_restaurants(city: str) -> str:
    """Get restaurant and food recommendations for a city.

    Args:
        city: City name
    """
    return (
        "Chengdu food picks:\n"
        "Breakfast: Lai Tangyuan (glutinous rice balls, old brand, ~CNY 15/person)\n"
        "Lunch: Liao Ji Bang Bang Chicken (authentic Sichuan, ~CNY 45/person)\n"
        "Dinner: Da Long Yi Hot Pot (most popular hotpot, ~CNY 80/person, queue early)\n"
        "Late-night: Yulin Chuanchuan Xiang (skewers, locals' favourite, ~CNY 30/person)"
    )


TRAVEL_PLANNER = {
    "name": "travel_planner",
    "description": (
        "Chengdu travel itinerary expert. Given the number of days and preferences, "
        "autonomously queries attractions and restaurants to produce a detailed daily plan. "
        "TRIGGER: Use when the user needs travel planning, attraction or restaurant recommendations."
    ),
    "system_prompt": (
        "You are a professional Chengdu travel planner.\n"
        "When asked to plan a trip:\n"
        "1. Call get_attractions for each theme (cultural / nature / general)\n"
        "2. Call get_restaurants to get food recommendations\n"
        "3. Build a day-by-day itinerary -- consider travel distances and visit durations\n"
        "4. Each day: morning attraction, lunch, afternoon attraction, dinner\n"
        "Output clearly, one section per day."
    ),
    "tools": [get_attractions, get_restaurants],
}


async def main() -> None:
    agent = (
        RegnexeAgentBuilder()
        .with_default_model(Vendor.DEEPSEEK, "deepseek-v4-flash")
        .with_subagent(
            capability_id="travel.travel_planner",
            sub_agent=TRAVEL_PLANNER,
            tags=["travel", "planning", "chengdu"],
        )
        .with_event_listener(ConsoleEventListener())
        .build()
    )

    result = await agent.ainvoke(
        "Plan a 3-day Chengdu trip for me: "
        "Day 1 -- cultural heritage; Day 2 -- nature scenery; Day 3 -- food tour. "
        "Please provide a detailed daily itinerary.",
        app_id="demo", user_id="user1", session_id="travel-1",
    )

    print("\n========== TravelPlanner Result ==========")
    print("Status    :", result.status)
    print("Itinerary :\n", result.final_text)
    print("==========================================\n")


if __name__ == "__main__":
    asyncio.run(main())
