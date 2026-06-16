<p align="center">
  <h1 align="center">Regnexe Python</h1>
  <p align="center"><b>基于 deepagents 的应用级 Python Agent 框架</b></p>
  <p align="center">用插件、Skill、子 Agent、记忆、事件和人工审批构建可落地的 Agent 应用。</p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11%2B-blue" alt="Python 3.11+"/>
  <img src="https://img.shields.io/badge/deepagents-0.6.8%2B-purple" alt="deepagents 0.6.8+"/>
  <img src="https://img.shields.io/badge/LangGraph-0.5%2B-green" alt="LangGraph 0.5+"/>
  <img src="https://img.shields.io/badge/license-not%20specified-lightgrey" alt="License not specified"/>
</p>

---

很多 Agent 代码一开始都是直接把 `tools`、`skills`、`subagents` 传给 deepagents。
这对原型很好用。regnexe-py 保留 deepagents 作为底层运行引擎，并在它之上补齐应用框架层：
能力市场、插件装饰器、显式应用/用户/会话身份、跨会话任务记忆、结构化事件、模型厂商路由，以及
与 Regnexe Java 侧一致的概念模型。

```
用户目标
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
  | 能力加载来源：                                 |
  |  @plugin Python 对象                           |
  |  SKILL.md 目录                                 |
  |  plugin.yaml / plugin.yml                      |
  |  Builder 能力注册方法                          |
  |                         |                      |
  |                         v                      |
  |              CapabilityDescriptor              |
  |        +----------+---------+-------------+     |
  |        | MCP_TOOL | SKILL   | SUB_AGENT   |     |
  |        +----------+---------+-------------+     |
  +------------------------------------------------+
```

**相比直接使用 deepagents，regnexe-py 的突出优势：**

- **应用结构，而不只是图构建**：把业务工具、Skill、子 Agent、记忆、事件和模型选择统一放进 Builder。
- **插件市场**：能力只需注册一次，框架会映射到 deepagents 的 `tools`、`skills`、`subagents`。
- **业务友好的工具开发**：用 `@plugin` 和 `@agent_tool` 暴露普通 Python 类，不需要重复写 `StructuredTool`。
- **显式身份与记忆**：每次运行都携带 `app_id`、`user_id`、`session_id`，并可把近期任务摘要注入后续会话。
- **执行过程可观测**：事件监听器可接收 LLM 调用、工具调用、工具结果、Token 元数据和 Agent 生命周期事件。
- **对齐 Regnexe 生态**：Python 项目可以沿用 Java `regnexe-agent` 的 Plugin / Skill / SubAgent 语言。

---

## 目录

