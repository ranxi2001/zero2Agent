---
layout: default
title: Pi Agent Framework
description: 从最小内核与扩展生长理解轻量 Agent 框架的工程边界
eyebrow: Module 11
---

# Pi Agent Framework

当一个 Coding Agent 框架说自己是"minimal terminal coding harness"，它在做一个明确的工程判断：**核心只负责循环和工具调度，其余一切通过扩展生长。**

Pi（GitHub ~95k stars，earendil-works 组织维护，原 badlogic/pi-mono）是这个判断最典型的实践者。它不内置权限系统，不绑定单一模型 Provider，不提供 IDE 集成。它选择把安全交给容器化基础设施，把模型差异交给统一适配层，把产品功能交给社区扩展。这些选择有明确的收益，也有真实的代价。

这个模块不是 Pi 的使用教程。它关心的是：一个轻量 Agent 框架如何划定自己的工程边界，这些边界在什么条件下成立，什么条件下会崩塌。

---

## 这个模块的主线

你可以把 Pi 的设计哲学概括为三个递进的判断：

1. **内核应该尽可能小。** Agent Loop + 工具调度 + 扩展注册，不多不少。
2. **安全不是框架的事。** 容器化环境提供隔离，框架内部不做权限检查。
3. **功能通过扩展生长。** Extension、Skill、Package 三层抽象覆盖从工具到完整工作流。

这三个判断互相支撑：内核小才能让扩展自由，安全外置才能让内核保持简单，扩展体系才能弥补内核不做的事。但它们也互相绑定——如果容器化假设不成立，整个体系的安全性就会失效。

## 阅读顺序

1. [Pi 是什么：定位、架构与安全模型](./01-what-is-pi/index.html)
2. [pi-ai：统一多 Provider 的适配层设计](./02-pi-ai-provider/index.html)
3. [扩展体系：从 Extension 到 Package 的能力组合](./03-extension-system/index.html)
4. [pi-mcp-adapter：MCP 工具的 Token 经济学](./04-mcp-adapter/index.html)
5. [安全模型深入：容器化隔离的实际边界](./05-security-model/index.html)
6. [社区生态：Fork、移植与跨框架兼容](./06-ecosystem/index.html)
7. [Pi vs Claude Code vs DSH：三种 Harness 哲学的工程对比](./07-comparison/index.html)

## 每篇文章的作用

| 文章 | 核心问题 |
| --- | --- |
| 01 定位与架构 | Pi 是什么、不是什么，四包结构如何划分职责 |
| 02 Provider 适配 | pi-ai 如何用一个接口统一 OpenAI/Anthropic/Google/Bedrock |
| 03 扩展体系 | Extension、Skill、Package 三层抽象的边界和组合方式 |
| 04 MCP 适配 | pi-mcp-adapter 把 MCP 工具 token 从 10k+ 降到 ~200 的设计 |
| 05 安全模型 | 不内置权限在生产环境中意味着什么，容器化隔离的实际边界 |
| 06 社区生态 | Senpi、Pix-mono、pi-mono-python、pi_agent_rust 如何继承和分叉 |
| 07 横向对比 | 三种 Harness 哲学（最小内核 / 内置安全 / 可组合运行时）的工程 tradeoff |

## 前置知识

- 已读 [learn-agent-basic](../learn-agent-basic/index.html) 的前 10 篇，理解 Agent Loop、工具调用和上下文管理
- 了解 [Claude Code](../learn-claude-code/index.html) 或 [DeepSeek Harness](../learn-deepseek-harness/index.html) 中至少一个框架的设计方式（用于对比）
- 基本的 TypeScript 阅读能力（Pi 核心是 TypeScript monorepo）

## 资料边界

文章以 [earendil-works/pi](https://github.com/earendil-works/pi) 仓库（原 badlogic/pi-mono）的架构和 README 为事实基线。社区 fork（Senpi、Pix-mono）和语言移植（pi-mono-python、pi_agent_rust）用来说明设计选择的后果，不代表官方实现。生产案例（如 BreachWeave——腾讯云黑客松冠军的渗透测试多 Agent 系统）引用时会标注其特殊上下文。

Pi 迭代快，API 变动频繁。本模块关心可迁移的设计问题——最小内核的收益与代价、扩展体系的边界、安全模型的 tradeoff——而不是追踪最新版本号。
