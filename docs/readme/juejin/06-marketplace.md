# 能力市场换成数据库要改多少代码？regnexe-py 只需要替换 Marketplace

> 「Regnexe Python 工程化系列」第 6 篇（共 10 篇），对应仓库 [`examples/readme/06_marketplace.py`](https://github.com/flower-trees/regnexe-py/blob/master/examples/readme/06_marketplace.py)。上一篇：[05. 插件不想重新发版？with_directory 让 SKILL.md 直接变成 Agent 能力](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/juejin/05-file-directory-loading.md)。

## 一个容易被忽略的架构问题

Agent Demo 里最常见的能力管理方式，就是启动时手写一个列表：

```python
tools = [get_weather, search_docs, query_order]
```

这在 Demo 里没问题。但到了平台型应用，能力可能来自不同业务线、不同租户、不同环境。你迟早会问：能力到底应该存在代码里、数据库里，还是配置中心里？

regnexe-py 的答案是：**Agent 不直接关心能力存在哪里，它只依赖 Marketplace 接口**。

## 默认实现：SimpleMarketplace

示例第一部分不跑 LLM，只演示市场的基本动作：安装、搜索、解析。

```python
marketplace = SimpleMarketplace()
marketplace.install(weather_plugin)

candidates = marketplace.search("Check today's weather in Beijing")
resolved = marketplace.resolve("weather-plugin.get_weather")
```

当前版本的 `search()` 很简单，主要是能力索引入口。以后你要按标签、关键词、向量召回优化，也是在这一层做。

## 自定义市场：假装背后是一张 DB 表

示例里写了一个 `InMemoryDbMarketplace`：

```python
class InMemoryDbMarketplace(SimpleMarketplace):
    def __init__(self) -> None:
        super().__init__()
        self.table: dict[str, PluginDescriptor] = {}

    def install(self, plugin: PluginDescriptor) -> None:
        self.table[plugin.plugin_id] = plugin
        super().install(plugin)

    def find_by_tag(self, tag: str) -> list[PluginDescriptor]:
        return [
            p for p in self.table.values()
            if any(tag in cap.tags for cap in p.capabilities)
        ]
```

真实项目里，`table` 可以换成 ORM、SQL 查询、配置中心或远程能力服务。

## 接入 Agent 不改主流程

换市场时，Agent 侧只改这一行：

```python
agent = (
    RegnexeAgentBuilder()
    .with_default_model(Vendor.DEEPSEEK, "deepseek-v4-flash")
    .with_marketplace(marketplace)
    .with_event_listener(ConsoleEventListener())
    .build()
)
```

这就是 Marketplace 的价值：能力管理怎么演进，不应该让 Agent 主流程跟着重写。

## 小结

Marketplace 解决的是能力治理问题：

- 能力统一安装和查询
- 能力 id 稳定可解析
- 能力来源可以从内存换成数据库
- 自定义查询方法可以服务管理后台
- Agent 构建逻辑不被存储细节污染

一句话：**能力市场不是一个列表，而是 Agent 应用的能力索引层**。

---

📌 上一篇：[05. 插件不想重新发版？with_directory 让 SKILL.md 直接变成 Agent 能力](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/juejin/05-file-directory-loading.md) ｜ 下一篇：[07. Agent 记不住上下文？别急着手写 history，先把 session_id 设计对](https://github.com/flower-trees/regnexe-py/blob/master/docs/readme/juejin/07-three-layer-memory.md)  
📌 项目地址：https://github.com/flower-trees/regnexe-py
