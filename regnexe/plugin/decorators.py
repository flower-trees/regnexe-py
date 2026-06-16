"""Decorators for defining plugins and tools, aligned with regnexe-agent's @Plugin / @AgentTool."""

from __future__ import annotations

_PLUGIN_META_ATTR = "__regnexe_plugin__"
_TOOL_META_ATTR = "__regnexe_tool__"


def plugin(id: str, name: str, description: str = ""):
    """Class decorator that marks a class as a regnexe plugin.

    Usage::

        @plugin(id="weather", name="Weather Plugin")
        class WeatherPlugin:
            @agent_tool("Get today's weather for a city")
            def get_weather(self, city: str) -> str: ...
    """
    def decorator(cls):
        setattr(cls, _PLUGIN_META_ATTR, {"id": id, "name": name, "description": description})
        return cls
    return decorator


def agent_tool(description: str, tags: list[str] | None = None):
    """Method decorator that marks a method as an agent-callable tool.

    Args:
        description: Human-readable description used by the LLM to decide when to call this tool.
        tags: Optional tags for marketplace filtering.
    """
    def decorator(fn):
        setattr(fn, _TOOL_META_ATTR, {"description": description, "tags": tags or []})
        return fn
    return decorator
