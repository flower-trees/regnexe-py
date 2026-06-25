<p align="center">
  <h1 align="center">Regnexe Python</h1>
  <p align="center"><b>Application-ready agents on top of deepagents</b></p>
  <p align="center">Plugins, skills, sub-agents, memory, events, and approval gates for Python agent systems.</p>
</p>

<p align="center">
  <a href="https://pypi.org/project/regnexe-py/"><img src="https://img.shields.io/pypi/v/regnexe-py?label=PyPI" alt="PyPI"/></a>
  <img src="https://img.shields.io/badge/Python-3.11%2B-blue" alt="Python 3.11+"/>
  <img src="https://img.shields.io/badge/deepagents-0.6.8%2B-purple" alt="deepagents 0.6.8+"/>
  <img src="https://img.shields.io/badge/LangGraph-0.5%2B-green" alt="LangGraph 0.5+"/>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache%202.0-blue.svg" alt="Apache 2.0 License"/></a>
</p>

---

Most agent code starts by passing `tools`, `skills`, and `subagents` directly into
deepagents. That works well for prototypes. regnexe-py keeps deepagents as the runtime
engine, then adds the missing application layer around it: a capability marketplace,
plugin decorators, explicit app/user/session identity, cross-session task memory,
structured events, model vendor routing, and user-triggered cancellation.

```
User Goal
    |
    v
RegnexeAgent
    |
    v
deepagents graph  ->  LangGraph checkpointer / store
    |
    v
Plugin Marketplace
    +------------------------------------------------+
    | Loading channels:                              |
    |  @plugin Python object  ·  PluginDescriptor     |
    |  SKILL.md / plugin.yaml directory               |
    |  builder capability methods (with_tool/skill/   |
    |  subagent)                                      |
    |                         |                      |
    |                         v                      |
    |              CapabilityDescriptor              |
    |        +----------+---------+-------------+     |
    |        | MCP_TOOL | SKILL   | SUB_AGENT   |     |
    |        +----------+---------+-------------+     |
    +------------------------------------------------+
```

**What sets it apart from using deepagents directly:**

- **Application structure, not just graph construction** — business tools, skills,
  sub-agents, memory, events, and model selection behind one builder API.
- **Plugin marketplace** — register capabilities once; swap the backing store
  (in-memory, database, ...) without touching agent code.
- **Business-friendly tool authoring** — expose ordinary Python classes with `@plugin`
  and `@agent_tool`; no repetitive `StructuredTool` wiring.
- **Explicit identity and memory** — every run carries `app_id`, `user_id`, and
  `session_id`; recent task summaries can be injected into later sessions.
- **User-triggered cancellation** — stop an in-flight run from a concurrent task at
  any point, then continue from the last completed step.
- **Observable execution** — event listeners receive LLM calls, tool calls, tool
  results, token metadata, and agent lifecycle events.

This README goes from "one tool call" to the full framework, one layer at a time.
Every code block below is adapted from a real, runnable script under
[`examples/readme/`](examples/readme).

---

## Quick Start

### 1. Install

```bash
pip install regnexe-py
```

For local development from this repository:

```bash
pip install -e ".[dev]"
```

### 2. Configure your LLM

```bash
export DEEPSEEK_KEY=sk-...
export ALIYUN_KEY=sk-...
export OPENAI_API_KEY=sk-...
```

Ollama uses the local Ollama runtime and does not require an API key.

### 3. Register tools and run

`with_tool(...)` registers pre-built LangChain tools directly — no class, no
decorator, the fastest path to a running agent. See
[`examples/readme/01_multi_tool.py`](examples/readme/01_multi_tool.py).

