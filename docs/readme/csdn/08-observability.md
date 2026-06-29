# Agent 答案错了怎么排查？先把 LLM 和工具调用事件打出来

> 「Regnexe Python 实战系列」第 8 篇（共 10 篇），对应仓库 [`examples/readme/08_observability.py`](https://github.com/flower-trees/regnexe-py/blob/master/examples/readme/08_observability.py)。上一篇：[07. Agent 记不住上下文？别再手写 history，先把 session_id 设计对](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/csdn/07-three-layer-memory.md)。

## 排查 Agent 问题最痛苦的地方

普通业务代码出错，看日志、看堆栈，大概率能定位。

Agent 不一样。最终回答错了，可能是模型没选对工具，可能是工具参数错了，可能是工具结果没被正确使用，也可能是某次 LLM 调用成本异常。

如果没有事件流，你看到的只有一句"答案不对"。

regnexe-py 的解法是：**把 Agent 生命周期、LLM 调用、工具调用、工具结果都做成事件**，通过 `AgentEventListener` 统一暴露，业务侧只管订阅。

## 默认模式：只看 Agent 骨架

`ConsoleEventListener()` 不带参数时，LLM 内部事件被过滤掉，只打印 Agent 启动、工具调用和完成：

```python
agent = (
    RegnexeAgentBuilder()
    .with_default_model(Vendor.DEEPSEEK, "deepseek-v4-flash")
    .with_plugin(WeatherPlugin())
    .with_event_listener(ConsoleEventListener())
    .build()
)
result = await agent.ainvoke(
    "Check today's weather in Beijing. Is it good for running?",
    app_id="readme", user_id="reader", session_id="08-observability-default",
)
```

实际输出：

```text
============================================================
[AGENT ▶] RegnexeAgent
          goal: Check today's weather in Beijing. Is it good for running?
[TOOL  ▶] mcp_tool:get_weather  input={"city": "Beijing"}
[TOOL  ■] mcp_tool:get_weather  output=Beijing: sunny, 22 C, excellent air quality.
[AGENT ■] status=completed
============================================================

Status : completed
Output : Beijing's weather today is **sunny, 22°C, with excellent air quality**.
         This is **ideal for running** ...
```

这几行已经回答了排查最常见的两个问题：

- **工具有没有被调用？** `[TOOL ▶]` 行说明模型确实选择了 `get_weather`。
- **参数和返回值是什么？** `input={"city": "Beijing"}` 和 `output=Beijing: sunny...` 一目了然。

如果这两行都正确，问题就出在模型对结果的处理上，排查方向就变了。

## 详细模式：看 LLM 调用全过程

默认模式看不到 LLM 被调用了几次、每次拿到什么消息、用了多少 token。加两个参数打开：

```python
ConsoleEventListener(show_llm_events=True, show_token_usage=True)
```

实际输出：

```text
============================================================
[AGENT ▶] RegnexeAgent
          goal: Check today's weather in Beijing. Is it good for running?

[LLM   ▶] ChatOpenAI
  [system] <7588 chars — set show_system_prompt=True to display>
  [human] Check today's weather in Beijing. Is it good for running?
[LLM   ■] ChatOpenAI  tokens={'input_tokens': 6041, 'output_tokens': 71,
           'total_tokens': 6112, 'input_token_details': {'cache_read': 6016},
           'output_token_details': {'reasoning': 26}}

[TOOL  ▶] mcp_tool:get_weather  input={"city": "Beijing"}
[TOOL  ■] mcp_tool:get_weather  output=Beijing: sunny, 22 C, excellent air quality.

[LLM   ▶] ChatOpenAI
  [system] <7588 chars — set show_system_prompt=True to display>
  [human] Check today's weather in Beijing. Is it good for running?
  [ai→tool_call] get_weather({"city": "Beijing"})
  [tool] (tool_call_id=call_00_feosLv17JcLfgOHqse9J6319) Beijing: sunny, 22 C, excellent air quality.
[LLM   ■] ChatOpenAI  tokens={'input_tokens': 6135, 'output_tokens': 190,
           'total_tokens': 6325, 'input_token_details': {'cache_read': 6016},
           'output_token_details': {'reasoning': 73}}
          → **Beijing Weather Today:** Sunny, 22°C, excellent air quality.
            **Verdict: Yes, it's great for running.** ...

[AGENT ■] status=completed
============================================================
```

这段输出信息密度很高，逐条解读：

**一次 `ainvoke()` 调了两次 LLM**

第一次：模型拿到用户问题，决定调 `get_weather` 工具（`output_tokens: 71`，只输出了一个 tool call）。  
第二次：模型拿到工具返回结果，组织最终答案（`output_tokens: 190`，输出完整回答）。

这个"两次 LLM 调用"的结构是 ReAct 模式的基本形态。如果你发现某次调用里 LLM 没有选工具，或者消息列表里缺少了 `[tool]` 行，问题就定位到了具体的哪一步。

**`cache_read: 6016`——系统提示在复用缓存**

第一次调用：`input_tokens: 6041`，其中 `cache_read: 6016`，说明 6016 个 token 从缓存命中。系统提示（7588 字符）大部分走了 prompt cache，没有重复计费。

第二次调用：`input_tokens: 6135`（多了工具消息），但 `cache_read` 仍然是 6016，系统提示继续复用。

这对成本排查很有用：如果 `cache_read` 一直是 0，意味着系统提示没有被缓存，每次都在全量计费。

**`reasoning: 26 / 73`——模型用了内部思考**

`output_token_details.reasoning` 是模型在给出输出前的内部推理 token（chain-of-thought）。  
第一次调用 reasoning 26 token，第二次 73 token。这些 token 计入成本，但通常不出现在最终回答里。如果 reasoning token 异常高，可能是模型在绕弯子，值得检查。

## 过滤规则可以直接查询

不用实际跑一次才知道某个事件会不会被打印，`should_handle()` 可以直接检查：

```python
quiet = ConsoleEventListener()
verbose = ConsoleEventListener(show_llm_events=True)

print(quiet.should_handle("AGENT_STARTED"))   # True
print(quiet.should_handle("LLM_START"))       # False
print(verbose.should_handle("LLM_START"))     # True
```

输出：

```text
quiet.should_handle('AGENT_STARTED')  -> True
quiet.should_handle('LLM_START')       -> False
verbose.should_handle('LLM_START')     -> True
```

`AGENT_STARTED` 两种模式都处理；`LLM_START` 默认被屏蔽，只有 `show_llm_events=True` 时才开放。这个接口适合在测试里断言监听器的过滤行为，不需要构造实际的 Agent 调用。

## 生产环境怎么做

生产环境通常不会直接打 stdout。继承 `AgentEventListener` 或 `AbstractEventListener`，把事件路由到需要的地方：

| 目标 | 用法 |
|---|---|
| JSON 结构化日志 | 在 `dispatch()` 里序列化事件写 logger |
| OpenTelemetry | 把 `AGENT_STARTED / AGENT_COMPLETED` 映射成 span |
| SSE 前端流 | 把 `TOOL_CALLED / TOOL_RESULT` 推给前端显示进度 |
| Token 成本统计 | 提取 `LLM_END` 事件的 `usage` 字段累加 |
| 审计表 | 把完整事件序列写入数据库 |

仓库里的 `examples/06_custom_event_listener.py` 和 `examples/07_streaming_api.py` 是贴近生产的参考实现。

## 小结

可观测性不是附加功能，而是 Agent 从 Demo 到应用必须补的一层。

一次 `ainvoke()` 背后可能有多次 LLM 调用、多次工具调用、缓存命中和 reasoning 消耗，靠最终答案根本看不出来。通过事件流，至少能回答：

- Agent 有没有开始执行，目标是什么？
- 工具选对了吗？参数和返回值是什么？
- LLM 被调了几次？每次 token 用量和缓存命中情况？
- reasoning token 是否异常？

两行代码的差距——默认模式看骨架，详细模式看全貌：

```python
ConsoleEventListener()                                      # 只看工具调用链
ConsoleEventListener(show_llm_events=True, show_token_usage=True)  # 看完整 LLM 流水
```

---

📌 上一篇：[07. Agent 记不住上下文？别再手写 history，先把 session_id 设计对](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/csdn/07-three-layer-memory.md) ｜ 下一篇：[09. 停止生成只停前端？后端 Agent 还在跑，acancel 才是真取消](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/csdn/09-cancel-and-resume.md)  
📌 项目地址：https://github.com/flower-trees/regnexe-py
