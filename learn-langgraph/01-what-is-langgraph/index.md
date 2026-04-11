---
layout: default
title: LangGraph 是什么，为什么不用链式调用
description: 链式调用的局限，LangGraph 的图结构抽象，以及什么时候该用 LangGraph
eyebrow: learn-langgraph · 01
---

# LangGraph 是什么，为什么不用链式调用

## 链式调用能做什么，做不到什么

最早大家写 LLM 应用是这样的：

```python
response1 = llm.invoke(prompt1)
response2 = llm.invoke(prompt2 + response1.content)
response3 = llm.invoke(prompt3 + response2.content)
```

这叫**链式调用（Chain）**。简单，直观，能跑通 80% 的 Demo。

但一旦业务复杂起来，问题就来了：

**问题一：没有条件分支**

```python
# 如果想根据情绪走不同分支，代码变成这样：
sentiment = analyze_sentiment(user_input)
if sentiment == "positive":
    response = positive_handler(user_input)
elif sentiment == "negative":
    response = negative_handler(user_input)
else:
    response = neutral_handler(user_input)
# 再加一个分支？再加一层 if-else
```

代码开始膨胀，而且每次改分支逻辑都要找对位置修改。

**问题二：没有循环和重试**

如果某个步骤失败了，想重试怎么办？链式调用里你只能手写 `while True` 然后 `break`，状态要自己传来传去。

**问题三：状态管理混乱**

链式调用里，数据通过变量传递。一旦有多个分支、多个节点，你需要手动决定“哪个变量传给哪个步骤”，代码的全局状态变成了隐式依赖。

## LangGraph 的核心思路

LangGraph 的回答是：**把执行流描述成一张图（Graph）**。

```
节点（Node）= 一个操作（函数）
边（Edge）  = 节点之间的转移
状态（State）= 贯穿整张图的数据容器
```

执行过程就是：从起点出发，按边走过各个节点，每个节点读取状态、修改状态，最终到达终点。

用图来描述逻辑，有几个好处：

1. **条件分支变成路由函数**——不是 if-else，而是一个返回“下一个节点名”的函数
2. **循环变成图里的环**——节点可以指回之前的节点，天然支持重试和迭代
3. **状态是显式的**——所有节点共享同一个状态对象，谁改了什么一目了然
4. **可视化**——图结构可以直接画出来，方便理解和调试

## 三个核心概念

### State（状态）

用 Python 的 `TypedDict` 定义，是整张图的“内存”：

```python
from typing import TypedDict

class AgentState(TypedDict):
    user_input: str
    sentiment: str
    reply: str
```

图里的每个节点都接收这个 state，修改后返回新的 state。

### Node（节点）

普通的 Python 函数，签名是 `(state: State) -> dict`：

```python
def analyze_node(state: AgentState) -> dict:
    # 读取状态
    text = state["user_input"]
    # 做处理
    sentiment = "positive" if "好" in text else "negative"
    # 返回要更新的字段
    return {"sentiment": sentiment}
```

返回的 dict 会被合并进全局 state，不需要返回完整的 state 对象。

### Graph（图）

把节点和边组装起来：

```python
from langgraph.graph import StateGraph, END

graph = StateGraph(AgentState)
graph.add_node("analyze", analyze_node)
graph.add_node("reply", reply_node)

graph.set_entry_point("analyze")
graph.add_edge("analyze", "reply")
graph.add_edge("reply", END)

app = graph.compile()
```

`compile()` 之后得到一个可执行的 `app`，用 `invoke` 运行：

```python
result = app.invoke({"user_input": "今天心情很好"})
print(result)
```

## 和链式调用对比

| 维度 | 链式调用 | LangGraph |
|------|----------|-----------|
| 分支逻辑 | if-else 散落在代码里 | `add_conditional_edges` 集中管理 |
| 循环/重试 | 手写 while，状态容易乱 | 图里直接连回去 |
| 状态管理 | 变量传递，隐式依赖 | TypedDict，显式且类型安全 |
| 可维护性 | 流程越复杂越难改 | 改节点不影响其他节点 |
| 调试 | print 大法 | 可可视化图结构，节点独立测试 |

## 什么时候用 LangGraph

**适合用 LangGraph 的场景：**

- 执行流有条件分支（根据 LLM 输出决定走哪条路）
- 需要循环迭代（Agent 反复调用工具直到完成）
- 多个 Agent 协作（每个 Agent 是一个节点）
- 需要 human-in-the-loop（暂停等待人工确认）
- 需要错误恢复和重试

**不一定需要 LangGraph 的场景：**

- 单次 LLM 调用
- 固定的线性流程（prompt → response → done）
- 非常简单的两步 chain

## 小结

LangGraph 解决的核心问题是：**当 Agent 的执行逻辑变复杂之后，怎么让代码还能维护**。

它不是万能的，简单场景用链式调用更快。但一旦你的 Agent 需要分支、循环、或者多个子任务协作，LangGraph 的图结构会让你省很多力气。

下一篇我们动手写代码：[State、Node、Graph 三件套](../02-state-node-graph/index.html)。