```python
import asyncio
from langchain_core.tools import tool
from regnexe import ConsoleEventListener, RegnexeAgentBuilder, Vendor


@tool
def get_weather(city: str) -> str:
    """Get today's weather for a city."""
    return "Beijing: sunny, 22 C."


@tool
def get_air_quality(city: str) -> str:
    """Get today's air quality index (AQI) for a city."""
    return "Beijing: AQI 35, excellent air quality."


async def main() -> None:
    agent = (
        RegnexeAgentBuilder()
        .with_default_model(Vendor.DEEPSEEK, "deepseek-v4-flash")
        .with_tool(get_weather, get_air_quality)         # as many as you need, one call
        .with_event_listener(ConsoleEventListener())
        .build()
    )

    result = await agent.ainvoke(
        "Check today's weather and air quality in Beijing, then tell me if it's good for outdoor running.",
        app_id="demo", user_id="user1", session_id="morning-run",
    )

    print(result.status)        # completed
    print(result.final_text)


asyncio.run(main())
```

`ConsoleEventListener` prints every tool call and result as the loop runs:

```
[AGENT ▶] RegnexeAgent
          goal: Check today's weather and air quality in Beijing...
[TOOL  ▶] get_weather  input={"city": "Beijing"}
[TOOL  ■] get_weather  output=Beijing: sunny, 22 C.
[TOOL  ▶] get_air_quality  input={"city": "Beijing"}
[TOOL  ■] get_air_quality  output=Beijing: AQI 35, excellent air quality.
[AGENT ■] status=completed
```

## Why Not Just deepagents?

deepagents is the orchestration engine. regnexe-py is the application framework around
that engine.

| Need | Direct deepagents | regnexe-py |
|------|-------------------|------------|
| Register business tools | Manually create and pass tools | `with_tool(...)`, or `@plugin`/`@agent_tool` on a class |
| Mix tools, skills, sub-agents | Maintain separate lists yourself | Register all capabilities through one builder and marketplace |
| Bundle mixed capabilities under one id | Build each spec separately | A `PluginDescriptor` of `CapabilityDescriptor`s, one `plugin_id` |
| Preserve user/session identity | Design your own thread naming scheme | Use explicit `app_id`, `user_id`, and `session_id` |
| Reuse prior task outcomes | Build storage and prompt injection yourself | `TaskResultStore` injects recent cross-session task summaries |
| Observe execution | Consume graph events directly | Attach `AgentEventListener` for structured LLM/tool/agent events |
| Stop a run mid-flight | Hold and cancel the asyncio Task yourself | `agent.acancel(...)` looks it up by session and cancels it |
| Support many model vendors | Instantiate each LangChain model yourself | Use `Vendor` or `with_model_spec("vendor:model")` |

Use deepagents directly for small experiments. Use regnexe-py when the agent is
becoming an application: multiple business plugins, reusable skills, user sessions,
streaming UI, audit logs, or provider switching.

---

## 1. Going deeper: Skill vs Sub-Agent

A single tool call only goes so far. Two richer capability types compose multi-step
behavior, and they make opposite tradeoffs on purpose. See
[`examples/readme/02_skill_vs_subagent.py`](examples/readme/02_skill_vs_subagent.py).

### Skill (`with_skill`) — shares the parent's model and tools

A Skill's `sub_agent` dict has no `model` key at all — `install_skill_agent()` raises
if you try to pass one. A Skill **always inherits the parent agent's model**, and its
`tools` must be `str` capability ids already registered in the marketplace — it
borrows, it doesn't own. Use a Skill for a focused, repeatable sub-workflow that should
stay cheap and stay in lockstep with the main agent's model.

```python
from langchain_core.tools import tool


@tool
def get_weather(city: str) -> str:
    """Get today's weather for a city."""
    return "Beijing: sunny, 22 C, excellent air quality."


travel_advisor = {
    "name": "travel_advisor",
    "description": (
        "Calls get_weather for the city the user mentions and gives outdoor-activity "
        "advice based on the current weather. TRIGGER: Use when the user asks whether "
        "the weather is suitable for an outdoor activity."
    ),
    "system_prompt": (
        "You are an outdoor-activity advisor.\n"
        "1. Call get_weather for the city the user mentions.\n"
        "2. Based on the result, give a short, direct go/no-go recommendation."
    ),
    "tools": ["get_weather"],   # borrowed by capability id, not owned
}

agent = (
    RegnexeAgentBuilder()
    .with_default_model(Vendor.DEEPSEEK, "deepseek-v4-flash")
    .with_tool(get_weather)                        # the Skill borrows this; must exist first
    .with_skill("travel.travel_advisor", travel_advisor)
    .build()
)
```

