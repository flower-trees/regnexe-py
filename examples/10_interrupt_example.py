"""Example 10 — Human-in-the-loop: interrupt + review + resume

Demonstrates with_interrupt_on() for human approval gates.

Flow:
  1. Agent starts, plans next steps, then PAUSES before executing a sensitive tool.
  2. The calling code inspects the pending state and asks for human approval.
  3. On approval, the same session_id is used to resume -- LangGraph restores the
     exact graph state from the checkpointer and continues from the interrupt point.
  4. On rejection, the session is abandoned.

Under the hood:
  - with_interrupt_on() maps directly to deepagents' interrupt_on parameter, which deepagents
    forwards to langchain's HumanInTheLoopMiddleware. The shape is keyed by TOOL NAME (not by
    graph node name): dict[str, bool | InterruptOnConfig].
      * True                            -> interrupt; allow approve/edit/reject/respond
      * False                           -> auto-approve, no interrupt
      * {"allowed_decisions": [...]}    -> interrupt; restrict to the listed decisions
  - LangGraph checkpointer persists the paused state keyed by thread_id.
  - A plain ainvoke() with a follow-up message does NOT fulfill the interrupt -- the
    paused tool call needs an explicit human decision. Resuming uses agent.aresume(),
    which sends Command(resume={"decisions": [...]}) on the same session_id/thread.
"""

import asyncio

from regnexe import ConsoleEventListener, RegnexeAgentBuilder, Vendor, agent_tool, plugin


# ── Sensitive tool that should require human approval before execution ─────────

@plugin(id="finance", name="Finance Plugin")
class FinancePlugin:
    @agent_tool(
        "Transfer funds between accounts. Requires human approval before execution.",
        tags=["finance", "transfer"],
    )
    def transfer_funds(self, from_account: str, to_account: str, amount: float) -> str:
        """Execute a fund transfer. Input: source account, destination account, amount."""
        return (
            f"Transfer completed: CNY {amount:.2f} from {from_account} to {to_account}. "
            f"Transaction ID: TXN-{abs(hash(from_account + to_account))% 1_000_000:06d}"
        )

    @agent_tool("Check the balance of an account.", tags=["finance"])
    def check_balance(self, account: str) -> str:
        """Check account balance. Input: account identifier."""
        balances = {"ACC-001": 50_000.00, "ACC-002": 12_300.50}
        balance = balances.get(account, 0.0)
        return f"Account {account} balance: CNY {balance:,.2f}"


async def run_with_interrupt() -> None:
    """Two-phase invocation: initial run -> human review -> resume."""

    # Configure interrupt_on keyed by tool name: pause before transfer_funds (sensitive),
    # but leave check_balance auto-approved since it has no entry here.
    agent = (
        RegnexeAgentBuilder()
        .with_default_model(Vendor.DEEPSEEK, "deepseek-v4-flash")
        .with_plugin(FinancePlugin())
        .with_event_listener(ConsoleEventListener())
        .with_interrupt_on({"transfer_funds": True})
        .build()
    )

    session_id = "finance-approval-1"

    # ── Phase 1: initial invocation -- agent plans and hits the interrupt ──────
    print("=" * 60)
    print("Phase 1: Agent starts, may hit interrupt before tool call")
    print("=" * 60)

    result1 = await agent.ainvoke(
        "Check the balance of account ACC-001, then transfer CNY 5000 to ACC-002.",
        app_id="finance-app", user_id="manager1", session_id=session_id,
    )

    print("\n=== Phase 1 result ===")
    print("Status :", result1.status)
    if result1.status == "interrupted":
        for pending in result1.metadata["interrupt"]:
            for req in pending["action_requests"]:
                print(f"  Pending action: {req['name']}({req['args']})")
    else:
        print("Output :", result1.final_text[:300])
        return

    # ── Human review step ─────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    approved = _human_approval_gate()
    print("=" * 60)

    # ── Phase 2: resume with the same session_id ──────────────────────────────
    decision = {"type": "approve"} if approved else {"type": "reject", "message": "Rejected by human reviewer."}
    print("\nPhase 2: Resuming with decision:", decision)

    result2 = await agent.aresume(
        [decision],
        app_id="finance-app", user_id="manager1", session_id=session_id,  # same session
    )

    print("\n=== Phase 2 result (resumed) ===")
    print("Status :", result2.status)
    print("Output :\n", result2.final_text)


def _human_approval_gate() -> bool:
    """Simulate a human reviewing the agent's proposed action."""
    print("\n[HUMAN REVIEW] Agent paused with a pending action awaiting approval.")
    print("\n[HUMAN REVIEW] Approve? Simulating: YES")
    return True   # change to False to simulate rejection


async def main() -> None:
    await run_with_interrupt()


if __name__ == "__main__":
    asyncio.run(main())
