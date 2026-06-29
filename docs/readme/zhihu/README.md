# Regnexe Python 设计札记（知乎文章，共 10 篇）

这组文章用于发布到知乎，写法偏问题讨论和工程判断：少一点“教程式罗列”，多一点为什么、边界在哪里、什么时候值得用。

- 项目地址：https://github.com/flower-trees/regnexe-py
- 发布目录：`docs/readme/zhihu/`
- 写作结构：问题切入 -> 设计取舍 -> 关键代码 -> 边界说明 -> 上下篇导航
- 内容原则：标题要有讨论性，但不夸大实现；尤其是会话记忆、Marketplace、取消任务，按当前代码能力说明。

| # | 文章 | 对应示例 | 讨论点 |
|---|---|---|---|
| 00 | [为什么很多 Python Agent Demo，一进业务系统就开始失控？](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/zhihu/00-intro.md) | 系列开篇 | 讨论为什么 Agent Demo 进入业务系统后会失控 |
| 01 | [Python Agent 接工具，真的一开始就需要插件体系吗？](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/zhihu/01-multi-tool.md) | [`examples/readme/01_multi_tool.py`](https://github.com/flower-trees/regnexe-py/blob/master/examples/readme/01_multi_tool.py) | 讨论快速接工具和完整插件体系之间的取舍 |
| 02 | [Agent 里的 Skill 和 Sub-Agent，本质区别到底是什么？](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/zhihu/02-skill-vs-subagent.md) | [`examples/readme/02_skill_vs_subagent.py`](https://github.com/flower-trees/regnexe-py/blob/master/examples/readme/02_skill_vs_subagent.py) | 讨论 Skill 和 Sub-Agent 的共享/隔离边界 |
| 03 | [Agent 能力为什么需要被打包成插件？](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/zhihu/03-plugin-packaging.md) | [`examples/readme/03_plugin_packaging.py`](https://github.com/flower-trees/regnexe-py/blob/master/examples/readme/03_plugin_packaging.py) | 讨论为什么能力需要稳定 id 和插件边界 |
| 04 | [普通 Python 类，能不能直接变成 Agent 插件？](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/zhihu/04-plugin-decorator.md) | [`examples/readme/04_plugin_decorator.py`](https://github.com/flower-trees/regnexe-py/blob/master/examples/readme/04_plugin_decorator.py) | 讨论普通 Python 类如何低成本进入 Agent 能力体系 |
| 05 | [Agent 能力一定要写进代码里吗？](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/zhihu/05-file-directory-loading.md) | [`examples/readme/05_file_directory_loading.py`](https://github.com/flower-trees/regnexe-py/blob/master/examples/readme/05_file_directory_loading.py) | 讨论代码能力和文件型能力的边界 |
| 06 | [能力市场换成数据库，对 Agent 架构意味着什么？](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/zhihu/06-marketplace.md) | [`examples/readme/06_marketplace.py`](https://github.com/flower-trees/regnexe-py/blob/master/examples/readme/06_marketplace.py) | 讨论能力市场替换成数据库时的架构含义 |
| 07 | [Agent 的会话记忆，为什么不能只靠一个 history？](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/zhihu/07-three-layer-memory.md) | [`examples/readme/07_three_layer_memory.py`](https://github.com/flower-trees/regnexe-py/blob/master/examples/readme/07_three_layer_memory.py) | 讨论当前会话记忆机制的真实边界 |
| 08 | [Agent 系统出问题怎么排查？先聊可观测性设计](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/zhihu/08-observability.md) | [`examples/readme/08_observability.py`](https://github.com/flower-trees/regnexe-py/blob/master/examples/readme/08_observability.py) | 讨论 Agent 黑盒问题和事件可观测性 |
| 09 | [聊天框里的「停止生成」，到底应该停掉什么？](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/zhihu/09-cancel-and-resume.md) | [`examples/readme/09_cancel_and_resume.py`](https://github.com/flower-trees/regnexe-py/blob/master/examples/readme/09_cancel_and_resume.py) | 讨论停止生成在后端任务层面的含义 |