### Sub-Agent (`with_subagent`) — owns its own model and private tools

A Sub-Agent's `sub_agent["model"]` can be a *different* `BaseChatModel` than the
parent's (or omitted to inherit it), and its `tools` can be private `BaseTool` objects
that are **never** registered in the marketplace, so the outer agent can never call
them directly. Use a Sub-Agent for an independent sub-task that needs its own
reasoning loop, its own tools, or a cheaper/faster model.

```python
from regnexe.llm.model_provider import ModelProvider


@tool
def estimate_trip_cost(days: int, city: str) -> str:
    """Estimate total cost for a multi-day business trip."""
    return f"{days}-day {city} trip estimate: 3600 CNY total."


expense_estimator = {
    "name": "expense_estimator",
    "description": (
        "Estimates the total cost of a business trip. "
        "TRIGGER: Use when the user asks for a trip budget or cost estimate."
    ),
    "model": ModelProvider().resolve(Vendor.ALIYUN, "qwen-plus"),   # own model
    "system_prompt": (
        "You are a travel expense estimator.\n"
        "1. Call estimate_trip_cost with the trip length and destination.\n"
        "2. Report the total and a one-line breakdown."
    ),
    "tools": [estimate_trip_cost],   # private — invisible to the outer agent
}

agent = (
    RegnexeAgentBuilder()
    .with_default_model(Vendor.DEEPSEEK, "deepseek-v4-flash")
    .with_subagent("travel.expense_estimator", expense_estimator)
    .build()
)
```

### Which one?

| | Skill | Sub-Agent |
|---|---|---|
| Model | Always inherits the parent's | Own `BaseChatModel`, or inherit |
| Tools | Borrowed by capability id (`tools: [str]`) | Private (`tools: [BaseTool]`), invisible outside |
| Best for | Cheap, repeatable sub-workflows tightly coupled to the main agent | Independent sub-tasks that need isolation or a different model |

---

## 2. Plugin packaging: `PluginDescriptor.builder()`

Every loading channel in this README (`with_tool`, `with_skill`, `with_subagent`,
`with_plugin`, `with_directory`) ultimately builds the same thing: a
`PluginDescriptor` holding one or more `CapabilityDescriptor`s, installed into a
`Marketplace`. The most direct way to build one by hand is `PluginDescriptor.builder()`,
which has `tool(...)`, `skill_config(...)`, and `sub_agent_config(...)` — each wraps
the raw tool/config dict into a `CapabilityDescriptor` automatically, id'd as
`"<plugin_id>.<name>"`. One call bundles a whole mixed-type plugin instead of
hand-building each `CapabilityDescriptor` separately. See
[`examples/readme/03_plugin_packaging.py`](examples/readme/03_plugin_packaging.py).

