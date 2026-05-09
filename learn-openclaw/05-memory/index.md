---
layout: default
title: Context Engine：OpenClaw 的记忆架构
description: 从 MEMORY.md 持久化到可插拔 Context Engine，生产级 Agent 的完整记忆系统
eyebrow: OpenClaw / 05
---

# Context Engine：OpenClaw 的记忆架构

Agent 的"记忆"不是一个简单的消息列表。OpenClaw 的记忆系统分三层：

```
持久化记忆（MEMORY.md）  ← 跨 Session 存活，人类可编辑
Context Engine           ← 每轮动态组装上下文，token 预算内最大化信息量
Session 管理             ← 会话生命周期、transcript 持久化
```

这三层各自解决不同的问题，组合起来才是一个完整的生产级记忆系统。

---

## 第一层：MEMORY.md — 文件级持久化

OpenClaw 使用 Markdown 文件作为跨 Session 记忆的载体：

```typescript
// src/memory/root-memory-files.ts
export const MEMORY_FILE_NAMES = ['MEMORY.md', 'memory.md'] // canonical + legacy

export function findMemoryFile(workspacePath: string): string | null {
  for (const name of MEMORY_FILE_NAMES) {
    const fullPath = path.join(workspacePath, name)
    if (fs.existsSync(fullPath)) return fullPath
  }
  return null
}
```

### MEMORY.md 的设计哲学

为什么是 Markdown 文件而不是数据库？

1. **人类可读可编辑**：用户可以直接打开文件查看、修改、删除记忆
2. **Git 友好**：可以版本控制、diff、回滚
3. **零依赖**：不需要额外服务（Redis、Postgres），文件系统就够了
4. **LLM 原生格式**：Markdown 是 LLM 最擅长读写的格式

### MEMORY.md 的结构

```markdown
- [用户偏好](user_preferences.md) — 喜欢简洁回复，代码注释用英文
- [项目架构](project_arch.md) — monorepo，pnpm workspace，TypeScript
- [禁止操作](forbidden.md) — 不允许 git push，不删除 .env
```

每条记忆是一个独立的 `.md` 文件，MEMORY.md 是索引。这样：
- 单条记忆可以独立更新/删除
- 索引文件保持简短，不超出上下文预算
- Agent 按需读取具体记忆文件

### 记忆的写入时机

```typescript
// Agent 在以下时机写入记忆：
// 1. 用户显式要求 "记住这个"
// 2. 用户纠正了 Agent 的行为（feedback 类型）
// 3. 发现了非显而易见的项目规则
// 4. 用户角色/偏好信息

// 记忆不应该存储的：
// - 代码结构（读文件就能得到）
// - Git 历史（git log 就能查到）
// - 临时任务状态（用 task list 跟踪）
```

---

## 第二层：Context Engine — 可插拔的上下文管理

这是 OpenClaw 记忆系统的核心。Context Engine 负责在每次 LLM 调用前，**在 token 预算内组装最优的上下文**。

### 接口定义

```typescript
// src/context-engine/index.ts
export interface ContextEngine {
  // 初始化：加载 MEMORY.md、系统指令等
  bootstrap(config: EngineConfig): Promise<void>

  // 摄入新内容（用户消息、工具结果）
  ingest(event: ContextEvent): Promise<void>

  // 核心方法：组装发送给 LLM 的完整 messages
  assemble(budget: TokenBudget): Promise<Message[]>

  // 压缩：当上下文接近预算上限时触发
  compact(): Promise<void>

  // 每轮结束后的维护（更新摘要、清理过期内容）
  maintain(): Promise<void>

  // 生命周期钩子
  afterTurn(turnResult: TurnResult): Promise<void>
}
```

### assemble()：上下文组装的核心

`assemble()` 是整个记忆系统最关键的方法。它要在有限的 token 预算内，决定哪些信息进入上下文：

