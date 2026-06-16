# regnexe-py Examples

Ten progressively more advanced examples covering every major feature of regnexe-py.

| # | File | Capability type | Key feature |
|---|------|-----------------|-------------|
| 01 | [01_weather_example.py](01_weather_example.py) | MCP_TOOL | `@plugin` / `@agent_tool` basics, multi-turn session |
| 02 | [02_contract_analyzer.py](02_contract_analyzer.py) | SKILL | SubAgent with private tools (mirrors Java Skill) |
| 03 | [03_travel_planner.py](03_travel_planner.py) | SUB_AGENT | Fully autonomous nested agent |
| 04 | [04_business_trip.py](04_business_trip.py) | Mixed | All three capability types in one agent |
| 05 | [05_session_memory.py](05_session_memory.py) | — | Layer 2 (same session) + Layer 3 (cross-session) memory |
| 06 | [06_custom_event_listener.py](06_custom_event_listener.py) | — | Custom listener: JSON logs + token aggregation |
| 07 | [07_streaming_api.py](07_streaming_api.py) | — | SSE-style streaming via event listener |
| 08 | [08_multi_model.py](08_multi_model.py) | — | Different vendors for outer agent vs inner skill |
| 09 | [09_file_plugin_loading.py](09_file_plugin_loading.py) | SKILL | `with_directory()` — load SKILL.md from files |
| 10 | [10_interrupt_example.py](10_interrupt_example.py) | — | Human-in-the-loop: interrupt + approve + resume |

## Prerequisites

```bash
pip install regnexe-py
```

Set at least one API key:

```bash
export DEEPSEEK_API_KEY=sk-...   # used in most examples
export DASHSCOPE_API_KEY=sk-...  # Aliyun Qwen (example 08)
```

## Running an example

```bash
python examples/01_weather_example.py
```

## Capability type quick reference

| Type | Builder method | deepagents mapping |
|------|---------------|-------------------|
| `MCP_TOOL` | `.with_plugin(instance)` | passed as `tools=` |
| `SKILL` | `.with_skill_agent(id, name, desc, sub_agent)` | passed as `subagents=` with focused system_prompt |
| `SKILL` (file) | `.with_skill(id, name, desc, path)` or `.with_directory(path)` | passed as `skills=` |
| `SUB_AGENT` | `.with_subagent(id, name, desc, sub_agent)` | passed as `subagents=` |
