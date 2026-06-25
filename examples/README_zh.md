# regnexe-py 示例

由浅入深的示例，覆盖 regnexe-py 的所有核心功能，外加一套
[`readme/`](readme)，对应顶层 [`README.md`](../README.md) 的每一节。

| 编号 | 文件 | 能力类型 | 核心特性 |
|------|------|----------|----------|
| 01 | [01_weather_example.py](01_weather_example.py) | MCP_TOOL | `@plugin` / `@agent_tool` 基础用法，多轮会话 |
| 02 | [02_contract_analyzer.py](02_contract_analyzer.py) | SKILL | 带私有工具的 SubAgent（对应 Java Skill） |
| 03 | [03_travel_planner.py](03_travel_planner.py) | SUB_AGENT | 完全自主的嵌套 Agent |
| 04 | [04_business_trip.py](04_business_trip.py) | 混合 | 三种能力类型同时使用 |
| 05 | [05_session_memory.py](05_session_memory.py) | — | 三层记忆：Layer 2（同 session）+ Layer 3（跨 session） |
| 06 | [06_custom_event_listener.py](06_custom_event_listener.py) | — | 自定义监听器：JSON 结构化日志 + Token 统计 |
| 07 | [07_streaming_api.py](07_streaming_api.py) | — | SSE 流式输出，适合 Web 场景 |
| 08 | [08_multi_model.py](08_multi_model.py) | — | 外层 Agent 与内层 Skill 使用不同厂商模型 |
| 09 | [09_file_plugin_loading.py](09_file_plugin_loading.py) | SKILL | `with_directory()` 从文件加载 SKILL.md |
| 10 | [10_interrupt_example.py](10_interrupt_example.py) | — | 人工审批：中断 → 人工确认 → 恢复执行 |
| 11 | [11_cancel_example.py](11_cancel_example.py) | — | 用户主动触发中途取消，再继续执行 |

按 README 章节对应的版本见 [`readme/`](readme)（Skill 与 Sub-Agent、插件打包、
Marketplace、三层记忆、可观测性、取消与恢复）。

## 快速开始

```bash
pip install regnexe-py
```

配置 API Key（至少一个）：

```bash
export DEEPSEEK_KEY=sk-...   # 大多数示例使用
export ALIYUN_KEY=sk-...     # 阿里云通义（示例 08，以及 readme/02、readme/04 中 Sub-Agent 自己的模型）
```

运行示例：

```bash
python examples/01_weather_example.py
```

## 能力类型速查

| 类型 | Builder 方法 | deepagents 映射 | Java 对应 |
|------|-------------|-----------------|-----------|
| `MCP_TOOL` | `.with_tool(*工具)` 或 `.with_plugin(实例)` | `tools=` | Plugin Tool |
| `SKILL` | `.with_skill(capability_id, sub_agent, ...)` | `subagents=`，带专属 system_prompt，不允许传 `model` 键 | SkillConfig |
| `SKILL`（文件） | `.with_skill_dir(capability_id, name, desc, 路径)` 或 `.with_directory(路径)` | `skills=` | SKILL.md |
| `SUB_AGENT` | `.with_subagent(capability_id, sub_agent, ...)` | `subagents=`，`sub_agent["model"]` 可以和父 Agent 不同 | SubAgent |

## 三层记忆说明

| 层级 | 范围 | 实现机制 |
|------|------|----------|
| Layer 1 | 单次 LLM 调用 | ToolMessage 直接写入消息状态 |
| Layer 2 | 同一 session | LangGraph Checkpointer（`MemorySaver` 或自定义） |
| Layer 3 | 跨 session / 用户 | `TaskResultStore` → LangGraph `BaseStore`（或内存） |

详见示例 05。
