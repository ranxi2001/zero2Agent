---
layout: default
title: 构建你的 OpenClaw
description: Fork pi-mono，接入你的 LLM，定制 Skill，部署到消息平台
eyebrow: OpenClaw / 08
---

# 构建你的 OpenClaw

这一节是动手实践。目标：把 pi-mono 改造成属于你自己的 Agent，部署后通过 Slack 或飞书对话。

完成之后你会有一个叫 `[YourName]Claw` 的个人 Coding Agent。

---

## 第一步：Fork 并运行 pi-mono

```bash
# Fork（在 GitHub 上操作）然后克隆
git clone https://github.com/[你的用户名]/pi-mono
cd pi-mono

# 安装依赖（pnpm monorepo）
pnpm install

# 构建所有包
pnpm build

# 运行 coding-agent
pnpm -F coding-agent start
```

先跑通原版，确认环境没问题。你应该能在终端与 Agent 对话。

---

## 第二步：配置 LLM Provider

pi-mono 支持多家 LLM。编辑配置文件或设置环境变量：

```bash
# 方案 A：使用 Anthropic（推荐，和 Claude Code 同源）
export ANTHROPIC_API_KEY="sk-ant-xxx"
export LLM_PROVIDER="anthropic"
export LLM_MODEL="claude-sonnet-4-6"

# 方案 B：使用 OpenAI 兼容协议（DeepSeek / Kimi / 智谱）
export OPENAI_API_KEY="sk-xxx"
export OPENAI_BASE_URL="https://api.deepseek.com/v1"
export LLM_PROVIDER="openai"
export LLM_MODEL="deepseek-chat"

# 方案 C：使用 Google Gemini
export GOOGLE_API_KEY="xxx"
export LLM_PROVIDER="google"
export LLM_MODEL="gemini-2.5-pro"
```

建议写进 `.env` 文件（加入 `.gitignore`）：

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-xxx
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-6
```

---

## 第三步：定制系统指令

创建你自己的 system prompt 文件：

```markdown
<!-- AGENTS.md — 你的 Agent 的"人格" -->
你是 [YourName]Claw，一个专注于 TypeScript 和 Python 的 Coding Agent。

## 工作方式
- 修改代码前先读取并理解现有实现
- 遇到不确定的需求，直接问用户
- 每次修改后运行相关测试
- 用中文和用户对话，代码注释用英文

## 限制
- 不修改 .env 文件
- 不执行 git push（需要用户确认）
- 不删除 node_modules 以外的目录

## 知识
- 熟悉 pnpm workspace monorepo 结构
- 了解 ESLint + Prettier 规范
- 知道项目使用 vitest 做测试
```

在 OpenClaw 架构中，这个文件对应 `AGENTS.md`（定义行为）和 `SOUL.md`（定义人格）。

---

## 第四步：修改工具集

根据你的场景增删工具：

```typescript
// packages/agent/src/tools/index.ts
import { readTool } from './read'
import { writeTool } from './write'
import { editTool } from './edit'
import { bashTool } from './bash'
import { grepTool } from './grep'
// import { webFetchTool } from './web-fetch'  // 不需要联网就注释掉

export const defaultTools = [
  readTool,
  writeTool,
  editTool,
  bashTool,
  grepTool,
  // 添加你的自定义工具
  myCustomTool,
]
```

### 自定义工具示例

```typescript
// packages/agent/src/tools/deploy.ts
import { ToolDefinition } from '../types'

export const deployTool: ToolDefinition = {
  name: 'Deploy',
  description: '部署当前分支到测试环境。只在用户明确要求时使用。',
  parameters: {
    type: 'object',
    properties: {
      environment: {
        type: 'string',
        enum: ['staging', 'preview'],
        description: '目标环境'
      }
    },
    required: ['environment']
  },
  execute: async ({ environment }) => {
    const { stdout } = await exec(`deploy.sh --env ${environment}`)
    return stdout
  }
}
```

---

## 第五步：添加 MEMORY.md 支持

pi-mono 原版没有跨 Session 记忆。按 OpenClaw 模式添加：

```typescript
// packages/agent/src/memory.ts
import * as fs from 'fs'
import * as path from 'path'

const MEMORY_DIR = path.join(process.env.HOME!, '.myclaw', 'memory')
const INDEX_FILE = path.join(MEMORY_DIR, 'MEMORY.md')

export function loadMemoryIndex(): string | null {
  if (!fs.existsSync(INDEX_FILE)) return null
  return fs.readFileSync(INDEX_FILE, 'utf-8')
}

