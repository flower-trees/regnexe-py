# 停止生成不能只停前端：Python Agent 后端任务也要能取消

> 「Regnexe Python 工程化系列」第 9 篇（共 10 篇），对应仓库 [`examples/readme/09_cancel_and_resume.py`](https://github.com/flower-trees/regnexe-py/blob/master/examples/readme/09_cancel_and_resume.py)。上一篇：[08. Agent 答案错了怎么查？先把 LLM 和工具调用事件打出来](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/juejin/08-observability.md)。

## 一个产品里绕不开的需求

只要你做过聊天式 Agent，就一定会遇到“停止生成”按钮。

很多实现只是把前端流断开，用户看起来停止了，但后端任务还在跑：模型还在输出，工具还在执行，账单还在增加。

regnexe-py 的 `acancel()` 解决的是后端任务取消：按 `app_id / user_id / session_id` 找到正在运行的 Agent 任务，并请求取消。

## 实战代码：先启动一个慢工具

示例里故意做了一个慢工具：

```python
@plugin(id="reports", name="Reports Plugin")
class ReportsPlugin:
    @agent_tool("Generate a financial report for a topic. Takes a while to run.", tags=["reports"])
    def generate_report(self, topic: str) -> str:
        time.sleep(6)
        return f"Report on {topic}: revenue up 12% quarter-over-quarter."
```

为了确定工具真的开始执行，示例还写了一个监听器：

```python
class ToolStartListener(ConsoleEventListener):
    def __init__(self, tool_started: asyncio.Event) -> None:
        super().__init__()
        self._tool_started = tool_started

    async def on_event(self, event_type: str, name: str, data: dict[str, Any]) -> None:
        await super().on_event(event_type, name, data)
        if event_type == "TOOL_CALLED":
            self._tool_started.set()
```

这个 `asyncio.Event` 用来避免靠 `sleep` 猜时机。

## 关键点：ainvoke 要放到独立 Task 里

取消要并发触达正在运行的任务，所以示例这样启动：

```python
run = asyncio.create_task(
    agent.ainvoke(
        "Generate a financial report on Q2 sales.",
        app_id="readme", user_id="reader", session_id=session_id,
    )
)
```

等工具开始后，调用：

```python
cancelled = await agent.acancel(
    app_id="readme", user_id="reader", session_id=session_id,
)
```

被取消的运行不会直接把异常抛给业务层，而是返回：

```python
AgentResult(status="cancelled")
```

这对 API 层很友好。你可以把状态明确返回给前端，而不是让一次取消变成 500 错误。

## 继续执行：同一个 session 再调用

示例第二阶段没有调用特殊的 `resume()`，而是对同一个 `session_id` 发起普通 `ainvoke()`：

```python
result2 = await agent.ainvoke(
    "Please go ahead and finish generating that report.",
    app_id="readme", user_id="reader", session_id=session_id,
)
```

原因是这里没有人工审批卡点，只是用户主动取消。LangGraph 已经在完成步骤后保存 checkpoint，同一个 session 可以继续推进。

如果是人工审批式中断，那是另一个 API：`aresume()`。仓库顶层 `examples/10_interrupt_example.py` 专门演示这个场景。

## 小结

`acancel()` 适合这些产品交互：

- 聊天框停止生成
- 用户取消长报告生成
- 前端页面关闭后终止后端 Agent 任务
- 任务耗时过长时主动停止

记住两个关键点：

- 运行中的 `ainvoke()` 要放在独立 `asyncio.Task` 里
- 取消要用同一组 `app_id / user_id / session_id` 定位任务

到这里，regnexe-py 的 9 个 README 示例就串完了：从 `with_tool` 快速接入，到 Skill/Sub-Agent、插件、目录加载、Marketplace、记忆、事件，再到取消与继续。它们解决的不是“怎么调一次模型”，而是“怎么把 Agent 做成一个能接业务系统的 Python 应用”。

---

📌 上一篇：[08. Agent 答案错了怎么查？先把 LLM 和工具调用事件打出来](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/juejin/08-observability.md) ｜ 系列开篇：[00. 别再把 Python Agent 写成 Demo 了：插件、记忆、事件、取消都得管起来](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/juejin/00-intro.md)  
📌 项目地址：https://github.com/flower-trees/regnexe-py