```python
from regnexe.market.simple_marketplace import SimpleMarketplace
from regnexe.plugin.descriptor import PluginDescriptor

travel_advisor = {
    "name": "travel_advisor",
    "description": "Outdoor-activity advice based on current weather.",
    "system_prompt": "Call get_weather, then give a go/no-go running recommendation.",
    "tools": ["trip-plugin.get_weather"],   # fully-qualified capability id, not owned
}

expense_estimator = {
    "name": "expense_estimator",
    "description": "Estimates business trip cost.",
    "system_prompt": "Call estimate_trip_cost, then report the total.",
    "model": "aliyun:qwen-plus",   # plain "vendor:model_name" string -- own model
    "tools": [estimate_trip_cost],
}

trip_plugin = (
    PluginDescriptor.builder()
    .plugin_id("trip-plugin")
    .version("1.0")
    .name("Trip Plugin")
    .description("Bundles a tool, a skill, and a sub-agent for trip planning")
    .tool(get_weather)                     # -> trip-plugin.get_weather
    .skill_config(travel_advisor)          # -> trip-plugin.travel_advisor
    .sub_agent_config(expense_estimator)   # -> trip-plugin.expense_estimator
    .build()
)

marketplace = SimpleMarketplace()
marketplace.install(trip_plugin)

agent = (
    RegnexeAgentBuilder()
    .with_default_model(Vendor.DEEPSEEK, "deepseek-v4-flash")
    .with_marketplace(marketplace)
    .build()
)
```

> A Skill's `tools` must reference the tool's *fully-qualified* capability id. If the
> tool and the skill share a `plugin_id` here, that id is `"trip-plugin.get_weather"`,
> not bare `"get_weather"`. `skill_config()` raises if a `"model"` key is present —
> a Skill always inherits the parent's model.

---

## 3. Plugin concept: `@plugin`, `@agent_tool`, `@agent_skill`, `@agent_subagent`

The two getting-started tools become `@agent_tool` methods on one `@plugin`-decorated
class. `@agent_skill` and `@agent_subagent` — the same Skill and Sub-Agent from
section 1, as decorators instead of raw dicts — nest as inner classes of that same
`@plugin` class, bundling everything under one `plugin_id`: one
`with_plugin(WeatherPlugin())` call registers two tools, a skill, and a sub-agent at
once. `@agent_skill` is a pure marker (a Skill never owns tools, so no methods are
needed); `@agent_subagent` reuses `@agent_tool` for its private tools, exactly like the
outer `@plugin` does for MCP_TOOL — the only difference is the resulting capability
type. See
[`examples/readme/04_plugin_decorator.py`](examples/readme/04_plugin_decorator.py).

```python
from regnexe import agent_skill, agent_subagent, agent_tool, plugin


@plugin(id="weather", name="Weather Plugin", description="Weather, advice, and trip cost estimation")
class WeatherPlugin:
    @agent_tool("Get today's weather for a city.", tags=["weather"])
    def get_weather(self, city: str) -> str:
        return "Beijing: sunny, 22 C."

    @agent_tool("Get today's air quality index (AQI) for a city.", tags=["weather"])
    def get_air_quality(self, city: str) -> str:
        return "Beijing: AQI 35, excellent air quality."

    @agent_skill(
        id="travel_advisor",
        description=(
            "Gives outdoor-activity advice based on the current weather for a city. "
            "TRIGGER: Use when the user asks whether the weather is suitable for an outdoor activity."
        ),
        system_prompt="Call get_weather, then give a short go/no-go running recommendation.",
        allowed_tools=["weather.get_weather"],   # full capability id within this plugin
    )
    class TravelAdvisorSkill:
        pass   # No @agent_tool methods -- a Skill can't own private tools.

    @agent_subagent(
        id="expense_estimator",
        description="Estimates the total cost of a business trip. TRIGGER: Use when the user asks for a trip budget.",
        system_prompt="Call estimate_trip_cost with the trip length and destination, then report the total.",
        model="aliyun:qwen-plus",   # own model, independent of the parent's default model
    )
    class ExpenseEstimatorSubAgent:
        @agent_tool("Estimates total cost for a multi-day business trip.")
        def estimate_trip_cost(self, days: int, city: str) -> str:
            return f"{days}-day {city} trip estimate: 3600 CNY total."


agent = (
    RegnexeAgentBuilder()
    .with_default_model(Vendor.DEEPSEEK, "deepseek-v4-flash")
    .with_plugin(WeatherPlugin())   # one call: two tools, a skill, and a sub-agent
    .build()
)
```

