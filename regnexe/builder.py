"""RegnexeAgentBuilder — fluent API for constructing a RegnexeAgent."""

from __future__ import annotations

from typing import Any, Self

from langchain_core.language_models import BaseChatModel

from regnexe.agent import RegnexeAgent
from regnexe.event.listener import AgentEventListener
from regnexe.llm.model_provider import ModelProvider
from regnexe.llm.vendor import Vendor
from regnexe.market.simple_marketplace import SimpleMarketplace
from regnexe.session.task_store import TaskResultStore


class RegnexeAgentBuilder:
    """Builder for :class:`RegnexeAgent`.

    Usage::

        agent = (
            RegnexeAgentBuilder()
            .with_default_model(Vendor.ALIYUN, "qwen-max")
            .with_plugin(WeatherPlugin())
            .with_event_listener(ConsoleEventListener())
            .build()
        )
    """

    def __init__(self) -> None:
        self._model: BaseChatModel | None = None
        self._marketplace = SimpleMarketplace()
        self._checkpointer: Any = None
        self._store: Any = None
        self._listener: AgentEventListener | None = None
        self._interrupt_on: dict[str, Any] | None = None
        self._system_prompt: str | None = None
        self._session_buffer_size: int = 10
        self._model_provider = ModelProvider()

    # ------------------------------------------------------------------ model

    def with_default_model(self, vendor: Vendor, model_name: str) -> Self:
        """Set the LLM provider and model."""
        self._model = self._model_provider.resolve(vendor, model_name)
        return self

    def with_model(self, model: BaseChatModel) -> Self:
        """Pass a pre-built LangChain BaseChatModel directly."""
        self._model = model
        return self

    def with_model_spec(self, spec: str) -> Self:
        """Set model from a ``vendor:model_name`` string, e.g. ``'aliyun:qwen-max'``."""
        self._model = self._model_provider.resolve_from_spec(spec)
        return self

    # ------------------------------------------------------------------ capabilities

    def with_plugin(self, *instances: object) -> Self:
        """Register one or more @plugin-decorated class instances."""
        for inst in instances:
            self._marketplace.install_instance(inst)
        return self

    def with_directory(self, path: str) -> Self:
        """Scan a directory for SKILL.md and plugin.yaml capability files."""
        self._marketplace.install_from_file(path)
        return self

    def with_skill(
        self,
        capability_id: str,
        name: str,
        description: str,
        skill_path: str,
        tags: list[str] | None = None,
    ) -> Self:
        """Register a SKILL capability (a directory containing SKILL.md)."""
        self._marketplace.install_skill(capability_id, name, description, skill_path, tags)
        return self

    def with_skill_agent(
        self,
        capability_id: str,
        name: str,
        description: str,
        sub_agent: Any,
        tags: list[str] | None = None,
    ) -> Self:
        """Register a SKILL capability: SubAgent with focused system_prompt and private tools.

        Use this when the capability has its own system_prompt and private tools
        (mirrors Java's Skill). Use with_skill() for pure SKILL.md knowledge skills.
        """
        self._marketplace.install_skill_agent(capability_id, name, description, sub_agent, tags)
        return self

    def with_subagent(
        self,
        capability_id: str,
        name: str,
        description: str,
        sub_agent: Any,
        tags: list[str] | None = None,
    ) -> Self:
        """Register a SUB_AGENT capability (deepagents SubAgent TypedDict)."""
        self._marketplace.install_subagent(capability_id, name, description, sub_agent, tags)
        return self

    # ------------------------------------------------------------------ session / persistence

    def with_checkpointer(self, checkpointer: Any) -> Self:
        """Set the LangGraph checkpointer for within-session state (Layer 2)."""
        self._checkpointer = checkpointer
        return self

    def with_store(self, store: Any) -> Self:
        """Set the LangGraph BaseStore for cross-session task history (Layer 3)."""
        self._store = store
        return self

    def with_session_buffer_size(self, size: int) -> Self:
        """Max conversation turns kept verbatim before summarization kicks in."""
        self._session_buffer_size = size
        return self

    # ------------------------------------------------------------------ observability / control

    def with_event_listener(self, listener: AgentEventListener) -> Self:
        """Attach an event listener (e.g. ConsoleEventListener)."""
        self._listener = listener
        return self

    def with_interrupt_on(self, interrupt_on: dict[str, Any]) -> Self:
        """Configure deepagents interrupt_on for human-in-the-loop gates."""
        self._interrupt_on = interrupt_on
        return self

    def with_system_prompt(self, prompt: str) -> Self:
        """Prepend a custom system prompt to every invocation."""
        self._system_prompt = prompt
        return self

    # ------------------------------------------------------------------ build

    def build(self) -> RegnexeAgent:
        if self._model is None:
            raise ValueError("No model configured. Call with_default_model() or with_model() first.")

        checkpointer = self._checkpointer
        if checkpointer is None:
            from langgraph.checkpoint.memory import MemorySaver
            checkpointer = MemorySaver()

        task_store = TaskResultStore(store=self._store)

        return RegnexeAgent(
            model=self._model,
            marketplace=self._marketplace,
            checkpointer=checkpointer,
            store=self._store,
            task_store=task_store,
            listener=self._listener,
            interrupt_on=self._interrupt_on,
            system_prompt=self._system_prompt,
            session_buffer_size=self._session_buffer_size,
        )
