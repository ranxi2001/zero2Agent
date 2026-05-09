---
layout: default
title: Agent Loop：EventStream 驱动的核心循环
description: pi-mono 的 agentLoop 实现——从入口到工具执行的完整数据流
eyebrow: OpenClaw / 02
---

# Agent Loop：EventStream 驱动的核心循环

pi-mono 的核心在 `packages/agent/src/agent-loop.ts`。这个文件实现了整个 Agent 的执行引擎。

读懂它，就理解了所有生产级 Coding Agent 的运行原理。

---

## 两个入口

```typescript
// packages/agent/src/agent-loop.ts

// 全新对话
export function agentLoop(config: AgentConfig): EventStream { ... }

// 恢复已有对话（从上次中断处继续）
export function agentLoopContinue(config: AgentConfig, transcript: Event[]): EventStream { ... }
```

`agentLoop()` 启动新对话，`agentLoopContinue()` 从历史 transcript 恢复。两者返回同一种类型：**EventStream**——一个异步事件生成器。

---

## EventStream 架构

pi-mono 不像传统框架那样返回最终结果，而是**流式发射生命周期事件**：

```typescript
type Event =
  | { type: 'agent_start' }
  | { type: 'turn_start' }
  | { type: 'message_start', role: 'assistant' }
  | { type: 'message_update', delta: string }
  | { type: 'message_end', content: Message }
  | { type: 'tool_execution_start', toolCall: ToolCall }
  | { type: 'tool_execution_update', delta: string }
  | { type: 'tool_execution_end', result: ToolResult }
  | { type: 'turn_end' }
  | { type: 'agent_end' }
```

调用方（CLI、Web UI、测试）通过消费这个 EventStream 来驱动 UI 渲染、日志记录、进度展示。

**为什么这么设计？**

1. **UI 解耦**：TUI、Web UI、测试 harness 都消费同一个 EventStream，Agent 逻辑不需要知道渲染细节
2. **可观测性**：每个事件都是结构化数据，天然支持日志、trace、metrics
3. **可恢复**：事件序列就是 transcript，崩溃后从 transcript 恢复

---

## 核心循环的数据流

<div class="mermaid">
flowchart TD
    A[agentLoop 启动] --> B[outer loop: 等待用户消息]
    B --> C[inner loop: 调用 LLM]
    C --> D{有 tool_calls?}
    D -->|是| E[并行执行工具]
    E --> F[emit tool_execution_end]
    F --> G[工具结果追加到 messages]
    G --> C
    D -->|否| H[emit message_end]
    H --> I{需要 follow-up?}
    I -->|是| B
    I -->|否| J[emit agent_end]
</div>

关键设计：

- **外层循环**处理多轮对话（follow-up messages）
- **内层循环**处理单轮中的多次工具调用
- 工具执行默认**并行**（`Promise.all`），可配置为顺序执行

---

## 工具执行：并行是默认

```typescript
// 简化自 agent-loop.ts
const toolResults = await Promise.all(
  response.toolCalls.map(async (toolCall) => {
    yield { type: 'tool_execution_start', toolCall }

    const result = await executeTool(toolCall, config)

    yield { type: 'tool_execution_end', result }
    return result
  })
)
```

当模型一次返回多个 tool_calls（比如同时读 3 个文件），pi-mono 会**并行执行所有工具**。这是 Coding Agent 速度快的关键原因之一。

对比 LangChain 的默认串行执行：

| 模式 | 3 个工具各 2 秒 | 总耗时 |
|------|----------------|--------|
| 串行 | 2 + 2 + 2 | 6 秒 |
| 并行 | max(2, 2, 2) | 2 秒 |

---

## Hooks：拦截与变换

pi-mono 提供了四个 Hook 点，让你在不修改核心循环的情况下注入逻辑：

```typescript
interface AgentHooks {
  beforeToolCall?: (toolCall: ToolCall) => ToolCall | null  // 拦截/修改工具调用
  afterToolCall?: (result: ToolResult) => ToolResult        // 修改工具结果
  transformContext?: (messages: Message[]) => Message[]      // 发送给 LLM 前变换上下文
  convertToLlm?: (message: Message) => LlmMessage          // 自定义消息格式转换
}
```

实际用途：

- `beforeToolCall`：安全过滤（阻止危险命令）、权限控制
- `afterToolCall`：结果截断（大文件只保留前 N 行）
- `transformContext`：上下文压缩、注入系统指令
- `convertToLlm`：适配不同 LLM Provider 的消息格式

---

## OpenClaw 的 5 阶段执行模型

pi-mono 的 Agent Loop 是基础，OpenClaw 在此之上增加了更完整的执行阶段：

```
Stage 1: RPC Validation
    → 验证请求格式、权限检查、速率限制
Stage 2: Skill Loading
    → 根据用户输入动态加载匹配的 Skill（SKILL.md）
Stage 3: Pi-Agent Runtime
    → 核心 Agent Loop（即 pi-mono 的 agentLoop）
Stage 4: Event Bridging
    → 把 EventStream 事件桥接到具体渠道（Slack/飞书/Web）
Stage 5: Persistence
    → JSONL transcript 持久化 + MEMORY.md 更新
```

### Hook 介入点

OpenClaw 定义了 4 个 Hook 介入点，覆盖执行全流程：

