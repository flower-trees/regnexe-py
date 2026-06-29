"""RegnexeAgentBuilder — fluent API for constructing a RegnexeAgent."""

from __future__ import annotations

from typing import Any, Self

from langchain_core.language_models import BaseChatModel

from regnexe.agent import RegnexeAgent
from regnexe.event.listener import AgentEventListener
from regnexe.llm.model_provider import ModelProvider
from regnexe.llm.vendor import Vendor
from regnexe.market.simple_marketplace import SimpleMarketplace
from regnexe.plugin.descriptor import PluginDescriptor


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
        self._middleware: list[Any] = []
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

    def with_marketplace(self, marketplace: SimpleMarketplace) -> Self:
        """Replace the default in-memory marketplace with a custom backing store.

        Must expose the same interface as SimpleMarketplace (install/search/resolve/
        split_by_type) -- RegnexeAgent's graph construction calls split_by_type()
        internally, which isn't part of the Marketplace protocol, so the simplest way
        to swap storage (e.g. a database table) is subclassing SimpleMarketplace and
        overriding install()/search()/resolve().
        """
        self._marketplace = marketplace
        return self

    def with_plugin(self, *plugins: object) -> Self:
        """Register PluginDescriptor objects or @plugin-decorated class instances."""
        for plugin in plugins:
            if isinstance(plugin, PluginDescriptor):
                self._marketplace.install(plugin)
            else:
                self._marketplace.install_instance(plugin)
        return self

    def with_directory(self, path: str) -> Self:
        """Scan a directory for SKILL.md and plugin.yaml capability files."""
        self._marketplace.install_from_file(path)
        return self

    def with_skill_dir(
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

    def with_skill(
        self,
        capability_id: str,
        sub_agent: Any,
        tags: list[str] | None = None,
        name: str | None = None,
        description: str | None = None,
    ) -> Self:
        """Register a SKILL capability: SubAgent sharing tools from the parent marketplace.

        name/description default to sub_agent["name"] / sub_agent["description"].
        tools in sub_agent must be str capability IDs already registered in the marketplace.
        Use with_subagent() for private @tool objects invisible to the main agent.
        """
        self._marketplace.install_skill_agent(capability_id, sub_agent, tags, name, description)
        return self

    def with_tool(self, *tools: Any) -> Self:
        """Register one or more pre-built LangChain tools directly as MCP_TOOL capabilities."""
        for tool in tools:
            self._marketplace.install_tool(tool)
        return self

    def with_subagent(
        self,
        capability_id: str,
        sub_agent: Any,
        tags: list[str] | None = None,
        name: str | None = None,
        description: str | None = None,
    ) -> Self:
        """Register a SUB_AGENT capability (deepagents SubAgent TypedDict).

        name/description default to sub_agent["name"] / sub_agent["description"].
        tools can be private @tool objects invisible to the outer agent.
        """
        self._marketplace.install_subagent(capability_id, sub_agent, tags, name, description)
        return self

    # ------------------------------------------------------------------ session / persistence

    def with_checkpointer(self, checkpointer: Any) -> Self:
        """Set the LangGraph checkpointer for session memory.

        Defaults to MemorySaver (in-process). Replace with a persistent
        checkpointer (e.g. AsyncSqliteSaver, RedisSaver) to survive restarts.
        All ainvoke() calls sharing the same session_id land on the same thread.
        """
        self._checkpointer = checkpointer
        return self

    def with_store(self, store: Any) -> Self:
        """Set the LangGraph BaseStore passed through to create_deep_agent."""
        self._store = store
        return self

    def with_middleware(self, *middleware: Any) -> Self:
        """Append one or more deepagents middleware objects to the agent's stack.

        Use this to customise context management, e.g. swap the default
        SummarizationMiddleware for one tuned to your token budget::

            from deepagents.middleware.summarization import SummarizationMiddleware
            from deepagents.backends import StateBackend

            summ = SummarizationMiddleware(
                model=my_model,
                backend=StateBackend(),
                trigger=("tokens", 60_000),
                keep=("messages", 10),
            )
            agent = RegnexeAgentBuilder()
                .with_default_model(...)
                .with_middleware(summ)
                .build()
        """
        self._middleware.extend(middleware)
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

        return RegnexeAgent(
            model=self._model,
            marketplace=self._marketplace,
            checkpointer=checkpointer,
            store=self._store,
            listener=self._listener,
            interrupt_on=self._interrupt_on,
            system_prompt=self._system_prompt,
            middleware=self._middleware,
        )
