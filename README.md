<p align="center">
  <h1 align="center">Regnexe Python</h1>
  <p align="center"><b>Application-ready agents on top of deepagents</b></p>
  <p align="center">Plugins, skills, sub-agents, memory, events, and approval gates for Python agent systems.</p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11%2B-blue" alt="Python 3.11+"/>
  <img src="https://img.shields.io/badge/deepagents-0.6.8%2B-purple" alt="deepagents 0.6.8+"/>
  <img src="https://img.shields.io/badge/LangGraph-0.5%2B-green" alt="LangGraph 0.5+"/>
  <img src="https://img.shields.io/badge/license-not%20specified-lightgrey" alt="License not specified"/>
</p>

---

Most agent code starts by passing `tools`, `skills`, and `subagents` directly into
deepagents. That works well for prototypes. regnexe-py keeps deepagents as the runtime
engine, then adds the missing application layer around it: a capability marketplace,
plugin decorators, explicit app/user/session identity, cross-session task memory,
structured events, model vendor routing, and Regnexe-compatible concepts.

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
    |  @plugin Python object                         |
    |  SKILL.md directory                            |
    |  plugin.yaml / plugin.yml                      |
    |  builder capability methods                    |
    |                         |                      |
    |                         v                      |
    |              CapabilityDescriptor              |
    |        +----------+---------+-------------+     |
    |        | MCP_TOOL | SKILL   | SUB_AGENT   |     |
    |        +----------+---------+-------------+     |
    +------------------------------------------------+
```

**What sets it apart from using deepagents directly:**

- **Application structure, not just graph construction**: keep business tools, skills,
  sub-agents, memory, events, and model selection behind one builder API.
- **Plugin marketplace**: register capabilities once, then let the framework map them to
  deepagents `tools`, `skills`, and `subagents`.
- **Business-friendly tool authoring**: expose ordinary Python classes with `@plugin` and
  `@agent_tool`; no repetitive `StructuredTool` wiring.
- **Explicit identity and memory**: every run carries `app_id`, `user_id`, and `session_id`;
  recent task summaries can be injected into later sessions.
- **Observable execution**: event listeners receive LLM calls, tool calls, tool results,
  token metadata, and agent lifecycle events.
- **Regnexe ecosystem alignment**: Python projects can use the same Plugin / Skill /
  SubAgent language as the Java `regnexe-agent` project.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Why Not Just deepagents?](#why-not-just-deepagents)
- [Core Model](#core-model)
- [Capability Loading](#capability-loading)
- [Memory](#memory)
- [Events and Streaming](#events-and-streaming)
- [Human Approval](#human-approval)
- [Examples](#examples)
- [Reference](#reference)

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

### 3. Write a plugin and run

```python
import asyncio

from regnexe import (
    ConsoleEventListener,
    RegnexeAgentBuilder,
    Vendor,
    agent_tool,
    plugin,
)


@plugin(id="weather", name="Weather Plugin", description="Weather queries")
class WeatherPlugin:
    @agent_tool("Get today's weather for a city, including activity advice.")
    def get_weather(self, city: str) -> str:
        return "Beijing: sunny, 22 C, excellent air quality. Great day for running."


async def main() -> None:
    agent = (
        RegnexeAgentBuilder()
        .with_default_model(Vendor.DEEPSEEK, "deepseek-v4-flash")
        .with_plugin(WeatherPlugin())               # one line to load a plugin
        .with_event_listener(ConsoleEventListener())
        .build()
    )

    result = await agent.ainvoke(
        "Check today's Beijing weather. Is it good for running?",
        app_id="demo",
        user_id="user1",
        session_id="morning-run",
    )

    print(result.status)
    print(result.final_text)


