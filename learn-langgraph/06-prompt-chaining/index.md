---
layout: default
title: Prompt Chaining：分步生成
description: 把复杂生成任务拆成多个步骤，每个节点完善上一步的输出——以博客文章生成为例
eyebrow: learn-langgraph · 06
---

# Prompt Chaining：分步生成

一次性让 LLM 生成完整的长文内容，效果往往不理想——模型容易跑题，或者生成质量参差不齐。

**Prompt Chaining** 的思路是：把大任务拆成多个步骤，每个步骤用单独的 prompt，上一步的输出作为下一步的输入。每个节点专注一件事，最终串联出高质量的结果。

## 为什么要拆步骤

一次性生成 vs 分步生成的区别：

| 方式 | 优点 | 缺点 |
|------|------|------|
| 一次性生成 | 简单快速 | 长文质量不稳定，难以干预中间过程 |
| Prompt Chaining | 每步可控，中间结果可检查 | 多次 LLM 调用，耗时更长 |

分步生成适合需要**结构化输出**的场景：文章生成、报告撰写、代码生成等。

## 示例：博客文章三步生成

步骤：
1. **生成大纲**：给定主题，输出文章结构
2. **展开内容**：根据大纲，生成正文草稿
3. **润色优化**：改进语言，让文章更流畅

```
主题输入 --> [生成大纲] --> [展开内容] --> [润色优化] --> 最终文章
```

### 代码实现

这里用 HuggingFace 的 Mistral 模型作为示例，也可以替换成 OpenAI。

```python
from typing import TypedDict
from langgraph.graph import StateGraph, END

# ===== State =====
class BlogState(TypedDict):
    topic: str
    outline: str
    draft: str
    final_article: str

# ===== 节点（不依赖特定 LLM，方便你替换）=====

def generate_outline(state: BlogState) -> dict:
    """第一步：生成文章大纲"""
    topic = state["topic"]

    # 这里用占位符表示 LLM 调用，下面会展示真实代码
    prompt = f"""为以下主题创建一个清晰的博客文章大纲：

主题：{topic}

请提供：
1. 引言要点
2. 3-4 个主要章节标题
3. 结论要点

大纲："""

    # outline = llm.invoke(prompt)  # 替换成真实 LLM 调用
    # 示例输出（演示用）
    outline = f"""
## {topic} 完整指南

**引言**：介绍 {topic} 的背景和重要性

**第一章：基础概念**
- 核心定义
- 关键术语

**第二章：实现方式**
- 主流方案对比
- 最佳实践

**第三章：实战案例**
- 具体示例
- 常见问题

**结论**：总结要点，给出建议
""".strip()

    return {"outline": outline}

def expand_content(state: BlogState) -> dict:
    """第二步：根据大纲生成正文草稿"""
    outline = state["outline"]
    topic = state["topic"]

    prompt = f"""根据以下大纲，为主题"{topic}"写一篇详细的博客文章草稿。
每个章节至少写 2-3 段，包含具体示例。

大纲：
{outline}

文章草稿："""

    # draft = llm.invoke(prompt)  # 替换成真实 LLM 调用
    draft = f"""# {topic} 完整指南

## 引言

{topic} 是现代软件开发中的重要话题...（正文草稿）

## 基础概念

理解 {topic} 首先需要掌握几个核心概念...

## 实现方式

在实际项目中，有多种方式可以实现 {topic}...

## 实战案例

以下是一个典型的 {topic} 应用场景...

## 结论

通过本文的介绍，我们深入了解了 {topic} 的各个方面...
""".strip()

    return {"draft": draft}

def polish_article(state: BlogState) -> dict:
    """第三步：润色优化文章"""
    draft = state["draft"]

    prompt = f"""请对以下文章草稿进行润色，使其：
1. 语言更流畅自然
2. 逻辑更清晰
3. 适合技术博客读者

草稿：
{draft}

润色后的文章："""

    # final = llm.invoke(prompt)  # 替换成真实 LLM 调用
    final = draft + "\n\n---\n*（已润色优化）*"

    return {"final_article": final}

# ===== 组装图 =====

graph = StateGraph(BlogState)

graph.add_node("outline", generate_outline)
graph.add_node("expand", expand_content)
graph.add_node("polish", polish_article)

graph.set_entry_point("outline")
graph.add_edge("outline", "expand")
graph.add_edge("expand", "polish")
graph.add_edge("polish", END)

app = graph.compile()
```