- [快速开始](#快速开始)
- [为什么不直接用 deepagents](#为什么不直接用-deepagents)
- [核心模型](#核心模型)
- [能力加载方式](#能力加载方式)
- [记忆](#记忆)
- [事件与流式输出](#事件与流式输出)
- [人工审批](#人工审批)
- [示例](#示例)
- [参考](#参考)

## 快速开始

### 1. 安装

```bash
pip install regnexe-py
```

本地开发安装：

```bash
pip install -e ".[dev]"
```

### 2. 配置模型 Key

```bash
export DEEPSEEK_KEY=sk-...
export ALIYUN_KEY=sk-...
export OPENAI_API_KEY=sk-...
```

Ollama 使用本地 Ollama 运行时，不需要 API Key。

### 3. 定义插件并运行

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
        .with_plugin(WeatherPlugin())               # 一行加载插件
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

## 为什么不直接用 deepagents

deepagents 是编排引擎。regnexe-py 是围绕这个引擎构建的应用框架。

| 需求 | 直接使用 deepagents | 使用 regnexe-py |
|------|---------------------|-----------------|
| 注册业务工具 | 手动创建并传入 tools | 用 `@plugin` 和 `@agent_tool` 装饰普通 Python 类 |
| 混合工具、Skill、子 Agent | 自己维护多个列表 | 通过统一 Builder 和 Marketplace 注册所有能力 |
| 加载文件型 Skill | 手动传入 skill 路径 | 使用 `.with_skill()` 或 `.with_directory()` 扫描 `SKILL.md` |
| 保留用户/会话身份 | 自己设计 thread 命名规则 | 显式使用 `app_id`、`user_id`、`session_id` |
| 复用历史任务结果 | 自己实现存储和 Prompt 注入 | 使用 `TaskResultStore` 注入近期跨会话任务摘要 |
| 观察执行过程 | 直接消费 graph events | 接入 `AgentEventListener`，获得结构化 LLM/Tool/Agent 事件 |
| 支持多模型厂商 | 自己实例化各类 LangChain model | 使用 `Vendor` 或 `with_model_spec("vendor:model")` |
| 对齐 Python 与 Java Agent | 自己定义概念体系 | 复用 Regnexe 风格的 Plugin、Skill、SubAgent 和能力描述 |

小实验可以直接用 deepagents。只要 Agent 开始变成应用，例如有多个业务插件、可复用 Skill、
用户会话、流式前端、审计日志、模型切换，或需要和 Java Regnexe 栈保持一致，regnexe-py 会更合适。

## 核心模型

regnexe-py 运行时由三层组成：

| 层级 | 作用 |
|------|------|
| `RegnexeAgent` | 包装延迟创建的 deepagents graph，并执行用户目标 |
| `SimpleMarketplace` | 管理能力描述，并按 deepagents 需要拆分能力 |
| `CapabilityDescriptor` | 对 Tool、Skill、Sub-Agent 的统一抽象 |

### 三种能力类型

| 类型 | 是什么 | 适合什么场景 |
|------|--------|--------------|
| `MCP_TOOL` | 单个可调用 Python 工具 | 查询、计算、API 调用、业务动作 |
| `SKILL` | `SKILL.md` 目录，或带私有工具的聚焦子 Agent | 领域指令、合同分析、翻译、报告任务 |
| `SUB_AGENT` | 自治的 deepagents 子 Agent | 旅行规划、调研等复杂独立子任务 |

当前 Marketplace 保持简单：v1 返回所有已注册能力。这让行为更透明，也为后续检索、排序、
权限过滤和基于 Embedding 的能力选择留出空间。

## 能力加载方式

所有能力都通过 Marketplace 进入 Agent。Python 版 Builder 为当前支持的能力类型提供了聚焦的快捷注册方法。

### 方式一：Python 对象插件

适合业务服务、快速原型和本地工具。

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

### 方式二：文件系统目录

适合运维管理或仓库管理的 Skill。

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

`with_directory()` 会扫描 `SKILL.md`、`plugin.yaml` 和 `plugin.yml`。

<details>
<summary>SKILL.md 格式</summary>

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

### 方式三：带私有工具的 Skill Agent

适合拥有独立 Prompt 和私有工具的领域能力。

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

### 方式四：Sub-Agent

适合复杂、可独立处理的子任务。

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

## 记忆

regnexe-py 将记忆拆成三层：

```
LLM / Tool 当前回合
  |
  v
Session 状态
  |
  v
跨 Session 任务历史
```

| 层级 | 范围 | 实现机制 |
|------|------|----------|
| Layer 1 | 当前 LLM/Tool 回合 | 活跃图状态中的消息和工具结果 |
| Layer 2 | 同一 session | LangGraph checkpointer，默认使用 `MemorySaver` |
| Layer 3 | 跨 session 用户历史 | `TaskResultStore`，可接 LangGraph `BaseStore`，也可用进程内存 |

```python
await agent.ainvoke(
    "Continue the plan from last time",
    app_id="crm",
    user_id="alice",
    session_id="q2-planning",
)
```

`(app_id, user_id, session_id)` 会生成会话线程身份。`(app_id, user_id)` 的近期任务摘要可以注入后续 Prompt。

## 事件与流式输出

```python
agent = (
    RegnexeAgentBuilder()
    .with_model_spec("deepseek:deepseek-v4-flash")
    .with_event_listener(ConsoleEventListener(show_system_prompt=False))
    .build()
)
```

监听器会收到结构化事件：

| 事件 | 含义 |
|------|------|
| `AGENT_STARTED` | 目标开始执行 |
| `LLM_START` | 即将发起模型调用 |
| `LLM_END` | 模型调用结束，包含可用的 Token 元数据 |
| `TOOL_CALLED` | 工具调用开始 |
| `TOOL_RESULT` | 工具返回结果 |
| `AGENT_COMPLETED` | 执行完成或出错 |

可用于控制台日志、JSON Trace、Token 统计、WebSocket 更新或 SSE 风格流式接口。

## 人工审批

对于敏感工作流，可以通过 Builder 传入 deepagents 中断规则：

```python
agent = (
    RegnexeAgentBuilder()
    .with_model_spec("deepseek:deepseek-v4-flash")
    .with_interrupt_on({"dangerous_tool": True})
    .build()
)
```

审批与恢复流程可参考 `examples/10_interrupt_example.py`。

## 示例

`examples/` 目录提供 10 个由浅入深的示例：

| 编号 | 示例 | 展示内容 |
|------|------|----------|
| 01 | `01_weather_example.py` | `@plugin`、`@agent_tool`、直接工具调用、多轮会话 |
| 02 | `02_contract_analyzer.py` | 带私有工具的 Skill 风格子 Agent |
| 03 | `03_travel_planner.py` | 完全自治的嵌套子 Agent |
| 04 | `04_business_trip.py` | 工具 + Skill + 子 Agent 混合工作流 |
| 05 | `05_session_memory.py` | 同会话与跨会话记忆 |
| 06 | `06_custom_event_listener.py` | 自定义监听器、JSON 日志、Token 聚合 |
| 07 | `07_streaming_api.py` | 基于事件回调的 SSE 风格流式输出 |
| 08 | `08_multi_model.py` | 外层 Agent 与内层 Skill 使用不同模型 |
| 09 | `09_file_plugin_loading.py` | 从文件加载 `SKILL.md` |
| 10 | `10_interrupt_example.py` | 人工审批、中断与恢复 |

```bash
python examples/01_weather_example.py
```

更多说明见：[examples/README_zh.md](examples/README_zh.md)

## 参考

<details>
<summary>Builder 参数</summary>

| 方法 | 默认值 | 说明 |
|------|--------|------|
| `with_default_model(Vendor, str)` | - | 指定 LLM 厂商和模型名称 |
| `with_model(BaseChatModel)` | - | 传入已构建的 LangChain ChatModel |
| `with_model_spec(str)` | - | 解析 `vendor:model_name` 并创建模型 |
| `with_plugin(*instances)` | - | 注册一个或多个 `@plugin` Python 对象 |
| `with_directory(path)` | - | 扫描目录中的 `SKILL.md` 和插件描述文件 |
| `with_skill(...)` | - | 注册文件型 Skill 目录 |
| `with_skill_agent(...)` | - | 注册由子 Agent 配置承载的聚焦 Skill |
| `with_subagent(...)` | - | 注册自治 deepagents 子 Agent 配置 |
| `with_checkpointer(checkpointer)` | `MemorySaver` | LangGraph 同会话状态 |
| `with_store(store)` | 进程内存兜底 | 跨会话任务历史使用的 LangGraph store |
| `with_event_listener(listener)` | 无 | 监听 LLM、Tool 和 Agent 生命周期事件 |
| `with_interrupt_on(dict)` | 无 | 人工审批和中断配置 |
| `with_system_prompt(str)` | 无 | 追加自定义系统提示词 |
| `with_session_buffer_size(int)` | `10` | 预留的会话 buffer 配置 |

</details>

<details>
<summary>支持的 LLM 厂商</summary>

| 枚举值 | 厂商 | 环境变量 |
|--------|------|----------|
| `Vendor.ALIYUN` | 阿里云 DashScope 兼容接口 | `ALIYUN_KEY` |
| `Vendor.DEEPSEEK` | DeepSeek | `DEEPSEEK_KEY` |
| `Vendor.DOUBAO` | 字节跳动豆包 | `DOUBAO_KEY` |
| `Vendor.HUNYUAN` | 腾讯混元 | `HUNYUAN_KEY` |
| `Vendor.LINGYI` | 零一万物 | `LINGYI_KEY` |
| `Vendor.MINIMAX` | MiniMax | `MINIMAX_KEY` |
| `Vendor.MOONSHOT` | Moonshot / Kimi | `MOONSHOT_KEY` |
| `Vendor.OLLAMA` | Ollama 本地运行时 | 不需要 API Key |
| `Vendor.OPENAI` | OpenAI | `OPENAI_API_KEY` |
| `Vendor.QIANFAN` | 百度千帆 | `QIANFAN_KEY` |
| `Vendor.STEPFUN` | 阶跃星辰 | `STEPFUN_KEY` |
| `Vendor.ZHIPU` | 智谱 AI / GLM | `ZHIPU_KEY` |

</details>

<details>
<summary>任务状态</summary>

| 状态 | 含义 |
|------|------|
| `completed` | 目标完成 |
| `error` | 执行异常，返回错误文本 |
| `interrupted` | 为中断流程预留的状态 |

</details>

---

如果 regnexe-py 对你有帮助，欢迎给 GitHub 项目点个 Star。

[English README](README.md)
