"""Example 02 — SKILL capability: SubAgent with private tools

Scenario: legal risk analysis of contract clauses.
Capability type: SKILL — a SubAgent with dedicated system_prompt and private tools.

The outer agent decides to delegate to contract_analyzer.
contract_analyzer calls its private analyze_clause tool clause by clause,
then returns a risk report to the outer agent.

Mirrors: ContractAnalyzerTest in regnexe-agent (Java)
  SkillConfig.systemPrompt -> SubAgent["system_prompt"]
  Skill.tools(analyzeClauseTool) -> SubAgent["tools"]
"""

import asyncio

from langchain_core.tools import tool

from regnexe import ConsoleEventListener, RegnexeAgentBuilder, Vendor


@tool
def analyze_clause(clause: str) -> str:
    """Assess the legal risk of a single contract clause. Input: the clause text."""
    if "unilaterally" in clause.lower() or "sole discretion" in clause.lower():
        return (
            "Risk level: HIGH\n"
            "Issue: Clause grants one-sided rights, creating severe imbalance.\n"
            "Suggestion: Add the other party's right to object and specify compensation terms."
        )
    if "penalty" in clause.lower() or "liquidated damages" in clause.lower():
        return (
            "Risk level: MEDIUM\n"
            "Issue: Penalty clause lacks a clear calculation method or cap.\n"
            "Suggestion: Define the formula and set a reasonable cap (e.g. <= 30% of contract value)."
        )
    return "Risk level: LOW\nIssue: No obvious legal risk detected.\nSuggestion: Keep current wording."


CONTRACT_SKILL = {
    "name": "contract_analyzer",
    "description": (
        "Professional legal risk analysis for contract clauses. "
        "Input clause text, output risk level and improvement suggestions. "
        "TRIGGER: Use when the user needs to analyse contracts, agreements, or clause risks."
    ),
    "system_prompt": (
        "You are a professional legal contract risk analyst.\n"
        "When given contract clauses:\n"
        "1. Call analyze_clause for each key clause\n"
        "2. Summarise risk levels (HIGH / MEDIUM / LOW) for all clauses\n"
        "3. Provide an overall risk assessment and revision recommendations\n"
        "Respond clearly and concisely."
    ),
    "tools": [analyze_clause],
}


async def main() -> None:
    agent = (
        RegnexeAgentBuilder()
        .with_default_model(Vendor.DEEPSEEK, "deepseek-v4-flash")
        .with_skill_agent(
            capability_id="legal.contract_analyzer",
            name="contract_analyzer",
            description=(
                "Professional legal risk analysis for contract clauses. "
                "Input clause text, output risk level and improvement suggestions."
            ),
            sub_agent=CONTRACT_SKILL,
            tags=["legal", "contract", "risk"],
        )
        .with_event_listener(ConsoleEventListener(show_system_prompt=True))
        .build()
    )

    result = await agent.ainvoke(
        "Please analyse the legal risk of the following contract clauses:\n"
        "Clause 3: Party A may unilaterally amend any term of this agreement. "
        "Party B must confirm in writing within 5 days of notice; silence constitutes acceptance.\n"
        "Clause 7: Liquidated damages for Party B's breach shall be 50% of the total contract value; "
        "Party A bears no liability for its own breach.",
        app_id="demo", user_id="user1", session_id="contract-1",
    )

    print("\n========== ContractAnalyzer Result ==========")
    print("Status  :", result.status)
    print("Task ID :", result.task_id)
    print("Analysis:\n", result.final_text)
    print("=============================================\n")


if __name__ == "__main__":
    asyncio.run(main())
