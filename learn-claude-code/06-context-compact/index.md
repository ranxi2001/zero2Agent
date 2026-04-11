---
layout: default
title: Context Compact：三层压缩换无限会话
description: 微压缩 + 全量压缩 + 自动压缩，上下文总会满，要有办法腾地方
eyebrow: Claude Code / s06
---

# Context Compact：三层压缩换无限会话

> *“上下文总会满，要有办法腾地方”*

读一个 1000 行的文件就吃掉约 4000 token；读 30 个文件、跑 20 条命令，轻松突破 100k token。不压缩，Agent 根本没法在大项目里干活。

Claude Code 的解决方案是一套**三层压缩系统**，激进程度递增，外加一个轻量级的 Session Memory 辅助机制。

---

## 源码实证：真实的三层架构

<div class="mermaid">
flowchart TD
    A([每轮 LLM 调用前]) --> B

    B["Layer 1: Microcompact\n清除旧 tool_result 内容\n两条路径：时间触发 / 缓存编辑"]
    B --> C{token > context_window - 13K?}

    C -->|否| D([继续调用 LLM])
    C -->|是| E

    E["Layer 3: Auto Compact\n先尝试 Session Memory 压缩\n失败则触发 Full Compact"]
    E --> F["Layer 2: Full Compact\nfork Sonnet 生成摘要\nPTL 重试循环\n附加最近文件 / plan / skill"]
    F --> D
</div>

完整历史通过 transcript 保存在磁盘。信息没有真正丢失，只是移出了活跃上下文。

---

## Layer 1：Microcompact — 无 LLM 调用的静默清理

> 源码位置：`src/services/compact/microCompact.ts`

Microcompact 是最轻量的一层，**不调用 LLM**，直接在消息数组上做原地修改（mutation）。它有两条触发路径：

### 路径 A：常规 Microcompact

每次 LLM 调用前执行，把旧的 tool_result 替换为占位符。只处理特定工具类型：

```typescript
// 源码：microCompact.ts:41-50
const COMPACTABLE_TOOLS = new Set<string>([
  FILE_READ_TOOL_NAME,
  ...SHELL_TOOL_NAMES,    // Bash, BashBackground 等
  GREP_TOOL_NAME,
  GLOB_TOOL_NAME,
  WEB_SEARCH_TOOL_NAME,
  WEB_FETCH_TOOL_NAME,
  FILE_EDIT_TOOL_NAME,
  FILE_WRITE_TOOL_NAME,
])
```

保留最近 N 个结果（由 `keepRecent` 控制，默认 5），早期结果被替换为 `[Old tool result content cleared]`。

### 路径 B：时间触发 Microcompact

当用户离开超过 30-60 分钟再回来时，服务端的 prompt cache 几乎必然已过期。此时触发更激进的清理：

```typescript
// 源码：timeBasedMCConfig.ts:30-34
const TIME_BASED_MC_CONFIG_DEFAULTS: TimeBasedMCConfig = {
  enabled: false,
  gapThresholdMinutes: 60,   // 服务端 1h cache TTL 过期
  keepRecent: 5,
}
```

### 路径 C：缓存编辑（Cached Microcompact）

内部版本还有一条 `cache_edits` API 路径——不是直接修改消息，而是通过 API 的缓存编辑能力在服务端清除旧内容，保持 prompt cache 命中率。

### 从零实现

核心思路很简单——把旧的工具输出替换为一行占位符：

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

效果：大量工具输出被压缩为一行，模型仍然知道“做过这件事”，但不再占用大量上下文。

---

## Layer 2：Full Compact — Fork Sonnet 生成结构化摘要

> 源码位置：`src/services/compact/compact.ts` + `src/services/compact/prompt.ts`

Full Compact 是真正的“重炮”——fork 一个 Sonnet 子进程，用专门的 summary prompt 把整段对话浓缩成结构化摘要。

### 核心流程

**Step 1：预处理**

发送给摘要模型之前，先做两步清理：

```typescript
// 源码：compact.ts:145-199 — 剥离图片和文档
export function stripImagesFromMessages(messages: Message[]): Message[] {
  // image -> [image], document -> [document]
  // 包括嵌套在 tool_result 里的媒体块
}

// 源码：compact.ts:211-223 — 剥离会被重新注入的 attachment
export function stripReinjectedAttachments(messages: Message[]): Message[] {
  // 移除 skill_discovery / skill_listing 类型的 attachment
  // 因为压缩后会重新注入
}
```

