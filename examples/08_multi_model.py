"""Example 08 — Multi-model: different LLM vendors for different capabilities

Scenario: a business trip assistant where each capability uses the best model for its task.
  Outer orchestrator : DeepSeek (fast, cost-effective, strong at tool routing)
  Contract analysis  : Aliyun Qwen-Max (strong at Chinese legal text comprehension)

Pattern: wrap the inner skill agent as a regular MCP_TOOL using @agent_tool,
so the outer agent calls it like any other tool. The inner agent is built with
its own model via .with_model(inner_model).
"""

import asyncio

from langchain_core.tools import tool

from regnexe import RegnexeAgentBuilder, Vendor, agent_tool, plugin
from regnexe.llm.model_provider import ModelProvider
from regnexe.llm.vendor import Vendor as V


# ── Model instances ───────────────────────────────────────────────────────────

provider = ModelProvider()
# Outer orchestrator: DeepSeek -- fast routing and planning
outer_model = provider.resolve(V.DEEPSEEK, "deepseek-v4-flash")
# Inner skill: Aliyun Qwen-Max -- better at Chinese legal analysis
inner_model = provider.resolve(V.ALIYUN, "qwen-max")


# ── Private tool for the inner contract-analysis agent ────────────────────────

@tool
def analyze_clause(clause: str) -> str:
    """Assess the legal risk of a single contract clause. Input: the clause text."""
    if "not reimbursable" in clause.lower() or "borne by the employee" in clause.lower():
        return "Risk: HIGH -- blanket exclusion; add a specific list and appeal process."
    if "cap" in clause.lower() or "limit" in clause.lower():
        return "Risk: MEDIUM -- fixed cap may lag inflation; add CPI-adjustment clause."
    return "Risk: LOW -- clause is clear, no obvious issues."


# ── Inner contract-analysis agent (uses Qwen-Max) ─────────────────────────────

_CONTRACT_SKILL = {
    "name": "contract_analyzer",
    "description": "Legal risk analysis for contract clauses.",
    "system_prompt": (
        "You are a legal contract risk analyst.\n"
        "For each clause call analyze_clause, then summarise all risks and give recommendations."
    ),
    "tools": [analyze_clause],
}


async def _run_contract_analysis(clauses: str) -> str:
    inner_agent = (
        RegnexeAgentBuilder()
        .with_model(inner_model)
        .with_skill_agent(
            capability_id="legal.contract_analyzer",
            name="contract_analyzer",
            description="Legal risk analysis for contract clauses.",
            sub_agent=_CONTRACT_SKILL,
        )
        .build()
    )
    result = await inner_agent.ainvoke(
        clauses, app_id="inner", user_id="u1", session_id="contract-inner"
    )
    return result.final_text


# ── Outer plugin: wraps the inner agent as an MCP_TOOL ───────────────────────

@plugin(id="legal", name="Legal Plugin")
class LegalPlugin:
    @agent_tool(
        "Analyse the legal risk of contract or reimbursement clauses using an expert model.",
        tags=["legal", "contract"],
    )
    def contract_analysis(self, clauses: str) -> str:
        """Run contract clause risk analysis. Input: one or more clause texts."""
        return asyncio.get_event_loop().run_until_complete(_run_contract_analysis(clauses))


@plugin(id="weather", name="Weather Plugin")
class WeatherPlugin:
    @agent_tool("Get today's weather for a city.", tags=["weather"])
    def get_weather(self, city: str) -> str:
        return "Chengdu: partly cloudy, 22 degrees C -- bring a light jacket."


# ── Outer agent (DeepSeek) orchestrates both plugins ─────────────────────────

async def main() -> None:
    agent = (
        RegnexeAgentBuilder()
        .with_model(outer_model)
        .with_plugin(WeatherPlugin(), LegalPlugin())
        .build()
    )

    result = await agent.ainvoke(
        "Check Chengdu weather and analyse these reimbursement clauses:\n"
        "Clause 2: Hotel cap CNY 500/night; any excess is borne by the employee.\n"
        "Clause 5: Meal expenses are not reimbursable; employees cover their own meals.",
        app_id="demo", user_id="user1", session_id="multi-model-1",
    )

    print("\n========== Multi-Model Result ==========")
    print("Outer model :", "deepseek-v4-flash  (routing & planning)")
    print("Inner model :", "qwen-max           (contract analysis)")
    print("Status      :", result.status)
    print("Result      :\n", result.final_text)
    print("========================================\n")


if __name__ == "__main__":
    asyncio.run(main())
