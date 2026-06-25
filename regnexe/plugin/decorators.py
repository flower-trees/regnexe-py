"""Decorators for defining plugins and tools, aligned with regnexe-agent's
@Plugin / @AgentTool / @AgentSkill / @AgentSubAgent.
"""

from __future__ import annotations

_PLUGIN_META_ATTR = "__regnexe_plugin__"
_TOOL_META_ATTR = "__regnexe_tool__"
_SKILL_META_ATTR = "__regnexe_skill__"
_SUBAGENT_META_ATTR = "__regnexe_subagent__"


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


def agent_skill(
    id: str,
    description: str,
    system_prompt: str,
    allowed_tools: list[str] | None = None,
    tags: list[str] | None = None,
):
    """Class decorator marking a class as a Skill (mirrors regnexe-agent's @AgentSkill).

    A Skill always inherits the parent agent's model and can only borrow tools already
    registered in the marketplace, by capability id (``allowed_tools``) -- it never
    owns private tools, so the decorated class needs no ``@agent_tool`` methods.

    Usage::

        # Standalone: with_plugin(TravelAdvisorSkill()) registers it as its own
        # single-capability plugin -- capability_id = plugin_id = "travel_advisor".
        @agent_skill(
            id="travel_advisor",
            description="...",
            system_prompt="...",
            allowed_tools=["get_weather"],
        )
        class TravelAdvisorSkill:
            pass

        # Nested: as an inner class of an @plugin class, capability_id becomes
        # "<outer_plugin_id>.travel_advisor", sharing the outer plugin_id.
        @plugin(id="weather", name="Weather Plugin")
        class WeatherPlugin:
            @agent_skill(id="travel_advisor", description="...", system_prompt="...",
                         allowed_tools=["weather.get_weather"])
            class TravelAdvisorSkill:
                pass
    """
    def decorator(cls):
        setattr(cls, _SKILL_META_ATTR, {
            "id": id,
            "description": description,
            "system_prompt": system_prompt,
            "allowed_tools": allowed_tools or [],
            "tags": tags or [],
        })
        return cls
    return decorator


def agent_subagent(
    id: str,
    description: str,
    system_prompt: str,
    model: str | None = None,
    tags: list[str] | None = None,
):
    """Class decorator marking a class as a Sub-Agent (mirrors regnexe-agent's @AgentSubAgent).

    Unlike a Skill, a Sub-Agent can own a model different from the parent's
    (``model="vendor:model_name"``, omitted to inherit the parent's model), and
    ``@agent_tool`` methods on the decorated class become private tools -- never
    registered in the marketplace, invisible to the outer agent -- exactly like the
    outer ``@plugin`` scans ``@agent_tool`` for MCP_TOOL.

    Usage::

        # Standalone: with_plugin(ExpenseEstimatorSubAgent()) registers it as its own
        # single-capability plugin -- capability_id = plugin_id = "expense_estimator".
        @agent_subagent(id="expense_estimator", description="...", system_prompt="...",
                         model="aliyun:qwen-plus")
        class ExpenseEstimatorSubAgent:
            @agent_tool("Estimates total cost for a multi-day business trip.")
            def estimate_trip_cost(self, days: int, city: str) -> str: ...

        # Nested: as an inner class of an @plugin class, capability_id becomes
        # "<outer_plugin_id>.expense_estimator".
    """
    def decorator(cls):
        setattr(cls, _SUBAGENT_META_ATTR, {
            "id": id,
            "description": description,
            "system_prompt": system_prompt,
            "model": model,
            "tags": tags or [],
        })
        return cls
    return decorator
