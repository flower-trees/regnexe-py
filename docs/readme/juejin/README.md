# Regnexe Python 工程化系列（掘金文章，共 10 篇）

这组文章用于发布到掘金，目标是“能吸引点击，也能经得起工程读者细看”：标题强调痛点和收益，正文保留可运行代码、运行日志、设计边界和踩坑提醒。

- 项目地址：https://github.com/flower-trees/regnexe-py
- 发布目录：`docs/readme/juejin/`
- 写作结构：强痛点开场 -> 关键代码 -> 运行效果 / 设计关键点 -> 踩坑提醒 -> 小结与上下篇导航
- 内容原则：可以有传播钩子，但不夸大当前实现能力；尤其是会话记忆、Marketplace、取消任务这些部分，按代码现状说明边界。

| # | 文章 | 对应示例 | 核心卖点 |
|---|---|---|---|
| 00 | [别再把 Python Agent 写成 Demo 了：插件、记忆、事件、取消都得管起来](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/juejin/00-intro.md) | 系列开篇 | 说明 Python Agent 从 Demo 走向应用时，为什么需要插件、记忆、事件和取消控制 |
| 01 | [别一上来就造插件！Python Agent 多工具调用先用 with_tool 跑通](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/juejin/01-multi-tool.md) | [`examples/readme/01_multi_tool.py`](https://github.com/flower-trees/regnexe-py/blob/master/examples/readme/01_multi_tool.py) | 先用 `with_tool(...)` 接入多个 LangChain tool，并通过事件日志确认调用链路 |
| 02 | [Skill 还是 Sub-Agent？Python Agent 子任务拆错了真的很难维护](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/juejin/02-skill-vs-subagent.md) | [`examples/readme/02_skill_vs_subagent.py`](https://github.com/flower-trees/regnexe-py/blob/master/examples/readme/02_skill_vs_subagent.py) | 讲清 Skill 共享模型/工具，Sub-Agent 隔离模型/私有工具 |
| 03 | [Tool、Skill、Sub-Agent 越写越散？用 PluginDescriptor 打成一个插件](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/juejin/03-plugin-packaging.md) | [`examples/readme/03_plugin_packaging.py`](https://github.com/flower-trees/regnexe-py/blob/master/examples/readme/03_plugin_packaging.py) | 用 `PluginDescriptor.builder()` 打包混合能力，并通过 `with_plugin(...)` 注册 |
| 04 | [给普通 Python 类加几个装饰器，就能变成 Agent 插件](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/juejin/04-plugin-decorator.md) | [`examples/readme/04_plugin_decorator.py`](https://github.com/flower-trees/regnexe-py/blob/master/examples/readme/04_plugin_decorator.py) | 用 `@plugin` 系列装饰器把普通 Python 类变成业务插件 |
| 05 | [不想为一个 Skill 改文案就发版？with_directory 这条路很实用](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/juejin/05-file-directory-loading.md) | [`examples/readme/05_file_directory_loading.py`](https://github.com/flower-trees/regnexe-py/blob/master/examples/readme/05_file_directory_loading.py) | 用 `plugin.yaml` 和 `SKILL.md` 做文件型能力加载，降低发版成本 |
| 06 | [能力市场换成数据库要改多少代码？regnexe-py 只需要替换 Marketplace](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/juejin/06-marketplace.md) | [`examples/readme/06_marketplace.py`](https://github.com/flower-trees/regnexe-py/blob/master/examples/readme/06_marketplace.py) | 说明 Marketplace 如何解耦能力来源和 Agent 主流程 |
| 07 | [Agent 记不住上下文？别急着手写 history，先把 session_id 设计对](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/juejin/07-three-layer-memory.md) | [`examples/readme/07_three_layer_memory.py`](https://github.com/flower-trees/regnexe-py/blob/master/examples/readme/07_three_layer_memory.py) | 准确说明当前轮状态、同 session 记忆、跨 session 任务摘要的能力边界 |
| 08 | [Agent 答案错了别靠猜：先把 LLM 和工具调用事件打出来](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/juejin/08-observability.md) | [`examples/readme/08_observability.py`](https://github.com/flower-trees/regnexe-py/blob/master/examples/readme/08_observability.py) | 用事件监听器暴露 Agent、LLM、Tool 调用，解决黑盒排查问题 |
| 09 | [停止生成不能只停前端：Python Agent 后端任务也要能取消](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/juejin/09-cancel-and-resume.md) | [`examples/readme/09_cancel_and_resume.py`](https://github.com/flower-trees/regnexe-py/blob/master/examples/readme/09_cancel_and_resume.py) | 用 `acancel()` 真正取消后端 Agent 任务，并基于同 session 继续 |