**Step 2：Fork Sonnet 生成摘要**

Prompt 要求模型输出两个 XML 块：

- `<analysis>` — 思维草稿（scratchpad），压缩后会被丢弃
- `<summary>` — 最终摘要，包含 9 个结构化部分

```
// 源码：prompt.ts — summary 的 9 个部分
1. Primary Request and Intent — 用户的明确请求
2. Key Technical Concepts — 技术概念和框架
3. Files and Code Sections — 涉及的文件和代码片段
4. Errors and fixes — 遇到的错误和修复方式
5. Problem Solving — 已解决的问题
6. All user messages — 所有非 tool_result 的用户消息
7. Pending Tasks — 待完成的任务
8. Current Work — 压缩前正在做的事
9. Optional Next Step — 下一步计划（含原文引用防止漂移）
```

**Step 3：PTL 重试循环**

如果 compact 本身的请求也超出了 prompt-too-long 限制，会进入重试循环：

```typescript
// 源码：compact.ts:227-291
const MAX_PTL_RETRIES = 3

export function truncateHeadForPTLRetry(
  messages: Message[],
  ptlResponse: AssistantMessage,
): Message[] | null {
  // 按 API-round 分组（groupMessagesByApiRound）
  // 从头部丢弃最老的组，直到腾出足够空间
  // 如果有 tokenGap 信息，精确丢弃；否则丢弃 20% 的组
  // 至少保留一个组用于生成摘要
}
```

**Step 4：后置附件注入**

压缩完成后，自动附加关键上下文，确保模型不会“失忆”：

```typescript
// 源码：compact.ts:122-131
export const POST_COMPACT_MAX_FILES_TO_RESTORE = 5   // 最多恢复 5 个最近读取的文件
export const POST_COMPACT_TOKEN_BUDGET = 50_000       // 总预算 50K token
export const POST_COMPACT_MAX_TOKENS_PER_FILE = 5_000
export const POST_COMPACT_MAX_TOKENS_PER_SKILL = 5_000
export const POST_COMPACT_SKILLS_TOKEN_BUDGET = 25_000
```

附件包括：最近读取的文件内容、当前 plan、已激活的 skill、工具/agent 列表变化量。

### Partial Compact

Full Compact 还支持两种**部分压缩**方向：

- `from` 方向：保留前缀（cache 友好），只压缩后半段对话
- `up_to` 方向：保留后缀（最近消息不动），只压缩前半段

### 从零实现

```python
import json, time
from pathlib import Path

TRANSCRIPT_DIR = Path(".transcripts")
TRANSCRIPT_DIR.mkdir(exist_ok=True)

def full_compact(messages: list) -> list:
    """Fork Sonnet 生成结构化摘要"""
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
                "请生成一份结构化摘要，包含：\n"
                "1. 用户请求  2. 技术概念  3. 文件和代码\n"
                "4. 错误和修复  5. 待完成任务  6. 当前工作\n\n"
                "先在 <analysis> 中梳理思路，再在 <summary> 中给出最终摘要。\n\n"
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

## Layer 3：Auto Compact — 阈值触发 + 熔断器

> 源码位置：`src/services/compact/autoCompact.ts`

Auto Compact 是调度层——决定**何时**触发压缩，以及选择**哪种**压缩方式。

### 触发阈值

```typescript
// 源码：autoCompact.ts:63-66
export const AUTOCOMPACT_BUFFER_TOKENS = 13_000
export const WARNING_THRESHOLD_BUFFER_TOKENS = 20_000
export const ERROR_THRESHOLD_BUFFER_TOKENS = 20_000
export const MANUAL_COMPACT_BUFFER_TOKENS = 3_000
```

阈值计算：`context_window - max_output_tokens - AUTOCOMPACT_BUFFER_TOKENS`

例如 200K 窗口、20K 输出保留，autocompact 阈值 = 200K - 20K - 13K = **167K**。

### 熔断器

连续失败 3 次后停止重试，避免浪费 API 调用：

```typescript
// 源码：autoCompact.ts:70
const MAX_CONSECUTIVE_AUTOCOMPACT_FAILURES = 3
// BQ 2026-03-10: 1,279 sessions had 50+ consecutive failures
// wasting ~250K API calls/day globally
```

### 压缩策略选择

Auto Compact 触发后，**先尝试轻量级的 Session Memory 压缩**，失败才回退到 Full Compact：

```typescript
// 源码：autoCompact.ts:288-310
// EXPERIMENT: Try session memory compaction first
const sessionMemoryResult = await trySessionMemoryCompaction(
  messages,
  toolUseContext.agentId,
  recompactionInfo.autoCompactThreshold,
)
if (sessionMemoryResult) {
  setLastSummarizedMessageId(undefined)
  runPostCompactCleanup(querySource)
  return { wasCompacted: true, compactionResult: sessionMemoryResult }
}

