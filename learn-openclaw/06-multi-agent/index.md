---
layout: default
title: Multi-Agent：子进程隔离与多渠道路由
description: OpenClaw 的 SubAgent 生成、上下文隔离和 20+ 渠道统一接入架构
eyebrow: OpenClaw / 06
---

# Multi-Agent：子进程隔离与多渠道路由

OpenClaw 的多 Agent 架构有两个维度：

1. **SubAgent**：主 Agent 派生子 Agent 处理独立子任务（上下文隔离）
2. **Multi-Channel**：同一个 Agent 通过 20+ 消息平台接入（统一路由）

---

## SubAgent：上下文隔离的正确姿势

### 为什么需要 SubAgent

单 Agent 处理复杂任务时，上下文会被中间过程污染：

```
任务：审查 3 个模块的安全问题

单 Agent 做法：
  读 auth.py（500 行进入上下文）
  → 分析 auth.py（LLM 输出 200 token）
  → 读 api.py（800 行进入上下文）
  → 分析 api.py（上下文已经很满了）
  → 读 db.py（上下文溢出，早期分析被压缩/截断）
  → 最终报告质量很差（前面的分析已经丢了）
```

SubAgent 做法：每个模块由独立的子 Agent 处理，各自维护独立上下文：

```
主 Agent：拆任务 + 收结果
  ├── SubAgent 1：审查 auth.py（独立上下文）→ 返回报告
  ├── SubAgent 2：审查 api.py（独立上下文）→ 返回报告
  └── SubAgent 3：审查 db.py（独立上下文）→ 返回报告
主 Agent：合并 3 份报告
```

### OpenClaw 的 SubAgent 实现

```typescript
// src/context-engine/index.ts
export interface ContextEngine {
  // SubAgent 生命周期
  prepareSubagentSpawn(task: SubagentTask): SpawnConfig
  onSubagentEnded(result: SubagentResult): void
}
```

```typescript
// 主 Agent 中派生子 Agent
const subagentResult = await spawnSubagent({
  task: '审查 src/auth.py 的安全问题，返回发现的漏洞列表',
  tools: ['Read', 'Grep', 'Bash'],  // 子 Agent 可用的工具子集
  budget: { maxTokens: 32000 },       // 独立的 token 预算
  systemPrompt: '你是安全审计专家...'  // 可以有专用指令
})

// subagentResult 只包含最终输出，不包含中间过程
// 主 Agent 的上下文不会被子 Agent 的工具调用记录污染
```

### 关键设计决策

| 决策 | pi-mono / OpenClaw 的选择 | 原因 |
|------|--------------------------|------|
| 子 Agent 进程模型 | 同进程异步（非 fork） | 避免进程间通信开销 |
| 上下文共享 | 不共享（完全隔离） | 防止上下文污染 |
| 工具权限 | 子集（主 Agent 指定） | 最小权限原则 |
| 结果格式 | 纯文本摘要 | 主 Agent 只需结论，不需过程 |

---

## Worktree 隔离：文件系统级并行

当多个 SubAgent 需要**同时修改代码**时，上下文隔离不够——还需要文件系统隔离：

```typescript
// Git Worktree：每个子 Agent 在独立的工作目录中操作
async function spawnWithWorktree(task: SubagentTask): Promise<SubagentResult> {
  // 创建临时 worktree
  const worktreePath = await git.worktree.add(`/tmp/agent-${uuid()}`, 'HEAD')

  const result = await spawnSubagent({
    ...task,
    workingDirectory: worktreePath  // 子 Agent 在 worktree 中工作
  })

  if (result.hasChanges) {
    // 子 Agent 有代码修改：返回 worktree 路径和分支
    return { ...result, worktreePath, branch: result.branch }
  } else {
    // 无修改：自动清理 worktree
    await git.worktree.remove(worktreePath)
    return result
  }
}
```

这解决了并行 Agent 的"踩踏"问题——两个 Agent 同时改同一个文件不会冲突。

---

## Multi-Channel 路由：20+ 平台统一接入

OpenClaw 的另一个多 Agent 维度是**渠道**——同一个 Agent 能力通过不同消息平台接入：

```typescript
// src/channels/index.ts
export interface Channel {
  name: string
  connect(): Promise<void>
  onMessage(handler: MessageHandler): void
  sendMessage(userId: string, content: string): Promise<void>
}
```

```
src/channels/
  telegram/     ← Telegram Bot API
  slack/        ← Slack Bolt
  discord/      ← Discord.js
  whatsapp/     ← WhatsApp Business API
  feishu/       ← 飞书开放平台
  dingtalk/     ← 钉钉机器人
  wechat/       ← 微信公众号/企业微信
  matrix/       ← Matrix 协议
  irc/          ← IRC
  email/        ← IMAP/SMTP
  web/          ← WebSocket
  cli/          ← 终端标准输入输出
  ...           ← 共 20+ 渠道
```

### 统一网关架构

<div class="mermaid">
flowchart LR
    A[Telegram] --> G[Gateway]
    B[Slack] --> G
    C[飞书] --> G
    D[Web] --> G
    E[CLI] --> G
    G --> H[Session Router]
    H --> I[Agent Instance\n+ Context Engine]
    I --> J[Tools / MCP]
</div>

