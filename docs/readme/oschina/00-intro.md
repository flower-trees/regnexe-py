# 开源一个 Python Agent 应用框架：插件、会话、事件、取消都内置

> 本文是「regnexe-py 开源实践系列」开篇（共 10 篇），系列文章会把 [regnexe-py](https://github.com/flower-trees/regnexe-py) 仓库里 9 个可直接运行的示例（`examples/readme/01~09`）逐一拆解。示例都来自仓库，适合直接拉代码验证。

## 为什么做这个框架

你现在写 Python Agent，是不是大概长这样：

```python
agent = create_deep_agent(
    model=model,
    tools=[get_weather, get_air_quality, search_docs, query_order],
    subagents=[travel_advisor, contract_checker],
)
```

原型阶段这样很好用：工具能调，模型能回，Demo 很快就能演示。

但只要它开始变成业务应用，问题就会一起冒出来：

- 工具越来越多，谁负责注册、分组、查询？
- 同一个用户的不同会话怎么区分？
- 上一次任务的结果，下一次能不能复用？
- 前端要展示“正在调用哪个工具”，事件从哪里来？
- 用户点了“停止”，后端 Agent 还在跑怎么办？
- DeepSeek、通义、OpenAI、Ollama 怎么统一切换？

因此，这个项目的重点不是再造一个 Demo，而是把插件、会话、事件、身份、取消这些应用层问题收敛到一个框架里。

这就是我写 regnexe-py 的原因。

## 项目定位

一句话：**regnexe-py 是一个面向应用落地的开源 Python Agent 框架**。

它补齐的是 Agent 应用真正会用到的工程层：

```text
业务插件 / Tool / Skill / Sub-Agent
          │
          ▼
Marketplace 能力市场
          │
          ▼
RegnexeAgentBuilder
          │
          ▼
deepagents / LangGraph 运行时
          │
          ▼
AgentResult + 事件 + 记忆 + 取消控制
```

你仍然可以用 LangChain 的 `@tool`，仍然可以用 deepagents 的能力模型；区别是 regnexe-py 会把这些能力放进一个更适合应用开发的结构里。

## 最简上手示例

安装：

```bash
pip install regnexe-py
```

配置模型 Key：

```bash
export DEEPSEEK_KEY=sk-...
export ALIYUN_KEY=sk-...
export OPENAI_API_KEY=sk-...
```

然后直接注册一个 LangChain tool，发起一次最简单的调用：

```python
import asyncio

from langchain_core.tools import tool
from regnexe import ConsoleEventListener, RegnexeAgentBuilder, Vendor

@tool
def get_weather(city: str) -> str:
    """Get today's weather for a city."""
    return "Beijing: sunny, 22 C, excellent air quality."

async def main() -> None:
    agent = (
        RegnexeAgentBuilder()
        .with_default_model(Vendor.DEEPSEEK, "deepseek-v4-flash")
        .with_tool(get_weather)
        .with_event_listener(ConsoleEventListener())
        .build()
    )

    result = await agent.ainvoke(
        "Check today's weather in Beijing. Is it good for outdoor running?"
    )

    print(result.status)
    print(result.final_text)


asyncio.run(main())
```

接上 `ConsoleEventListener` 之后，控制台能直接看到 Agent 在做什么：

```text
[AGENT ▶] RegnexeAgent
          goal: Check today's weather in Beijing. Is it good for outdoor running?
[TOOL  ▶] mcp_tool:get_weather  input={"city": "Beijing"}
[TOOL  ■] mcp_tool:get_weather  output=Beijing: sunny, 22 C, excellent air quality.
[AGENT ■] status=completed
```

这就是开篇想强调的核心：regnexe-py 不是让你多写一层包装，而是把工具、模型、事件和结果收进同一个应用入口里。多工具协作、工具选择和结果合并，下一篇再展开。

## 系列大纲

接下来 9 篇文章，会按这个顺序拆仓库里的 `examples/readme/`：

| # | 主题 | 一句话 |
|---|---|---|
| 01 | [`with_tool` 多工具入门](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/oschina/01-multi-tool.md) | 不建插件类，直接把 LangChain tool 接进 Agent |
| 02 | [Skill vs Sub-Agent](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/oschina/02-skill-vs-subagent.md) | Skill 借工具、继承模型；Sub-Agent 拥有私有工具和独立模型 |
| 03 | [PluginDescriptor 打包](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/oschina/03-plugin-packaging.md) | Tool、Skill、Sub-Agent 统一变成能力描述符 |
| 04 | [`@plugin` 装饰器](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/oschina/04-plugin-decorator.md) | 普通 Python 类一次注册工具、Skill、Sub-Agent |
| 05 | [目录加载](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/oschina/05-file-directory-loading.md) | `plugin.yaml` + `SKILL.md` 让能力脱离发版流程 |
| 06 | [Marketplace](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/oschina/06-marketplace.md) | 能力市场可以替换成 DB / 配置中心 |
| 07 | [会话记忆机制](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/oschina/07-three-layer-memory.md) | 用 `session_id` 接住 LangGraph 上下文，跨 session 只做轻量任务摘要 |
| 08 | [可观测性](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/oschina/08-observability.md) | LLM 调用、工具调用、Token 用量都能通过事件暴露 |
| 09 | [取消与继续](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/oschina/09-cancel-and-resume.md) | `acancel()` 真的取消后端任务，不只是停前端流 |

每一篇都不是空对空讲概念，代码都来自仓库里的真实示例。

## 和普通 Agent Demo 的区别

Demo 看的是“模型能不能调工具”。应用看的是“这套东西能不能长期维护”。

regnexe-py 解决的不是一次工具调用，而是这些更工程化的问题：

- 能力怎么注册、打包、查询、替换
- 用户、会话、应用身份怎么贯穿一次运行
- 任务结果怎么沉淀到后续会话
- 执行过程怎么暴露给日志、前端和监控
- 运行中的任务怎么被用户主动取消
- 多模型厂商怎么统一路由

小实验可以直接用 deepagents。只要 Agent 开始接业务插件、用户系统、审计日志、前端流式界面，regnexe-py 就有意义。

---

项目地址：https://github.com/flower-trees/regnexe-py  
下一篇：[01. with_tool 极简接入：不建插件类，几行代码注册多个 LangChain 工具](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/oschina/01-multi-tool.md)