// 失败则走 Full Compact
const compactionResult = await compactConversation(
  messages, toolUseContext, cacheSafeParams,
  true,      // suppressFollowUpQuestions
  undefined, // no custom instructions
  true,      // isAutoCompact
)
```

### 禁用条件

Auto Compact 在以下情况会被跳过：

- `DISABLE_COMPACT` 或 `DISABLE_AUTO_COMPACT` 环境变量
- 用户配置 `autoCompactEnabled = false`
- Context-Collapse 模式激活（Collapse 有自己的上下文管理）
- Reactive-Compact 模式激活（让 API 的 prompt-too-long 来触发）
- 子 Agent（session_memory / compact / marble_origami）

### 从零实现

```python
THRESHOLD = 50_000    # token 阈值
MAX_FAILURES = 3      # 熔断器

_consecutive_failures = 0

def auto_compact_if_needed(messages: list) -> list:
    """阈值触发自动压缩，带熔断器"""
    global _consecutive_failures

    if _consecutive_failures >= MAX_FAILURES:
        return messages

    if estimate_tokens(messages) < THRESHOLD:
        return messages

    try:
        result = full_compact(messages)
        _consecutive_failures = 0
        return result
    except Exception:
        _consecutive_failures += 1
        return messages
```

---

## 辅助机制：Session Memory

> 源码位置：`src/services/SessionMemory/`

Session Memory 是一个**更轻量级的会话记忆系统**，独立于三层压缩之外。它维护一个 markdown 格式的笔记文件，由 post-sampling hook 在后台更新。

### 触发条件

Session Memory 基于两个阈值的**双重门控**：

```typescript
// 源码：sessionMemoryUtils.ts:31-36
export const DEFAULT_SESSION_MEMORY_CONFIG: SessionMemoryConfig = {
  minimumMessageTokensToInit: 10000,   // 首次触发：上下文达 10K token
  minimumTokensBetweenUpdate: 5000,    // 后续更新：增长 5K token
  toolCallsBetweenUpdates: 3,          // 且至少 3 次工具调用
}
```

必须**同时满足** token 增长阈值 AND 工具调用阈值（或当前轮没有工具调用时只需 token 阈值）。

### 笔记模板

```markdown
# Session Title
# Current State     ← 压缩后恢复的关键
# Task specification
# Files and Functions
# Workflow
# Errors & Corrections
# Codebase and System Documentation
# Learnings
# Key results
# Worklog
```

每个 section 上限约 2000 token，全文上限 12000 token。超限时模型被提示“MUST condense”。

### 与压缩的关系

Session Memory 不替代 Full Compact，而是提供了一种**更省钱的替代路径**。Auto Compact 触发时会先尝试 `trySessionMemoryCompaction()`——如果 session memory 里已经有了足够的上下文，可以跳过昂贵的 Sonnet fork。

---

## 完整循环集成

### 从零实现

```python
# 手动压缩工具
TOOL_HANDLERS["compact"] = lambda **kw: _manual_compact()
_compact_requested = False

def _manual_compact():
    global _compact_requested
    _compact_requested = True
    return "Compacting conversation..."

def agent_loop(messages: list):
    while True:
        # Layer 1：静默微压缩（每轮）
        micro_compact(messages)

        # Layer 3：超出阈值自动压缩（内部调用 Layer 2）
        messages[:] = auto_compact_if_needed(messages)

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

        # 手动压缩标志
        global _compact_requested
        if _compact_requested:
            messages[:] = full_compact(messages)
            _compact_requested = False