```typescript
async assemble(budget: TokenBudget): Promise<Message[]> {
  const messages: Message[] = []
  let tokensUsed = 0

  // 1. 系统指令（最高优先级，必须包含）
  const systemPrompt = this.buildSystemPrompt()
  messages.push({ role: 'system', content: systemPrompt })
  tokensUsed += countTokens(systemPrompt)

  // 2. MEMORY.md 索引（持久化记忆）
  const memoryContent = await this.loadMemoryIndex()
  if (memoryContent) {
    messages[0].content += `\n\n# Memory\n${memoryContent}`
    tokensUsed += countTokens(memoryContent)
  }

  // 3. 早期对话的压缩摘要（如果有）
  if (this.compressedSummary) {
    messages.push({ role: 'assistant', content: `[Earlier context]\n${this.compressedSummary}` })
    tokensUsed += countTokens(this.compressedSummary)
  }

  // 4. 近期对话（从最新往前填充，直到预算用完）
  const recentMessages = this.transcript.slice().reverse()
  const fittingMessages: Message[] = []

  for (const msg of recentMessages) {
    const msgTokens = countTokens(msg.content)
    if (tokensUsed + msgTokens > budget.maxTokens) break
    fittingMessages.unshift(msg)
    tokensUsed += msgTokens
  }

  messages.push(...fittingMessages)
  return messages
}
```

**优先级从高到低**：系统指令 > 持久化记忆 > 压缩摘要 > 近期对话。预算不够时，从低优先级开始裁剪。

### compact()：上下文压缩

当对话历史接近 token 预算时触发压缩：

```typescript
async compact(): Promise<void> {
  // 取出需要压缩的早期消息
  const cutoff = this.transcript.length - this.keepRecentCount
  const toCompress = this.transcript.slice(0, cutoff)

  // 用 LLM 生成摘要
  const summary = await this.llm.chat([
    { role: 'system', content: 'Summarize the key decisions, findings, and context from this conversation. Preserve actionable information.' },
    ...toCompress
  ])

  // 替换为摘要
  this.compressedSummary = summary.content
  this.transcript = this.transcript.slice(cutoff)
}
```

**面试关键区分：压缩 vs 截断**

| 方案 | 做法 | 问题 |
|------|------|------|
| 截断 | 直接丢弃最早的消息 | 可能丢失关键决策和约束 |
| 压缩 | 用 LLM 生成摘要替代原始消息 | 保留语义，代价是一次 LLM 调用 |
| OpenClaw 方案 | 压缩 + 持久化关键信息到 MEMORY.md | 重要信息永不丢失 |

### 可插拔架构

```typescript
// src/context-engine/registry.ts
// 进程全局单例注册表，支持切换不同的 Context Engine 实现
class ContextEngineRegistry {
  private engines: Map<string, ContextEngineFactory> = new Map()
  private activeEngine: string = 'default'

  register(name: string, factory: ContextEngineFactory): void {
    this.engines.set(name, factory)
  }

  getActive(): ContextEngine {
    return this.engines.get(this.activeEngine)!.create()
  }
}

// 配置文件中选择策略
// config.plugins.slots.contextEngine = "legacy" | "semantic" | "custom"
```

为什么做成可插拔的？不同场景需要不同的上下文策略：
- 短对话场景：不需要压缩，直接全量传入
- 长任务场景：激进压缩，只保留最近几轮 + 任务计划
- RAG 场景：每轮动态注入检索结果，压缩早期检索内容

---

## Dreaming 系统：记忆的自动整理

OpenClaw 独有的 Dreaming 机制——受人类睡眠中记忆巩固的启发，通过定时任务自动整理和丰富长期记忆。

### 三阶段合成

| 阶段 | 对应睡眠 | 做什么 |
|------|---------|--------|
| **Light Sleep** | 浅睡眠 | 扫描当日对话，提取候选记忆片段 |
| **Deep Sleep** | 深睡眠 | 合并相似主题、修复引用、消除矛盾 |
| **REM** | 快速眼动 | 跨主题关联、生成新的 Compiled Truth |

### 记忆评分公式

每条候选记忆通过加权评分决定是否被"提升"为长期记忆：

```
Score = frequency(0.24) + relevance(0.30) + query_diversity(0.15)
      + recency(0.15) + consolidation(0.10) + conceptual_richness(0.06)
