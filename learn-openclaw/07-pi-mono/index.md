---
layout: default
title: 读懂 Pi（原 pi-mono）源码
description: TypeScript Agent Harness 的源码分层、核心包与阅读方法
eyebrow: OpenClaw / 07
---

# 读懂 Pi（原 pi-mono）源码

[Pi](https://github.com/earendil-works/pi) 是 Mario Zechner 发起的 TypeScript Agent Harness 项目。`pi-mono` 是它早期的源码仓库名；仓库后来迁移并更名为 `earendil-works/pi`，旧链接仍会重定向到当前仓库。

本章阅读的是 Pi 的源码仓库。重点关注 `pi-ai` 和 `pi-agent-core` 如何组成底层运行时，再看 `pi-coding-agent` 如何把这些能力组装成用户实际运行的 `pi` CLI。

> **版本说明（2026-07）**：Pi 和 OpenClaw 都在快速演进。本章使用当前包名和 npm workspace 结构；历史文章里的 `badlogic/pi-mono`、pnpm 命令和 `web-ui` 包已经不再对应当前主分支。

---

## 仓库信息

```
当前仓库：https://github.com/earendil-works/pi
历史名称：badlogic/pi-mono（旧链接自动重定向）
语言：TypeScript
包管理：npm workspaces（monorepo）
公开包：@earendil-works/pi-*
```

---

## 包结构

```
pi/
├── packages/
│   ├── agent/         ← @earendil-works/pi-agent-core：通用 Agent Runtime
│   ├── ai/            ← @earendil-works/pi-ai：多 Provider LLM 接口
│   ├── coding-agent/  ← @earendil-works/pi-coding-agent：交互式 CLI
│   ├── tui/           ← @earendil-works/pi-tui：终端 UI
│   └── orchestrator/  ← 实验性编排包
├── package-lock.json
└── package.json
```

### packages/agent — 必读

这是整个项目的核心。关键文件：

```
packages/agent/src/
├── agent-loop.ts      ← Agent Loop 主循环（最重要的文件）
├── agent.ts           ← Agent 状态与生命周期封装
├── harness/           ← Prompt、Session、Skills 等 Harness 能力
├── node.ts            ← Node.js 运行时入口
├── proxy.ts           ← Runtime 代理与适配
└── types.ts           ← 类型定义
```

`pi-agent-core` 保持通用，不直接捆绑 Read、Edit、Bash 等 Coding 工具。这些面向编码场景的工具位于 `packages/coding-agent/src/core/tools/`，由产品层选择和组装。

### packages/ai — 选读

统一的 LLM 调用层，抹平不同 Provider 的 API 差异：

```
packages/ai/src/
├── api/               ← 各类 API 协议与流式适配
├── providers/         ← Provider 注册与配置
├── models.ts          ← 模型定义和发现
├── types.ts           ← 统一消息、工具和流式事件类型
└── index.ts           ← 对外导出
```

关键设计：所有 Provider 共享同一个 `ChatRequest` / `ChatResponse` 类型，上层代码不关心底层用的是哪家 LLM。

### packages/coding-agent — 参考

实际的 CLI 应用，展示了如何基于 `packages/agent` 构建一个可用的产品：

```
packages/coding-agent/src/
├── cli.ts             ← pi 命令入口
├── main.ts            ← 应用启动与模式选择
├── core/              ← Session、Prompt、Skills、工具与配置
├── modes/             ← 交互模式与输出模式
└── config.ts          ← CLI 配置
```

### packages/tui — 选读

终端 UI 的差分渲染实现。和 Agent 逻辑无关，但展示了 EventStream 如何驱动 UI：

```typescript
// 消费 EventStream，实时渲染到终端
for await (const event of agentLoop(config)) {
  switch (event.type) {
    case 'message_update':
      tui.appendText(event.delta)
      break
    case 'tool_execution_start':
      tui.showSpinner(`Running ${event.toolCall.name}...`)
      break
    case 'tool_execution_end':
      tui.hideSpinner()
      tui.showResult(event.result)
      break
  }
}
```

---

## 核心文件：agent-loop.ts 深度解析

### 入口函数

```typescript
// 两个入口，返回同一种 EventStream
export async function* agentLoop(config: AgentConfig): AsyncGenerator<AgentEvent> {
  yield { type: 'agent_start' }

  const messages: Message[] = [
    { role: 'system', content: config.systemPrompt }
  ]

  // 外层循环：处理多轮用户输入
  while (true) {
    const userMessage = await config.getNextMessage()
    if (!userMessage) break

    messages.push({ role: 'user', content: userMessage })
    yield { type: 'turn_start' }

    // 内层循环：处理工具调用链
    while (true) {
      const response = await config.llm.chat(messages, { tools: config.tools })
      messages.push(response)

      yield { type: 'message_end', content: response }

      if (!response.toolCalls?.length) break

      // 并行执行所有工具
      const results = await Promise.all(
        response.toolCalls.map(async (tc) => {
          yield { type: 'tool_execution_start', toolCall: tc }
          const result = await executeToolCall(tc, config)
          yield { type: 'tool_execution_end', result }
          return result
        })
      )

      // 工具结果追加到 messages
      messages.push(...results.map(r => ({ role: 'tool', ...r })))
    }

    yield { type: 'turn_end' }
  }

  yield { type: 'agent_end' }
}
```

### 恢复函数

```typescript
export async function* agentLoopContinue(
  config: AgentConfig,
  transcript: AgentEvent[]
): AsyncGenerator<AgentEvent> {
  // 从 transcript 重建 messages 状态
  const messages = rebuildMessagesFromTranscript(transcript)

  // 然后进入和 agentLoop 一样的循环
  // ...（同上）
}
```

`agentLoopContinue` 的存在让 Agent 支持断点续传——进程崩溃或用户关闭终端后，从持久化的 transcript 恢复。

---

## packages/ai：多 Provider 统一接口

```typescript
// packages/ai/src/unified-api.ts
export interface LlmProvider {
  chat(request: ChatRequest): Promise<ChatResponse>
  stream(request: ChatRequest): AsyncGenerator<ChatChunk>
  countTokens(text: string): number
}

export interface ChatRequest {
  messages: Message[]
  tools?: ToolDefinition[]
  maxTokens?: number
  temperature?: number
}

export interface ChatResponse {
  role: 'assistant'
  content: string
  toolCalls?: ToolCall[]
  usage: { inputTokens: number; outputTokens: number }
}
```

```typescript
// 按配置选择 Provider
export function createProvider(config: ProviderConfig): LlmProvider {
  switch (config.provider) {
    case 'openai': return new OpenAIProvider(config)
    case 'anthropic': return new AnthropicProvider(config)
    case 'google': return new GoogleProvider(config)
    case 'bedrock': return new BedrockProvider(config)
  }
}
```

这意味着切换 LLM 只需要改配置，不需要改任何 Agent 逻辑代码。

---

## 关键设计决策

### 1. TypeScript 而非 Python

Pi 选择 TypeScript 的原因：
- **类型安全**：工具参数、LLM 响应都有编译期类型检查
- **异步原生**：`async/await` + `AsyncGenerator` 天然适配流式处理
- **性能**：V8 引擎的并发性能远超 CPython
- **前后端统一**：Web UI 和 Agent 共享类型定义

### 2. AsyncGenerator 作为 EventStream

为什么不用 EventEmitter 或 Observable？

```typescript
// AsyncGenerator 的优势：背压控制
for await (const event of agentLoop(config)) {
  // 消费者慢了，生产者自动暂停
  await slowRender(event)
}
```

AsyncGenerator 天然支持背压（backpressure）——如果 UI 渲染慢了，Agent Loop 会自动暂停等待，不会堆积事件导致内存爆炸。

### 3. offset/limit 的文件读取

```typescript
// 不是 readFile 整个文件
const content = await readTool.execute({
  path: 'src/main.ts',
  offset: 50,   // 从第 50 行开始
  limit: 30     // 只读 30 行
})
```

对大型代码库，这个设计让上下文使用量降低约 60%。模型先读文件头了解结构，再精确读需要的部分。

### 4. 工具结果截断

```typescript
function truncateToolResult(result: string, maxChars: number = 10000): string {
  if (result.length <= maxChars) return result
  const half = maxChars / 2
  return `${result.slice(0, half)}\n\n[... ${result.length - maxChars} chars omitted ...]\n\n${result.slice(-half)}`
}
```

Shell 命令输出、大文件内容——保留头尾，截断中间。比完整塞入上下文或完全丢弃都好。

---

## 4 小时阅读计划

| 时间 | 内容 | 目标 |
|------|------|------|
| 第 1 小时 | 跑通 `packages/coding-agent`，用它完成一个简单任务 | 建立直觉 |
| 第 2 小时 | 读 `packages/agent/src/agent-loop.ts` | 理解核心循环 |
| 第 3 小时 | 读 `packages/ai/src/providers/` 任选一个 | 理解 LLM 调用层 |
| 第 4 小时 | 改一个工具（如增加 offset/limit 参数）或切换 Provider | 验证理解 |

```bash
# 开始
git clone https://github.com/earendil-works/pi
cd pi
npm install --ignore-scripts
npm run build

# macOS / Linux / Git Bash：从源码启动 pi
./pi-test.sh
```

Windows PowerShell 可以先全局安装 `@earendil-works/pi-coding-agent` 后运行 `pi`；如果要直接调试源码，使用 Git Bash 或 WSL 执行 `pi-test.sh` 更省事。

第 4 小时的"改"是关键——读懂代码最快的方式是改代码，不是读文档。

---

## pi-skills 生态（1.6k stars）

Pi 生态有独立的 Skill 仓库 [pi-skills](https://github.com/earendil-works/pi-skills)，采用基于 `SKILL.md` 的 Skill 格式：

- 8 个官方 Skill（code-review、security-audit、test-writer 等）
- 使用 SKILL.md 格式（前文工具章节已介绍）
- 兼容 Claude Code、OpenClaw、Codex CLI、Amp、Droid

这意味着为 Pi 编写的 Skill 可以较低成本迁移到其他采用兼容 `SKILL.md` 约定的 Agent；具体字段和加载规则仍应以各项目文档为准。

## Session Sharing 基础设施

Pi 包含 Session 数据共享基础设施，用于社区贡献训练数据：

```typescript
// 用户可以选择性分享 session transcript
sessionSharing:
  enabled: false           // 默认关闭
  anonymize: true          // 开启时自动脱敏
  excludeTools: ['Bash']   // 排除 shell 命令（可能含敏感信息）
```

这为 Agent 的持续改进提供了数据来源——用户自愿贡献的真实使用轨迹。

---

## 面试中如何描述 Pi / pi-mono

**一句话版**：Pi 是 TypeScript 实现的 Agent Harness 与终端 Coding Agent；pi-mono 是它的历史仓库名。它将多模型接口、通用 Agent Runtime、终端 UI 和 CLI 产品拆成独立包。

**展开版（30 秒）**：

> Pi 当前包含 5 个工作区包：agent 包实现通用运行时，ai 包抹平 OpenAI、Anthropic、Google 等 Provider 的差异，coding-agent 是 CLI 产品层，tui 负责终端渲染，orchestrator 提供实验性编排能力。这样的分层让上层产品可以组合底层能力，而不必把完整 `pi` CLI 当成黑盒进程调用。

---

下一篇：[构建你的 OpenClaw](../08-build-openclaw/index.html)
