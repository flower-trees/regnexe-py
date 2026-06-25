"""SimpleMarketplace — in-memory registry, v1 returns all capabilities on search."""

from __future__ import annotations

import inspect
from typing import Any

from langchain_core.tools import StructuredTool

from regnexe.llm.model_provider import resolve_sub_agent_model
from regnexe.plugin.decorators import (
    _PLUGIN_META_ATTR,
    _SKILL_META_ATTR,
    _SUBAGENT_META_ATTR,
    _TOOL_META_ATTR,
)
from regnexe.plugin.descriptor import CapabilityDescriptor, PluginDescriptor
from regnexe.plugin.enums import CapabilityType


class SimpleMarketplace:
    def __init__(self) -> None:
        self._capabilities: dict[str, CapabilityDescriptor] = {}

    # ------------------------------------------------------------------ install

    def install(self, plugin: PluginDescriptor) -> None:
        """Register a fully-built PluginDescriptor."""
        for cap in plugin.capabilities:
            self._capabilities[cap.capability_id] = cap

    def install_instance(self, instance: object) -> None:
        """Scan a decorated class instance and register its capabilities.

        Dispatches on whichever class-level decorator is present:
        - ``@plugin``: scans ``@agent_tool`` methods (MCP_TOOL), plus nested
          ``@agent_skill``/``@agent_subagent`` inner classes, all bundled under one
          ``plugin_id``.
        - ``@agent_skill`` / ``@agent_subagent`` (standalone, no ``@plugin``):
          registers as its own single-capability plugin -- capability_id = plugin_id
          = the decorator's ``id``.
        """
        cls = type(instance)

        plugin_meta = getattr(cls, _PLUGIN_META_ATTR, None)
        if plugin_meta is not None:
            self._install_plugin_bean(instance, cls, plugin_meta["id"])
            return

        skill_meta = getattr(cls, _SKILL_META_ATTR, None)
        if skill_meta is not None:
            self._register_skill(skill_meta["id"], skill_meta)
            return

        subagent_meta = getattr(cls, _SUBAGENT_META_ATTR, None)
        if subagent_meta is not None:
            self._register_subagent(subagent_meta["id"], subagent_meta, instance, cls)
            return

        raise ValueError(
            f"{cls.__name__} must be decorated with @plugin, @agent_skill, or @agent_subagent"
        )

    def _install_plugin_bean(self, instance: object, cls: type, plugin_id: str) -> None:
        for method_name, bound, tool_meta in self._scan_tool_methods(instance, cls):
            lc_tool = StructuredTool.from_function(
                func=bound, name=method_name, description=tool_meta["description"],
            )
            capability_id = f"{plugin_id}.{method_name}"
            self._capabilities[capability_id] = CapabilityDescriptor(
                capability_id=capability_id,
                plugin_id=plugin_id,
                type=CapabilityType.MCP_TOOL,
                name=method_name,
                description=tool_meta["description"],
                tags=tool_meta["tags"],
                tool=lc_tool,
            )

        for _, nested_cls in inspect.getmembers(cls, predicate=inspect.isclass):
            nested_skill_meta = getattr(nested_cls, _SKILL_META_ATTR, None)
            if nested_skill_meta is not None:
                self._register_skill(f"{plugin_id}.{nested_skill_meta['id']}", nested_skill_meta)
                continue

            nested_subagent_meta = getattr(nested_cls, _SUBAGENT_META_ATTR, None)
            if nested_subagent_meta is not None:
                nested_instance = nested_cls()   # no-arg construction, like Java's reflective newInstance()
                self._register_subagent(
                    f"{plugin_id}.{nested_subagent_meta['id']}",
                    nested_subagent_meta, nested_instance, nested_cls,
                )

    def _register_skill(self, capability_id: str, skill_meta: dict) -> None:
        self.install_skill_agent(
            capability_id=capability_id,
            sub_agent={
                "name": skill_meta["id"],
                "description": skill_meta["description"],
                "system_prompt": skill_meta["system_prompt"],
                "tools": skill_meta["allowed_tools"],
            },
            tags=skill_meta["tags"],
        )

    def _register_subagent(
        self, capability_id: str, subagent_meta: dict, instance: object, cls: type,
    ) -> None:
        sub_agent: dict[str, Any] = {
            "name": subagent_meta["id"],
            "description": subagent_meta["description"],
            "system_prompt": subagent_meta["system_prompt"],
            "tools": self._scan_own_tools(instance, cls),
        }
        if subagent_meta["model"]:
            sub_agent["model"] = subagent_meta["model"]   # resolved by install_subagent()
        self.install_subagent(capability_id=capability_id, sub_agent=sub_agent, tags=subagent_meta["tags"])

    @staticmethod
    def _scan_tool_methods(instance: object, cls: type) -> list[tuple[str, Any, dict]]:
        """Find @agent_tool-decorated methods on cls, bound to instance."""
        results = []
        for method_name, _ in inspect.getmembers(cls, predicate=inspect.isfunction):
            fn = getattr(cls, method_name)
            tool_meta = getattr(fn, _TOOL_META_ATTR, None)
            if tool_meta is None:
                continue
            results.append((method_name, getattr(instance, method_name), tool_meta))
        return results

    def _scan_own_tools(self, instance: object, cls: type) -> list[StructuredTool]:
        return [
            StructuredTool.from_function(func=bound, name=method_name, description=tool_meta["description"])
            for method_name, bound, tool_meta in self._scan_tool_methods(instance, cls)
        ]

    def install_skill(
        self,
        capability_id: str,
        name: str,
        description: str,
        skill_path: str,
        tags: list[str] | None = None,
    ) -> None:
        """Register a SKILL capability pointing to a directory containing SKILL.md."""
        self._capabilities[capability_id] = CapabilityDescriptor(
            capability_id=capability_id,
            plugin_id=capability_id.split(".")[0],
            type=CapabilityType.SKILL,
            name=name,
            description=description,
            tags=tags or [],
            skill_path=skill_path,
        )

    def install_subagent(
        self,
        capability_id: str,
        sub_agent: Any,
        tags: list[str] | None = None,
        name: str | None = None,
        description: str | None = None,
    ) -> None:
        """Register a SUB_AGENT capability (deepagents SubAgent TypedDict)."""
        sub_agent = resolve_sub_agent_model(sub_agent)
        self._capabilities[capability_id] = CapabilityDescriptor(
            capability_id=capability_id,
            plugin_id=capability_id.split(".")[0],
            type=CapabilityType.SUB_AGENT,
            name=name or sub_agent.get("name", capability_id),
            description=description or sub_agent.get("description", ""),
            tags=tags or [],
            sub_agent=sub_agent,
        )

    def install_skill_agent(
        self,
        capability_id: str,
        sub_agent: Any,
        tags: list[str] | None = None,
        name: str | None = None,
        description: str | None = None,
    ) -> None:
        """Register a SKILL capability backed by a SubAgent (system_prompt + shared tools).

        Mirrors Java Skill: inherits parent model, tools must be str capability IDs already
        registered in this marketplace (resolved to BaseTool at build time).
        Use install_subagent() for private @tool objects invisible to the main agent.
        """
        if "model" in sub_agent:
            raise ValueError(
                f"with_skill '{capability_id}': model is not allowed; "
                "skill agents inherit the parent model. Use with_subagent() to specify a custom model."
            )
        tools = sub_agent.get("tools", [])
        for t in tools:
            if not isinstance(t, str):
                raise ValueError(
                    f"with_skill '{capability_id}': tools must be str capability IDs "
                    f"registered in the marketplace, got {type(t).__name__!r}. "
                    "Use with_subagent() for private @tool objects."
                )
        self._capabilities[capability_id] = CapabilityDescriptor(
            capability_id=capability_id,
            plugin_id=capability_id.split(".")[0],
            type=CapabilityType.SKILL,
            name=name or sub_agent.get("name", capability_id),
            description=description or sub_agent.get("description", ""),
            tags=tags or [],
            sub_agent=sub_agent,
        )

    def install_tool(self, tool: Any, tags: list[str] | None = None) -> None:
        """Register a pre-built LangChain BaseTool directly as a MCP_TOOL capability."""
        capability_id = tool.name
        self._capabilities[capability_id] = CapabilityDescriptor(
            capability_id=capability_id,
            plugin_id=capability_id,
            type=CapabilityType.MCP_TOOL,
            name=tool.name,
            description=tool.description,
            tags=tags or [],
            tool=tool,
        )

    def install_from_file(self, directory: str) -> None:
        """Scan a directory for SKILL.md and plugin.yaml files and register them."""
        from regnexe.market.loader import FileCapabilityLoader
        descriptors = FileCapabilityLoader().load_directory(directory)
        for desc in descriptors:
            self._capabilities[desc.capability_id] = desc

    # ------------------------------------------------------------------ query

    def search(self, query: str) -> list[CapabilityDescriptor]:
        # v1: return all (query ignored); later can add embedding-based filtering
        return list(self._capabilities.values())

    def resolve(self, capability_id: str) -> CapabilityDescriptor:
        cap = self._capabilities.get(capability_id)
        if cap is None:
            raise KeyError(f"Capability not found: {capability_id!r}")
        return cap

    # ------------------------------------------------------------------ helpers

    def split_by_type(
        self, descriptors: list[CapabilityDescriptor]
    ) -> tuple[list, list[str], list]:
        """Split a descriptor list into (tools, skill_paths, subagents) for create_deep_agent."""
        tools = [d.tool for d in descriptors if d.type == CapabilityType.MCP_TOOL and d.tool is not None]
        # SKILL.md directories (pure knowledge, no private tools)
        skill_paths = list({d.skill_path for d in descriptors if d.type == CapabilityType.SKILL and d.skill_path and not d.sub_agent})
        # SubAgents: both SUB_AGENT type and SKILL-with-SubAgent type
        subagents = [d.sub_agent for d in descriptors if d.sub_agent is not None and d.type in (CapabilityType.SUB_AGENT, CapabilityType.SKILL)]
        return tools, skill_paths, subagents