### 运行

```python
result = app.invoke({
    "topic": "LangGraph 入门指南",
    "outline": "",
    "draft": "",
    "final_article": "",
})

print("=== 大纲 ===")
print(result["outline"])
print("\n=== 最终文章 ===")
print(result["final_article"])
```

### 用 stream 观察每一步

```python
for step in app.stream({
    "topic": "LangGraph 入门指南",
    "outline": "",
    "draft": "",
    "final_article": "",
}):
    node_name = list(step.keys())[0]
    print(f"\n--- [{node_name}] 完成 ---")
    if node_name == "outline":
        print(step["outline"]["outline"][:200])
    elif node_name == "expand":
        print(step["expand"]["draft"][:200])
    elif node_name == "polish":
        print("文章已润色完成")
```

## 接入真实 LLM

### 使用 OpenAI

```python
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

def generate_outline(state: BlogState) -> dict:
    topic = state["topic"]
    prompt = f"为主题'{topic}'创建博客大纲（3-4个章节）："

    response = llm.invoke([HumanMessage(content=prompt)])
    return {"outline": response.content}
```

### 使用 HuggingFace（Mistral）

```python
import os
from langchain_huggingface import HuggingFaceEndpoint

# 需要 HuggingFace API token
llm = HuggingFaceEndpoint(
    repo_id="mistralai/Mistral-7B-Instruct-v0.2",
    huggingfacehub_api_token=os.environ["HUGGINGFACEHUB_API_TOKEN"],
    task="text-generation",
    max_new_tokens=512,
    temperature=0.7,
)

def generate_outline(state: BlogState) -> dict:
    topic = state["topic"]
    prompt = f"[INST] 为主题'{topic}'创建博客大纲（3-4个章节）：[/INST]"

    response = llm.invoke(prompt)
    return {"outline": response}
```

### 两者可互换

LangGraph 里的 LLM 调用只在节点函数里，切换模型只需要修改节点内部——**图的结构完全不变**。这是 Prompt Chaining 模式的一个好处：执行逻辑和模型选择解耦。

## 中间结果检查

分步生成的另一个优势：可以在节点之间检查中间结果，决定是否继续。

```python
def check_outline_quality(state: BlogState) -> str:
    """检查大纲质量，决定是直接展开还是重新生成"""
    outline = state["outline"]

    # 简单检查：大纲是否包含足够的章节
    if outline.count("##") >= 3:
        return "expand"  # 质量够，继续展开
    else:
        return "regenerate_outline"  # 质量不够，重新生成

graph.add_conditional_edges(
    "outline",
    check_outline_quality,
    {
        "expand": "expand",
        "regenerate_outline": "outline",  # 循环回去重新生成
    }
)
```

这就把 Prompt Chaining 和条件分支结合起来了，形成一个**可以自我修正的生成循环**。

## 小结

Prompt Chaining 的要点：

- 把大任务拆成多个小步骤，每步一个节点
- 上一步的输出存到 state，下一步从 state 里读
- 每个节点的 prompt 只关注当前步骤，不用一次性解决所有问题
- 中间结果可以用条件分支检查质量，不满足就重跑
- LLM 只在节点函数里，切换模型不影响图结构

下一篇：在节点里直接接入 LLM 的详细用法：[接入 LLM：OpenAI 与 HuggingFace](../07-llm-integration/index.html)。
