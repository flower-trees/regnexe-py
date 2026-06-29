# regnexe-py 开源实践系列（开源中国文章，共 10 篇）

这组文章用于发布到开源中国，风格偏开源项目介绍和架构实践：重点说明项目定位、接口设计、扩展边界和真实可运行示例。

- 项目地址：https://github.com/flower-trees/regnexe-py
- 发布目录：`docs/readme/oschina/`
- 文章结构：项目/架构问题 -> 代码示例 -> 设计关键点 -> 适用场景 -> 上下篇导航
- 内容原则：突出开源项目价值，但不夸大当前能力；会话记忆、Marketplace、取消任务均按当前实现边界说明。

| # | 文章 | 对应示例 | 核心内容 |
|---|---|---|---|
| 00 | [开源一个 Python Agent 应用框架：插件、会话、事件、取消都内置](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/oschina/00-intro.md) | 系列开篇 | 介绍 regnexe-py 的开源定位：插件、会话、事件、取消等应用层能力 |
| 01 | [with_tool 极简接入：不建插件类，几行代码注册多个 LangChain 工具](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/oschina/01-multi-tool.md) | [`examples/readme/01_multi_tool.py`](https://github.com/flower-trees/regnexe-py/blob/master/examples/readme/01_multi_tool.py) | `with_tool(...)` 极简注册多个 LangChain 工具，并暴露事件流 |
| 02 | [Skill / Sub-Agent 设计解析：共享模型和私有工具该怎么取舍](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/oschina/02-skill-vs-subagent.md) | [`examples/readme/02_skill_vs_subagent.py`](https://github.com/flower-trees/regnexe-py/blob/master/examples/readme/02_skill_vs_subagent.py) | 解析 Skill 与 Sub-Agent 在模型、工具、隔离性上的区别 |
| 03 | [PluginDescriptor：把 Tool、Skill、Sub-Agent 打包成一个业务插件](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/oschina/03-plugin-packaging.md) | [`examples/readme/03_plugin_packaging.py`](https://github.com/flower-trees/regnexe-py/blob/master/examples/readme/03_plugin_packaging.py) | 用 `PluginDescriptor.builder()` 打包 Tool、Skill、Sub-Agent，并通过 `with_plugin(...)` 注册 |
| 04 | [@plugin 装饰器设计：一个 Python 类注册多种 Agent 能力](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/oschina/04-plugin-decorator.md) | [`examples/readme/04_plugin_decorator.py`](https://github.com/flower-trees/regnexe-py/blob/master/examples/readme/04_plugin_decorator.py) | 用装饰器把普通 Python 类声明成插件能力 |
| 05 | [目录加载机制：plugin.yaml 和 SKILL.md 如何变成 Agent 能力](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/oschina/05-file-directory-loading.md) | [`examples/readme/05_file_directory_loading.py`](https://github.com/flower-trees/regnexe-py/blob/master/examples/readme/05_file_directory_loading.py) | 通过目录加载 `plugin.yaml` 和 `SKILL.md` |
| 06 | [能力市场换成数据库要改多少代码？regnexe-py 的 Marketplace 设计](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/oschina/06-marketplace.md) | [`examples/readme/06_marketplace.py`](https://github.com/flower-trees/regnexe-py/blob/master/examples/readme/06_marketplace.py) | 说明 Marketplace 接口如何支持自定义能力存储 |
| 07 | [会话记忆机制设计：regnexe-py 如何用 session_id 接住上下文](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/oschina/07-three-layer-memory.md) | [`examples/readme/07_three_layer_memory.py`](https://github.com/flower-trees/regnexe-py/blob/master/examples/readme/07_three_layer_memory.py) | 说明 session 记忆、当前轮状态和跨 session 摘要的边界 |
| 08 | [可观测性设计：regnexe-py 如何暴露 LLM 和工具调用事件](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/oschina/08-observability.md) | [`examples/readme/08_observability.py`](https://github.com/flower-trees/regnexe-py/blob/master/examples/readme/08_observability.py) | 说明事件监听器如何支持调试和生产观测 |
| 09 | [任务取消机制设计：regnexe-py 如何真正停止后端 Agent 运行](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/oschina/09-cancel-and-resume.md) | [`examples/readme/09_cancel_and_resume.py`](https://github.com/flower-trees/regnexe-py/blob/master/examples/readme/09_cancel_and_resume.py) | 说明 `acancel()` 如何取消运行中的后端 Agent 任务 |
