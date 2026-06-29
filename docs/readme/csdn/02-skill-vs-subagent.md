# Skill 和 Sub-Agent 到底差在哪？一个借工具，一个有私有工具

> 「Regnexe Python 实战系列」第 2 篇（共 10 篇），对应仓库 [`examples/readme/02_skill_vs_subagent.py`](https://github.com/flower-trees/regnexe-py/blob/master/examples/readme/02_skill_vs_subagent.py)。上一篇：[01. 10 行代码跑通 LLM 多工具调用！不用插件、不建类，with_tool 直接上手](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/csdn/01-multi-tool.md)。

## 一个最容易纠结的问题

Agent 能力一复杂，就会遇到这个问题：

> “这个子任务到底该做成 Skill，还是做成 Sub-Agent？”

两个名字听起来都像“子能力”，但工程边界完全不同。选错了，轻则工具暴露混乱，重则模型成本和权限边界都失控。

regnexe-py 的规则很清楚：**Skill 借用父 Agent 的模型和工具，Sub-Agent 可以拥有自己的模型和私有工具**。

## Skill：继承模型，只能借工具

示例里的 Skill 是一个户外活动顾问：它先调用天气工具，再给出去不去跑步的建议。

```python
travel_advisor = {
    "name": "travel_advisor",
    "description": (
        "Calls get_weather for the city the user mentions and gives outdoor-activity "
        "advice based on the current weather. TRIGGER: Use when the user asks whether "
        "the weather is suitable for an outdoor activity."
    ),
    "system_prompt": (
        "You are an outdoor-activity advisor."
        "1. Call get_weather for the city the user mentions."
        "2. Based on the result, give a short, direct go/no-go recommendation."
    ),
    "tools": ["get_weather"],   # borrowed by capability id, not owned
}
```

关键点是 `tools` 里放的是能力 id 字符串，不是工具对象。也就是说，Skill 只能借已经注册过的工具。

更重要的是：Skill 没有自己的模型字段。示例注释里写得很直接：`install_skill_agent()` 发现你给 Skill 传 `model` 会报错。

## Sub-Agent：自己的模型，自己的私有工具

同一个示例里，费用估算被做成了 Sub-Agent：

```python
@tool
def estimate_trip_cost(days: int, city: str) -> str:
    """Estimate total cost for a multi-day business trip."""
    return f"{days}-day {city} trip estimate: flights 1800 CNY, hotel 1200 CNY, meals 600 CNY. Total: 3600 CNY."

expense_estimator = {
    "name": "expense_estimator",
    "model": ModelProvider().resolve(Vendor.ALIYUN, "qwen-plus"),
    "system_prompt": "You are a travel expense estimator.",
    "tools": [estimate_trip_cost],   # private -- invisible to the outer agent
}
```

这里的 `estimate_trip_cost` 是私有工具，不会注册到外层 Marketplace。外层 Agent 不能直接调用它，只能把费用估算这个任务交给 Sub-Agent。

这就是隔离的价值：外层负责总目标，内层负责专业子任务。

## 实战代码：两个能力放在同一个 Agent 里

```python
agent = (
    RegnexeAgentBuilder()
    .with_default_model(Vendor.DEEPSEEK, "deepseek-v4-flash")
    .with_tool(get_weather)
    .with_skill("travel.travel_advisor", travel_advisor)
    .with_subagent("travel.expense_estimator", expense_estimator)
    .with_event_listener(ConsoleEventListener())
    .build()
)
```

主 Agent 用 DeepSeek。Skill 继承它。Sub-Agent 自己用通义 `qwen-plus`。

## 小结：三秒判断

- 子能力只是复用主流程里的工具和模型：用 Skill
- 子能力需要独立模型：用 Sub-Agent
- 子能力需要私有工具，不想暴露给外层：用 Sub-Agent
- 子能力只是一个轻量工作流，比如“查天气后给建议”：用 Skill

记住一句话：**Skill 是借，Sub-Agent 是拥有**。

---

📌 上一篇：[01. 10 行代码跑通 LLM 多工具调用！不用插件、不建类，with_tool 直接上手](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/csdn/01-multi-tool.md) ｜ 下一篇：[03. Tool、Skill、Sub-Agent 散成一地？PluginDescriptor 一次打成业务插件](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/csdn/03-plugin-packaging.md)  
📌 项目地址：https://github.com/flower-trees/regnexe-py