```

| 维度 | 权重 | 含义 |
|------|------|------|
| relevance | 0.30 | 与用户核心工作的相关度 |
| frequency | 0.24 | 被提及/使用的频率 |
| query_diversity | 0.15 | 在不同类型查询中出现 |
| recency | 0.15 | 最近的信息权重更高 |
| consolidation | 0.10 | 已经被其他记忆引用的次数 |
| conceptual_richness | 0.06 | 包含的概念复杂度 |

只有**有据可查的记忆片段**（grounded snippets）才有资格被提升——防止幻觉记忆进入长期存储。

### 运行机制

```typescript
// 默认 cron 配置：每天凌晨 3 点运行
dreaming:
  schedule: "0 3 * * *"
  phases: [light, deep, rem]
  maxDuration: 1800  // 最多运行 30 分钟
```

输出写入 `DREAMS.md`——Agent 的"巩固日记"：

```markdown
<!-- DREAMS.md -->
## 2026-05-09 Consolidation

### Promoted to long-term
- 用户偏好 TypeScript monorepo 结构 (score: 0.87)
- 项目禁止 git push 到 remote (score: 0.82)

### Merged
- "API 架构偏好" + "微服务选型" → 合并为 "后端架构偏好"

### Retired
- "调试 ESLint 配置" — 问题已解决，不再相关
```

### 面试价值

Dreaming 系统体现了一个关键认知：**记忆不是只写不删的日志，而是需要主动维护的知识库**。面试中提到这个机制，能展示你对"记忆质量 > 记忆数量"这个生产级认知的理解。

---

## Compaction：标识符保留策略

OpenClaw 的 Compaction 不是简单的"用 LLM 总结"——它有一套精确的规则确保压缩后的上下文仍然可用：

```typescript
// 压缩时的标识符保留策略
compaction:
  identifierPreservation: "strict"  // 默认严格模式
  // strict: 文件路径、函数名、变量名、行号必须原样保留
  // relaxed: 只保留文件路径和函数名
  // none: 不做特殊保留（不推荐）
```

**为什么需要标识符保留？**

```
// 不保留标识符的压缩结果：
"之前分析了认证模块，发现了几个安全问题。"
→ Agent 无法继续工作（哪个文件？哪个函数？哪一行？）

// 保留标识符的压缩结果：
"分析了 src/auth/login.ts:42-78 的 validateToken() 函数，
发现 JWT 验证缺少 exp 字段检查（第 56 行）。"
→ Agent 可以直接定位并继续操作
```

Compaction 还支持**双模式**：
- **自动模式**：token 使用率超过阈值时自动触发
- **手动模式**：用户显式请求（如 Claude Code 的 `/compact` 命令）

压缩前会执行 **auto-flush**——把关键信息写入 MEMORY.md，确保压缩不会导致知识丢失。

---

## 记忆后端：可插拔存储

OpenClaw 支持多种记忆后端：

| 后端 | 适用场景 | 特点 |
|------|---------|------|
| **SQLite**（默认） | 个人使用、本地部署 | 零配置、单文件、够用 |
| **LanceDB** | 需要向量检索 | 嵌入式向量库，无服务 |
| **Honcho** | 多用户、大规模 | 专为 AI Agent 设计的记忆服务 |
| **GBrain** | 生产级、企业级 | Postgres + pgvector，功能最全 |

---

## 第三层：Session 管理

```typescript
// src/sessions/index.ts
export interface Session {
  id: string                    // 唯一标识
  createdAt: Date
  lastActiveAt: Date
  transcript: TranscriptEvent[] // 完整事件记录
  config: SessionConfig         // 模型、级别等覆盖配置
}
```

Session 管理解决的问题：
- **多用户隔离**：不同用户的会话互不干扰
- **断点续传**：`agentLoopContinue()` 从 transcript 恢复
- **审计追踪**：所有交互都有记录

---

## GBrain：外部记忆宿主（高级）

[GBrain](https://github.com/garrytan/gbrain) 是 OpenClaw 的生产级外部记忆系统，解决 MEMORY.md 无法处理的大规模记忆场景：

### 架构

```
Postgres + pgvector
    ├── 混合检索（向量 + BM25 + RRF 融合）
    ├── Compiled Truth 页（当前理解，可被更新）
    ├── Timeline 条目（追加式证据链，不可变）
    └── 知识图谱（实体引用 + 类型化链接）
