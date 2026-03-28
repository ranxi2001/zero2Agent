---
layout: default
title: 条件分支：add_conditional_edges
description: 用路由函数实现条件跳转，结合情感分析案例演示 LangGraph 的 add_conditional_edges
eyebrow: learn-langgraph · 04
---

# 条件分支：add_conditional_edges

顺序图里每条边都是固定的：A 之后必须走 B。但真实的 Agent 需要根据运行结果决定下一步——用户反馈是正面的走一条路，负面的走另一条路。

LangGraph 用 `add_conditional_edges` 来处理这种情况。

## 核心 API

```python
graph.add_conditional_edges(
    "source_node",          # 从哪个节点出发
    routing_function,       # 路由函数：接收 state，返回下一个节点名
    {
        "route_a": "node_a",  # 路由函数返回 "route_a" 时，走 node_a
        "route_b": "node_b",  # 路由函数返回 "route_b" 时，走 node_b
        "end": END,           # 路由函数返回 "end" 时，结束
    }
)
```

路由函数就是一个普通 Python 函数：

```python
def routing_function(state: MyState) -> str:
    if state["some_condition"]:
        return "route_a"
    else:
        return "route_b"
```

它接收当前 state，返回一个**字符串 key**，LangGraph 用这个 key 从映射表里找到下一个节点。

## 示例：用户反馈路由

场景：客服系统收到用户反馈，根据情绪（正面/负面/中性）走不同的处理流程。

```
用户输入
  |
情绪分析
  |
  +-- 正面 --> 感谢回复
  |
  +-- 负面 --> 道歉 + 升级处理
  |
  +-- 中性 --> 标准回复
  |
最终格式化输出
```

### 实现

```python
from typing import TypedDict
from langgraph.graph import StateGraph, END

class FeedbackState(TypedDict):
    user_input: str
    sentiment: str      # "positive" / "negative" / "neutral"
    response: str
    final_output: str

# ===== 节点 =====

def analyze_sentiment(state: FeedbackState) -> dict:
    """情绪分析（简化版，实际可以用 LLM）"""
    text = state["user_input"].lower()

    positive_words = ["好", "棒", "满意", "喜欢", "excellent", "great", "happy"]
    negative_words = ["差", "烂", "不满", "投诉", "terrible", "bad", "angry"]

    pos_count = sum(1 for w in positive_words if w in text)
    neg_count = sum(1 for w in negative_words if w in text)

    if pos_count > neg_count:
        sentiment = "positive"
    elif neg_count > pos_count:
        sentiment = "negative"
    else:
        sentiment = "neutral"

    return {"sentiment": sentiment}

def handle_positive(state: FeedbackState) -> dict:
    """处理正面反馈"""
    response = f"感谢您的好评！很高兴我们的服务让您满意。您的反馈：'{state['user_input']}'"
    return {"response": response}

def handle_negative(state: FeedbackState) -> dict:
    """处理负面反馈"""
    response = (
        f"非常抱歉给您带来了不好的体验！"
        f"您的反馈已记录：'{state['user_input']}'。"
        f"我们的高级客服将在 24 小时内联系您。"
    )
    return {"response": response}

def handle_neutral(state: FeedbackState) -> dict:
    """处理中性反馈"""
    response = f"感谢您的反馈：'{state['user_input']}'。我们会继续改进服务。"
    return {"response": response}

def format_output(state: FeedbackState) -> dict:
    """格式化最终输出"""
    output = f"[情绪：{state['sentiment']}]\n{state['response']}"
    return {"final_output": output}

# ===== 路由函数 =====

def route_by_sentiment(state: FeedbackState) -> str:
    """根据情绪返回路由 key"""
    return state["sentiment"]  # 直接返回 "positive" / "negative" / "neutral"

# ===== 组装图 =====

graph = StateGraph(FeedbackState)

graph.add_node("analyze", analyze_sentiment)
graph.add_node("positive_handler", handle_positive)
graph.add_node("negative_handler", handle_negative)
graph.add_node("neutral_handler", handle_neutral)
graph.add_node("format", format_output)

graph.set_entry_point("analyze")

# 条件分支：analyze 之后根据 sentiment 走不同节点
graph.add_conditional_edges(
    "analyze",
    route_by_sentiment,
    {
        "positive": "positive_handler",
        "negative": "negative_handler",
        "neutral": "neutral_handler",
    }
)

# 三个分支最终都汇入 format
graph.add_edge("positive_handler", "format")
graph.add_edge("negative_handler", "format")
graph.add_edge("neutral_handler", "format")
graph.add_edge("format", END)

app = graph.compile()
```

