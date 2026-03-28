---
layout: default
title: Context Compact：三层压缩换无限会话
description: 微压缩 + 自动压缩 + 手动压缩，上下文总会满，要有办法腾地方
eyebrow: Claude Code / s06
---

# Context Compact：三层压缩换无限会话

> *"上下文总会满，要有办法腾地方"*

读一个 1000 行的文件就吃掉约 4000 token；读 30 个文件、跑 20 条命令，轻松突破 100k token。不压缩，Agent 根本没法在大项目里干活。

这一节实现三层压缩策略，激进程度递增。

---

## 三层压缩

<div class="mermaid">
flowchart TD
    A([每轮 LLM 调用前]) --> B

    B["第一层：micro_compact\n旧 tool_result 替换为占位符\nPrevious: used bash"]
    B --> C{token 数 > 50000?}

    C -->|否| D([继续调用 LLM])
    C -->|是| E

    E["第二层：auto_compact\n完整对话存磁盘\nLLM 生成摘要\nmessages 替换为摘要"]
    E --> F["第三层：compact 工具\n模型主动调用\n同 auto_compact"]
    F --> D
</div>

完整历史通过 transcript 保存在磁盘。信息没有真正丢失，只是移出了活跃上下文。

---

## 第一层：micro_compact

每次 LLM 调用前，把旧的工具结果替换为占位符：

```python
KEEP_RECENT = 3   # 保留最近 3 个 tool_result

def micro_compact(messages: list) -> list:
    """把旧的 tool_result 替换为简短占位符"""
    # 收集所有 tool_result
    tool_results = []
    for i, msg in enumerate(messages):
        if msg["role"] == "user" and isinstance(msg.get("content"), list):
            for j, part in enumerate(msg["content"]):
                if isinstance(part, dict) and part.get("type") == "tool_result":
                    tool_results.append((i, j, part))

    if len(tool_results) <= KEEP_RECENT:
        return messages

    # 把早期的大结果替换为占位符
    for i, j, part in tool_results[:-KEEP_RECENT]:
        if len(str(part.get("content", ""))) > 100:
            # 从对应的 tool_use block 里找工具名
            tool_name = _find_tool_name(messages, part.get("tool_use_id", ""))
            part["content"] = f"[Previous: used {tool_name}]"

    return messages

def _find_tool_name(messages: list, tool_use_id: str) -> str:
    for msg in messages:
        if msg["role"] == "assistant":
            for block in (msg.get("content") or []):
                if hasattr(block, "id") and block.id == tool_use_id:
                    return block.name
    return "tool"
```

效果：大量工具输出被压缩为一行，模型仍然知道"做过这件事"，但不再占用大量上下文。

---

## 第二层：auto_compact

token 超出阈值时自动触发：

```python
import json, time
from pathlib import Path

THRESHOLD = 50_000    # token 阈值
TRANSCRIPT_DIR = Path(".transcripts")
TRANSCRIPT_DIR.mkdir(exist_ok=True)

def estimate_tokens(messages: list) -> int:
    """粗略估计 token 数（字符数 / 4）"""
    return len(json.dumps(messages, default=str)) // 4

def auto_compact(messages: list) -> list:
    """保存完整对话到磁盘，用 LLM 摘要替换"""
    # 1. 保存完整记录
    path = TRANSCRIPT_DIR / f"transcript_{int(time.time())}.jsonl"
    with open(path, "w") as f:
        for msg in messages:
            f.write(json.dumps(msg, default=str) + "\n")
    print(f"[compact] Saved transcript to {path}")

    # 2. LLM 生成摘要
    response = client.messages.create(
        model=MODEL,
        messages=[{
            "role": "user",
            "content": (
                "以下是一段 Agent 的对话记录。"
                "请生成一份简洁的摘要，包含：已完成的操作、关键发现、当前状态。"
                "摘要将用于恢复 Agent 上下文，需保留所有重要信息。\n\n"
                + json.dumps(messages, default=str)[:80000]
            )
        }],
        max_tokens=2000,
    )
    summary = response.content[0].text

    # 3. 用摘要替换整个 messages
    return [
        {"role": "user", "content": f"[对话摘要]\n\n{summary}"},
        {"role": "assistant", "content": "明白，我会在此基础上继续。"},
    ]
```

---

## 第三层：compact 工具

模型也可以主动调用压缩：

```python
TOOL_HANDLERS["compact"] = lambda **kw: _manual_compact()

_compact_requested = False

def _manual_compact():
    global _compact_requested
    _compact_requested = True
    return "Compacting conversation..."
```

在 agent_loop 里检查标志并执行压缩：

```python
# 执行工具后检查
if _compact_requested:
    messages[:] = auto_compact(messages)
    _compact_requested = False
```

---

## 完整循环集成

```python
def agent_loop(messages: list):
    while True:
        # 第一层：静默微压缩
        micro_compact(messages)

        # 第二层：超出阈值自动压缩
        if estimate_tokens(messages) > THRESHOLD:
            messages[:] = auto_compact(messages)

        response = client.messages.create(
            model=MODEL, system=SYSTEM,
            messages=messages, tools=TOOLS, max_tokens=8000,
        )
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            break

        results = []
        for block in response.content:
            if block.type == "tool_use":
                output = TOOL_HANDLERS.get(block.name, lambda **kw: "Unknown tool")(**block.input)
                results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": str(output)[:50000]
                })
        messages.append({"role": "user", "content": results})

        # 第三层：手动压缩标志
        global _compact_requested
        if _compact_requested:
            messages[:] = auto_compact(messages)
            _compact_requested = False
```

---

## 为什么三层而不是一层

| 层级 | 频率 | 目的 | 信息损失 |
|------|------|------|---------|
| micro_compact | 每轮 | 清理旧工具输出 | 极低（占位符保留操作记录） |
| auto_compact | 阈值触发 | 重置上下文 | 中（摘要可能丢失细节） |
| compact 工具 | 按需 | 模型主动管理 | 中 |

三层各有侧重。micro_compact 是低成本的持续清理；auto_compact 是大规模重置；compact 工具让模型自己判断何时压缩最合适。

---

## .transcripts/ 目录

```
.transcripts/
  transcript_1735000000.jsonl   ← 第一次压缩前的完整记录
  transcript_1735001234.jsonl   ← 第二次压缩前的完整记录
```

信息没有真正丢失。如果发现摘要丢失了重要内容，可以从 transcript 里恢复。

---

下一篇：[Task System：持久化任务图](../07-task-system/index.html)
