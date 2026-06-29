# @plugin 装饰器设计：一个 Python 类注册多种 Agent 能力

> 「regnexe-py 开源实践系列」第 4 篇（共 10 篇），对应仓库 [`examples/readme/04_plugin_decorator.py`](https://github.com/flower-trees/regnexe-py/blob/master/examples/readme/04_plugin_decorator.py)。上一篇：[03. PluginDescriptor：把 Tool、Skill、Sub-Agent 打包成一个业务插件](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/oschina/03-plugin-packaging.md)。

## 装配代码膨胀是实际工程问题

`PluginDescriptor.builder()` 很适合动态拼装，但固定业务模块如果都手写 descriptor，会显得啰嗦。

比如天气插件，本来就可以是一个普通 Python 类：查天气、查空气质量、户外建议、费用估算都属于这个领域。更自然的写法是直接在类和方法上标注能力。

这就是 `@plugin` / `@agent_tool` / `@agent_skill` / `@agent_subagent` 的用途。

## 代码示例：一个类注册工具

```python
@plugin(id="weather", name="Weather Plugin", description="Weather, advice, and trip cost estimation")
class WeatherPlugin:
    @agent_tool("Get today's weather for a city.", tags=["weather"])
    def get_weather(self, city: str) -> str:
        return "Beijing: sunny, 22 C."

    @agent_tool("Get today's air quality index (AQI) for a city.", tags=["weather"])
    def get_air_quality(self, city: str) -> str:
        return "Beijing: AQI 35, excellent air quality."
```

到这里，一个普通类已经变成了插件，两个方法已经变成了 Agent 可调用工具。

## 同一个插件内声明 Skill 和 Sub-Agent

示例里同一个插件类还嵌套了 Skill：

```python
@agent_skill(
    id="travel_advisor",
    description="Gives outdoor-activity advice based on the current weather for a city.",
    system_prompt="You are an outdoor-activity advisor.",
    allowed_tools=["weather.get_weather"],
)
class TravelAdvisorSkill:
    pass
```

注意 `allowed_tools` 仍然是完整能力 id：`weather.get_weather`。

Sub-Agent 也可以嵌套，而且可以有自己的私有工具：

```python
@agent_subagent(
    id="expense_estimator",
    description="Estimates the total cost of a business trip.",
    system_prompt="You are a travel expense estimator.",
    model="aliyun:qwen-plus",
)
class ExpenseEstimatorSubAgent:
    @agent_tool("Estimates total cost for a multi-day business trip.")
    def estimate_trip_cost(self, days: int, city: str) -> str:
        return f"{days}-day {city} trip estimate: 3600 CNY total."
```

## 注册方式

真正接入 Agent 时只有一行：

```python
agent = (
    RegnexeAgentBuilder()
    .with_default_model(Vendor.DEEPSEEK, "deepseek-v4-flash")
    .with_plugin(WeatherPlugin())
    .with_event_listener(ConsoleEventListener())
    .build()
)
```

这一个 `with_plugin(WeatherPlugin())` 同时注册了：

- `weather.get_weather`
- `weather.get_air_quality`
- `weather.travel_advisor`
- `weather.expense_estimator`

## 两个设计边界

第一，Skill 里面不要写 `@agent_tool`。Skill 只能借工具，不能拥有私有工具。

第二，Sub-Agent 里面的 `@agent_tool` 是私有工具，不会暴露给外层 Agent。外层只能调用 Sub-Agent 这个能力，不能直接调用它内部的方法。

## 小结

`@plugin` 适合固定业务模块：代码结构清晰，能力元数据贴着业务方法写，一次实例化就能注册整组能力。

如果说 `PluginDescriptor.builder()` 适合动态拼装，那么 `@plugin` 就适合日常业务开发。

---

上一篇：[03. PluginDescriptor：把 Tool、Skill、Sub-Agent 打包成一个业务插件](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/oschina/03-plugin-packaging.md) ｜ 下一篇：[05. 目录加载机制：plugin.yaml 和 SKILL.md 如何变成 Agent 能力](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/oschina/05-file-directory-loading.md)  
项目地址：https://github.com/flower-trees/regnexe-py
