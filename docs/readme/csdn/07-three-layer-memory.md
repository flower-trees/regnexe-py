# Agent 记不住上下文？别再手写 history，先把 session_id 设计对

> 「Regnexe Python 实战系列」第 7 篇（共 10 篇），对应仓库 [`examples/readme/07_three_layer_memory.py`](https://github.com/flower-trees/regnexe-py/blob/master/examples/readme/07_three_layer_memory.py)。上一篇：[06. 能力市场换成数据库要改多少代码？regnexe-py 一个 Marketplace 搞定](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/csdn/06-marketplace.md)。

## 问题的起点

Agent 调用一次完整地回答了问题。下次继续聊，它还记得上次说了什么吗？

这不是一个可以靠"塞进 history 列表"来解决的问题——谁来裁剪？裁多少？超出上下文怎么办？regnexe-py 把这些事情交给了底层架构来处理，而不是在业务代码里手动维护。

## 会话如何挂载到线程

每次 `ainvoke()` 都会传三个身份字段：

```python
result = await agent.ainvoke(
    "Check today's weather in Beijing.",
    app_id="readme", user_id="reader", session_id="07-memory-a",
)
```

内部会把它们拼成 LangGraph 的 `thread_id`：

```text
readme:reader:07-memory-a
```

checkpointer（默认 `MemorySaver`）以这个 thread_id 为键，存取图的完整运行状态。同一个 `session_id` 的多次调用落在同一条线程上；换 `session_id` 就是全新线程，没有任何历史。

## 消息是怎么积累的

deepagents 的图状态（`DeepAgentState`）里有一个 `messages` 字段，类型是 `DeltaChannel`——每次图节点执行只写入增量，每 50 次才做一次完整快照，从 O(N²) 降到 O(N) 的存储开销。

同一 session 下连续两次 `ainvoke()`，消息会持续追加：

```
第 1 次调用（问天气）：
  HumanMessage("Check today's weather in Beijing...")
  AIMessage(tool_calls=[{name: "get_weather", args: {"city": "Beijing"}}])
  ToolMessage("Beijing: sunny, 22 C, excellent air quality.")
  AIMessage("Yes, today is great for outdoor running.")

第 2 次调用（追问，同 session_id）：
  HumanMessage("Based on the weather you just looked up...")
  AIMessage("Since it's sunny and 22°C, here are a few tips...")
```

LangGraph 在第二次调用前自动恢复线程状态，模型拿到的是完整的对话历史，不需要业务层做任何额外处理。

示例里验证这个行为只需保持 `session_id` 不变：

```python
# Turn 1: tool is called
result1 = await agent.ainvoke(
    "Check today's weather in Beijing and tell me if it's good for outdoor running.",
    app_id="readme", user_id="reader", session_id="07-memory-a",
)

# Turn 2: model already knows the weather, no tool re-call needed
result2 = await agent.ainvoke(
    "Based on the weather you just looked up, what should I keep in mind while running? "
    "No need to check the weather again.",
    app_id="readme", user_id="reader", session_id="07-memory-a",
)
```

## 上下文压缩：SummarizationMiddleware

消息无限积累必然撑爆模型的 context window。deepagents 默认内置了 `SummarizationMiddleware`，它的触发逻辑是：

- 有模型 profile（知道 max_input_tokens）：token 用量达到 **85%** 时压缩，保留最近 **10%** 的窗口
- 无 profile：超过 **170,000 tokens** 时压缩，保留最近 **6 条**消息

触发后，它做三件事：

1. 把旧消息用 LLM 压缩成一段摘要
2. 把原始消息卸载到后端（`/conversation_history/{thread_id}.md`），方便 agent 之后用 `read_file` 查看
3. 在私有状态字段 `_summarization_event` 里记录 `{cutoff_index, summary_message, file_path}`

**关键设计**：`state["messages"]` 里的原始消息**永远不会被删除**。只有发给 LLM 的那一份视图被替换成 `[summary_message] + messages[cutoff:]`。这样 checkpoint 里的完整日志可以用于 replay 和 eval，不因压缩而丢失。

## 可替换点

### 替换 checkpointer——持久化会话

默认的 `MemorySaver` 在进程重启后丢失所有会话。换成持久化后端：

```python
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

async with AsyncSqliteSaver.from_conn_string("sessions.db") as checkpointer:
    agent = (
        RegnexeAgentBuilder()
        .with_default_model(Vendor.DEEPSEEK, "deepseek-v4-flash")
        .with_plugin(WeatherPlugin())
        .with_checkpointer(checkpointer)
        .build()
    )
```

换 checkpointer 不影响业务代码里的 `app_id / user_id / session_id` 用法，线程映射逻辑完全不变。

### 替换 SummarizationMiddleware——控制压缩时机

默认触发阈值对大多数场景够用。如果需要更早压缩（比如控制成本）或调整保留窗口：

```python
from deepagents.middleware.summarization import SummarizationMiddleware
from deepagents.backends import StateBackend

summ = SummarizationMiddleware(
    model=my_model,
    backend=StateBackend(),
    trigger=("tokens", 60_000),   # 6 万 token 时就压缩
    keep=("messages", 10),        # 保留最近 10 条
)

agent = (
    RegnexeAgentBuilder()
    .with_default_model(Vendor.DEEPSEEK, "deepseek-v4-flash")
    .with_plugin(WeatherPlugin())
    .with_middleware(summ)
    .build()
)
```

`with_middleware()` 把自定义 middleware 追加到 deepagents 的 middleware 栈，传给 `create_deep_agent(middleware=...)`。如果同时注册了和默认栈相同类型的 middleware，需要通过 deepagents 的 `HarnessProfile.excluded_middleware` 先移除默认的——这属于进阶用法，通常只覆写触发参数就够了。

## 小结

| 关注点 | 机制 | 可替换 |
|---|---|---|
| 会话线程映射 | `app_id:user_id:session_id` → `thread_id` | 不需要替换 |
| 消息持久化 | LangGraph checkpointer（默认 MemorySaver） | `with_checkpointer()` |
| 消息存储结构 | `DeltaChannel`，只存增量，O(N) 开销 | 内部实现，不暴露 |
| 上下文压缩 | `SummarizationMiddleware`（内置，按 token 比例触发） | `with_middleware()` |
| 原始消息保留 | `state["messages"]` 永远不被截断 | 内部设计 |

regnexe-py 不重新实现这些机制，而是把 `app_id / user_id / session_id` 的业务身份体系接到 deepagents / LangGraph 的状态管理上，让架构替你管记忆。

---

📌 上一篇：[06. 能力市场换成数据库要改多少代码？regnexe-py 一个 Marketplace 搞定](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/csdn/06-marketplace.md) ｜ 下一篇：[08. Agent 答案错了怎么排查？先把 LLM 和工具调用事件打出来](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/csdn/08-observability.md)  
📌 项目地址：https://github.com/flower-trees/regnexe-py
