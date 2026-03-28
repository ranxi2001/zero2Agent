---
layout: default
title: Agent Loop：一个循环就是一个 Agent
description: 从 30 行代码理解 Agent 的核心结构——while True + stop_reason
eyebrow: Claude Code / s01
---

# Agent Loop：一个循环就是一个 Agent

> *"One loop & Bash is all you need"*

这一节只做一件事：搭出 Agent 的最小可运行版本。

不到 30 行代码，这就是整个 Agent。后面 11 章都在这个循环上叠加机制——**循环本身始终不变**。

---

## 问题

语言模型能推理代码，但碰不到真实世界——不能读文件、跑测试、看报错。

没有循环，每次工具调用你都得手动把结果粘回去。**你自己就是那个循环。**

---

## 解决方案

<div class="mermaid">
flowchart LR
    A([用户 prompt]) --> B[LLM]
    B -->|tool_use| C[执行工具]
    C -->|tool_result| B
    B -->|stop| D([结束])
</div>

一个退出条件控制整个流程：循环持续运行，直到模型不再调用工具。

---

## 完整实现

```python
import anthropic

client = anthropic.Anthropic()
MODEL = "claude-opus-4-6"

SYSTEM = "你是一个 Coding Agent，可以执行 bash 命令来完成任务。"

TOOLS = [{
    "name": "bash",
    "description": "执行 shell 命令，返回输出",
    "input_schema": {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "要执行的 shell 命令"}
        },
        "required": ["command"]
    }
}]

import subprocess

def run_bash(command: str) -> str:
    result = subprocess.run(
        command, shell=True, capture_output=True, text=True, timeout=30
    )
    return result.stdout + result.stderr


def agent_loop(query: str):
    messages = [{"role": "user", "content": query}]

    while True:
        response = client.messages.create(
            model=MODEL, system=SYSTEM,
            messages=messages, tools=TOOLS, max_tokens=8000,
        )
        messages.append({"role": "assistant", "content": response.content})

        # 没有工具调用 → 结束
        if response.stop_reason != "tool_use":
            for block in response.content:
                if hasattr(block, "text"):
                    print(block.text)
            return

        # 执行所有工具调用，收集结果
        results = []
        for block in response.content:
            if block.type == "tool_use":
                output = run_bash(block.input["command"])
                print(f"[bash] {block.input['command']}")
                print(f"  → {output[:200]}")
                results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": output,
                })
        messages.append({"role": "user", "content": results})


if __name__ == "__main__":
    query = input("You: ").strip()
    agent_loop(query)
```

---

## 关键设计解析

### 1. messages 是累积的

每一轮对话的 LLM 响应和工具结果都**追加**进 messages，不是替换。这让模型始终能看到完整的执行历史。

```python
# 轮次 1：用户消息
messages = [{"role": "user", "content": "列出当前目录的 Python 文件"}]

# 轮次 1：LLM 响应（包含 tool_use block）
messages.append({"role": "assistant", "content": response.content})

# 轮次 1：工具结果
messages.append({"role": "user", "content": [tool_result]})

# 轮次 2：LLM 继续推理...
```

### 2. stop_reason 是唯一的退出条件

| stop_reason | 含义 |
|------------|------|
| `"tool_use"` | 模型想调用工具，继续循环 |
| `"end_turn"` | 模型完成任务，退出循环 |
| `"max_tokens"` | 超出 token 限制，通常需要处理 |

### 3. tool_result 的格式

工具结果必须以 `role: "user"` 消息的形式返回，且 content 是一个列表：

```python
{
    "role": "user",
    "content": [
        {
            "type": "tool_result",
            "tool_use_id": block.id,  # 必须和 tool_use 的 id 匹配
            "content": "命令输出..."
        }
    ]
}
```

---

## 这 30 行代码做了什么

```
用户输入
   ↓
messages = [user_message]
   ↓
while True:
    LLM 调用 → 追加 assistant 响应
    if stop_reason != "tool_use": break
    执行每个工具调用 → 追加 tool_result
```

仅此而已。没有魔法，没有框架，没有隐藏逻辑。

---

## 试一试

```bash
git clone https://github.com/shareAI-lab/learn-claude-code
cd learn-claude-code
export ANTHROPIC_API_KEY="sk-ant-xxx"
python agents/s01_agent_loop.py
```

试试这些任务：

- `列出当前目录的所有 Python 文件`
- `创建一个叫 hello.py 的文件，打印 Hello World`
- `当前 git 分支是什么？`
- `创建 test_output 目录并在里面写 3 个文件`

---

下一篇：[Tool Use：扩展模型能触达的边界](../02-tool-use/index.html)
