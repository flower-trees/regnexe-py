"""SimpleMarketplace — in-memory registry, v1 returns all capabilities on search."""

from __future__ import annotations

import inspect
from typing import Any

from langchain_core.tools import StructuredTool

from regnexe.plugin.decorators import _PLUGIN_META_ATTR, _TOOL_META_ATTR
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
        """Scan a @plugin-decorated class instance and register its @agent_tool methods."""
        cls = type(instance)
        plugin_meta = getattr(cls, _PLUGIN_META_ATTR, None)
        if plugin_meta is None:
            raise ValueError(f"{cls.__name__} must be decorated with @plugin")

        plugin_id = plugin_meta["id"]
        for method_name, _ in inspect.getmembers(cls, predicate=inspect.isfunction):
            fn = getattr(cls, method_name)
            tool_meta = getattr(fn, _TOOL_META_ATTR, None)
            if tool_meta is None:
                continue

            bound = getattr(instance, method_name)
            lc_tool = StructuredTool.from_function(
                func=bound,
                name=method_name,
                description=tool_meta["description"],
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
        name: str,
        description: str,
        sub_agent: Any,
        tags: list[str] | None = None,
    ) -> None:
        """Register a SUB_AGENT capability (deepagents SubAgent TypedDict)."""
        self._capabilities[capability_id] = CapabilityDescriptor(
            capability_id=capability_id,
            plugin_id=capability_id.split(".")[0],
            type=CapabilityType.SUB_AGENT,
            name=name,
            description=description,
            tags=tags or [],
            sub_agent=sub_agent,
        )

    def install_skill_agent(
        self,
        capability_id: str,
        name: str,
        description: str,
        sub_agent: Any,
        tags: list[str] | None = None,
    ) -> None:
        """Register a SKILL capability backed by a SubAgent (system_prompt + private tools).

        Mirrors Java Skill: custom system_prompt + private tools, labelled CapabilityType.SKILL.
        Different from install_skill() which registers a SKILL.md directory path.
        """
        self._capabilities[capability_id] = CapabilityDescriptor(
            capability_id=capability_id,
            plugin_id=capability_id.split(".")[0],
            type=CapabilityType.SKILL,
            name=name,
            description=description,
            tags=tags or [],
            sub_agent=sub_agent,
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
