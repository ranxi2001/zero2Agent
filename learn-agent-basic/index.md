---
layout: default
title: learn-agent-basic
description: Agent 基础认知、核心概念、工程边界与进阶模式
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
- 大模型 API 的输入、输出和工具调用轨迹如何组成 Agent Loop
- 为什么很多 Demo 能跑，但一落地就开始不稳定

## 学习目标

学完这一部分，你至少应该能做到下面几件事：

1. 能用工程视角解释什么是 Agent，而不是把它当成营销词。
2. 能区分 Workflow、LLM App、Agent 这三类系统。
3. 能读懂一轮模型 API 请求、响应、工具调用和结果回传。
4. 知道 Context、State、Memory、Tool、Planning、RAG 在系统里分别扮演什么角色。
5. 能判断一个 Agent 设计是”可用系统”，还是”看起来会动的 Demo”。
6. 知道怎么评估 Agent 的质量，而不是只凭直觉说”能跑”。
7. 理解为什么 Coding Agent 是当前最成功的落地形态，以及它的成功模式如何迁移。
8. 了解多模态 Agent（Voice、Computer Use）、异步架构和 Agent 自进化的工程模式。
9. 掌握高级 RAG（GraphRAG、Contextual Retrieval）和双层记忆架构的设计思路。

## 建议阅读顺序

1. [什么是 Agent](./01-what-is-an-agent/index.html)
2. [Workflow 和 Agent 的区别](./02-workflow-vs-agent/index.html)
3. [一个 Agent 系统的核心组成](./03-core-components/index.html)
4. [为什么很多 Agent Demo 一落地就不稳定](./04-why-agent-demos-break/index.html)
5. [大模型 API 输入输出与 Tool Calling](./05-tool-calling-basics/index.html)
6. [Context、State 与 Memory](./06-memory-patterns/index.html)
7. [Planning、Reflection、RAG 分别解决什么问题](./07-planning-reflection-rag/index.html)
8. [单 Agent 和多 Agent 的边界](./08-single-vs-multi-agent/index.html)
9. [Agent Infra：从 Harness 到生产环境](./09-agent-infra/index.html)
10. [Loop Engineering：让 Agent 自主迭代直到正确](./10-loop-engineering/index.html)
11. [Agent 评估：怎么知道你的 Agent 好不好](./11-agent-evaluation/index.html)
12. [Coding Agent：最成功的 Agent 落地形态](./12-coding-agent-patterns/index.html)
13. [Context Engineering：系统化设计模型输入](./13-context-engineering/index.html)
14. [多模态与实时交互 Agent](./14-multimodal-realtime/index.html)
15. [Agent 自进化：不改权重也能持续变强](./15-agent-self-evolution/index.html)
16. [高级 RAG 与记忆架构](./16-advanced-rag-memory/index.html)
17. [异步 Agent 与事件驱动架构](./17-async-event-driven/index.html)

## 这一部分的主线

你可以把 Agent 先理解成一个公式和一个闭环。

公式：**Agent = LLM + Context + Tools**

闭环：

1. 接收目标
2. 感知当前上下文
3. 决定下一步动作
4. 调用模型或工具执行动作
5. 根据结果更新状态
6. 判断是否继续，直到完成或退出

真正的区别不在于”它是不是调用了大模型”，而在于：

- 它是否有状态
- 它是否能根据中间结果改变下一步行为
- 它是否能调用外部工具
- 它是否能在不确定环境中持续推进任务

前 10 篇建立核心概念和工程方法，11-12 篇讲评估和最成功的 Coding Agent 案例，13 篇系统化 Context Engineering 方法论，14-17 篇覆盖多模态、自进化、高级 RAG 和异步架构等进阶模式。

## 当前文章