```

### Compiled Truth + Timeline 模式

传统做法：每次新信息来了就追加一条记忆。问题：记忆越来越多，检索越来越难。

GBrain 的做法：

```
Page: "用户的技术栈偏好"
├── Compiled Truth: "偏好 TypeScript + pnpm，讨厌 Python 类型系统"
└── Timeline:
    ├── 2025-03-01: 用户说 "我主要写 TypeScript"
    ├── 2025-03-15: 用户说 "Python 的类型注解太弱了"
    └── 2025-04-02: 用户在项目中使用了 pnpm workspace
```

Compiled Truth 是 Agent 直接使用的结论；Timeline 是支撑这个结论的原始证据。当新信息到来时，更新 Compiled Truth。

### Dream Cycle（夜间合成）

GBrain 运行定时任务进行知识整理：
- 合并相似主题的 Pages
- 检测过时信息并标记
- 从 Timeline 中提取新的 Compiled Truth
- 丰富知识图谱的链接关系

---

## GBrain 生产数据

GBrain 在实际生产环境中的规模（Garry Tan 的个人使用）：

```
- 17,888 个知识页面
- 4,383 个人物实体
- 723 个公司实体
- P@5: 49.1%（前 5 结果中有正确答案的概率）
- R@5: 97.9%（正确答案出现在前 5 的概率）
```

### Minions Job Queue

GBrain 用 Postgres 原生 Job Queue（Minions）替代了不稳定的 sub-agent 方式做后台任务：

```typescript
// 传统方式：spawn sub-agent 做异步任务
// 问题：进程崩溃丢失状态、无法重试、无法观测

// GBrain 方式：Postgres 持久化 Job Queue
await minions.enqueue({
  type: 'consolidate_memory',
  payload: { pageId: 'tech-preferences', newEvidence: '...' },
  retries: 3,
  timeout: 60_000
})
```

好处：crash-safe、可重试、可观测、有事务保证。

### 设计原则：确定性操作优先于 LLM 判断

GBrain 在能用确定性逻辑的地方绝不用 LLM：
- 实体抽取：正则 + 规则，不用 NER 模型
- 关系链接：模式匹配（"works_at"、"invested_in"），不用 LLM 推理
- 知识图谱连边：基于共现和明确语法结构，不用向量相似度

LLM 只在必须推理时使用（如 Compiled Truth 的更新、Deep Sleep 阶段的冲突消解）。

---

## 对比：各家 Agent 的记忆方案

| Agent | 短期记忆 | 长期记忆 | 跨 Session |
|-------|---------|---------|-----------|
| ChatGPT | 消息列表 | Memory 功能（自然语言） | ✅ |
| Claude Code | 消息列表 + compact | CLAUDE.md + MEMORY.md | ✅ |
| pi-mono | 消息列表 | ❌ | ❌ |
| OpenClaw | Context Engine | MEMORY.md + GBrain | ✅ |
| LangChain | ConversationBufferMemory | 向量数据库 | 需自建 |

---

## 面试高频题

**Q：Agent 的"记忆"和"上下文"有什么区别？**

> 上下文是单次 LLM 调用时传入的 messages——有 token 上限，会话结束就消失。记忆是跨会话持久化的信息——用户偏好、项目规则、关键决策。Context Engine 的工作就是把合适的记忆加载进当前上下文。

**Q：为什么 OpenClaw 用文件（MEMORY.md）而不是数据库存记忆？**

> 三个原因：1) 人类可直接查看和编辑（透明性）；2) Git 版本控制（可追溯）；3) 零依赖（不需要额外服务）。对大规模记忆场景（数千条），再引入 GBrain（Postgres）。

**Q：Context Engine 的 assemble() 方法为什么重要？**

> 它解决了 Agent 的核心难题：token 预算有限，但需要最大化上下文信息量。assemble() 的优先级策略决定了 Agent "记住什么、忘记什么"——这直接影响任务完成质量。好的 assemble 策略 = 好的 Agent。

**Q：压缩摘要的弊端是什么？怎么缓解？**

> 弊端：摘要会丢失细节（具体代码行号、精确数字）。缓解方案：1) 把关键信息持久化到 MEMORY.md（不依赖摘要）；2) 压缩时用 LLM 判断哪些细节必须保留；3) 保留最近 N 轮完整消息不压缩（近期信息最重要）。

---

下一篇：[Multi-Agent：子进程隔离与多渠道路由](../06-multi-agent/index.html)