### 运行

```python
# 正面反馈
r = app.invoke({
    "user_input": "产品很棒，服务也很满意！",
    "sentiment": "",
    "response": "",
    "final_output": ""
})
print(r["final_output"])
# [情绪：positive]
# 感谢您的好评！很高兴我们的服务让您满意。...

# 负面反馈
r = app.invoke({
    "user_input": "太差了，完全不满意，要投诉！",
    "sentiment": "",
    "response": "",
    "final_output": ""
})
print(r["final_output"])
# [情绪：negative]
# 非常抱歉给您带来了不好的体验！...
```

## 图结构

```
START
  |
analyze
  |
  +-- positive --> positive_handler --> format --> END
  |
  +-- negative --> negative_handler --> format --> END
  |
  +-- neutral  --> neutral_handler  --> format --> END
```

三条分支汇入同一个 format 节点——这叫 **Fan-out + Fan-in**，是多分支合并的标准模式。

## 配合 LLM 做情绪分析

实际项目里，`analyze_sentiment` 会调用 LLM：

```python
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

def analyze_sentiment(state: FeedbackState) -> dict:
    prompt = f"""分析以下文本的情绪，只回复 "positive"、"negative" 或 "neutral" 之一。

文本：{state['user_input']}"""

    response = llm.invoke([HumanMessage(content=prompt)])
    sentiment = response.content.strip().lower()

    # 容错处理
    if sentiment not in ["positive", "negative", "neutral"]:
        sentiment = "neutral"

    return {"sentiment": sentiment}
```

路由函数本身不需要改，它只看 state 里的 `sentiment` 字段。**节点负责更新状态，路由函数负责读状态做决策** ——这是 LangGraph 里关注点分离的核心思路。

## Pydantic 结构化输出

如果你想用 Pydantic 让 LLM 输出更可靠：

```python
from pydantic import BaseModel
from langchain_openai import ChatOpenAI

class SentimentOutput(BaseModel):
    sentiment: str     # "positive" / "negative" / "neutral"
    confidence: float  # 0.0 ~ 1.0
    reason: str        # 判断原因

llm = ChatOpenAI(model="gpt-4o-mini")
structured_llm = llm.with_structured_output(SentimentOutput)

def analyze_sentiment(state: FeedbackState) -> dict:
    result = structured_llm.invoke(
        f"分析情绪：{state['user_input']}"
    )
    return {
        "sentiment": result.sentiment,
        "confidence": result.confidence,
    }
```

`with_structured_output` 让 LLM 返回结构化的 Pydantic 对象，而不是纯文本。这样路由函数拿到的字段更可靠。

## 条件分支 vs if-else

你可能会问：直接在一个节点里写 if-else 不是一样的效果吗？

**技术上可以，但有缺点：**

1. **可见性**：`add_conditional_edges` 让图的结构可以被可视化，if-else 藏在函数里看不出来
2. **可测试性**：路由函数可以单独测试，不依赖完整的节点执行
3. **可维护性**：加一条新分支只需要加一个节点 + 在映射表里加一行，不用修改现有逻辑

## 小结

- `add_conditional_edges(source, routing_fn, mapping)` 是 LangGraph 的条件分支 API
- 路由函数返回字符串 key，mapping 表把 key 映射到节点名
- 路由函数只读 state，不做操作——决策和操作分离
- 多个分支可以汇入同一个节点（Fan-in）

下一篇：多个节点并行执行：[并行执行：Fan-out / Fan-in](../05-parallel-workflows/index.html)。
