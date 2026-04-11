---
layout: default
title: Agent Loop：一个循环就是一个 Agent
description: 从 30 行代码理解 Agent 的核心结构——while True + stop_reason
eyebrow: Claude Code / s01
---

# Agent Loop：一个循环就是一个 Agent

> *“One loop & Bash is all you need”*

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

## 从零实现

> **注意**：下面这 30 行 Python 是教学用的最小实现。真实的 Claude Code 远比这复杂——它用 1700+ 行 TypeScript 实现了状态机、自动压缩、token 恢复等机制。我们在后面的“源码实证”小节会深入对比。

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

## 源码实证

上面的 30 行代码只覆盖了最核心的 happy path。Claude Code 的真实实现在 `src/query.ts` 中，是一个 **1729 行的 `while(true)` 状态机**。让我们看看生产级 Agent Loop 到底在处理什么。

### 两层架构：QueryEngine + queryLoop

Claude Code 把 Agent Loop 拆成两层：

| 层 | 文件 | 职责 |
|---|------|------|
| **QueryEngine** | `src/QueryEngine.ts` | 会话生命周期管理：持有 `mutableMessages[]`、`abortController`、`readFileState`（文件缓存）、`totalUsage`（token 用量）。一个 QueryEngine 对应一次完整对话。 |
| **queryLoop** | `src/query.ts` | 单轮 Agent 循环：状态机驱动的 `while(true)`，处理 API 调用、工具执行、错误恢复、自动压缩。 |

`QueryEngine` 的核心字段直接映射了我们教学实现中的 `messages` 列表：

```typescript
// src/QueryEngine.ts
export class QueryEngine {
  private mutableMessages: Message[]      // ← 对应我们的 messages = []
  private abortController: AbortController // ← 我们没有：取消信号
  private readFileState: FileStateCache    // ← 我们没有：文件读取缓存
  private totalUsage: NonNullableUsage     // ← 我们没有：token 用量追踪
  private permissionDenials: SDKPermissionDenial[]
  // ...
}
```

### queryLoop 的状态机

我们的 `while True` 里只有一个判断：`stop_reason != "tool_use"` 就退出。而真实的 `queryLoop` 在每次迭代中携带一个 `State` 对象，跟踪压缩状态、恢复计数和 stop hook：

```typescript
// src/query.ts — 循环状态
type State = {
  messages: Message[]
  toolUseContext: ToolUseContext
  autoCompactTracking: AutoCompactTrackingState | undefined
  maxOutputTokensRecoveryCount: number
  hasAttemptedReactiveCompact: boolean
  maxOutputTokensOverride: number | undefined
  pendingToolUseSummary: Promise<ToolUseSummaryMessage | null> | undefined
  stopHookActive: boolean | undefined
  turnCount: number
  transition: Continue | undefined  // ← 上一轮为什么 continue 了
}
```

每轮循环结束时，状态机通过 `transition.reason` 决定下一步。终止时返回 `Terminal`：

### 六种状态转移

<div class="mermaid">
flowchart TD
    START([进入 while true]) --> API[调用 API]
    API --> CHECK{检查结果}

    CHECK -->|prompt_too_long| COLLAPSE[context collapse:<br>折叠历史上下文]
    COLLAPSE -->|collapse_drain_retry| API

    COLLAPSE -->|仍然太长| REACTIVE[reactive compact:<br>激进压缩]
    REACTIVE -->|reactive_compact_retry| API

    CHECK -->|max_output_tokens| ESCALATE[max_output_tokens_escalate:<br>8k → 64k]
    ESCALATE --> API

    ESCALATE -->|仍然超限| RECOVERY[max_output_tokens_recovery:<br>多轮恢复]
    RECOVERY --> API

    CHECK -->|stop hook 失败| HOOK[stop_hook_blocking:<br>注入错误重试]
    HOOK --> API

    CHECK -->|工具调用| TOOLS[执行工具]
    TOOLS -->|next_turn| API

    CHECK -->|end_turn / 无工具| DONE([completed])
</div>

具体来说：

