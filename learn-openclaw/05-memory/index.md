---
layout: default
title: Context 与 Memory
description: 短期上下文 + 长期压缩摘要，不需要向量数据库
eyebrow: OpenClaw / 05
---

# Context 与 Memory

Agent 的"记忆"其实很简单：

```
memory = 短期上下文 + 长期上下文
```

短期是最近几轮完整对话，长期是更早对话的压缩摘要。大多数场景用这两层就够了。

---

## 为什么不需要向量数据库做 Memory

很多教程会告诉你：Agent 需要向量数据库来存记忆，然后每轮检索。

实际上，**大多数对话场景不需要这个**。

向量检索解决的是"从海量文档里找相关片段"的问题——这是 RAG 的使用场景。

Memory 解决的是"之前我们聊了什么"的问题。这个问题只需要：

1. 把近期对话放进 messages（短期上下文）
2. 超出窗口时，把早期对话压缩成摘要，拼在 messages 前面（长期上下文）

---

## 实现：两层 Memory

### 层 1：短期上下文

`shared["messages"]` 就是短期上下文——完整保留最近 N 轮对话。

```python
shared["messages"] = [
    {"role": "system", "content": "你是一个 Coding Assistant"},
    {"role": "user",   "content": "帮我分析 main.py"},
    {"role": "assistant", "content": "..."},
    {"role": "user",   "content": "再看看 utils.py"},
    # ...
]
```

这个列表直接传给 LLM。越新的内容越接近列表末尾，模型天然会更关注。

### 层 2：长期上下文（压缩摘要）

当 messages 超过一定长度时，把最早的若干轮压缩成一段摘要，替换掉原始内容。

```python
# core/memory.py
from core.llm import call_llm_simple

COMPRESS_THRESHOLD = 20   # 超过 20 条消息时触发
KEEP_RECENT = 10          # 保留最近 10 条完整消息

def compress_if_needed(messages: list) -> list:
    """如果消息过多，把早期对话压缩为摘要"""
    if len(messages) <= COMPRESS_THRESHOLD:
        return messages

    # 分离：需要压缩的早期消息 vs 保留的近期消息
    to_compress = messages[:-KEEP_RECENT]
    recent = messages[-KEEP_RECENT:]

    # 生成摘要
    conv_text = "\n".join(
        f"{m['role'].upper()}: {m['content']}"
        for m in to_compress
        if m["role"] != "system"
    )
    summary = call_llm_simple(
        f"请用简洁的语言总结以下对话的关键内容，保留重要决策和结论：\n\n{conv_text}"
    )

    # 重建 messages：system + 摘要 + 近期消息
    system_msgs = [m for m in messages if m["role"] == "system"]
    compressed = system_msgs + [
        {"role": "assistant", "content": f"[对话摘要]\n{summary}"}
    ] + recent

    return compressed
```

使用：

```python
class ChatNode(Node):
    def exec(self, _):
        # 每轮调用前先检查是否需要压缩
        shared["messages"] = compress_if_needed(shared["messages"])

        response = call_llm(shared["messages"])
        shared["messages"].append(response)

        if response.get("tool_calls"):
            return "tool_call", response["tool_calls"]
        return "output", response["content"]
```

---

## 可视化：Memory 的工作方式

<div class="mermaid">
flowchart TD
    A[messages 列表] --> B{长度 > 阈值?}
    B -->|否| C[直接传给 LLM]
    B -->|是| D[早期消息 → LLM 压缩]
    D --> E[摘要 + 近期消息]
    E --> C
</div>

---

## 为什么压缩而不是截断

最简单的做法是截断——超出窗口就丢掉最早的消息。

但截断有一个问题：丢失的内容可能包含关键信息（用户在第一轮说的目标、重要的约束条件）。

压缩保留了语义，代价是一次额外的 LLM 调用（通常使用便宜的小模型）。

---

## 工具执行结果的处理

工具结果也进入 messages，但可以更激进地压缩：

```python
def trim_tool_result(result: str, max_chars: int = 2000) -> str:
    """工具输出太长时截断，保留头尾"""
    if len(result) <= max_chars:
        return result
    head = result[:max_chars // 2]
    tail = result[-(max_chars // 2):]
    return f"{head}\n\n[... 省略中间内容 ...]\n\n{tail}"
```

文件读取、shell 命令输出、搜索结果——这些工具的返回值可能很长。截断比压缩更合适，因为中间内容往往不如头尾重要。

---

## 多轮 Agentic 任务的 Memory

对于长任务（比如"帮我重构整个项目"），单纯依赖对话历史会有问题：任务过程中的工具调用记录会占满上下文。

更好的方案是**任务计划 + 进度跟踪**：

```python
shared["task_plan"] = """
## 任务：重构项目
1. [x] 分析现有代码结构
2. [ ] 提取公共函数到 utils.py
3. [ ] 更新所有引用
4. [ ] 运行测试
"""
```

把任务计划放在 system prompt 或 messages 开头，让模型始终知道自己在做什么、做到哪里了。这比靠对话历史"记住"进度要可靠得多。

---

## 完整的 Memory 模块

```
core/
  memory.py          ← compress_if_needed, trim_tool_result
  llm.py             ← call_llm, call_llm_simple
  node.py            ← Node, Flow, shared
```

`shared` 字典是整个 Agent 运行期间的全局状态，memory 相关的所有数据都存在这里：

```python
shared = {
    "messages": [],          # 对话历史（含压缩摘要）
    "task_plan": "",         # 当前任务计划（可选）
    "query": "",             # 当前轮用户查询（workflow 用）
    "search_results": [],    # 搜索结果缓存（workflow 用）
}
```

---

下一篇：[Multi-Agent 与 Agent Teams](../06-multi-agent/index.html)
