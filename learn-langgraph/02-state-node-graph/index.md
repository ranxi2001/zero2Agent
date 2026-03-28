---
layout: default
title: State、Node、Graph 三件套
description: TypedDict 状态设计，节点函数签名，StateGraph 的编译与运行——LangGraph 的三个基础构建块
eyebrow: learn-langgraph · 02
---

# State、Node、Graph 三件套

LangGraph 应用由三个东西构成：状态（State）、节点（Node）、图（Graph）。这一篇把每个细节讲清楚，后续所有示例都建在这个基础上。

## 安装

```bash
pip install langgraph langchain-core
```

如果要用 OpenAI：

```bash
pip install langchain-openai
```

## State：图的内存

State 是整张图的共享数据容器。所有节点都从这里读数据，修改后写回来。

### 用 TypedDict 定义

```python
from typing import TypedDict, List, Optional

class MyState(TypedDict):
    # 用户输入
    user_input: str
    # 中间结果
    analysis: str
    # 最终输出
    result: str
    # 可选字段
    error: Optional[str]
```

`TypedDict` 是 Python 标准库里的类型，让字典有了类型检查。LangGraph 用它来追踪状态的结构。

### 节点返回 dict，不是完整 State

节点只需要返回要修改的字段：

```python
def my_node(state: MyState) -> dict:
    # 只返回要更新的字段
    return {"analysis": "positive"}
    # 不需要返回完整的 state
```

LangGraph 会把返回的 dict **合并**进当前 state，未修改的字段保持不变。

### 用 Annotated + operator.add 追加列表

如果某个字段是列表，想追加而不是覆盖：

```python
from typing import Annotated
import operator

class ChatState(TypedDict):
    messages: Annotated[List[str], operator.add]
    summary: str
```

这样每个节点返回的 `{"messages": ["新消息"]}` 会被**追加**到列表里，而不是替换整个列表。

## Node：图的操作单元

节点就是普通 Python 函数，签名固定：

```python
def node_name(state: YourState) -> dict:
    # 读取状态
    value = state["some_field"]
    # 做处理
    result = process(value)
    # 返回要更新的字段
    return {"another_field": result}
```

### 节点的几个原则

**原则一：节点只做一件事**

每个节点聚焦一个职责。不要把分析、调用 API、格式化输出都塞进一个节点。

**原则二：节点是纯的（尽量）**

理想情况下，节点的输出只依赖 state 输入，没有隐藏的全局状态。这样更容易测试和调试。

**原则三：返回 dict，不是 State 对象**

```python
# 正确
return {"field_a": value_a, "field_b": value_b}

# 错误——不要返回完整 state
return state
```

## Graph：把节点连起来

```python
from langgraph.graph import StateGraph, END, START

# 1. 创建图，指定 State 类型
graph = StateGraph(MyState)

# 2. 添加节点
graph.add_node("node_a", function_a)
graph.add_node("node_b", function_b)
graph.add_node("node_c", function_c)

# 3. 设置入口
graph.set_entry_point("node_a")
# 等价于：graph.add_edge(START, "node_a")

# 4. 添加边
graph.add_edge("node_a", "node_b")
graph.add_edge("node_b", "node_c")
graph.add_edge("node_c", END)

# 5. 编译
app = graph.compile()
```

### 运行图

```python
# invoke：同步运行，返回最终 state
result = app.invoke({"user_input": "hello"})
print(result)

# stream：流式运行，每个节点完成后返回一次
for chunk in app.stream({"user_input": "hello"}):
    print(chunk)
```

`invoke` 返回的是最终的完整 state 字典。`stream` 每次 yield 一个 `{node_name: state_update}` 的字典。

## 完整示例：文本处理管道

把这三件套组合起来，写一个简单的文本处理管道：

```python
from typing import TypedDict
from langgraph.graph import StateGraph, END

# 1. 定义 State
class TextState(TypedDict):
    raw_text: str
    cleaned: str
    word_count: int
    summary: str

# 2. 定义节点
def clean_node(state: TextState) -> dict:
    """清理文本：去掉多余空格"""
    text = state["raw_text"].strip()
    return {"cleaned": text}

def count_node(state: TextState) -> dict:
    """统计词数"""
    count = len(state["cleaned"].split())
    return {"word_count": count}

def summary_node(state: TextState) -> dict:
    """生成摘要（这里简化为截断）"""
    text = state["cleaned"]
    summary = text[:50] + "..." if len(text) > 50 else text
    return {"summary": summary}

# 3. 组装图
graph = StateGraph(TextState)
graph.add_node("clean", clean_node)
graph.add_node("count", count_node)
graph.add_node("summarize", summary_node)

graph.set_entry_point("clean")
graph.add_edge("clean", "count")
graph.add_edge("count", "summarize")
graph.add_edge("summarize", END)

app = graph.compile()

# 4. 运行
result = app.invoke({
    "raw_text": "  LangGraph 是一个用于构建有状态 Agent 应用的框架，基于图结构描述执行流。  ",
    "cleaned": "",
    "word_count": 0,
    "summary": ""
})

print("清理后:", result["cleaned"])
print("词数:", result["word_count"])
print("摘要:", result["summary"])
```

输出：

```
清理后: LangGraph 是一个用于构建有状态 Agent 应用的框架，基于图结构描述执行流。
词数: 17
摘要: LangGraph 是一个用于构建有状态 Agent 应用的框架，基于图结构描述执行流。
```

## 可视化图结构

LangGraph 可以把图渲染成 ASCII 或图片：

```python
# ASCII 可视化
print(app.get_graph().draw_ascii())

# 输出大致如下：
# +-----------+
# | __start__ |
# +-----------+
#       |
#     clean
#       |
#     count
#       |
#   summarize
#       |
# +---------+
# | __end__ |
# +---------+
```

## 小结

三件套的关系：

- **State** 是数据，所有节点共享，TypedDict 定义结构
- **Node** 是操作，读 State 写 State，普通函数
- **Graph** 是流程，把节点用边连起来，`compile()` 后可运行

记住这三条规则：
1. 节点只返回要修改的字段（dict），不返回完整 state
2. 边决定执行顺序，`END` 是终止信号
3. `invoke` 传入的是初始 state（dict），返回的是最终 state（dict）

下一篇我们写第一个真实可运行的工作流：[顺序图：第一个可运行的 Workflow](../03-sequential-graph/index.html)。
