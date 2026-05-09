---
layout: default
title: 为什么要自己写 Agent
description: 从主流框架的局限到生产级架构的核心模式
eyebrow: OpenClaw / 01
---

# 为什么要自己写 Agent

你大概已经用过 LangChain、Dify 或者 Coze。Demo 阶段很顺，部署到生产后开始出问题：

- 行为不稳定，但 debug 时全是框架内部堆栈
- 想改一个细节，发现要翻三层抽象
- 上了生产遇到安全漏洞，依赖链太长修不动

这不是你用得不好，是框架架构决定的。

---

## 真正跑在生产的 Coding Agent 用什么

Claude Code、Cursor、pi-mono——目前公认最好的 Coding Agent——都没有用 LangChain 或 Dify。

它们的共同模式：

| 特征 | 框架方案 | 生产级方案 |
|------|---------|-----------|
| 执行模型 | 链式调用 / DAG | EventStream + Agent Loop |
| 上下文管理 | 截断或摘要 | 可插拔 Context Engine |
| 工具调用 | 串行 + 同步 | 并行（Promise.all）+ MCP |
| 记忆 | 向量数据库存对话 | 文件级持久化（MEMORY.md）|
| 语言 | Python | TypeScript（性能 + 类型安全）|

---

## pi-mono：开源生产级 Coding Agent

[pi-mono](https://github.com/badlogic/pi-mono) 是 Mario Zechner 开源的终端 Coding Agent monorepo，TypeScript 实现，约 3000 行核心代码。

```
packages/
  agent/         ← Agent Loop + EventStream 生命周期
  ai/           ← 多 Provider LLM API（OpenAI / Anthropic / Google / Bedrock）
  coding-agent/ ← 交互式编码 Agent CLI
  tui/          ← 终端差分渲染 UI
  web-ui/       ← Web 聊天组件
```

它的架构直接影响了 Claude Code 的设计思路。

---

## OpenClaw：pi-mono 之上的完整平台

[OpenClaw](https://github.com/openclaw/openclaw) 在 pi-mono 的基础上增加了企业级特性：

```
src/
  memory/          ← MEMORY.md 文件持久化
  context-engine/  ← 可插拔上下文组装/压缩
  sessions/        ← Session 生命周期管理
  agents/          ← Agent 运行时、沙箱、Skills
  tools/           ← 工具执行、安全策略
  mcp/             ← MCP 协议桥接
  channels/        ← 20+ 消息平台集成
  gateway/         ← API 网关
  hooks/           ← 事件钩子系统
  plugins/         ← 插件 SDK
  security/        ← SSRF 策略、命令授权、密钥管理
```

核心能力差异：

| 能力 | pi-mono | OpenClaw |
|------|---------|----------|
| Agent Loop | ✅ | ✅（继承） |
| 持久化记忆 | ❌ | ✅ MEMORY.md + Context Engine |
| 多渠道接入 | ❌ | ✅ 20+ 平台 |
| 沙箱安全 | ❌ | ✅ Docker / SSH / OpenShell |
| 插件系统 | ❌ | ✅ ClawHub Skills Registry |

---

## Agent 的本质：一个循环

不管框架怎么包装，所有 Agent 的核心结构是同一个循环：

```typescript
// 伪代码，简化自 pi-mono agent-loop.ts
async function agentLoop(messages: Message[]): AsyncGenerator<Event> {
  while (true) {
    // 1. 调用 LLM
    const response = await llm.chat(messages)
    yield { type: 'message_end', content: response }

    // 2. 如果没有 tool_calls，结束
    if (!response.toolCalls?.length) break

    // 3. 并行执行所有工具
    const results = await Promise.all(
      response.toolCalls.map(call => executeTool(call))
    )
    yield { type: 'tool_execution_end', results }

    // 4. 把工具结果追加到 messages，继续循环
    messages.push(...results.map(toMessage))
  }
}
```

这就是全部。Agent 和 Chatbot 的区别只有一个：**当模型返回 tool_calls 时，执行工具并继续循环，而不是直接结束。**

---

## 这条路适合什么人

- 你想理解 Claude Code / Cursor 这类产品的底层原理
- 你在准备 Agent 方向的技术面试，需要展示源码级理解
- 你要开发部署一个真正可控的 Agent

它不适合：只想快速出 Demo、不关心底层原理的场景。

---

## 学习路径

```
阅读 pi-mono 源码（TypeScript）
    ↓
理解 Agent Loop / EventStream 模式
    ↓
理解 Context Engine / Memory 架构
    ↓
Fork pi-mono，接入你的 LLM
    ↓
部署为你自己的 [YourName]Claw
```

---

## 推荐学习资源

| 资源 | 类型 | 内容 |
|------|------|------|
| [OpenClaw-Internals](https://github.com/botx-work/OpenClaw-Internals) | 源码拆解 | 最深入的中文架构分析（WebSocket 协议、Agent Loop、安全） |
| [build-your-own-openclaw](https://github.com/czl9707/build-your-own-openclaw) | 动手教程 | 18 步 Python 实现（从 0 到 OpenClaw 克隆） |
| [how-to-build-a-coding-agent](https://github.com/ghuntley/how-to-build-a-coding-agent) | 动手教程 | Go 语言 6 阶段 Workshop |
| [AI-Coding-Guide-Zh](https://github.com/KimYx0207/AI-Coding-Guide-Zh) | 对比指南 | Claude Code + OpenClaw + Codex 三合一（39 篇教程） |
| [openclaw-architecture-analysis](https://github.com/VladBrok/openclaw-architecture-analysis) | 可视化 | D3.js 交互式架构演进图（15,000+ commits） |
| [claude-code-vs-openclaw](https://github.com/rrmars/claude-code-vs-openclaw) | 对比分析 | 11 维度机制对比 |

---

下一篇：[Agent Loop：EventStream 驱动的核心循环](../02-node-to-agent/index.html)