```typescript
interface OpenClawHooks {
  before_model_resolve: (req: ModelRequest) => ModelRequest
  // 可以动态切换模型（如简单问题用便宜模型）

  before_prompt_build: (context: ContextState) => ContextState
  // 在 assemble() 之前修改上下文状态

  before_tool_call: (call: ToolCall) => ToolCall | null
  // 拦截、修改或阻止工具调用（安全策略的主要入口）

  before_agent_reply: (reply: AgentReply) => AgentReply
  // 在回复发送给用户之前做后处理（脱敏、格式化）
}
```

### 并发控制：per-session 串行化

```typescript
// OpenClaw 用文件级写锁保证同一 session 不会并发执行
const lock = await acquireFileLock(`/tmp/openclaw-session-${sessionId}.lock`)
try {
  // 同一 session 的请求排队执行，不会并发
  await runAgentLoop(session)
} finally {
  await lock.release()
}
```

为什么？如果同一用户同时发两条消息，两个 Agent Loop 并发执行会导致：
- 消息顺序混乱（哪条先哪条后？）
- 上下文竞态（两个循环同时追加消息）
- 工具冲突（两个循环同时写同一个文件）

### 多层超时

```typescript
timeouts:
  waitForInput: 30_000      // 30 秒等待用户输入
  maxRuntime: 172_800_000   // 48 小时最大运行时间
  idleWatchdog: 300_000     // 5 分钟无活动自动暂停
  toolExecution: 120_000    // 单个工具最多 2 分钟
```

---

## Claude Code vs OpenClaw 的 Agent Loop 对比

根据 [claude-code-vs-openclaw](https://github.com/rrmars/claude-code-vs-openclaw) 的 11 维度对比（OpenClaw 赢 8 项）：

| 维度 | Claude Code | OpenClaw | 胜者 |
|------|-----------|----------|------|
| Context Compaction | LLM 摘要（无验证） | 标识符保留 + 质量检查点 + 重试 | OpenClaw |
| Context Pruning | 基于 token 计数 | 基于 `promptAuthority` 标志 + 语义重要性 | OpenClaw |
| Memory System | CLAUDE.md（单文件） | MEMORY.md + Daily Notes + DREAMS.md（三层） | OpenClaw |
| Agent Isolation | SubAgent（同进程） | 独立 workspace + 文件锁 | OpenClaw |
| Tool Safety | 命令黑名单 | 分层工具调度 + 沙箱 + Ed25519 签名 | OpenClaw |
| Cache Optimization | Prompt Caching（Anthropic 专有） | N/A | Claude Code |
| Frustration Detection | 检测用户沮丧并调整行为 | ❌ | Claude Code |

**核心差异**：Claude Code 是 Anthropic 的垂直集成产品（模型 + 工具 + 缓存一体化），OpenClaw 是 provider-agnostic 的开放架构。Claude Code 的 Prompt Caching 是独家优势，但 OpenClaw 在可插拔性和安全性上更强。

---

## 与传统框架的对比

### LangChain 的链式模型

```python
# LangChain: 每个步骤是一个 "chain"，线性组合
chain = prompt | llm | output_parser
result = chain.invoke({"question": "..."})
```

问题：当你需要工具调用循环时，链式模型就不够用了，需要引入 `AgentExecutor`，其内部实现和 pi-mono 的 Agent Loop 殊途同归。

### pi-mono 的循环模型

```typescript
// pi-mono: 一个循环就是整个 Agent
while (hasToolCalls) {
  results = await executeTools(toolCalls)
  messages.push(...results)
  response = await llm.chat(messages)
}
```

没有链、没有 DAG、没有中间抽象层。一个 while 循环解决所有问题。

---

## 面试高频题：Agent Loop 的设计决策

**Q：为什么用 EventStream 而不是直接返回结果？**

> 生产级 Agent 的单次任务可能执行几分钟甚至更长。如果等整个执行完才返回，用户体验极差（无响应）。EventStream 让 UI 可以实时渲染中间状态——正在思考、正在读文件、正在执行命令——每一步都有视觉反馈。

**Q：为什么默认并行执行工具？**

> Coding Agent 的典型操作（读文件、grep 搜索）是 IO 密集型，互相独立，没有数据依赖。并行执行可以将延迟从 O(n) 降到 O(1)。只有当工具间有显式依赖（写文件 → 读同一文件）时才需要串行。

**Q：Agent 和 Chatbot 的本质区别是什么？**

> 一行代码的区别：`if (response.toolCalls?.length) continue`。Chatbot 收到 LLM 回复就结束；Agent 检测到 tool_calls 后继续循环——执行工具、把结果追加到上下文、再次调用 LLM。这个循环持续到模型不再请求工具为止。

---

## 动手：跟踪一次完整执行

克隆 pi-mono 后，在 `agent-loop.ts` 的关键位置加 `console.log`：

```bash
git clone https://github.com/badlogic/pi-mono
cd pi-mono
```

观察一次 "读取 README.md 并总结" 任务的事件序列：

```
agent_start
turn_start
message_start (role: assistant)
message_update (delta: "让我读取...")
tool_execution_start (name: "read", args: {path: "README.md"})
tool_execution_end (result: "# pi-mono\n...")
message_start (role: assistant)
message_update (delta: "这个项目是...")
message_end
turn_end
agent_end
```

把这个事件流画成时序图，你就理解了整个执行模型。

---

下一篇：[RAG：检索增强的工程实现](../03-rag/index.html)
