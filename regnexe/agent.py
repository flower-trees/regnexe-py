"""RegnexeAgent — main agent orchestrator built on deepagents."""

from __future__ import annotations

import asyncio
import uuid
from typing import TYPE_CHECKING, Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage

from regnexe.event.listener import AgentEventListener
from regnexe.market.simple_marketplace import SimpleMarketplace
from regnexe.plugin.enums import CapabilityType
from regnexe.result import AgentResult
from regnexe.session.session_key import SessionKey

if TYPE_CHECKING:
    pass

# Display label for each CapabilityType, used to prefix TOOL_CALLED/TOOL_RESULT
# events as "<label>:<name>" (e.g. "skill:travel_advisor", "mcp_tool:get_weather").
_CAPABILITY_TYPE_LABELS: dict[CapabilityType, str] = {
    CapabilityType.MCP_TOOL: "mcp_tool",
    CapabilityType.SKILL: "skill",
    CapabilityType.SUB_AGENT: "subagent",
}


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
        listener: AgentEventListener | None,
        interrupt_on: dict[str, Any] | None,
        system_prompt: str | None,
        middleware: list[Any],
    ) -> None:
        self._model = model
        self._marketplace = marketplace
        self._checkpointer = checkpointer
        self._store = store
        self._listener = listener
        self._interrupt_on = interrupt_on
        self._system_prompt = system_prompt
        self._middleware = middleware
        self._session_key = SessionKey()
        self._deep_agent: Any = None   # lazy-compiled deepagents graph
        self._running_tasks: dict[str, asyncio.Task] = {}
        self._capability_types: dict[str, CapabilityType] = {}   # name -> type, for event labeling

    # ------------------------------------------------------------------ public

    async def ainvoke(
        self,
        goal: str,
        app_id: str = "default",
        user_id: str = "default",
        session_id: str = "default",
    ) -> AgentResult:
        thread_id = self._session_key.to_thread_id(app_id, user_id, session_id)
        deep_agent = self._get_or_create_agent()

        return await self._run_graph(
            deep_agent,
            thread_id=thread_id,
            input_={"messages": [HumanMessage(content=goal)]},
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
        deep_agent = self._get_or_create_agent()

        return await self._run_graph(
            deep_agent,
            thread_id=thread_id,
            input_=Command(resume={"decisions": decisions}),
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

    async def acancel(
        self,
        app_id: str = "default",
        user_id: str = "default",
        session_id: str = "default",
    ) -> bool:
        """Stop the run currently in flight for this session, at whatever point it's at.

        Unlike with_interrupt_on() (a pre-configured pause before a specific tool, for
        approval), this is a user-triggered stop that can land at any point. The target
        ainvoke()/aresume() call must be running as a separate asyncio.Task (e.g. via
        asyncio.create_task(...)) -- cancelling your own awaiting task is a no-op since
        there is no concurrent task to deliver the cancellation to.

        Returns True if a running task was found and cancelled, False if nothing was
        in flight for this session. The cancelled call returns a normal
        AgentResult(status="cancelled") rather than raising -- LangGraph checkpoints
        after every completed step, so a later plain ainvoke() on the same session_id
        continues from the last completed step (no aresume() needed; that path is only
        for fulfilling a pending with_interrupt_on() approval).
        """
        thread_id = self._session_key.to_thread_id(app_id, user_id, session_id)
        task = self._running_tasks.get(thread_id)
        if task is None or task.done():
            return False
        return task.cancel()

    def cancel(
        self,
        app_id: str = "default",
        user_id: str = "default",
        session_id: str = "default",
    ) -> bool:
        """Synchronous wrapper around :meth:`acancel`."""
        import asyncio
        return asyncio.get_event_loop().run_until_complete(
            self.acancel(app_id=app_id, user_id=user_id, session_id=session_id)
        )

    # ------------------------------------------------------------------ internals

    async def _run_graph(
        self,
        deep_agent: Any,
        thread_id: str,
        input_: Any,
        log_goal: str,
    ) -> AgentResult:
        task_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}

        if self._listener:
            await self._listener.dispatch("AGENT_STARTED", "RegnexeAgent", {"goal": log_goal, "task_id": task_id})

        final_text = ""
        status = "completed"
        interrupt_payload: Any = None

        self._running_tasks[thread_id] = asyncio.current_task()
        # Tracks in-flight subagent ("task" tool) calls for this run only, keyed by
        # run_id -- must stay local to this _run_graph() call, not on self, since
        # acancel() allows multiple ainvoke()/aresume() calls to run concurrently.
        in_flight: dict[str, dict[str, str]] = {}
        try:
            async for event in deep_agent.astream_events(input_, config=config, version="v2"):
                await self._dispatch(event, in_flight)

            state = await deep_agent.aget_state(config)
            final_text = self._extract_final_text(state)

            if state.next:
                status = "interrupted"
                interrupt_payload = [
                    interrupt.value for task in state.tasks for interrupt in task.interrupts
                ]

        except asyncio.CancelledError:
            # Deliberately not re-raised: LangGraph already checkpointed every step
            # completed so far, so callers get a normal AgentResult(status="cancelled")
            # instead of having to catch CancelledError themselves.
            status = "cancelled"
            state = await deep_agent.aget_state(config)
            final_text = self._extract_final_text(state)

        except Exception as exc:
            status = "error"
            final_text = str(exc)
        finally:
            self._running_tasks.pop(thread_id, None)

        if self._listener:
            await self._listener.dispatch("AGENT_COMPLETED", "RegnexeAgent", {"status": status})

        return AgentResult(
            status=status,
            final_text=final_text,
            task_id=task_id,
            thread_id=thread_id,
            metadata={"interrupt": interrupt_payload} if interrupt_payload else {},
        )

    def _get_or_create_agent(self) -> Any:
        """Build the deepagents graph on first call; reuse on subsequent calls."""
        if self._deep_agent is None:
            self._deep_agent = self._build_deep_agent(self._system_prompt)
        return self._deep_agent

    def _build_deep_agent(self, system_prompt: str | None) -> Any:
        from deepagents import create_deep_agent

        descriptors = self._marketplace.search("")
        descriptors = self._resolve_skill_agent_tools(descriptors)
        tools, skill_paths, subagents = self._marketplace.split_by_type(descriptors)
        self._capability_types = self._build_capability_type_map(descriptors)

        kwargs: dict[str, Any] = dict(
            model=self._model,
            tools=tools or None,
            skills=skill_paths or None,
            subagents=subagents or None,
            system_prompt=system_prompt,
            checkpointer=self._checkpointer,
            store=self._store,
            middleware=self._middleware or None,
        )
        if self._interrupt_on:
            kwargs["interrupt_on"] = self._interrupt_on

        return create_deep_agent(**{k: v for k, v in kwargs.items() if v is not None})

    @staticmethod
    def _build_capability_type_map(descriptors: list[Any]) -> dict[str, CapabilityType]:
        """Map the name each capability is *invoked* by (deepagents tool/subagent_type
        name) to its registered CapabilityType, for labeling TOOL_CALLED/TOOL_RESULT
        events. Unregistered names (e.g. deepagents' own built-in tools) are absent.
        """
        capability_types: dict[str, CapabilityType] = {}
        for desc in descriptors:
            if desc.type == CapabilityType.MCP_TOOL and desc.tool is not None:
                capability_types[desc.tool.name] = desc.type
            elif desc.sub_agent is not None:
                capability_types[desc.sub_agent.get("name", desc.name)] = desc.type
        return capability_types

    def _capability_label(self, name: str) -> str | None:
        cap_type = self._capability_types.get(name)
        return _CAPABILITY_TYPE_LABELS.get(cap_type) if cap_type else None

    def _resolve_skill_agent_tools(
        self, descriptors: list[Any]
    ) -> list[Any]:
        """For SKILL-type sub_agents, resolve string tool IDs to actual BaseTool objects."""
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

    async def _dispatch(self, event: dict[str, Any], in_flight: dict[str, dict[str, str]]) -> None:
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
                await self._dispatch_tool_start(event, in_flight)

            case "on_tool_end":
                await self._dispatch_tool_end(event, in_flight)

    async def _dispatch_tool_start(self, event: dict[str, Any], in_flight: dict[str, dict[str, str]]) -> None:
        name = event.get("name", "")
        run_id = event.get("run_id", "")
        raw_input = event.get("data", {}).get("input", {})
        nested_under = self._nested_under(event.get("parent_ids", []), in_flight)

        # deepagents dispatches a Skill/Sub-Agent through its own "task" tool,
        # subagent_type-keyed -- relabel using the subagent's own name instead of
        # the literal "task", and remember it so nested tool calls inside it (matched
        # by parent_ids) can be tagged "[<type>:<name>] ...".
        if name == "task" and isinstance(raw_input, dict) and "subagent_type" in raw_input:
            subagent_name = raw_input["subagent_type"]
            label = self._capability_label(subagent_name) or "subagent"
            in_flight[run_id] = {"type": label, "name": subagent_name}
            await self._listener.dispatch("TOOL_CALLED", subagent_name, {
                "input": raw_input.get("description", raw_input),
                "capability_type": label,
                "nested_under": nested_under,
            })
            return

        await self._listener.dispatch("TOOL_CALLED", name, {
            "input": raw_input,
            "capability_type": self._capability_label(name),
            "nested_under": nested_under,
        })

    async def _dispatch_tool_end(self, event: dict[str, Any], in_flight: dict[str, dict[str, str]]) -> None:
        name = event.get("name", "")
        run_id = event.get("run_id", "")
        raw_output = event.get("data", {}).get("output", "")
        nested_under = self._nested_under(event.get("parent_ids", []), in_flight)

        task_ctx = in_flight.pop(run_id, None)
        if task_ctx is not None:
            await self._listener.dispatch("TOOL_RESULT", task_ctx["name"], {
                "output": self._extract_output_text(raw_output),
                "capability_type": task_ctx["type"],
                "nested_under": nested_under,
            })
            return

        await self._listener.dispatch("TOOL_RESULT", name, {
            "output": self._extract_output_text(raw_output),
            "capability_type": self._capability_label(name),
            "nested_under": nested_under,
        })

    @staticmethod
    def _nested_under(parent_ids: list[str], in_flight: dict[str, dict[str, str]]) -> dict[str, str] | None:
        """Find the innermost active subagent ("task" tool) call this event is nested
        under, by walking parent_ids from the closest ancestor inward. Looked up by
        run_id rather than a shared stack, since concurrent ainvoke() calls (acancel())
        interleave events from independent runs.
        """
        for pid in reversed(parent_ids):
            if pid in in_flight:
                return in_flight[pid]
        return None

    @staticmethod
    def _extract_output_text(output: Any) -> str:
        """Extract human-readable text from a tool/task result.

        A deepagents "task" (subagent) result is a LangGraph Command whose final
        answer lives at output.update["messages"][-1].content; a plain tool result is
        usually a ToolMessage with .content directly.
        """
        update = getattr(output, "update", None)
        if isinstance(update, dict):
            messages = update.get("messages") or []
            if messages:
                content = getattr(messages[-1], "content", None)
                if isinstance(content, str):
                    return content

        content = getattr(output, "content", None)
        if isinstance(content, str):
            return content

        return str(output)

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