asyncio.run(main())
```

## Why Not Just deepagents?

deepagents is the orchestration engine. regnexe-py is the application framework around
that engine.

| Need | Direct deepagents | regnexe-py |
|------|-------------------|------------|
| Register business tools | Manually create and pass tools | Decorate normal Python classes with `@plugin` and `@agent_tool` |
| Mix tools, skills, sub-agents | Maintain separate lists yourself | Register all capabilities through one builder and marketplace |
| Load file-based skills | Pass skill paths manually | Use `.with_skill()` or `.with_directory()` to scan `SKILL.md` files |
| Preserve user/session identity | Design your own thread naming scheme | Use explicit `app_id`, `user_id`, and `session_id` |
| Reuse prior task outcomes | Build storage and prompt injection yourself | Use `TaskResultStore` for recent cross-session task summaries |
| Observe execution | Consume graph events directly | Attach `AgentEventListener` for structured LLM/tool/agent events |
| Support many model vendors | Instantiate each LangChain model yourself | Use `Vendor` or `with_model_spec("vendor:model")` |
| Align Python and Java agents | Define your own concepts | Reuse Regnexe-style Plugin, Skill, SubAgent, and descriptors |

Use deepagents directly for small experiments. Use regnexe-py when the agent is becoming
an application: multiple business plugins, reusable skills, user sessions, streaming UI,
audit logs, provider switching, or a Python/Java Regnexe stack.

## Core Model

regnexe-py has three runtime layers:

| Layer | Role |
|-------|------|
| `RegnexeAgent` | Wraps a lazily created deepagents graph and executes goals |
| `SimpleMarketplace` | Stores capability descriptors and splits them for deepagents |
| `CapabilityDescriptor` | Unified abstraction for Tool, Skill, and Sub-Agent |

### Capability types

| Type | What it is | When to use |
|------|------------|-------------|
| `MCP_TOOL` | A single callable Python tool | Lookups, calculations, API calls, business actions |
| `SKILL` | A `SKILL.md` directory or a focused sub-agent with private tools | Domain instructions, contract analysis, translation, report tasks |
| `SUB_AGENT` | An autonomous deepagents sub-agent | Complex independent sub-tasks such as travel planning or research |

The current marketplace is intentionally simple: v1 returns all registered capabilities.
That keeps behavior transparent today and leaves room for retrieval, ranking, permissions,
and embedding-based capability selection later.

## Capability Loading

All capabilities enter through the marketplace. The builder exposes focused shortcuts for
the capability types currently supported by the Python implementation.

### Method 1: Python object plugin

Best for business services, quick prototypes, and local tools.

```python
@plugin(id="weather", name="Weather Plugin")
class WeatherPlugin:
    @agent_tool("Get today's weather for a city.")
    def get_weather(self, city: str) -> str:
        return f"{city}: sunny, 22 C"


agent = (
    RegnexeAgentBuilder()
    .with_model_spec("deepseek:deepseek-v4-flash")
    .with_plugin(WeatherPlugin())
    .build()
)
```

### Method 2: File-system directory

Best for ops-managed or repository-managed skills.

```
examples/skills/
  translation/
    SKILL.md
```

```python
agent = (
    RegnexeAgentBuilder()
    .with_model_spec("deepseek:deepseek-v4-flash")
    .with_directory("examples/skills")
    .build()
)
```

`with_directory()` scans for `SKILL.md`, `plugin.yaml`, and `plugin.yml`.

<details>
<summary>SKILL.md format</summary>

```markdown
---
name: translator
plugin_id: translation
capability_id: translation.skill
description: "Translate text while preserving tone and domain terminology."
tags: [translation]
---
You are a professional translator. Preserve meaning, tone, and formatting.
```

</details>

### Method 3: Skill agent with private tools

Best when a domain capability needs its own prompt and private tools.

```python
from langchain_core.tools import tool


@tool
def analyze_clause(clause: str) -> str:
    """Assess legal risk for one contract clause."""
    return "Risk level: MEDIUM. Add a clearer exception process."


CONTRACT_SKILL = {
    "name": "contract_analyzer",
    "description": "Legal risk analysis. TRIGGER: use when analyzing contracts.",
    "system_prompt": "You are a contract risk analyst. Call tools, then summarize risks.",
    "tools": [analyze_clause],
}

agent = (
    RegnexeAgentBuilder()
    .with_model_spec("deepseek:deepseek-v4-flash")
    .with_skill_agent(
        "legal.contract_analyzer",
        "contract_analyzer",
        "Legal risk analysis for contract clauses.",
        CONTRACT_SKILL,
    )
    .build()
)
```

### Method 4: Sub-agent

Best for complex independent sub-tasks.

```python
TRAVEL_PLANNER = {
    "name": "travel_planner",
    "description": "Business trip planner. TRIGGER: use when planning travel.",
    "system_prompt": "Plan efficient business trips with meetings, meals, and travel gaps.",
    "tools": [],
}

agent = (
    RegnexeAgentBuilder()
    .with_model_spec("deepseek:deepseek-v4-flash")
    .with_subagent(
        "travel.travel_planner",
        "travel_planner",
        "Business trip planner.",
        TRAVEL_PLANNER,
    )
    .build()
)
```

## Memory

regnexe-py separates memory into practical layers:

```
LLM/tool turn
  |
  v
