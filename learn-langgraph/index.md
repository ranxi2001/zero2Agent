---
layout: default
title: learn-langgraph
description: 用状态图思维构建可维护的 Agent 系统——从最小示例到条件分支、并行执行和 LLM 集成
eyebrow: Module 04
---

# learn-langgraph

链式调用能跑通 Demo，但一旦加入条件分支、循环和错误恢复，代码就会变成意大利面。

LangGraph 用**图结构**来描述 Agent 的执行逻辑：节点是操作，边是转移，状态是贯穿全程的上下文。这不只是换了一种写法，而是换了一种思维方式——从"怎么写代码"变成"怎么设计状态机"。

## 这个模块覆盖什么

| # | 文章 | 你会学到什么 |
|---|------|------------|
| 01 | LangGraph 是什么，为什么不用链式调用 | 链式调用的局限，图结构的优势，核心抽象 |
| 02 | State、Node、Graph 三件套 | TypedDict 状态设计，节点函数签名，编译与运行 |
| 03 | 顺序图：第一个可运行的 Workflow | add\_edge 模式，多节点顺序流，实战 BMI 计算器 |
| 04 | 条件分支：add\_conditional\_edges | 路由函数，情感分析路由，Pydantic 结构化输出 |
| 05 | 并行执行：Fan-out / Fan-in | 多节点同时启动，汇聚节点，cricket 统计实战 |
| 06 | Prompt Chaining：分步生成 | 拆解生成任务，节点间传递中间结果，HuggingFace 集成 |
| 07 | 接入 LLM：OpenAI 与 HuggingFace | ChatOpenAI，HuggingFaceEndpoint，在节点里调用模型 |

## 前置知识

- 读过 [Agent Basic](../learn-agent-basic/index.html) 或者知道什么是 Agent、Tool Calling
- 会写基本的 Python，知道 `TypedDict` 是什么
- 不需要 LangGraph 经验

## 从哪里开始

如果完全没接触过 LangGraph，从 [第 01 篇](01-what-is-langgraph/index.html) 开始读。

如果已经知道 LangGraph 是状态图，想直接上手，从 [第 02 篇](02-state-node-graph/index.html) 开始。