| transition.reason | 触发条件 | 恢复策略 |
|-------------------|---------|---------|
| `next_turn` | 正常的工具调用→结果→继续 | 我们的实现覆盖了这个 |
| `collapse_drain_retry` | API 返回 prompt-too-long | 先尝试 context collapse：折叠已有的历史摘要 |
| `reactive_compact_retry` | collapse 后仍然太长 | 激进压缩：对整个对话做摘要压缩 |
| `max_output_tokens_escalate` | 模型输出被截断 | 把 `max_tokens` 从 8,000 升级到 64,000 |
| `max_output_tokens_recovery` | 升级后仍然截断 | 注入恢复消息让模型在下一轮继续 |
| `stop_hook_blocking` | stop hook 报错（如 lint 失败） | 把错误注入 messages，让模型自行修复 |
| `completed` | 模型正常结束 / 不可恢复的错误 | 退出循环 |

### prompt-too-long 恢复链

这是最精妙的部分。当对话变得太长，API 返回 prompt-too-long 错误时，Claude Code 有一条三级恢复链：

```
prompt_too_long
    ↓
[1] context collapse — 折叠已暂存的历史摘要（轻量）
    ↓ 还是太长？
[2] reactive compact — 对整段对话做激进压缩（重量）
    ↓ 还是太长？
[3] 返回 { reason: 'prompt_too_long' } 终止
```

### max_output_tokens 恢复链

当模型输出被 `max_tokens` 截断时：

```
max_output_tokens
    ↓
[1] 把 max_tokens 从 8,000 升级到 64,000（ESCALATED_MAX_TOKENS）
    ↓ 还是被截断？
[2] 注入恢复消息，让模型用新一轮继续输出（最多 3 次）
    ↓ 超过重试限制？
[3] 返回 { reason: 'completed' } 终止
```

---

## 真实架构对比

| 维度 | 我们的 30 行实现 | Claude Code 生产代码 |
|-----|-----------------|-------------------|
| **核心循环** | `while True` + `stop_reason` | `while(true)` + `State` 状态机（1729 行） |
| **消息管理** | `messages.append()` | `QueryEngine.mutableMessages[]` + 序列化/持久化 |
| **退出条件** | `stop_reason != "tool_use"` | 6 种 transition reason + Terminal 类型 |
| **错误恢复** | 无 | prompt-too-long 三级恢复、max-output-tokens 升级+多轮恢复 |
| **上下文管理** | 无限累积直到超限 | auto compact 追踪 + context collapse + reactive compact |
| **token 控制** | 固定 `max_tokens=8000` | 动态：8k 起步，按需升级到 64k，带 task budget |
| **取消机制** | 无 | `AbortController` 信号贯穿全链路 |
| **文件状态** | 无 | `FileStateCache` 缓存文件读取，避免重复读取 |
| **stop hooks** | 无 | 执行后置钩子（如 lint），失败则注入错误让模型修复 |

核心洞察：**我们的 30 行代码和 Claude Code 的 1729 行代码共享同一个骨架**——`while(true)` 循环驱动 LLM 调用和工具执行。差异全在**容错和优化**上。理解了 30 行版本，你就理解了那 1729 行的骨架。

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

而 Claude Code 在这个骨架上加了一层状态机外壳：

```
while (true):
    API 调用 → 流式处理 → 追加消息
    if prompt_too_long → collapse → reactive compact → 终止
    if max_output_tokens → 升级 8k→64k → 多轮恢复 → 终止
    if stop_hook 失败 → 注入错误重试
    if 有工具调用 → 执行 → state.transition = next_turn → continue
    return { reason: 'completed' }
```

---

## 设计哲学：从 REPL 到 Agent

Claude Code 设计指南将 Agent Loop 放在一条清晰的进化线上：

```
Lisp REPL (1960) → Shell (1971) → Jupyter (2014) → ChatGPT (2022) → Claude Code (2024)
```

所有这些系统共享同一个骨架：**Read → Eval → Print → Loop**。区别在于 Eval 的能力边界——Shell eval 系统命令，Jupyter eval 代码块，而 Claude Code eval 的是 LLM 推理 + 工具调用。

这意味着 `while True` 循环不是一个实现细节，而是 **Agent 系统的本质结构**。设计指南总结的 “Agent 公式” 也证实了这一点：

> **Tool Calls + Context Management + Task Planning + Error Handling + Permission Control + State Persistence = Agent System**

我们的 30 行循环覆盖了前两项（Tool Calls + Context Management），后续章节逐步补全其余部分。

从 chatbot 到 agent 的关键跃迁只有一个：**stop_reason 从 “end_turn” 变成了 “tool_use”**。chatbot 在模型说完话时停下，agent 在模型没有更多工具要调用时才停下。这个看似微小的判断条件，决定了系统是被动应答还是主动执行。

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
