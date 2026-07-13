---
layout: default
title: OpenClaw Agent
description: 从 Pi Agent Harness 到 OpenClaw，理解生产级 Agent 的架构与实现
---

# OpenClaw Agent

> "读懂 Pi 的核心运行时，就理解了生产级 Coding Agent 的共同骨架。"

这个模块的目标：**通过阅读真实源码，理解生产级 Coding Agent 的工程架构，并在此基础上构建你自己的 Agent。**

核心参考项目：

- [Pi（原 pi-mono）](https://github.com/earendil-works/pi) — Mario Zechner 发起的 TypeScript Agent Harness 与终端 Coding Agent
- [OpenClaw](https://github.com/openclaw/openclaw) — 部分实现改编自 Pi、面向多渠道和长期运行场景的个人 AI 助手
- [Learn-OpenClaw](https://github.com/lasywolf/Learn-OpenClaw) — 用 Python 简化重写的教学版（入门参考，非生产代码）

---

## 先分清 Pi、pi-mono 与 OpenClaw

这几个名字处在不同层级，不能互换：

| 名称 | 它是什么 | 与其他部分的关系 |
|------|----------|------------------|
| **Pi** | 项目名；广义上指 Pi Agent Harness，狭义上也指用户运行的 `pi` CLI | 整套底层库和终端产品的总称 |
| **pi-mono** | Pi 早期的 monorepo 仓库名；当前仓库已迁移并更名为 `earendil-works/pi` | 存放 Pi 各 npm 包的源码，不是另一个 Agent 产品 |
| **pi-ai / pi-agent-core** | 多 Provider LLM 接口与通用 Agent Runtime | 可被上层应用组合使用的“发动机零件” |
| **pi-coding-agent** | 基于底层包构建的交互式终端 Coding Agent | 安装后提供用户实际运行的 `pi` 命令 |
| **OpenClaw** | 独立的 Gateway / 个人助理项目 | 借鉴并改编了 Pi 的部分实现，重点建设消息渠道、会话、Skills 和自动化 |

当前 Pi 仓库的核心关系如下：

```text
Pi（项目 / Agent Harness）
└── earendil-works/pi（原 pi-mono 源码仓库）
    ├── @earendil-works/pi-ai            多模型 Provider 统一接口
    ├── @earendil-works/pi-agent-core    Agent Loop、状态与工具调用
    ├── @earendil-works/pi-coding-agent  终端产品，提供 pi 命令
    ├── @earendil-works/pi-tui           终端 UI 组件
    └── @earendil-works/pi-orchestrator  实验性编排包
```

### 为什么 OpenClaw 选择从 Pi 出发

OpenClaw 的差异化不在重新发明一次 Agent Loop，而在把 Agent 接进真实生活场景。Pi 适合作为起点，主要因为：

1. **核心轻且边界清楚**：模型调用、消息流、工具循环和状态管理被拆成独立包，适合阅读、改编和嵌入。
2. **技术栈一致**：两者都以 TypeScript / Node.js 为主，可以共享异步事件模型和类型，不需要维护跨进程协议。
3. **多模型抽象成熟**：Pi 已处理不同 Provider 的流式事件、Tool Calling 和消息格式差异，上层可以专注产品能力。
4. **比套用商业 CLI 更可控**：改编 SDK 和源码可以直接控制事件、工具与状态，不必解析终端输出，也不会与另一套权限、Session 和 UI 生命周期冲突。
5. **把投入留给应用层**：OpenClaw 可以集中建设 Gateway、消息平台、Skills、Cron、设备节点、长期记忆和安全策略。

可以把两者理解为两种使用同类发动机思路的产品：Pi CLI 面向终端编码，OpenClaw 面向长期驻留的多渠道个人助理。

### 历史来源不等于当前直接依赖

这里需要区分“代码来源”与“当前依赖”。OpenClaw 的[第三方声明](https://github.com/openclaw/openclaw/blob/main/THIRD_PARTY_NOTICES.md)写明，部分代码改编自 Pi / pi-mono；但截至 2026 年 7 月，[OpenClaw Agent Runtime 架构说明](https://github.com/openclaw/openclaw/blob/main/docs/agent-runtime-architecture.md)已经明确其内置 Runtime 由项目自身维护，核心代码位于 `packages/agent-core` 和 `src/agents`，不再把 `pi-ai` 或 `pi-agent-core` 作为外部 Agent 框架直接运行。当前保留的 Pi 直接依赖主要是用于终端渲染的 `@earendil-works/pi-tui`。

因此更准确的关系是：**Pi 提供了重要的架构起点和代码来源，OpenClaw 在此基础上完成了适配、内化和面向个人助理场景的持续演化。**

---

## 本模块的核心主张

主流 Agent 框架（LangChain、Dify、Coze）在 Demo 阶段很好用，但它们的过度抽象在生产环境会成为负担——行为不可预测、排查困难、安全面大。

真正跑在生产上的 Coding Agent——Claude Code、Cursor、Pi——用的都是轻量级自定义架构。它们的共同模式：

1. **EventStream 驱动的 Agent Loop**（不是链式调用）
2. **可插拔的 Context Engine**（不是简单的消息截断）
3. **并行工具执行 + MCP 协议**（不是串行函数调用）
4. **文件级持久化记忆**（不是向量数据库存对话）

这套模块带你逐层拆解这些模式。

---

## 章节列表

1. [为什么要自己写 Agent](./01-core-idea/index.html)
2. [Agent Loop：EventStream 驱动的核心循环](./02-node-to-agent/index.html)
3. [RAG：检索增强的工程实现](./03-rag/index.html)
4. [工具系统：MCP 协议与并行执行](./04-tools/index.html)
5. [Context Engine：OpenClaw 的记忆架构](./05-memory/index.html)
6. [Multi-Agent：子进程隔离与多渠道路由](./06-multi-agent/index.html)
7. [读懂 Pi（原 pi-mono）源码](./07-pi-mono/index.html)
8. [构建你的 OpenClaw](./08-build-openclaw/index.html)
9. [面试与实习准备](./09-interview/index.html)
