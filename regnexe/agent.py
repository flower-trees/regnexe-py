"""RegnexeAgent — main agent orchestrator built on deepagents."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage

from regnexe.event.listener import AgentEventListener
from regnexe.market.simple_marketplace import SimpleMarketplace
from regnexe.result import AgentResult
from regnexe.session.session_key import SessionKey
from regnexe.session.task_store import TaskResultStore

if TYPE_CHECKING:
    pass


class RegnexeAgent:
    """Agent orchestrator that wraps deepagents' create_deep_agent.

    Call :meth:`ainvoke` (async) or :meth:`invoke` (sync wrapper) to run a task.
    The underlying deepagents graph is created lazily on the first invocation and
    cached for subsequent calls (since v1 marketplace search always returns all
    capabilities).
    """

    def __init__(
        self,
        model: BaseChatModel,
        marketplace: SimpleMarketplace,
        checkpointer: Any,
        store: Any | None,
        task_store: TaskResultStore,
        listener: AgentEventListener | None,
        interrupt_on: dict[str, Any] | None,
        system_prompt: str | None,
        session_buffer_size: int,
    ) -> None:
        self._model = model
        self._marketplace = marketplace
        self._checkpointer = checkpointer
        self._store = store
        self._task_store = task_store
        self._listener = listener
        self._interrupt_on = interrupt_on
        self._system_prompt = system_prompt
        self._session_buffer_size = session_buffer_size
        self._session_key = SessionKey()
        self._deep_agent: Any = None   # lazy-compiled deepagents graph

    # ------------------------------------------------------------------ public

    async def ainvoke(
        self,
        goal: str,
        app_id: str = "default",
        user_id: str = "default",
        session_id: str = "default",
    ) -> AgentResult:
        thread_id = self._session_key.to_thread_id(app_id, user_id, session_id)
        effective_system = await self._effective_system_prompt(app_id, user_id)
        deep_agent = self._get_or_create_agent(effective_system)

        return await self._run_graph(
            deep_agent,
            thread_id=thread_id,
            input_={"messages": [HumanMessage(content=goal)]},
            app_id=app_id,
            user_id=user_id,
            log_goal=goal,
        )

    def invoke(
        self,
        goal: str,
        app_id: str = "default",
        user_id: str = "default",
        session_id: str = "default",
    ) -> AgentResult:
        """Synchronous wrapper around :meth:`ainvoke`."""
        import asyncio
        return asyncio.get_event_loop().run_until_complete(
            self.ainvoke(goal, app_id=app_id, user_id=user_id, session_id=session_id)
        )

    async def aresume(
        self,
        decisions: list[dict[str, Any]],
        app_id: str = "default",
        user_id: str = "default",
        session_id: str = "default",
    ) -> AgentResult:
        """Resume a thread paused by with_interrupt_on() with human decisions.

        Each decision matches langgraph/langchain's HumanInTheLoopMiddleware Decision
        shape, e.g. ``{"type": "approve"}``, ``{"type": "reject", "message": "..."}``,
        ``{"type": "edit", "edited_action": {...}}``, or
        ``{"type": "respond", "message": "..."}``. Supply exactly one decision per
        pending interrupted tool call, in the same order they were requested (see
        ``AgentResult.metadata["interrupt"]`` from the call that produced the pause).
        """
        from langgraph.types import Command

        thread_id = self._session_key.to_thread_id(app_id, user_id, session_id)
        effective_system = await self._effective_system_prompt(app_id, user_id)
        deep_agent = self._get_or_create_agent(effective_system)

        return await self._run_graph(
            deep_agent,
            thread_id=thread_id,
            input_=Command(resume={"decisions": decisions}),
            app_id=app_id,
            user_id=user_id,
            log_goal=f"[resume] decisions={decisions}",
        )

    def resume(
        self,
        decisions: list[dict[str, Any]],
        app_id: str = "default",
        user_id: str = "default",
        session_id: str = "default",
    ) -> AgentResult:
        """Synchronous wrapper around :meth:`aresume`."""
        import asyncio
        return asyncio.get_event_loop().run_until_complete(
            self.aresume(decisions, app_id=app_id, user_id=user_id, session_id=session_id)
        )

    # ------------------------------------------------------------------ internals

    async def _effective_system_prompt(self, app_id: str, user_id: str) -> str | None:
        """Layer 3: inject recent cross-session task history into the system prompt."""
        recent = await self._task_store.load_recent(app_id, user_id)
        history_ctx = TaskResultStore.format_for_prompt(recent)
        system_parts = [p for p in [self._system_prompt, history_ctx] if p]
        return "\n\n".join(system_parts) if system_parts else None

    async def _run_graph(
        self,
        deep_agent: Any,
        thread_id: str,
        input_: Any,
        app_id: str,
        user_id: str,
        log_goal: str,
    ) -> AgentResult:
        task_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}

        if self._listener:
            await self._listener.dispatch("AGENT_STARTED", "RegnexeAgent", {"goal": log_goal, "task_id": task_id})

        final_text = ""
        status = "completed"
        interrupt_payload: Any = None

        try:
            async for event in deep_agent.astream_events(input_, config=config, version="v2"):
                await self._dispatch(event)

            state = await deep_agent.aget_state(config)
            final_text = self._extract_final_text(state)

            if state.next:
                status = "interrupted"
                interrupt_payload = [
                    interrupt.value for task in state.tasks for interrupt in task.interrupts
                ]

        except Exception as exc:
            status = "error"
            final_text = str(exc)

        # Layer 3: persist task result
        await self._task_store.save(
            app_id, user_id, task_id, log_goal,
            summary=final_text[:500],
            status=status,
        )

        if self._listener:
            await self._listener.dispatch("AGENT_COMPLETED", "RegnexeAgent", {"status": status})

        return AgentResult(
            status=status,
            final_text=final_text,
            task_id=task_id,
            thread_id=thread_id,
            metadata={"interrupt": interrupt_payload} if interrupt_payload else {},
        )

    def _get_or_create_agent(self, system_prompt: str | None) -> Any:
        """Build the deepagents graph on first call; reuse on subsequent calls."""
        cache_key = system_prompt or ""
        if self._deep_agent is None or getattr(self._deep_agent, "_regnexe_sp_key", None) != cache_key:
            self._deep_agent = self._build_deep_agent(system_prompt)
            self._deep_agent._regnexe_sp_key = cache_key  # type: ignore[attr-defined]
        return self._deep_agent

    def _build_deep_agent(self, system_prompt: str | None) -> Any:
        from deepagents import create_deep_agent

        descriptors = self._marketplace.search("")
        descriptors = self._resolve_skill_agent_tools(descriptors)
        tools, skill_paths, subagents = self._marketplace.split_by_type(descriptors)

        kwargs: dict[str, Any] = dict(
            model=self._model,
            tools=tools or None,
            skills=skill_paths or None,
            subagents=subagents or None,
            system_prompt=system_prompt,
            checkpointer=self._checkpointer,
            store=self._store,
        )
        if self._interrupt_on:
            kwargs["interrupt_on"] = self._interrupt_on

        return create_deep_agent(**{k: v for k, v in kwargs.items() if v is not None})

    def _resolve_skill_agent_tools(
        self, descriptors: list[Any]
    ) -> list[Any]:
        """For SKILL-type sub_agents, resolve string tool IDs to actual BaseTool objects."""
        from regnexe.plugin.enums import CapabilityType
        result = []
        for desc in descriptors:
            if (
                desc.type == CapabilityType.SKILL
                and desc.sub_agent is not None
                and desc.skill_path is None
            ):
                tool_ids: list[str] = desc.sub_agent.get("tools", [])
                if tool_ids and isinstance(tool_ids[0], str):
                    resolved = []
                    for tid in tool_ids:
                        try:
                            resolved.append(self._marketplace.resolve(tid).tool)
                        except KeyError:
                            raise ValueError(
                                f"Skill agent tool ID {tid!r} not found in marketplace. "
                                "Register it with with_plugin() or with_tool() first."
                            )
                    import dataclasses
                    desc = dataclasses.replace(
                        desc, sub_agent={**desc.sub_agent, "tools": resolved}
                    )
            result.append(desc)
        return result

    async def _dispatch(self, event: dict[str, Any]) -> None:
        if not self._listener:
            return
        kind = event.get("event", "")
        name = event.get("name", "")
        data = event.get("data", {})

        match kind:
            case "on_chat_model_start":
                # data["input"]["messages"] is a list of batches; take the first batch
                raw = data.get("input", {}).get("messages", [])
                batch = raw[0] if raw else []
                messages = [_serialize_message(m) for m in batch]
                await self._listener.dispatch("LLM_START", name, {"messages": messages})

            case "on_chat_model_end":
                output = data.get("output")
                usage = getattr(output, "usage_metadata", None) or {}
                text = ""
                if output is not None:
                    content = getattr(output, "content", "")
                    text = content if isinstance(content, str) else str(content)
                await self._listener.dispatch("LLM_END", name, {"usage": usage, "text": text})

            case "on_tool_start":
                await self._listener.dispatch("TOOL_CALLED", name, {"input": data.get("input", {})})

            case "on_tool_end":
                await self._listener.dispatch("TOOL_RESULT", name, {"output": data.get("output", "")})

    @staticmethod
    def _extract_final_text(state: Any) -> str:
        messages = getattr(state, "values", {}).get("messages", [])
        for msg in reversed(messages):
            content = getattr(msg, "content", "")
            if content and not getattr(msg, "tool_calls", None) and type(msg).__name__ == "AIMessage":
                return content if isinstance(content, str) else str(content)
        return ""


def _serialize_message(msg: Any) -> dict[str, Any]:
    """Convert a LangChain message object to a plain dict for logging."""
    msg_type = type(msg).__name__.replace("Message", "").lower()  # SystemMessage→system
    content = getattr(msg, "content", "")
    result: dict[str, Any] = {
        "role": msg_type,
        "content": content if isinstance(content, str) else str(content),
    }
    tool_calls = getattr(msg, "tool_calls", None)
    if tool_calls:
        result["tool_calls"] = [
            {"name": tc.get("name", ""), "args": tc.get("args", {})}
            for tc in tool_calls
        ]
    tool_call_id = getattr(msg, "tool_call_id", None)
    if tool_call_id:
        result["tool_call_id"] = tool_call_id
    return result