`@agent_skill`/`@agent_subagent` also work standalone (not nested) —
`with_plugin(TravelAdvisorSkill())` on its own registers it as its own
single-capability plugin, the same way the code-first `with_skill()`/`with_subagent()`
from section 1 do.

---

## 4. File-system directory loading

Best for ops-managed, hot-pluggable capabilities — no Python classes or decorators,
just files on disk:

```
weather-plugin/
  plugin.yaml          <- metadata catalogue entry (MCP_TOOL descriptor)
  SKILL.md              <- skill content, with YAML frontmatter
```

```python
agent = (
    RegnexeAgentBuilder()
    .with_default_model(Vendor.DEEPSEEK, "deepseek-v4-flash")
    .with_directory("/opt/regnexe-plugins/weather-plugin")
    .build()
)
```

`with_directory()` scans for `SKILL.md` and `plugin.yaml`/`plugin.yml`, registering
both as `CapabilityDescriptor`s — searchable and resolvable through the marketplace
like any other loading channel. See
[`examples/readme/05_file_directory_loading.py`](examples/readme/05_file_directory_loading.py).

> **Current limitation**: deepagents only reads a `SKILL.md`'s *content* off real disk
> when the graph is built with a `FilesystemBackend(root_dir=...)`. `RegnexeAgent`
> doesn't configure one yet, so a directory-loaded skill is registered, searchable,
> and resolvable today, but not yet wired into a live agent run — unlike `with_skill()`,
> whose `system_prompt` lives in-process. Use `with_skill()` for an executable skill
> today; treat `with_directory()` as a capability catalogue.

<details>
<summary>File format reference</summary>

**`plugin.yaml`**
```yaml
plugin_id: weather-plugin
capabilities:
  - capability_id: weather-plugin.get_weather
    type: mcp_tool
    name: get_weather
    description: "Get today's weather for a city"
    tags: [weather]
```

**`SKILL.md`**
```markdown
---
name: advisor
plugin_id: weather-plugin
capability_id: weather-plugin.advisor
description: "Outdoor activity advisor. TRIGGER: when the user asks about outdoor plans."
tags: [weather]
---
You are a weather advisor. Given the user's question about an outdoor activity,
recommend whether to go, plus one practical tip.
```

</details>

---

## 5. Marketplace

Every loading channel above ends the same way: capabilities land in a marketplace. The
default `SimpleMarketplace` is an in-memory index — install, search, resolve. See
[`examples/readme/06_marketplace.py`](examples/readme/06_marketplace.py).

```python
marketplace = SimpleMarketplace()
marketplace.install(weather_plugin)

candidates = marketplace.search("Check today's weather in Beijing")   # v1: query ignored, returns all
resolved = marketplace.resolve("weather-plugin.get_weather")
```

The `Marketplace` protocol is `install`/`search`/`resolve` — but `RegnexeAgent`'s graph
construction also calls `split_by_type()` internally, which isn't part of the
protocol. The simplest way to swap the backing store (a database table, a vector
index, a tenant-aware service) is subclassing `SimpleMarketplace` and overriding
`install()`/`search()`/`resolve()`, keeping `split_by_type()` for free:

```python
class InMemoryDbMarketplace(SimpleMarketplace):
    def __init__(self) -> None:
        super().__init__()
        self.table: dict[str, PluginDescriptor] = {}

    def install(self, plugin: PluginDescriptor) -> None:
        self.table[plugin.plugin_id] = plugin
        super().install(plugin)

    def find_by_tag(self, tag: str) -> list[PluginDescriptor]:
        return [p for p in self.table.values()
                if any(tag in cap.tags for cap in p.capabilities)]


agent = (
    RegnexeAgentBuilder()
    .with_default_model(Vendor.DEEPSEEK, "deepseek-v4-flash")
    .with_marketplace(InMemoryDbMarketplace())   # any custom marketplace plugs in here
    .build()
)
```

---

## 6. Three layers of memory

