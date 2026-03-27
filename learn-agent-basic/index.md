---
layout: default
title: learn-agent-basic
description: Agent 基础认知、核心概念与工程边界
eyebrow: Module 01
---

# learn-agent-basic

这一部分是整个项目的概念地基。

如果你现在的状态是：

- 会用 ChatGPT、Claude、Cursor 这类工具
- 懂一些深度学习或大模型的基本概念
- 会写代码，但还没系统做过 Agent

那最应该先看的就是这一部分。

这里不会一上来就堆框架 API，也不会先教你“5 分钟搭一个 Agent”。相反，它会先帮你建立一套更稳定的认知：

- Agent 到底是什么
- 它和普通 LLM App、Workflow 的边界在哪里
- 一个可用的 Agent 系统最少由哪些部分组成
- 为什么很多 Demo 能跑，但一落地就开始不稳定

## 学习目标

学完这一部分，你至少应该能做到下面几件事：

1. 能用工程视角解释什么是 Agent，而不是把它当成营销词。
2. 能区分 Workflow、LLM App、Agent 这三类系统。
3. 知道 Tool、Memory、Planning、RAG 在系统里分别扮演什么角色。
4. 能判断一个 Agent 设计是“可用系统”，还是“看起来会动的 Demo”。

## 建议阅读顺序

1. [什么是 Agent](./01-what-is-an-agent/index.html)
2. [Workflow 和 Agent 的区别](./02-workflow-vs-agent/index.html)
3. [一个 Agent 系统的核心组成](./03-core-components/index.html)
4. [为什么很多 Agent Demo 一落地就不稳定](./04-why-agent-demos-break/index.html)
5. [Tool Calling 入门](./05-tool-calling-basics/index.html)
6. [Memory 设计模式](./06-memory-patterns/index.html)
7. [Planning、Reflection、RAG 分别解决什么问题](./07-planning-reflection-rag/index.html)
8. [单 Agent 和多 Agent 的边界](./08-single-vs-multi-agent/index.html)

## 这一部分的主线

你可以把 Agent 先理解成一个最小闭环：

1. 接收目标
2. 感知当前上下文
3. 决定下一步动作
4. 调用模型或工具执行动作
5. 根据结果更新状态
6. 判断是否继续，直到完成或退出

真正的区别不在于“它是不是调用了大模型”，而在于：

- 它是否有状态
- 它是否能根据中间结果改变下一步行为
- 它是否能调用外部工具
- 它是否能在不确定环境中持续推进任务

## 当前文章

| 文章 | 作用 |
| --- | --- |
| [什么是 Agent](./01-what-is-an-agent/index.html) | 建立最基本的定义和闭环认知 |
| [Workflow 和 Agent 的区别](./02-workflow-vs-agent/index.html) | 解决最常见的概念混淆 |
| [一个 Agent 系统的核心组成](./03-core-components/index.html) | 拆开 Tool、State、Memory、Planning 等模块 |
| [为什么很多 Agent Demo 一落地就不稳定](./04-why-agent-demos-break/index.html) | 提前建立工程视角，而不是只追求“能跑” |
| [Tool Calling 入门](./05-tool-calling-basics/index.html) | 理解模型为什么需要外部工具，以及工具系统怎么设计 |
| [Memory 设计模式](./06-memory-patterns/index.html) | 理清短期记忆、长期记忆和状态管理的边界 |
| [Planning、Reflection、RAG 分别解决什么问题](./07-planning-reflection-rag/index.html) | 防止把三个高频概念混成一团 |
| [单 Agent 和多 Agent 的边界](./08-single-vs-multi-agent/index.html) | 判断什么时候真的需要多 Agent，而不是跟风拆角色 |

## 读完之后再学什么

如果这一部分读完了，下一步建议进入：

- [learn-langgraph](../learn-langgraph/index.html)

因为 LangGraph 解决的不是“如何调用一次模型”，而是“如何把一个有状态、可分支、可恢复的 Agent 系统组织起来”。