| 文章 | 作用 |
| --- | --- |
| [什么是 Agent](./01-what-is-an-agent/index.html) | 建立最基本的定义和闭环认知 |
| [Workflow 和 Agent 的区别](./02-workflow-vs-agent/index.html) | 解决最常见的概念混淆 |
| [一个 Agent 系统的核心组成](./03-core-components/index.html) | 拆开 Tool、State、Memory、Planning 等模块 |
| [为什么很多 Agent Demo 一落地就不稳定](./04-why-agent-demos-break/index.html) | 提前建立工程视角，而不是只追求”能跑” |
| [大模型 API 输入输出与 Tool Calling](./05-tool-calling-basics/index.html) | 从请求、typed 响应、因果关联和流式事件看懂完整工具循环 |
| [Context、State 与 Memory](./06-memory-patterns/index.html) | 理清消息轨迹、缓存、压缩、状态与长期记忆的边界 |
| [Planning、Reflection、RAG 分别解决什么问题](./07-planning-reflection-rag/index.html) | 防止把三个高频概念混成一团 |
| [单 Agent 和多 Agent 的边界](./08-single-vs-multi-agent/index.html) | 判断什么时候真的需要多 Agent，而不是跟风拆角色 |
| [Agent Infra：从 Harness 到生产环境](./09-agent-infra/index.html) | 从 Harness 到上线，需要哪些基础设施支撑 |
| [Loop Engineering：让 Agent 自主迭代直到正确](./10-loop-engineering/index.html) | Agent 循环的退出条件、纠错策略和防护设计 |
| [Agent 评估：怎么知道你的 Agent 好不好](./11-agent-evaluation/index.html) | 从指标到方法，建立系统质量的工程判断标准 |
| [Coding Agent：最成功的 Agent 落地形态](./12-coding-agent-patterns/index.html) | 理解当前最成熟的 Agent 落地模式及其可迁移的设计原则 |
| [Context Engineering：系统化设计模型输入](./13-context-engineering/index.html) | 从 Skills 加载、Status Bar 到 Prompt 策略的工程方法论 |
| [多模态与实时交互 Agent](./14-multimodal-realtime/index.html) | Voice Agent、Computer Use、GUI 自动化与快慢解耦 |
| [Agent 自进化：不改权重也能持续变强](./15-agent-self-evolution/index.html) | 经验学习、工具创造、运行时自改进 |
| [高级 RAG 与记忆架构](./16-advanced-rag-memory/index.html) | GraphRAG、Contextual Retrieval、双层记忆、记忆评估 |
| [异步 Agent 与事件驱动架构](./17-async-event-driven/index.html) | 异步执行模式、事件触发、Safety Sidecar、安全隔离 |

## 配套实验

[Agent API Lab](../examples/agent-api-lab/index.html) 不需要 API Key，使用确定性 Fake Provider 展示模型请求、工具调用、结果回传、流式组装和故障注入。它还会主动破坏消息轨迹，验证删除 assistant 工具请求、错配 call ID、拍平角色或机械滑窗为什么会失败。

```powershell
python examples/agent-api-lab/run_lab.py --scenario parallel
python examples/agent-api-lab/run_lab.py --scenario parallel --all-ablations
python -m unittest discover -s examples/agent-api-lab/tests -v
```

## 阅读分层建议

17 篇不需要全部一口气读完。按需求分层：

| 层次 | 文章 | 适合谁 |
| --- | --- | --- |
| 核心必读 | 01-10 | 所有想做 Agent 的人 |
| 工程进阶 | 11-13 | 准备落地或面试的人 |
| 前沿拓展 | 14-17 | 关注行业趋势、准备深度面试 |

## 读完之后再学什么

如果这一部分读完了，下一步建议进入：

- [learn-langgraph](../learn-langgraph/index.html)——如何把有状态、可分支、可恢复的 Agent 系统组织起来
- [learn-agent-training](../learn-agent-training/index.html)——SFT / RL 训练层面让模型学会做 Agent
- [learn-agent-survey](../learn-agent-survey/index.html)——13 个主流框架的横向对比