Three independent layers, each solving a different problem. See
[`examples/readme/07_three_layer_memory.py`](examples/readme/07_three_layer_memory.py).

| Layer | Question it answers | Config knob | Default |
|---|---|---|---|
| Layer 1 — current turn | "What's in this one LLM/tool turn?" | always on | Messages and tool results in active graph state |
| Layer 2 — same session | "What did we say earlier in this `session_id`?" | `with_checkpointer(...)` | `MemorySaver` |
| Layer 3 — cross-session | "What did this user accomplish in past sessions?" | `with_store(...)` | In-process `TaskResultStore` |

```python
agent = (
    RegnexeAgentBuilder()
    .with_default_model(Vendor.DEEPSEEK, "deepseek-v4-flash")
    .with_plugin(WeatherPlugin())
    .build()
)

# Layer 2: same session_id -- Turn 2 recalls Turn 1 without re-querying the tool
await agent.ainvoke("Check today's weather in Beijing.", app_id="a", user_id="u", session_id="s1")
await agent.ainvoke("What should I wear, based on that?", app_id="a", user_id="u", session_id="s1")

# Layer 3: a brand-new session_id, same user -- recalls the prior task's summary
await agent.ainvoke("What was the weather I asked about earlier?", app_id="a", user_id="u", session_id="s2")
```

`(app_id, user_id, session_id)` becomes the thread identity for Layer 2. Recent task
summaries for `(app_id, user_id)` are injected into the system prompt of future
sessions for Layer 3.

---

## 7. Observability

`ConsoleEventListener` — used as the default throughout this README — prints
`AGENT_STARTED`/`LLM_START`/`LLM_END`/`TOOL_CALLED`/`TOOL_RESULT`/`AGENT_COMPLETED`
events to stdout. See
[`examples/readme/08_observability.py`](examples/readme/08_observability.py).

```python
agent = (
    RegnexeAgentBuilder()
    .with_default_model(Vendor.DEEPSEEK, "deepseek-v4-flash")
    .with_event_listener(ConsoleEventListener())
    .build()
)
```

`AbstractEventListener` (its base class) suppresses `LLM_START`/`LLM_END` by default —
pass `show_llm_events=True` to see them, plus `show_token_usage=True` for token
counts:

```python
ConsoleEventListener(show_llm_events=True, show_token_usage=True)
```

Write your own listener for structured JSON logs, token accounting, or SSE streaming
by extending `AbstractEventListener` (or `AgentEventListener` directly, for full
control over filtering) — override `on_event`, and optionally `should_handle` to pick
exactly which event types you care about. See
[`examples/06_custom_event_listener.py`](examples/06_custom_event_listener.py) and
[`examples/07_streaming_api.py`](examples/07_streaming_api.py).

---

## 8. Human approval and cancellation

Two independent control-flow mechanisms, for two different situations.

### Human approval (`with_interrupt_on` / `aresume`)

For sensitive tool calls, pre-configure a pause **before a specific tool**, keyed by
tool name:

```python
agent = (
    RegnexeAgentBuilder()
    .with_default_model(Vendor.DEEPSEEK, "deepseek-v4-flash")
    .with_interrupt_on({"transfer_funds": True})
    .build()
)

result = await agent.ainvoke("Transfer CNY 5000 to ACC-002.", app_id="a", user_id="u", session_id="s")
# result.status == "interrupted"; result.metadata["interrupt"] holds the pending action requests

result = await agent.aresume([{"type": "approve"}], app_id="a", user_id="u", session_id="s")
# result.status == "completed" -- the transfer actually ran
```

See [`examples/10_interrupt_example.py`](examples/10_interrupt_example.py) for the
full approval-and-resume flow.

### Cancel & Resume (`acancel` / `cancel`)

Unlike `with_interrupt_on()`, `acancel()` is **user-triggered** and can land at any
point — e.g. a "Stop" button in a chat UI — not just before a pre-configured tool. See
[`examples/readme/09_cancel_and_resume.py`](examples/readme/09_cancel_and_resume.py).