Session state
  |
  v
Cross-session task history
```

| Layer | Scope | Mechanism |
|-------|-------|-----------|
| Layer 1 | Current LLM/tool turn | Messages and tool results in the active graph state |
| Layer 2 | Same session | LangGraph checkpointer, `MemorySaver` by default |
| Layer 3 | Cross-session user history | `TaskResultStore`, backed by LangGraph `BaseStore` or in-process memory |

```python
await agent.ainvoke(
    "Continue the plan from last time",
    app_id="crm",
    user_id="alice",
    session_id="q2-planning",
)
```

The `(app_id, user_id, session_id)` tuple becomes the thread identity for session state.
Recent task summaries for `(app_id, user_id)` can be injected into future prompts.

## Events and Streaming

```python
agent = (
    RegnexeAgentBuilder()
    .with_model_spec("deepseek:deepseek-v4-flash")
    .with_event_listener(ConsoleEventListener(show_system_prompt=False))
    .build()
)
```

Listeners receive structured events:

| Event | Meaning |
|-------|---------|
| `AGENT_STARTED` | A goal has started |
| `LLM_START` | A model call is about to run |
| `LLM_END` | A model call finished, including token metadata when available |
| `TOOL_CALLED` | A tool invocation started |
| `TOOL_RESULT` | A tool returned output |
| `AGENT_COMPLETED` | The run completed or errored |

Use this for console logs, JSON traces, token accounting, WebSocket updates, or SSE-style
streaming APIs.

## Human Approval

For sensitive workflows, pass deepagents interrupt rules through the builder:

```python
agent = (
    RegnexeAgentBuilder()
    .with_model_spec("deepseek:deepseek-v4-flash")
    .with_interrupt_on({"dangerous_tool": True})
    .build()
)
```

See `examples/10_interrupt_example.py` for an approval and resume flow.

## Examples

The `examples/` directory contains ten progressive examples:

| # | Example | What it demonstrates |
|---|---------|----------------------|
| 01 | `01_weather_example.py` | `@plugin`, `@agent_tool`, direct tool calls, multi-turn session |
| 02 | `02_contract_analyzer.py` | Skill-style sub-agent with private tools |
| 03 | `03_travel_planner.py` | Fully autonomous nested sub-agent |
| 04 | `04_business_trip.py` | Tool + skill + sub-agent in one workflow |
| 05 | `05_session_memory.py` | Same-session and cross-session memory |
| 06 | `06_custom_event_listener.py` | Custom listener, JSON logs, token aggregation |
| 07 | `07_streaming_api.py` | SSE-style streaming through event callbacks |
| 08 | `08_multi_model.py` | Different models for outer agent and inner skill |
| 09 | `09_file_plugin_loading.py` | Loading `SKILL.md` from files |
| 10 | `10_interrupt_example.py` | Human approval, interrupt, and resume |

```bash
python examples/01_weather_example.py
```

More details: [examples/README.md](examples/README.md)

## Reference

<details>
<summary>Builder options</summary>

| Method | Default | Description |
|--------|---------|-------------|
| `with_default_model(Vendor, str)` | - | LLM vendor + model name |
| `with_model(BaseChatModel)` | - | Provide a pre-built LangChain chat model |
| `with_model_spec(str)` | - | Parse `vendor:model_name` and resolve the model |
| `with_plugin(*instances)` | - | Register one or more `@plugin` Python objects |
| `with_directory(path)` | - | Scan a directory for `SKILL.md` and plugin descriptor files |
| `with_skill(...)` | - | Register a file-based skill directory |
| `with_skill_agent(...)` | - | Register a focused skill backed by a sub-agent config |
| `with_subagent(...)` | - | Register an autonomous deepagents sub-agent config |
| `with_checkpointer(checkpointer)` | `MemorySaver` | LangGraph same-session state |
| `with_store(store)` | in-process memory fallback | LangGraph store for cross-session task history |
| `with_event_listener(listener)` | none | Hook for LLM, tool, and agent lifecycle events |
| `with_interrupt_on(dict)` | none | Human-in-the-loop interrupt configuration |
| `with_system_prompt(str)` | none | Prepend custom system instructions |
| `with_session_buffer_size(int)` | `10` | Reserved session buffer setting |

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
| `interrupted` | Reserved status for interrupted flows |

</details>

---

If regnexe-py saves you time, a star on GitHub goes a long way.

[中文文档](README_zh.md)
