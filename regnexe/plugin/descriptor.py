from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable

from langchain_core.tools import BaseTool

from regnexe.llm.model_provider import resolve_sub_agent_model

from .enums import CapabilityType

if TYPE_CHECKING:
    from deepagents.middleware.subagents import SubAgent


@dataclass
class CapabilityDescriptor:
    capability_id: str
    plugin_id: str
    type: CapabilityType
    name: str
    description: str
    tags: list[str] = field(default_factory=list)
    tool: Callable | BaseTool | None = None        # MCP_TOOL
    skill_path: str | None = None                  # SKILL → directory containing SKILL.md
    sub_agent: Any | None = None                   # SUB_AGENT → deepagents SubAgent TypedDict
    model_kwargs: dict[str, Any] | None = None


@dataclass
class PluginDescriptor:
    plugin_id: str
    name: str
    version: str | None = None
    description: str | None = None
    tags: list[str] = field(default_factory=list)
    capabilities: list[CapabilityDescriptor] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def builder() -> PluginDescriptorBuilder:
        return PluginDescriptorBuilder()


class PluginDescriptorBuilder:
    """Hand-rolled builder mirroring regnexe-agent's PluginDescriptor.Builder.

    tool()/skill_config()/sub_agent_config() wrap raw tools/config dicts into
    CapabilityDescriptors automatically, id'd as "<plugin_id>.<name>", deferred to
    build() time so caller order doesn't matter. One call can bundle a whole
    mixed-type plugin instead of hand-building each CapabilityDescriptor separately.
    """

    def __init__(self) -> None:
        self._plugin_id: str | None = None
        self._version: str | None = None
        self._name: str | None = None
        self._description: str | None = None
        self._tags: list[str] = []
        self._capabilities: list[CapabilityDescriptor] = []
        self._metadata: dict[str, Any] = {}
        self._tools: list[BaseTool] = []
        self._skill_configs: list[dict[str, Any]] = []
        self._sub_agent_configs: list[dict[str, Any]] = []

    def plugin_id(self, plugin_id: str) -> PluginDescriptorBuilder:
        self._plugin_id = plugin_id
        return self

    def version(self, version: str) -> PluginDescriptorBuilder:
        self._version = version
        return self

    def name(self, name: str) -> PluginDescriptorBuilder:
        self._name = name
        return self

    def description(self, description: str) -> PluginDescriptorBuilder:
        self._description = description
        return self

    def tags(self, tags: list[str]) -> PluginDescriptorBuilder:
        self._tags = tags
        return self

    def capabilities(self, capabilities: list[CapabilityDescriptor]) -> PluginDescriptorBuilder:
        self._capabilities = capabilities
        return self

    def metadata(self, metadata: dict[str, Any]) -> PluginDescriptorBuilder:
        self._metadata = metadata
        return self

    def tool(self, *tools: BaseTool) -> PluginDescriptorBuilder:
        """Wraps each tool into an MCP_TOOL capability, id'd as "<plugin_id>.<tool.name>"."""
        self._tools.extend(tools)
        return self

    def skill_config(self, *configs: dict[str, Any]) -> PluginDescriptorBuilder:
        """Wraps each dict (name/description/system_prompt/tools) into a SKILL
        capability, id'd as "<plugin_id>.<config['name']>".

        Mirrors with_skill(): tools must be str capability ids already registered in
        the marketplace, and "model" is not allowed -- a Skill always inherits the
        parent model.
        """
        for c in configs:
            if "model" in c:
                raise ValueError(
                    f"skill_config {c.get('name')!r}: model is not allowed; "
                    "skills inherit the parent model. Use sub_agent_config() to specify a custom model."
                )
        self._skill_configs.extend(configs)
        return self

    def sub_agent_config(self, *configs: dict[str, Any]) -> PluginDescriptorBuilder:
        """Wraps each dict (name/description/system_prompt/tools/model) into a
        SUB_AGENT capability, id'd as "<plugin_id>.<config['name']>".

        Mirrors with_subagent(): tools may be private BaseTool objects, and "model"
        may override the parent's model.
        """
        self._sub_agent_configs.extend(configs)
        return self

    def build(self) -> PluginDescriptor:
        if (self._tools or self._skill_configs or self._sub_agent_configs) and not self._plugin_id:
            raise ValueError("plugin_id must be set before adding tool/skill_config/sub_agent_config")

        all_capabilities = list(self._capabilities)
        for t in self._tools:
            all_capabilities.append(CapabilityDescriptor(
                capability_id=f"{self._plugin_id}.{t.name}",
                plugin_id=self._plugin_id,
                type=CapabilityType.MCP_TOOL,
                name=t.name,
                description=t.description,
                tool=t,
            ))
        for c in self._skill_configs:
            all_capabilities.append(CapabilityDescriptor(
                capability_id=f"{self._plugin_id}.{c['name']}",
                plugin_id=self._plugin_id,
                type=CapabilityType.SKILL,
                name=c["name"],
                description=c.get("description", ""),
                sub_agent=c,
            ))
        for c in self._sub_agent_configs:
            sub_agent = resolve_sub_agent_model(c)
            all_capabilities.append(CapabilityDescriptor(
                capability_id=f"{self._plugin_id}.{c['name']}",
                plugin_id=self._plugin_id,
                type=CapabilityType.SUB_AGENT,
                name=c["name"],
                description=c.get("description", ""),
                sub_agent=sub_agent,
            ))

        return PluginDescriptor(
            plugin_id=self._plugin_id,
            name=self._name,
            version=self._version,
            description=self._description,
            tags=self._tags,
            capabilities=all_capabilities,
            metadata=self._metadata,
        )