```typescript
// src/gateway/router.ts
export class SessionRouter {
  private sessions: Map<string, AgentSession> = new Map()

  async route(channelMessage: ChannelMessage): Promise<string> {
    // 用 channel + userId 唯一标识一个 session
    const sessionKey = `${channelMessage.channel}:${channelMessage.userId}`

    let session = this.sessions.get(sessionKey)
    if (!session) {
      session = await this.createSession(sessionKey)
      this.sessions.set(sessionKey, session)
    }

    // 将消息路由到对应 session 的 Agent
    return session.agent.processMessage(channelMessage.text)
  }
}
```

每个用户在每个渠道有独立的 Session，互不干扰。同一用户跨渠道可以选择共享 Session 或独立 Session。

### Binding-based 消息路由

当消息到达时，OpenClaw 用级联匹配策略决定路由到哪个 Agent 实例：

```
1. Exact Peer ID    → 指定了具体 Agent ID，直接路由
2. Thread Inherit   → 在已有会话线程中，继承该线程的 Agent
3. Role Routing     → 根据消息内容匹配 Agent 角色（如 @security-bot）
4. Account Fallback → 用户的默认 Agent
5. Default          → 系统兜底 Agent
```

### Session 重置策略

```typescript
session:
  resetPolicy: "daily"      // 每天 4 AM 重置上下文
  // 或
  resetPolicy: "idle"       // 5 分钟无活动后重置
  // 或
  resetPolicy: "manual"     // 只有用户手动 /reset 时重置

  isolationScope: "channel" // 按渠道隔离
  // 或
  isolationScope: "user"    // 按用户隔离（跨渠道共享）
```

### 跨 Agent 记忆搜索

多 Agent 场景下，Agent A 可以搜索 Agent B 的记忆（需要配置授权）：

```typescript
// 配置跨 Agent 记忆访问
memorySearch:
  qmd:
    extraCollections:
      - agentId: "security-bot"
        scope: "readonly"
      - agentId: "docs-bot"
        scope: "readonly"
```

这让专业化 Agent（安全审计、文档助手）的知识可以被通用 Agent 引用，而不需要重复存储。

---

## Agent Teams：协作模式

超越简单的 SubAgent 派生，OpenClaw 支持多种协作模式：

### 模式 1：Fan-out / Fan-in（并行）

```typescript
// 任务可并行拆分时
const tasks = [
  { task: '分析 auth 模块', agent: 'security-reviewer' },
  { task: '分析 api 模块', agent: 'security-reviewer' },
  { task: '检查测试覆盖', agent: 'test-analyst' }
]

// 并行执行所有子任务
const results = await Promise.all(
  tasks.map(t => spawnSubagent(t))
)

// 合并结果
const report = await synthesize(results)
```

### 模式 2：Pipeline（串行依赖）

```typescript
// 任务有先后依赖时
const analysis = await spawnSubagent({ task: '分析代码结构' })
const plan = await spawnSubagent({ task: `基于以下分析制定重构计划：${analysis}` })
const implementation = await spawnSubagent({ task: `执行以下重构计划：${plan}` })
```

### 模式 3：Debate（对抗验证）

```typescript
// 需要减少幻觉时：一个生成，一个验证
const proposal = await spawnSubagent({
  task: '给出修复方案',
  systemPrompt: '你是修复专家...'
})
const review = await spawnSubagent({
  task: `审查以下修复方案是否正确：${proposal}`,
  systemPrompt: '你是严格的代码审查者，找出方案中的问题...'
})
```

---

## 什么时候用多 Agent

| 信号 | 单 Agent | 多 Agent |
|------|---------|---------|
| 上下文会溢出 | ❌ | ✅ 子 Agent 各自维护小上下文 |
| 子任务可并行 | ❌ | ✅ Promise.all 加速 |
| 需要专业化 system prompt | ❌ | ✅ 不同子 Agent 不同人设 |
| 需要减少幻觉 | ❌ | ✅ 生成 + 验证对抗 |
| 需要同时改多个文件 | ❌ | ✅ Worktree 隔离 |
| 任务简单、上下文够用 | ✅ | ❌ 不要过度设计 |

**核心原则：如果单 Agent 能搞定，不要引入多 Agent。多 Agent 增加的复杂度必须被明确的收益覆盖。**

---

## 面试高频题

**Q：主从调度（Orchestrator + Worker）架构的问题是什么？**

> 核心问题是上下文污染。Worker 的执行细节（大量工具调用记录、中间结果）全部流回 Orchestrator，它的上下文迅速膨胀，判断力下降。正确做法是 Worker 只返回最终结论，不返回过程。

**Q：SubAgent 和 MCP Server 的区别？**

> SubAgent 是一个完整的 Agent（有 LLM 推理能力、有独立上下文），处理需要思考和决策的子任务。MCP Server 是纯工具（无 LLM 调用），执行确定性操作（查数据库、调 API）。选择依据：子任务是否需要"思考"。

**Q：如何设计多 Agent 间的通信协议？**

> OpenClaw 的做法是不通信——子 Agent 之间完全隔离，只通过主 Agent 的任务描述和结果汇总间接交互。避免了消息格式协商、死锁、竞态等分布式系统经典问题。如果确实需要通信（如 Debate 模式），用结构化文本（Markdown）作为接口，而不是自定义协议。

---

下一篇：[读懂 pi-mono 源码](../07-pi-mono/index.html)
