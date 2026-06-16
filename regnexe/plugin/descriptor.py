from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable

from langchain_core.tools import BaseTool

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
    capabilities: list[CapabilityDescriptor] = field(default_factory=list)