```

---

## 源码中的关键设计决策

### 为什么 Microcompact 不调用 LLM？

每轮都跑，必须零延迟。直接修改消息数组（mutation）或走 API 的 `cache_edits` 能力，不产生额外 API 调用。

### 为什么 Full Compact 输出 `<analysis>` + `<summary>` 两个块？

`<analysis>` 是思维草稿（scratchpad），让模型先梳理完整上下文再写摘要。压缩后 `<analysis>` 被丢弃，只保留 `<summary>` 进入新上下文——既保证摘要质量，又不浪费 token。

### 为什么要按 API-round 分组？

PTL 重试时需要从头部丢弃消息。按 API-round 分组（`groupMessagesByApiRound`）保证每个组是一次完整的 API 往返，不会拆散 tool_use/tool_result 配对。

### 为什么 Auto Compact 要加熔断器？

源码注释直接给了答案：*“1,279 sessions had 50+ consecutive failures (up to 3,272), wasting ~250K API calls/day globally.”* 3 次连续失败后停止重试。

### 压缩后为什么要注入附件？

摘要再好也会丢失细节。注入最近读取的 5 个文件（每个 5K token 上限）、当前 plan、已激活 skill、工具/agent 列表变化量，确保模型在压缩后仍能“接上”工作。

---

## 三层对比

| 层级 | 触发时机 | 是否调用 LLM | 信息损失 | 源码位置 |
|------|---------|-------------|---------|---------|
| Microcompact | 每轮 / 时间间隔 | 否 | 极低（占位符保留操作记录） | `microCompact.ts` |
| Full Compact | 被 Auto Compact 或手动 `/compact` 调用 | 是（Fork Sonnet） | 中（结构化摘要） | `compact.ts` |
| Auto Compact | token > `context_window - 13K` | 间接（调度层） | 取决于选择的压缩方式 | `autoCompact.ts` |
| Session Memory | token/tool-call 阈值 | 是（后台 fork） | 低（增量笔记） | `SessionMemory/` |

三层各有侧重。Microcompact 是零成本的持续清理；Full Compact 是 Sonnet 驱动的大规模摘要；Auto Compact 是智能调度器，先尝试轻量路径再回退到重量级方案。Session Memory 独立运行，为压缩提供辅助上下文。

## 设计哲学：Context Engineering 的核心命题

设计指南将 Claude Code 的上下文管理提升到一个独立的工程学科——**Context Engineering**，区别于大众熟知的 Prompt Engineering：

| 维度 | Prompt Engineering | Context Engineering |
|------|-------------------|---------------------|
| 关注点 | 单次输入的措辞 | 整个会话的信息流 |
| 时间尺度 | 一次请求 | 跨数百轮对话 |
| 核心挑战 | 如何表达清楚 | 如何在有限窗口中保留关键信息 |
| 对应机制 | system prompt 设计 | Compact + Memory + CLAUDE.md |

Auto-Compact 揭示了一个深刻的设计原则：**智能系统需要有选择地遗忘**。人类的记忆也是这样工作的——我们不记得每一个细节，但我们记得重要的事情。三层压缩架构正是对“遗忘的艺术”的工程实现：

- **Microcompact**（持续遗忘）：每轮自动清理工具输出的细节，只保留操作摘要
- **Full Compact**（主动遗忘）：用 LLM 判断什么值得记住，什么可以丢弃
- **Auto Compact**（防御性遗忘）：熔断器确保系统在极端情况下也不会崩溃

设计指南特别强调了**为失败设计**原则在压缩系统中的体现：Reactive Compact 是 Auto Compact 的“保险丝”——即使自动压缩没有及时触发，API 返回 `prompt_too_long` 时也能自动恢复。这种多层防御的设计，让系统在面对不可预测的对话长度时始终保持稳定。

---

## Post-Compact 清理

> 源码位置：`src/services/compact/postCompactCleanup.ts`

压缩完成后需要清理大量缓存状态：

- 重置 Microcompact 状态
- 清除 system prompt section 缓存
- 清除权限分类器审批缓存
- 清除 session messages 缓存
- 重置 Context-Collapse 状态（仅主线程）
- 清除 memory files 缓存（仅主线程）
- **不清除** skill 内容（需要跨多次压缩存活）

关键区分：子 Agent 与主线程共享进程级模块状态，所以子 Agent 压缩时**不重置**主线程的模块级状态（context-collapse、memory file cache），否则会污染主线程。

---

下一篇：[Task System：持久化任务图](../07-task-system/index.html)
