# Regnexe Python 实战系列（CSDN 文章，共 10 篇）

这组文章用于发布到 CSDN，目标是吸引对 Agent 工程化感兴趣的开发者：标题突出痛点和收益，正文保留可运行代码、运行日志、设计边界和踩坑提醒。

- 项目地址：https://github.com/flower-trees/regnexe-py
- 发布目录：`docs/readme/csdn/`
- 文章结构：痛点场景 -> 实战代码 -> 运行效果 / 关键点 -> 踩坑提醒 / 小结 -> 上下篇导航
- 内容原则：标题可以强，但实现不夸大；尤其是会话记忆、Marketplace、取消任务，按当前代码能力说明边界。

| # | 文章 | 对应示例 | 核心卖点 |
|---|---|---|---|
| 00 | [别再把 Python Agent 写成 Demo 了！我开源了一个能管插件、记忆、事件、取消的框架](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/csdn/00-intro.md) | 系列开篇 | 从 Demo 痛点切入，说明 regnexe-py 为什么要管插件、记忆、事件和取消 |
| 01 | [10 行代码跑通 LLM 多工具调用！不用插件、不建类，with_tool 直接上手](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/csdn/01-multi-tool.md) | [`examples/readme/01_multi_tool.py`](https://github.com/flower-trees/regnexe-py/blob/master/examples/readme/01_multi_tool.py) | `with_tool(...)` 快速接入多个 LangChain tool，并用事件日志看清调用过程 |
| 02 | [Skill 和 Sub-Agent 到底差在哪？一个借工具，一个有私有工具](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/csdn/02-skill-vs-subagent.md) | [`examples/readme/02_skill_vs_subagent.py`](https://github.com/flower-trees/regnexe-py/blob/master/examples/readme/02_skill_vs_subagent.py) | 讲清 Skill 借工具/继承模型，Sub-Agent 拥有私有工具/独立模型 |
| 03 | [Tool、Skill、Sub-Agent 散成一地？PluginDescriptor 一次打成业务插件](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/csdn/03-plugin-packaging.md) | [`examples/readme/03_plugin_packaging.py`](https://github.com/flower-trees/regnexe-py/blob/master/examples/readme/03_plugin_packaging.py) | 用 `PluginDescriptor.builder()` 打包混合能力，并通过 `with_plugin(...)` 注册 |
| 04 | [一个 Python 类，一次注册，搞定 2 个工具 + 1 个 Skill + 1 个 Sub-Agent](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/csdn/04-plugin-decorator.md) | [`examples/readme/04_plugin_decorator.py`](https://github.com/flower-trees/regnexe-py/blob/master/examples/readme/04_plugin_decorator.py) | 一个普通 Python 类一次注册工具、Skill、Sub-Agent |
| 05 | [改个 Skill 文案也要重新发版？with_directory 让插件目录直接生效](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/csdn/05-file-directory-loading.md) | [`examples/readme/05_file_directory_loading.py`](https://github.com/flower-trees/regnexe-py/blob/master/examples/readme/05_file_directory_loading.py) | 用 `with_directory(...)` 从 `plugin.yaml` 和 `SKILL.md` 加载文件型能力 |
| 06 | [能力市场换成数据库要改多少代码？regnexe-py 一个 Marketplace 搞定](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/csdn/06-marketplace.md) | [`examples/readme/06_marketplace.py`](https://github.com/flower-trees/regnexe-py/blob/master/examples/readme/06_marketplace.py) | 说明 Marketplace 是能力索引层，可替换成自定义存储 |
| 07 | [Agent 记不住上下文？别再手写 history，先把 session_id 设计对](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/csdn/07-three-layer-memory.md) | [`examples/readme/07_three_layer_memory.py`](https://github.com/flower-trees/regnexe-py/blob/master/examples/readme/07_three_layer_memory.py) | 说明当前记忆机制：当前轮依赖底层图状态，同 session 由 checkpointer 接住，跨 session 只做轻量任务摘要 |
| 08 | [Agent 答案错了怎么排查？先把 LLM 和工具调用事件打出来](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/csdn/08-observability.md) | [`examples/readme/08_observability.py`](https://github.com/flower-trees/regnexe-py/blob/master/examples/readme/08_observability.py) | 用 `ConsoleEventListener` 暴露 Agent、LLM、Tool 事件，排查黑盒问题 |
| 09 | [停止生成只停前端？后端 Agent 还在跑，acancel 才是真取消](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/csdn/09-cancel-and-resume.md) | [`examples/readme/09_cancel_and_resume.py`](https://github.com/flower-trees/regnexe-py/blob/master/examples/readme/09_cancel_and_resume.py) | 用 `acancel()` 取消运行中的后端 Agent 任务，并基于同 session 继续 |
