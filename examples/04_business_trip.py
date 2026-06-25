"""Example 04 — Mixed capability types: MCP_TOOL + SKILL + SUB_AGENT

Scenario: 3-day Chengdu business trip assistant using all three capability types.
  get_weather       MCP_TOOL  -- direct tool call via @plugin / @agent_tool
  contract_analyzer SKILL     -- skill agent sharing analyze_clause from parent marketplace
  travel_planner    SUB_AGENT -- fully autonomous nested agent with private tools

with_skill vs with_subagent:
  contract_analyzer uses with_skill: analyze_clause is registered in the parent
    marketplace and referenced by str ID "analyze_clause" in the skill's tools list.
  travel_planner uses with_subagent: get_attractions / get_restaurants are private
    @tool objects invisible to the outer agent.

Mirrors: BusinessTripAssistantTest in regnexe-agent (Java)
"""

import asyncio

from langchain_core.tools import tool

from regnexe import ConsoleEventListener, RegnexeAgentBuilder, Vendor, agent_tool, plugin


# ── 1. MCP_TOOL: get_weather ──────────────────────────────────────────────────

@plugin(id="weather", name="Weather Plugin")
class WeatherPlugin:
    @agent_tool(
        "Get the recent weather forecast for a city, including temperature and travel advice.",
        tags=["weather"],
    )
    def get_weather(self, city: str) -> str:
        if "chengdu" in city.lower():
            return (
                "Chengdu recent weather: partly cloudy, 18-25 degrees C, humidity 70%, occasional light rain. "
                "Bring an umbrella and a light jacket; mornings are best for outdoor activities."
            )
        return f"{city}: sunny, 20 degrees C."


# ── 2. SKILL: contract_analyzer (shared analyze_clause via str reference) ─────

@tool
def analyze_clause(clause: str) -> str:
    """Assess the legal risk of a business-trip reimbursement clause. Input: the clause text."""
    if "not reimbursable" in clause.lower() or "borne by the employee" in clause.lower():
        return (
            "Risk level: HIGH\n"
            "Issue: Blanket exclusion may block legitimate expense claims.\n"
            "Suggestion: List specific non-reimbursable items; add an exception/appeal process."
        )
    if "cap" in clause.lower() or "ceiling" in clause.lower() or "limit" in clause.lower():
        return (
            "Risk level: MEDIUM\n"
            "Issue: Fixed cap may become insufficient as prices rise.\n"
            "Suggestion: Add annual CPI-adjustment clause or a flexible approval channel."
        )
    return "Risk level: LOW\nIssue: Clause is clear, no obvious legal risk.\nSuggestion: Keep as-is."


CONTRACT_SKILL = {
    "name": "contract_analyzer",
    "description": (
        "Legal risk analysis for business-trip reimbursement clauses. "
        "Identifies unfair conditions and loopholes in expense policies. "
        "TRIGGER: Use when analysing contracts, agreements, or reimbursement policies."
    ),
    "system_prompt": (
        "You are a professional business-trip contract risk analyst.\n"
        "When given contract clauses:\n"
        "1. Identify key clauses (reimbursable scope, caps, exclusions)\n"
        "2. Call analyze_clause for each key clause\n"
        "3. Summarise all clause risks and provide overall recommendations\n"
        "Format: clause -> risk -> suggestion."
    ),
    "tools": ["analyze_clause"],   # str reference — resolved from parent marketplace at build time
}


# ── 3. SUB_AGENT: travel_planner (private tools, invisible to outer agent) ────

@tool
def get_attractions(theme: str) -> str:
    """Get Chengdu attractions by theme.

    Args:
        theme: cultural / nature / business
    """
    if "cultural" in theme.lower():
        return "Cultural: Wuhou Shrine (2 h), Kuanzhai Alley (1.5 h), Jinli Street (1 h)"
    if "nature" in theme.lower():
        return "Nature: Qingcheng Mountain (half-day), Dujiangyan (3 h), Huanhua Creek Park (1 h)"
    return "Business: Chunxi Road shopping district, Tianfu Int'l Conference Centre, IFS business dining"


@tool
def get_restaurants(type: str) -> str:
    """Get Chengdu restaurant recommendations.

    Args:
        type: business / local / fast
    """
    if "business" in type.lower():
        return (
            "Business dining: Yinshi Pan (Sichuan cuisine, ~CNY 150/person), "
            "JW Marriott business set (~CNY 200/person)"
        )
    return (
        "Local food: Da Long Yi Hot Pot (~CNY 80/person), "
        "Liao Ji Bang Bang Chicken (~CNY 45/person), Lai Tangyuan breakfast (~CNY 15/person)"
    )


TRAVEL_PLANNER = {
    "name": "travel_planner",
    "description": (
        "Chengdu business trip planner. Combines business objectives and weather to schedule "
        "meetings and sightseeing efficiently. "
        "TRIGGER: Use when planning a business trip or travel itinerary."
    ),
    "system_prompt": (
        "You are a professional business trip planner. Rule: work first, sightseeing in gaps.\n"
        "Steps:\n"
        "1. Call get_attractions for cultural / business surroundings\n"
        "2. Call get_restaurants for business and local dining options\n"
        "3. Output a 3-day schedule: morning / afternoon / evening per day\n"
        "Note: factor in the weather report the user provides when scheduling outdoor activities."
    ),
    "tools": [get_attractions, get_restaurants],   # private @tool objects
}


# ── Assemble: register all three capability types ─────────────────────────────

async def main() -> None:
    agent = (
        RegnexeAgentBuilder()
        .with_default_model(Vendor.DEEPSEEK, "deepseek-v4-flash")
        # MCP_TOOL: direct tool from @plugin
        .with_plugin(WeatherPlugin())
        # Register analyze_clause in parent marketplace so skill agent can reference it by ID
        .with_tool(analyze_clause)
        # SKILL: sub-agent with focused system_prompt, shares analyze_clause via str ID.
        # name/description come from CONTRACT_SKILL dict automatically.
        .with_skill(
            capability_id="legal.contract_analyzer",
            sub_agent=CONTRACT_SKILL,
            tags=["legal", "contract"],
        )
        # SUB_AGENT: fully autonomous nested agent with private tools.
        # name/description come from TRAVEL_PLANNER dict automatically.
        .with_subagent(
            capability_id="travel.travel_planner",
            sub_agent=TRAVEL_PLANNER,
            tags=["travel", "planning"],
        )
        .with_event_listener(ConsoleEventListener())
        .build()
    )

    result = await agent.ainvoke(
        "I have a 3-day business trip to Chengdu next week. Please help with three things:\n"
        "1. Check Chengdu's recent weather and advise on clothing and travel;\n"
        "2. Analyse the legal risk of these reimbursement clauses:\n"
        "   Clause 2: Hotel cap CNY 500/night; any excess is borne by the employee;\n"
        "   Clause 5: Meal expenses are not reimbursable; employees cover their own meals;\n"
        "3. Based on the weather, plan a 3-day schedule (including business and dining).",
        app_id="demo", user_id="user1", session_id="business-trip-1",
    )

    print("\n========== BusinessTripAssistant Result ==========")
    print("Status :", result.status)
    print("Result :\n", result.final_text)
    print("==================================================\n")


if __name__ == "__main__":
    asyncio.run(main())
