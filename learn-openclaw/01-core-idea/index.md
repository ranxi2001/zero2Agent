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

Claude Code、Cursor、Pi——这些主流 Coding Agent 都没有把 LangChain 或 Dify 作为核心运行时。

它们的共同模式：

| 特征 | 框架方案 | 生产级方案 |
|------|---------|-----------|
| 执行模型 | 链式调用 / DAG | EventStream + Agent Loop |
| 上下文管理 | 截断或摘要 | 可插拔 Context Engine |
| 工具调用 | 串行 + 同步 | 并行（Promise.all）+ MCP |
| 记忆 | 向量数据库存对话 | 文件级持久化（MEMORY.md）|
| 语言 | Python | TypeScript（性能 + 类型安全）|

---

## Pi 与 pi-mono：项目和源码仓库

[Pi](https://github.com/earendil-works/pi) 是 Mario Zechner 发起的 TypeScript Agent Harness 项目，也提供用户可直接运行的终端 Coding Agent。`pi-mono` 是它早期的 monorepo 仓库名，不是另一个产品；当前上游仓库已经更名为 `earendil-works/pi`。

本模块遵循一个术语规则：谈整套项目或终端产品时写 **Pi**，谈早期仓库和历史资料时写 **pi-mono**，谈可安装模块时写具体 npm 包名。

```
packages/
  agent/         ← @earendil-works/pi-agent-core：通用 Agent Runtime
  ai/            ← @earendil-works/pi-ai：多 Provider LLM API
  coding-agent/  ← @earendil-works/pi-coding-agent：提供 pi 命令
  tui/           ← @earendil-works/pi-tui：终端 UI
  orchestrator/  ← 实验性编排包
```

Pi 把 Provider、Agent Runtime 和终端产品拆成独立层，是研究生产级 Coding Agent 的公开源码样本。

---

## OpenClaw：从 Pi 出发的独立产品

[OpenClaw](https://github.com/openclaw/openclaw) 的部分实现改编自 Pi / pi-mono，但它不是 Pi 的改名或简单套壳。OpenClaw 面向长期运行的个人助理场景，重点建设完整的应用层：

```
OpenClaw
├── Gateway 与 WebSocket 控制面
├── Telegram / Slack / Discord 等消息渠道
├── Session、Workspace 与长期记忆
├── Skills、Cron、浏览器和设备节点
├── 工具策略、沙箱与多用户安全
└── OpenClaw 自有 Agent Runtime
```

截至 2026 年 7 月，OpenClaw 的[内置 Runtime](https://github.com/openclaw/openclaw/blob/main/docs/agent-runtime-architecture.md)已由项目自身维护，核心位于 `packages/agent-core` 与 `src/agents`。它保留 Pi 带来的架构和代码渊源，但当前并不是直接运行外部 `pi-agent-core`；明确保留的 Pi 包依赖主要是 `@earendil-works/pi-tui`。

核心能力差异：

| 能力 | Pi | OpenClaw |
|------|---------|----------|
| 核心运行时 | `pi-agent-core` | 自有 `@openclaw/agent-core` + embedded runtime |
| 主要入口 | 终端 `pi` 命令 | 长期驻留 Gateway |
| 多模型适配 | `pi-ai` | OpenClaw 自有 Provider 层 |
| 长期记忆 | 以 Coding Session 为中心 | Workspace 文件 + Session 存储 |
| 渠道与自动化 | 终端交互 | 多消息平台、Cron、设备节点 |

---

## Agent 的本质：一个循环

不管框架怎么包装，所有 Agent 的核心结构是同一个循环：

```typescript
// 伪代码，简化自 Pi 的 Agent Loop 模式
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
阅读 Pi（原 pi-mono）源码（TypeScript）
    ↓
理解 Agent Loop / EventStream 模式
    ↓
理解 Context Engine / Memory 架构
    ↓
基于 Pi 的分层改造并接入你的 LLM
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
