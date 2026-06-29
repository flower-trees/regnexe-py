# 别一上来就造插件！Python Agent 多工具调用先用 with_tool 跑通

> 「Regnexe Python 工程化系列」第 1 篇（共 10 篇），对应仓库 [`examples/readme/01_multi_tool.py`](https://github.com/flower-trees/regnexe-py/blob/master/examples/readme/01_multi_tool.py)。上一篇：[00. 别再把 Python Agent 写成 Demo 了：插件、记忆、事件、取消都得管起来](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/juejin/00-intro.md)。

## 痛点：只是想试个工具，为什么要先设计插件体系

很多人做 Agent 的第一步就开始设计插件、目录、注册表。方向没错，但第一步真的没必要这么重。

你只是想验证一件事：模型能不能同时查天气和空气质量，然后给出跑步建议。结果还没跑起来，先写了一堆工程结构。

regnexe-py 给了一条最短路径：**已有 LangChain tool，直接丢给 `with_tool(...)`**。

## 实战代码

来看仓库里的 [`01_multi_tool.py`](https://github.com/flower-trees/regnexe-py/blob/master/examples/readme/01_multi_tool.py)：

```python
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

agent = (
    RegnexeAgentBuilder()
    .with_default_model(Vendor.DEEPSEEK, "deepseek-v4-flash")
    .with_tool(get_weather, get_air_quality)   # 一次注册多个
    .with_event_listener(ConsoleEventListener())
    .build()
)
```

然后发起一次异步调用：

```python
result = await agent.ainvoke(
    "Check today's weather and air quality in Beijing, then tell me if it's good for outdoor running."
)
```

注意这里没有新建插件类，也没有写装饰器。`@tool` 仍然是 LangChain 的工具定义，regnexe-py 只是把它接进统一 Builder。

## 运行效果：先把事件打出来

示例里接了 `ConsoleEventListener()`。跑起来后，你能看到 Agent 什么时候开始、什么时候调用工具、工具返回了什么、最终状态是什么。

这点很重要。Agent 调试不能只看最终回答，否则你不知道模型到底有没有调用 `get_air_quality`，也不知道参数是不是传对了。

控制台会打印出类似这样的事件流：

```text
[AGENT ▶] RegnexeAgent
          goal: Check today's weather and air quality in Beijing, then tell me if it's good for outdoor running.
[TOOL  ▶] mcp_tool:get_air_quality  input={"city": "Beijing"}
[TOOL  ▶] mcp_tool:get_weather  input={"city": "Beijing"}
[TOOL  ■] mcp_tool:get_air_quality  output=Beijing: AQI 35, excellent air quality.
[TOOL  ■] mcp_tool:get_weather  output=Beijing: sunny, 22 C.
[AGENT ■] status=completed
```

## 踩坑提醒

`@tool` 的函数名和 docstring 会进入工具描述。函数名别写得太随意，docstring 也别只写一句“查询”。模型能不能选对工具，和工具描述质量直接相关。

另一个细节是多工具顺序不要写死在业务代码里。你只需要把工具注册进去，让模型根据目标决定是否都要调用；如果必须强约束顺序，那应该放到 Skill 或 Sub-Agent 里做成明确工作流。

## 小结

`with_tool(...)` 适合三类场景：

- PoC 阶段，先验证 Agent 能不能跑通
- 已经有现成 LangChain tool，不想重写插件类
- 工具数量少，暂时不需要版本、分组和市场管理

等工具开始变多，就该进入后面的插件和 Marketplace 体系了。

---

📌 上一篇：[00. 别再把 Python Agent 写成 Demo 了：插件、记忆、事件、取消都得管起来](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/juejin/00-intro.md) ｜ 下一篇：[02. Skill 和 Sub-Agent 到底怎么选？Python Agent 子任务别再乱拆了](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/juejin/02-skill-vs-subagent.md)  
📌 项目地址：https://github.com/flower-trees/regnexe-py ，欢迎 Star