```python
run = asyncio.create_task(
    agent.ainvoke("Generate a financial report on Q2 sales.", app_id="a", user_id="u", session_id="s")
)
# ... from a concurrent task, once you decide to stop it:
await agent.acancel(app_id="a", user_id="u", session_id="s")

result = await run
# result.status == "cancelled" -- not an exception, a normal AgentResult

# LangGraph checkpoints after every completed step; a later plain ainvoke() on the
# same session_id just continues -- no special resume call needed here.
await agent.ainvoke("Please finish that report.", app_id="a", user_id="u", session_id="s")
```

`acancel()` must be called from a different `asyncio.Task` than the one running
`ainvoke()`/`aresume()` — cancelling your own awaiting task is a no-op.

---

## Examples

The [`examples/`](examples) directory contains progressive, end-to-end-runnable
scripts, plus a [`examples/readme/`](examples/readme) set mirroring every section
above:

| # | Example | What it demonstrates |
|---|---------|----------------------|
| 01 | [`01_weather_example.py`](examples/01_weather_example.py) | `@plugin`, `@agent_tool`, direct tool calls, multi-turn session |
| 02 | [`02_contract_analyzer.py`](examples/02_contract_analyzer.py) | Skill-style sub-agent with private tools |
| 03 | [`03_travel_planner.py`](examples/03_travel_planner.py) | Fully autonomous nested sub-agent |
| 04 | [`04_business_trip.py`](examples/04_business_trip.py) | Tool + skill + sub-agent in one workflow |
| 05 | [`05_session_memory.py`](examples/05_session_memory.py) | Same-session and cross-session memory |
| 06 | [`06_custom_event_listener.py`](examples/06_custom_event_listener.py) | Custom listener, JSON logs, token aggregation |
| 07 | [`07_streaming_api.py`](examples/07_streaming_api.py) | SSE-style streaming through event callbacks |
| 08 | [`08_multi_model.py`](examples/08_multi_model.py) | Different models for outer agent and inner skill |
| 09 | [`09_file_plugin_loading.py`](examples/09_file_plugin_loading.py) | Loading `SKILL.md` from files |
| 10 | [`10_interrupt_example.py`](examples/10_interrupt_example.py) | Human approval, interrupt, and resume |
| 11 | [`11_cancel_example.py`](examples/11_cancel_example.py) | User-triggered cancellation mid-flight |

| # | README example | Section |
|---|-----------------|---------|
| 01 | [`readme/01_multi_tool.py`](examples/readme/01_multi_tool.py) | Quick Start |
| 02 | [`readme/02_skill_vs_subagent.py`](examples/readme/02_skill_vs_subagent.py) | 1. Skill vs Sub-Agent |
| 03 | [`readme/03_plugin_packaging.py`](examples/readme/03_plugin_packaging.py) | 2. Plugin packaging |
| 04 | [`readme/04_plugin_decorator.py`](examples/readme/04_plugin_decorator.py) | 3. `@plugin` and `@agent_tool` |
| 05 | [`readme/05_file_directory_loading.py`](examples/readme/05_file_directory_loading.py) | 4. File-system directory loading |
| 06 | [`readme/06_marketplace.py`](examples/readme/06_marketplace.py) | 5. Marketplace |
| 07 | [`readme/07_three_layer_memory.py`](examples/readme/07_three_layer_memory.py) | 6. Three layers of memory |
| 08 | [`readme/08_observability.py`](examples/readme/08_observability.py) | 7. Observability |
| 09 | [`readme/09_cancel_and_resume.py`](examples/readme/09_cancel_and_resume.py) | 8. Cancel & Resume |

```bash
python examples/readme/01_multi_tool.py
```

## Reference

<details>
<summary>Builder options</summary>

