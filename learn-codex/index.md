---
layout: default
title: OpenAI Codex CLI
description: 从 Rust 内核与平台原生沙箱理解 OpenAI 的终端 Coding Agent 设计
eyebrow: Module 12
---

# OpenAI Codex CLI

当 OpenAI 决定做终端 Coding Agent 时，它做了一个和 Claude Code、DeepSeek Harness 都不同的技术判断：**用 Rust 写内核，用操作系统原生沙箱机制（macOS Seatbelt / Linux Bubblewrap）做安全隔离，把配置和权限决策全部编码进 TOML 层级系统。**

Codex CLI（GitHub [openai/codex](https://github.com/openai/codex)）是 OpenAI 在 2025 年中发布的开源终端 Agent 工具。它不是 2021 年那个 GPT-3.5 级别的代码补全模型，而是一个完整的 Coding Agent：有 Agent Loop、有工具系统、有沙箱、有 MCP 支持、有 SDK 可编程接口。

ThoughtWorks Technology Radar Vol. 34（2026 年 4 月）把 Codex 放在 Trial 环，Claude Code 和 Cursor 在更高的 Adopt 环。这个差距不是功能缺失——Codex 的 MCP 集成甚至比竞品更深（1,100+ 合并的 MCP PR）——而是成熟度和一致性的差距。ThoughtWorks 明确警告：Codex 倾向于建议逻辑正确但功能过时的库模式。

这个模块不是 Codex 的使用教程。它关心的是：一个 Rust 原生、平台沙箱优先的 Agent 工具如何设计自己的安全和扩展边界，这些设计在什么条件下优于或劣于 Claude Code 和 DSH 的方案。

---

## 这个模块的主线

Codex CLI 的设计可以用三个核心判断概括：

1. **性能敏感层用 Rust，交互层用 TypeScript。** Agent Loop、沙箱执行、配置解析在 Rust 中实现，UI 和生态扩展在 TypeScript/Node 中。
2. **安全是平台原生的，不是应用层模拟的。** macOS 用 Seatbelt profile，Linux 用 Bubblewrap 命名空间隔离——不是 chroot，不是 Docker 容器，是操作系统级的进程约束。
3. **MCP 是一等公民，不是后加的适配层。** 从 2025 年 5 月（PR #787）开始，MCP 就内建在 Rust 层，有专用 crate（rmcp-client、mcp-server、codex-mcp），到 2026 年 8 月已有 1,100+ 合并的 MCP 相关 PR。

这三个判断互相支撑：Rust 让沙箱执行足够快（毫秒级），平台沙箱让权限模型可以做到文件系统粒度，MCP 原生支持让外部工具集成不需要绕过安全边界。

## 阅读顺序

1. [Codex CLI 是什么：定位、架构与 Agent Loop](./01-what-is-codex/index.html)
2. [配置与权限系统：TOML 层级与三种审批策略](./02-config-permission/index.html)
3. [沙箱与安全模型：平台原生隔离的工程边界](./03-sandbox-security/index.html)
4. [MCP 深度集成：1,100+ PR 背后的设计决策](./04-mcp-integration/index.html)
5. [Codex SDK：Thread-based 编程式 Agent 接口](./05-codex-sdk/index.html)
6. [开发者体验与生态评估：Trial 环的原因](./06-developer-experience/index.html)
7. [Codex vs Claude Code vs DSH：三种终端 Agent 的工程对比](./07-codex-vs-claude-code/index.html)

## 每篇文章的作用

| 文章 | 核心问题 |
| --- | --- |
| 01 定位与架构 | Codex CLI 是什么、不是什么，Rust + TS 双层如何分工 |
| 02 配置与权限 | TOML 三层配置如何控制沙箱模式和审批策略 |
| 03 沙箱安全 | Seatbelt/Bubblewrap 如何实现文件系统粒度隔离 |
| 04 MCP 集成 | STDIO + Streamable HTTP 双通道，per-tool 审批机制 |
| 05 Codex SDK | thread.run/thread.turn 的 per-turn 沙箱粒度控制 |
| 06 开发者体验 | ThoughtWorks 评估、outdated patterns 问题、社区反馈 |
| 07 横向对比 | 三种终端 Agent（平台沙箱 / 内置权限 / 策略平面）的工程 tradeoff |

## 前置知识

- 已读 [learn-agent-basic](../learn-agent-basic/index.html) 的前 10 篇，理解 Agent Loop、工具调用和权限模型
- 了解 [Claude Code](../learn-claude-code/index.html) 或 [DeepSeek Harness](../learn-deepseek-harness/index.html) 中至少一个框架（用于对比）
- 基本了解操作系统级安全机制（文件系统权限、进程隔离）有助于理解沙箱章节

## 资料边界

文章以 [openai/codex](https://github.com/openai/codex) 开源仓库和 [learn.chatgpt.com/codex](https://learn.chatgpt.com/codex/cli) 官方文档为事实基线。第三方评测（ThoughtWorks Radar Vol. 34、Simon Willison 博客、builder.io 对比）引用时标注来源。

需要注意：官方文档（learn.chatgpt.com）可能描述了比开源仓库更新的功能——部分配置键（如 approval_policy 的细粒度控制）在公开源码中未找到，暗示产品版本可能有闭源分支。本模块以可验证的开源代码为准，文档-only 的功能会标注"未在开源代码中确认"。
