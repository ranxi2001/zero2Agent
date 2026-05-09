---
layout: default
title: OpenClaw Agent
description: 基于 pi-mono 源码，理解生产级 Coding Agent 的架构与实现
---

# OpenClaw Agent

> "读懂 pi-mono 3000 行 TypeScript，就理解了 90% 的生产级 Coding Agent。"

这个模块的目标：**通过阅读真实源码，理解生产级 Coding Agent 的工程架构，并在此基础上构建你自己的 Agent。**

核心参考项目：

- [pi-mono](https://github.com/badlogic/pi-mono) — Mario Zechner 开源的终端 Coding Agent 运行时（TypeScript）
- [OpenClaw](https://github.com/openclaw/openclaw) — 基于 pi-mono 架构，增加了持久化记忆、多渠道接入、插件系统的个人 AI 助手框架
- [Learn-OpenClaw](https://github.com/lasywolf/Learn-OpenClaw) — 用 Python 简化重写的教学版（入门参考，非生产代码）

---

## 本模块的核心主张

主流 Agent 框架（LangChain、Dify、Coze）在 Demo 阶段很好用，但它们的过度抽象在生产环境会成为负担——行为不可预测、排查困难、安全面大。

真正跑在生产上的 Coding Agent——Claude Code、Cursor、pi-mono——用的都是轻量级自定义架构。它们的共同模式：

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
7. [读懂 pi-mono 源码](./07-pi-mono/index.html)
8. [构建你的 OpenClaw](./08-build-openclaw/index.html)
9. [面试与实习准备](./09-interview/index.html)
