# 不想为一个 Skill 改文案就发版？with_directory 这条路很实用

> 「Regnexe Python 工程化系列」第 5 篇（共 10 篇），对应仓库 [`examples/readme/05_file_directory_loading.py`](https://github.com/flower-trees/regnexe-py/blob/master/examples/readme/05_file_directory_loading.py)。上一篇：[04. 普通 Python 类怎么变成 Agent 插件？@plugin 一次注册四种能力](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/juejin/04-plugin-decorator.md)。

## 一个真实的团队矛盾

开发同学通常喜欢把能力写进代码：类型明确、能测试、能 Review。

但运营或运维同学经常有另一个诉求：

> “我只是想改一个 Skill 的提示词，或者加一个插件目录，能不能别重新发版？”

这两个诉求并不冲突。regnexe-py 用 `with_directory()` 支持文件系统目录加载，让一部分能力可以脱离 Python 类和发版流程。

## 目录长什么样

示例里临时创建了一个插件目录，大概结构是这样：

```text
weather-plugin/
  plugin.yaml
  SKILL.md
```

`plugin.yaml` 负责声明工具能力：

```yaml
plugin_id: weather-plugin
capabilities:
  - capability_id: weather-plugin.get_weather
    type: mcp_tool
    name: get_weather
    description: "Get today's weather for a city"
    tags: [weather]
```

`SKILL.md` 负责声明 Skill：

```markdown
---
name: advisor
plugin_id: weather-plugin
capability_id: weather-plugin.advisor
description: "Outdoor activity advisor..."
tags: [weather]
allowed_tools: [get_weather]
---
You are an outdoor activity advisor.
1. Call get_weather for the city the user mentions.
2. Based on the result, give a short go/no-go recommendation.
```

## 实战代码

接入目录只需要一行：

```python
agent = (
    RegnexeAgentBuilder()
    .with_default_model(Vendor.DEEPSEEK, "deepseek-v4-flash")
    .with_tool(get_weather)
    .with_directory(str(plugin_dir))
    .with_event_listener(ConsoleEventListener())
    .build()
)
```

这里 `get_weather` 仍然由代码提供，目录里的 `plugin.yaml` 和 `SKILL.md` 提供能力元数据和 Skill 内容。

Agent 构建时会扫描目录，把这些文件注册成 Marketplace 里的能力。对后续调用来说，它们和代码注册的能力没有区别。

## 适用场景

`with_directory()` 特别适合：

- Skill 提示词经常调整
- 插件由运维目录管理
- 不同部署环境启用不同能力
- 不希望每次改 Markdown 都重新发版

但它不适合所有东西。核心业务工具仍然建议写在 Python 代码里，方便测试和类型检查；目录加载更适合描述型、配置型、提示词型能力。

## 小结

regnexe-py 没有强迫你在“代码插件”和“文件插件”之间二选一。一个应用里完全可以核心能力走 `@plugin`，运营能力走 `with_directory()`。

关键是：不管来源是代码还是目录，最后都进入同一个 Marketplace。

---

📌 上一篇：[04. 普通 Python 类怎么变成 Agent 插件？@plugin 一次注册四种能力](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/juejin/04-plugin-decorator.md) ｜ 下一篇：[06. 能力市场要换成数据库？regnexe-py 只需要替换一个 Marketplace](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/juejin/06-marketplace.md)  
📌 项目地址：https://github.com/flower-trees/regnexe-py