export function saveMemory(filename: string, content: string): void {
  fs.mkdirSync(MEMORY_DIR, { recursive: true })
  fs.writeFileSync(path.join(MEMORY_DIR, filename), content)
}
```

在 Agent Loop 中，把 MEMORY.md 内容注入系统指令：

```typescript
// 修改 agent-loop.ts 的系统指令构建
const memoryContent = loadMemoryIndex()
const systemPrompt = [
  config.systemPrompt,
  memoryContent ? `\n\n# Memory\n${memoryContent}` : ''
].join('')
```

---

## 第六步：部署为服务

### 方案 A：HTTP 服务 + PM2

```typescript
// packages/coding-agent/src/server.ts
import express from 'express'
import { agentLoop } from '@pi-mono/agent'

const app = express()
app.use(express.json())

const sessions = new Map<string, Message[]>()

app.post('/message', async (req, res) => {
  const { userId, text } = req.body
  const messages = sessions.get(userId) || []
  messages.push({ role: 'user', content: text })

  let response = ''
  for await (const event of agentLoop({ messages, ...config })) {
    if (event.type === 'message_end') {
      response = event.content.content
    }
  }

  sessions.set(userId, messages)
  res.json({ text: response })
})

app.listen(5000)
```

```bash
# PM2 后台运行
npm install -g pm2
pm2 start "pnpm -F coding-agent serve" --name myclaw
pm2 save && pm2 startup
```

### 方案 B：直接集成消息平台 SDK

```typescript
// integrations/slack.ts
import { App } from '@slack/bolt'

const slackApp = new App({
  token: process.env.SLACK_BOT_TOKEN,
  signingSecret: process.env.SLACK_SIGNING_SECRET
})

slackApp.event('app_mention', async ({ event, say }) => {
  const text = event.text.replace(/<@\w+>/, '').trim()

  let response = ''
  for await (const ev of agentLoop({ messages: [{ role: 'user', content: text }], ...config })) {
    if (ev.type === 'message_end') response = ev.content.content
  }

  await say(response)
})
```

```typescript
// integrations/feishu.ts
import express from 'express'

const app = express()

app.post('/feishu/webhook', async (req, res) => {
  const { type, event } = req.body

  // 飞书 URL 验证
  if (type === 'url_verification') {
    return res.json({ challenge: req.body.challenge })
  }

  if (event?.message) {
    const text = JSON.parse(event.message.content).text
    // 调用 Agent...
    await sendFeishuMessage(event.sender.sender_id.user_id, response)
  }

  res.json({ code: 0 })
})
```

---

## 第七步：添加 Eval 测试

```typescript
// eval/run-eval.ts
interface EvalCase {
  id: string
  prompt: string
  assertions: string[]  // 用自然语言描述预期
}

const evalCases: EvalCase[] = [
  {
    id: 'read-and-summarize',
    prompt: '读取 README.md 并用一句话总结这个项目',
    assertions: [
      '输出中包含项目名称',
      '输出是一句中文句子'
    ]
  },
  {
    id: 'fix-typo',
    prompt: '修复 src/main.ts 第 10 行的拼写错误',
    assertions: [
      '调用了 Edit 工具',
      '修改后文件中不包含拼写错误'
    ]
  }
]

async function runEval(): Promise<void> {
  let passed = 0
  for (const evalCase of evalCases) {
    const result = await runAgentTask(evalCase.prompt)
    const checks = await verifyAssertions(result, evalCase.assertions)
    if (checks.every(c => c)) passed++
    console.log(`${evalCase.id}: ${checks.every(c => c) ? '✅' : '❌'}`)
  }
  console.log(`\nPass rate: ${passed}/${evalCases.length}`)
}
```

---

## 完整检查清单

```
□ Fork pi-mono，pnpm install && pnpm build 成功
□ 配置 LLM Provider（.env 文件）
□ 跑通原版 coding-agent（能对话、能调用工具）
□ 定制 AGENTS.md（系统指令）
□ 根据需要增删工具
□ 添加 MEMORY.md 持久化
□ 部署为 HTTP 服务或接入消息平台
□ 编写 5+ Eval case，跑通
□ PM2 后台运行 + 开机自启
```

---

## 命名约定

OpenClaw 社区的命名约定：`[YourName]Claw`。

- **AliceClaw** — Alice 的个人 Agent
- **BobClaw** — Bob 的个人 Agent

给你的 Agent 起个名字。它是你自己的代码、你自己的工具、你自己的系统指令。不是某个框架的实例。

---

下一篇：[面试与实习准备](../09-interview/index.html)
