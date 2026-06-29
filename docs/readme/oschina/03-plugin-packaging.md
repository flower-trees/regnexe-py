# PluginDescriptor：把 Tool、Skill、Sub-Agent 打包成一个业务插件

> 「regnexe-py 开源实践系列」第 3 篇（共 10 篇），对应仓库 [`examples/readme/03_plugin_packaging.py`](https://github.com/flower-trees/regnexe-py/blob/master/examples/readme/03_plugin_packaging.py)。上一篇：[02. Skill / Sub-Agent 设计解析：共享模型和私有工具该怎么取舍](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/oschina/02-skill-vs-subagent.md)。

## 为什么需要插件边界

前两篇里，我们已经有了 Tool、Skill、Sub-Agent。问题也随之出现：

```text
get_weather
estimate_trip_cost
travel_advisor
expense_estimator
```

这些能力如果一直散落在构建代码里，很快就会变成“看得见能跑，但没人敢改”的状态。

regnexe-py 的底层抽象是 `PluginDescriptor`：**一个插件里可以装多个 CapabilityDescriptor，每个能力都有稳定 id**。

## 代码示例：一个插件打包三种能力

示例里的核心代码是这段：

```python
trip_plugin = (
    PluginDescriptor.builder()
    .plugin_id("trip-plugin")
    .version("1.0")
    .name("Trip Plugin")
    .description("Bundles a tool, a skill, and a sub-agent for trip planning")
    .tool(get_weather)                    # -> trip-plugin.get_weather
    .skill_config(travel_advisor)         # -> trip-plugin.travel_advisor
    .sub_agent_config(expense_estimator)  # -> trip-plugin.expense_estimator
    .build()
)
```

这段代码做了两件事：

- 把三种不同能力统一包装成 CapabilityDescriptor
- 自动生成完整能力 id：`plugin_id.name`

所以 `get_weather` 不再只是一个裸函数，而是 `trip-plugin.get_weather` 这个业务插件里的能力。

## 需要注意的能力 id

示例里 `travel_advisor` 的工具列表是这样写的：

```python
travel_advisor = {
    "name": "travel_advisor",
    "tools": ["trip-plugin.get_weather"],
}
```

这里必须是 `trip-plugin.get_weather`，不是 `get_weather`。

原因很简单：Skill 借的是完整能力 id。插件化以后，同名工具可能来自不同插件，只写裸名称会失去边界。

## 接入 Agent

手动构造好的 `PluginDescriptor` 可以直接交给 `with_plugin(...)`：

```python
agent = (
    RegnexeAgentBuilder()
    .with_default_model(Vendor.DEEPSEEK, "deepseek-v4-flash")
    .with_plugin(trip_plugin)
    .with_event_listener(ConsoleEventListener())
    .build()
)
```

这样第 3 篇只需要关心“怎么把能力打成一个插件”，不用提前理解 Marketplace。至于能力市场怎么替换、怎么接数据库，后面第 6 篇再单独展开。

## 适用场景

`PluginDescriptor.builder()` 适合这些场景：

- 能力定义来自数据库或配置中心，需要运行时拼装
- 一个业务插件里混合 Tool、Skill、Sub-Agent
- 你想手动控制插件 id、版本、名称和描述
- 需要把能力从“代码变量”升级成“可管理资产”

一句话：**PluginDescriptor 是 regnexe-py 能力体系的底层真相**。

---

上一篇：[02. Skill / Sub-Agent 设计解析：共享模型和私有工具该怎么取舍](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/oschina/02-skill-vs-subagent.md) ｜ 下一篇：[04. @plugin 装饰器设计：一个 Python 类注册多种 Agent 能力](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/oschina/04-plugin-decorator.md)  
项目地址：https://github.com/flower-trees/regnexe-py
