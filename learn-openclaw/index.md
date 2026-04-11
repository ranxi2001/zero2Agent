---
layout: default
title: OpenClaw Agent
description: 从零构建属于自己的轻量级 Coding Agent
---

# OpenClaw Agent

> “Agent 其实很简单。”

这个模块要解决一个具体的问题：**怎么从零搭出一个真正跑在生产上的 Coding Agent。**

不是调包。不是用 LangChain 或 Dify 拖节点。是从 ~60 行核心代码出发，一步步推导出 Node、Flow、Chatbot、Agent，最终把自己的 Agent 部署起来，通过 Slack 或飞书跟它对话。

这个思路来自 [Learn-OpenClaw](https://github.com/lasywolf/Learn-OpenClaw) 和 [pi-mono](https://github.com/pi-mcp/pi-mono)。

---

## 本模块的核心主张

主流 Agent 框架（LangChain、Dify、Coze）在 Demo 阶段很好用，但它们都有一个共同问题：**过度抽象**。当你真的想控制行为、排查问题、或者上生产，你发现你不知道它在做什么。

真正跑在生产上的 Coding Agent——Claude Code、Cursor、Kimi-cli、pi-mono——用的都不是这些框架。它们都在用轻量级的自定义方案。

OpenClaw 的思路就是：学懂核心原理，然后改 pi-mono，变成属于你自己的 Agent。

---

## 章节列表

- [为什么要自己写 Agent](./01-core-idea/index.html)
