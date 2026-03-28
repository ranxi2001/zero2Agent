---
layout: default
title: Subagent：上下文隔离的正确姿势
description: 大任务拆小，子智能体用独立 messages[]，不污染主对话
eyebrow: Claude Code / s04
---

# Subagent：上下文隔离的正确姿势

> *"大任务拆小，每个小任务干净的上下文"*

这一节加一个 `task` 工具。调用它会启动一个子 Agent，子 Agent 有完整的工具能力，但它的上下文完全隔离——父 Agent 只看到最终摘要。

---

## 问题

Agent 工作越久，messages 数组越胖。读文件、跑命令的每条输出都永久留在上下文里。

"这个项目用什么测试框架？"可能要读 5 个文件，但父 Agent 只需要一个词："pytest"。

如果直接在父 Agent 里做，这 5 次 read_file 的完整输出都会留在 messages 里，占用宝贵的上下文空间，干扰模型对后续任务的判断。

---

## 解决方案

<div class="mermaid">
flowchart LR
    A[父 Agent\nmessages 保持干净] -->|task prompt| B[子 Agent\nmessages=空]
    B --> C[读文件 × 5]
    B --> D[跑命令]
    B --> E[分析结果]
    E -->|仅摘要文本| A
</div>

子 Agent 可能跑了 30 次工具调用，但整个消息历史直接丢弃。父 Agent 收到的只是一段摘要文本。

---

## 实现

```python
def run_subagent(prompt: str) -> str:
    """启动子 Agent，返回最终摘要文本"""
    sub_messages = [{"role": "user", "content": prompt}]

    for _ in range(30):  # 安全限制：最多 30 轮
        response = client.messages.create(
            model=MODEL,
            system=SUBAGENT_SYSTEM,
            messages=sub_messages,
            tools=CHILD_TOOLS,   # 子 Agent 没有 task 工具（禁止递归）
            max_tokens=8000,
        )
        sub_messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            break

        results = []
        for block in response.content:
            if block.type == "tool_use":
                handler = TOOL_HANDLERS.get(block.name)
                output = handler(**block.input) if handler else f"Unknown tool: {block.name}"
                results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": str(output)[:50000]
                })
        sub_messages.append({"role": "user", "content": results})

    # 只返回最后一条 assistant 消息的文本
    return "".join(
        b.text for b in response.content if hasattr(b, "text")
    ) or "(no summary)"
```

---

## task 工具定义

```python
PARENT_TOOLS = CHILD_TOOLS + [
    {
        "name": "task",
        "description": "启动子 Agent 处理子任务，返回摘要。适合需要大量工具调用但父 Agent 只关心结论的场景。",
        "input_schema": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "子任务的完整描述，需要自包含（子 Agent 没有父 Agent 的上下文）"
                }
            },
            "required": ["prompt"]
        }
    }
]

TOOL_HANDLERS["task"] = lambda **kw: run_subagent(kw["prompt"])
```

**关键限制：子 Agent 没有 `task` 工具。** 防止子 Agent 再生成孙子 Agent，避免递归爆炸。

---

## 子任务 prompt 要自包含

父 Agent 给子 Agent 的 prompt 必须包含所有必要的上下文，因为子 Agent 看不到父 Agent 的对话历史。

```python
# 错误：子 Agent 不知道"这个项目"是什么
"找出这个项目使用的测试框架"

# 正确：自包含的任务描述
"读取 /workspace/learn-claude-code 项目根目录下的文件，
 找出使用的测试框架（查看 requirements.txt、setup.py、pyproject.toml 等），
 返回测试框架名称和版本。"
```

---

## 相对 s03 的变化

| 组件 | s03 | s04 |
|------|-----|-----|
| 工具数量 | 5 | 5（子端）+ task（父端） |
| 上下文 | 单一共享 | 父/子隔离 |
| 子 Agent | 无 | `run_subagent()` |
| 返回值 | — | 仅摘要文本 |

---

## 什么时候用 task

适合用子 Agent 的场景：

- 需要读大量文件但只关心结论（"这个模块有什么问题？"）
- 需要独立验证（一个子 Agent 写代码，另一个子 Agent 审查）
- 独立的子任务，结果互不依赖

不适合用子 Agent 的场景：

- 子任务之间有依赖（A 的输出是 B 的输入）
- 任务简单，单次工具调用就能完成
- 需要父 Agent 全程参与推理

---

下一篇：[Skill Loading：按需加载领域知识](../05-skill-loading/index.html)