| Method | Default | Description |
|--------|---------|-------------|
| `with_default_model(Vendor, str)` | - | LLM vendor + model name |
| `with_model(BaseChatModel)` | - | Provide a pre-built LangChain chat model |
| `with_model_spec(str)` | - | Parse `vendor:model_name` and resolve the model |
| `with_tool(*tools)` | - | Register one or more pre-built LangChain tools as MCP_TOOL capabilities |
| `with_plugin(*instances)` | - | Register one or more `@plugin` Python objects |
| `with_directory(path)` | - | Scan a directory for `SKILL.md` and plugin descriptor files |
| `with_skill(...)` | - | Register a SKILL backed by a sub-agent config (inherits the parent model, shared tools) |
| `with_skill_dir(...)` | - | Register a file-based SKILL.md directory directly |
| `with_subagent(...)` | - | Register a SUB_AGENT config (own model, private tools) |
| `with_marketplace(marketplace)` | `SimpleMarketplace()` | Replace the default in-memory marketplace |
| `with_checkpointer(checkpointer)` | `MemorySaver` | LangGraph same-session state (Layer 2) |
| `with_store(store)` | in-process memory fallback | LangGraph store for cross-session task history (Layer 3) |
| `with_event_listener(listener)` | none | Hook for LLM, tool, and agent lifecycle events |
| `with_interrupt_on(dict)` | none | Human-in-the-loop interrupt configuration, keyed by tool name |
| `with_system_prompt(str)` | none | Prepend custom system instructions |
| `with_session_buffer_size(int)` | `10` | Reserved session buffer setting |

</details>

<details>
<summary>RegnexeAgent methods</summary>

| Method | Description |
|--------|-------------|
| `ainvoke(goal, app_id, user_id, session_id)` | Run a goal; async |
| `invoke(...)` | Synchronous wrapper around `ainvoke` |
| `aresume(decisions, app_id, user_id, session_id)` | Fulfil a pending `with_interrupt_on()` approval gate |
| `resume(...)` | Synchronous wrapper around `aresume` |
| `acancel(app_id, user_id, session_id)` | Stop the run in flight for this session; must be called from a concurrent `asyncio.Task` |
| `cancel(...)` | Synchronous wrapper around `acancel` |

</details>

<details>
<summary>Supported LLM vendors</summary>

| Enum | Provider | Env var |
|------|----------|---------|
| `Vendor.ALIYUN` | Alibaba Cloud DashScope compatible API | `ALIYUN_KEY` |
| `Vendor.DEEPSEEK` | DeepSeek | `DEEPSEEK_KEY` |
| `Vendor.DOUBAO` | ByteDance Doubao | `DOUBAO_KEY` |
| `Vendor.HUNYUAN` | Tencent Hunyuan | `HUNYUAN_KEY` |
| `Vendor.LINGYI` | 01.AI | `LINGYI_KEY` |
| `Vendor.MINIMAX` | MiniMax | `MINIMAX_KEY` |
| `Vendor.MOONSHOT` | Moonshot / Kimi | `MOONSHOT_KEY` |
| `Vendor.OLLAMA` | Ollama local runtime | No API key required |
| `Vendor.OPENAI` | OpenAI | `OPENAI_API_KEY` |
| `Vendor.QIANFAN` | Baidu Qianfan | `QIANFAN_KEY` |
| `Vendor.STEPFUN` | StepFun | `STEPFUN_KEY` |
| `Vendor.ZHIPU` | Zhipu AI / GLM | `ZHIPU_KEY` |

</details>

<details>
<summary>Task status</summary>

| Status | Meaning |
|--------|---------|
| `completed` | Goal completed |
| `error` | Execution raised an exception and returned the error text |
| `interrupted` | Paused at a `with_interrupt_on()` gate; resume with `aresume()` |
| `cancelled` | Stopped by `acancel()`; resume with a plain `ainvoke()` |

</details>

---

If regnexe-py saves you time, a star on GitHub goes a long way.

[中文文档](README_zh.md) · [PyPI](https://pypi.org/project/regnexe-py/) · [License](LICENSE)
