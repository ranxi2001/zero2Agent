---
layout: default
title: 读懂 pi-mono 源码
description: TypeScript 实现的生产级 Coding Agent 架构拆解——正确的仓库、正确的结构
eyebrow: OpenClaw / 07
---

# 读懂 pi-mono 源码

[pi-mono](https://github.com/badlogic/pi-mono) 是 Mario Zechner 开源的终端 Coding Agent monorepo。TypeScript 实现，约 3000 行核心代码。

它的架构是 OpenClaw 的基础，也是理解 Claude Code、Cursor 等产品的最佳切入点。

---

## 仓库信息

```
仓库地址：https://github.com/badlogic/pi-mono
语言：TypeScript
包管理：pnpm workspace（monorepo）
核心代码量：约 3000 行
```

---

## 包结构

```
pi-mono/
├── packages/
│   ├── agent/         ← 核心：Agent Loop + 工具执行
│   ├── ai/           ← LLM 统一接口（多 Provider）
│   ├── coding-agent/ ← 交互式编码 Agent CLI
│   ├── tui/          ← 终端 UI（差分渲染）
│   └── web-ui/       ← Web 聊天界面组件
├── pnpm-workspace.yaml
└── package.json
```

### packages/agent — 必读

这是整个项目的核心。关键文件：

```
packages/agent/src/
├── agent-loop.ts      ← Agent Loop 主循环（最重要的文件）
├── tools/             ← 工具定义和执行
│   ├── index.ts       ← 工具注册表
│   ├── read.ts        ← 文件读取（offset/limit）
│   ├── write.ts       ← 文件写入
│   ├── edit.ts        ← 精确替换
│   ├── bash.ts        ← Shell 执行
│   ├── grep.ts        ← 正则搜索
│   └── agent.ts       ← SubAgent 派生
├── config.ts          ← Agent 配置
└── types.ts           ← 类型定义
```

### packages/ai — 选读

统一的 LLM 调用层，抹平不同 Provider 的 API 差异：

```
packages/ai/src/
├── providers/
│   ├── openai.ts      ← OpenAI API
│   ├── anthropic.ts   ← Anthropic Messages API
│   ├── google.ts      ← Google Gemini
│   └── bedrock.ts     ← AWS Bedrock
├── unified-api.ts     ← 统一接口
└── token-counter.ts   ← Token 计数
```

关键设计：所有 Provider 共享同一个 `ChatRequest` / `ChatResponse` 类型，上层代码不关心底层用的是哪家 LLM。

### packages/coding-agent — 参考

实际的 CLI 应用，展示了如何基于 `packages/agent` 构建一个可用的产品：

```
packages/coding-agent/src/
├── main.ts            ← CLI 入口
├── system-prompt.ts   ← 系统指令模板
├── permissions.ts     ← 权限控制（哪些操作需要确认）
└── hooks.ts           ← 生命周期钩子
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

pi-mono 选择 TypeScript 的原因：
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
git clone https://github.com/badlogic/pi-mono
cd pi-mono
pnpm install
pnpm -F coding-agent build
pnpm -F coding-agent start
```

第 4 小时的"改"是关键——读懂代码最快的方式是改代码，不是读文档。

---

## pi-skills 生态（1.6k stars）

pi-mono 有一个独立的 Skill 仓库 [pi-skills](https://github.com/earendil-works/pi-skills)，定义了跨平台 Skill 标准：

- 8 个官方 Skill（code-review、security-audit、test-writer 等）
- 使用 SKILL.md 格式（前文工具章节已介绍）
- 兼容 Claude Code、OpenClaw、Codex CLI、Amp、Droid

这意味着你为 pi-mono 写的 Skill，可以直接在 Claude Code 中使用（反之亦然）。

## Session Sharing 基础设施

pi-mono 包含 session 数据共享基础设施，用于社区贡献训练数据：

```typescript
// 用户可以选择性分享 session transcript
sessionSharing:
  enabled: false           // 默认关闭
  anonymize: true          // 开启时自动脱敏
  excludeTools: ['Bash']   // 排除 shell 命令（可能含敏感信息）
```

这为 Agent 的持续改进提供了数据来源——用户自愿贡献的真实使用轨迹。

---

## 面试中如何描述 pi-mono

**一句话版**：pi-mono 是一个 TypeScript 实现的终端 Coding Agent，核心是一个 EventStream 驱动的 Agent Loop，支持多 LLM Provider 和并行工具执行。

**展开版（30 秒）**：

> pi-mono 的架构分 5 个包：agent 包实现核心循环，ai 包抹平 OpenAI/Anthropic/Google 的 API 差异，coding-agent 是 CLI 产品层。核心循环是一个 AsyncGenerator——外层循环处理多轮对话，内层循环处理工具调用链。工具默认 Promise.all 并行执行。EventStream 设计让 UI 层（TUI 或 Web）和 Agent 逻辑完全解耦。

---

下一篇：[构建你的 OpenClaw](../08-build-openclaw/index.html)
