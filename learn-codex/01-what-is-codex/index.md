---
layout: default
title: Codex CLI 是什么：定位、架构与 Agent Loop
description: 从 Rust 双层架构和 Turn-based Loop 理解 OpenAI 终端 Agent 的工程起点
eyebrow: Codex CLI / 01
---

# Codex CLI 是什么：定位、架构与 Agent Loop

## 为什么这个问题值得关注

2025 年 5 月，OpenAI 开源了 Codex CLI——一个终端 Coding Agent。这不是 2021 年那个 GPT-3.5 级别的代码补全 API（已被 GPT-4 系列取代），而是一个完整的 Agent 系统：有循环、有工具、有沙箱、有权限、有 MCP。

Codex CLI 的定位和 Claude Code 高度重叠：都是终端里的 Coding Agent，都能读写文件、执行命令、调用外部工具。但技术路线完全不同。Claude Code 用 TypeScript 实现全栈，安全靠应用层权限检查；Codex CLI 用 Rust 实现内核，安全靠操作系统原生沙箱。

理解这个分歧，能帮你判断：什么时候平台原生安全比应用层安全更可靠，什么时候反过来。

仓库地址：[openai/codex](https://github.com/openai/codex)

## Codex CLI 解决什么问题

Codex CLI 的官方定位是"one focused terminal loop for interactive work, automation, review, and delegation"。翻译成工程语言：

- 提供一个 Turn-based Agent Loop，用户和模型交替执行
- 提供平台原生沙箱，限制模型能访问的文件和进程
- 提供 MCP 原生集成，通过标准协议接入外部工具
- 提供 TOML 配置系统，控制权限和行为
- 提供 SDK 接口，支持编程式调用和自动化

和 Claude Code 的关键区别不在功能列表上（两者功能高度重叠），而在实现方式和安全假设上。

## 双层架构：Rust + TypeScript

Codex CLI 采用 Rust + TypeScript 双层结构：

```text
┌─────────────────────────────────────┐
│  codex (TypeScript/Node)            │
│  终端 UI · 用户交互 · 扩展加载       │
├─────────────────────────────────────┤
│  codex-rs (Rust)                    │
│  Agent Loop · 沙箱执行 · 配置解析    │
│  MCP 客户端 · 进程隔离              │
├─────────────────────────────────────┤
│  操作系统                            │
│  Seatbelt (macOS) / Bubblewrap (Linux) │
└─────────────────────────────────────┘
```

### 为什么内核用 Rust

三个工程原因：

**沙箱性能。** 每次模型决定执行命令，都需要经过沙箱策略检查和进程隔离。这是热路径——如果每次检查花 50ms，一个复杂任务可能需要几百次工具调用，延迟累积到秒级。Rust 的零成本抽象让这个检查在微秒级完成。

**安全边界清晰。** Rust 没有 GC、没有运行时反射、没有 eval——攻击面比 Node.js 小一个数量级。当你的代码直接操作操作系统安全原语（Seatbelt profile、namespace）时，实现语言的安全性直接影响整体安全性。

**系统调用集成。** 平台原生沙箱需要调用 macOS 的 sandbox_init 和 Linux 的 clone(CLONE_NEWNS | CLONE_NEWPID)。这些接口在 Rust 中有成熟的 FFI 支持（nix crate），在 Node.js 中要么绕很多弯，要么依赖 C addon。

### 为什么交互层用 TypeScript

两个实用原因：

**生态。** NPM 是开发者工具分发的事实标准。`npm install -g @openai/codex` 比编译 Rust binary 对用户友好得多。

**扩展性。** 扩展开发者用 TypeScript 写逻辑，不需要学 Rust。Pi 也做了同样的选择——扩展层面降低贡献门槛。

### 双层的代价

- 两套构建系统（Cargo + npm），CI 复杂度高
- Rust 和 TypeScript 之间的 IPC 是额外的延迟和故障点
- 调试时需要在两个运行时之间切换
- 生态贡献者需要理解两层的边界

## Turn-based Agent Loop

Codex CLI 的 Agent Loop 是 turn-based 的，和 Claude Code 的 continuous loop 不同。

```text
用户输入 → 模型思考 → 工具调用 → 用户可介入 → 模型继续 → ... → 任务完成
     ↑                              │
     └──────── turn 边界 ────────────┘
```

**Turn** 是 Codex 的核心抽象。每个 turn 代表模型的一次完整执行——从收到指令到产出结果。用户在 turn 之间可以：

- **Steer**：修改方向，不终止当前 turn
- **Inspect**：查看 turn 中产生的命令和 diff
- **Approve/Reject**：对需要审批的操作做决策

### Turn-based vs Continuous

**Claude Code** 的循环是 continuous 的：模型持续执行，遇到需要审批的操作才暂停。用户的角色是"异常处理者"——只在系统不确定时被调用。

**Codex CLI** 的循环是 turn-based 的：每个 turn 有明确的开始和结束。用户的角色是"每轮审查者"——即使一切正常，也有机会在 turn 边界介入。

这不是对错问题，是对"用户参与度"的不同假设：

| 维度 | Turn-based (Codex) | Continuous (Claude Code) |
| --- | --- | --- |
| 用户介入频率 | 每轮都可介入 | 仅在审批时 |
| 自动化程度 | 需要更多配置才能全自动 | 默认倾向全自动 |
| 错误发现时机 | 早（每轮可审查） | 晚（可能累积多步错误） |
| 吞吐量 | 低（人在循环中） | 高（减少人工等待） |
| 适合场景 | 安全敏感、学习式 | 批量任务、信任度高 |

### Multi-turn Sessions

Codex 支持多 turn 会话，前一个 turn 的上下文（文件状态、执行结果）传递到下一个 turn。这和 Claude Code 的会话概念类似，但 turn 边界让上下文切分更显式——你可以精确知道"第 3 个 turn 执行了什么"。

## 与 Claude Code 和 Pi 的定位对比

| 维度 | Codex CLI | Claude Code | Pi |
| --- | --- | --- | --- |
| 实现语言 | Rust + TypeScript | TypeScript | TypeScript |
| Agent Loop | Turn-based | Continuous | Continuous |
| 安全机制 | 平台原生沙箱 | 应用层权限检查 | 无（外部容器化） |
| MCP 支持 | 原生 Rust crate | 内置支持 | 适配器（pi-mcp-adapter） |
| 配置格式 | TOML 层级 | CLAUDE.md + JSON | TypeScript config |
| 开源状态 | 完全开源 | 部分开源 | 完全开源 |
| 发布时间 | 2025.5 | 2025.2 | 2025.1 |
| ThoughtWorks 评级 | Trial (2026.4) | Adopt (2026.4) | 未评级 |

三者都是终端 Coding Agent，但做了不同的工程判断：

- **Codex** 判断安全应该在操作系统层面解决，框架用 Rust 确保最小攻击面
- **Claude Code** 判断安全应该在应用层面解决，对用户更友好但依赖正确实现
- **Pi** 判断安全不是框架的事，完全交给外部基础设施

## 什么时候该关注 Codex CLI

适合关注 Codex 的场景：

- 你在 macOS 或 Linux 上工作，需要操作系统级别的安全保障
- 你需要编程式地集成 Agent（Codex SDK 提供 thread-based API）
- 你需要和 OpenAI 模型生态深度绑定（GPT-4o、o3 等）
- 你的工作流是 review-heavy 的——每步都需要人工审查
- 你需要 MCP 工具生态，且希望是 Rust 层面的原生集成

## 什么时候不该选 Codex CLI

- 你需要一个开箱即用、社区验证充分的方案——Claude Code 的成熟度更高（Adopt vs Trial）
- 你的主要模型不是 OpenAI 的——Codex 虽然支持其他 Provider，但优化重心在自家模型
- 你需要会话恢复和长任务管理——Codex 的 session 管理不如 Claude Code 成熟
- 你在 Windows 上开发——Codex 的平台原生沙箱只覆盖 macOS 和 Linux
- 你需要稳定的 API——ThoughtWorks 的 Trial 评级意味着还在快速迭代和 breaking changes

## 小结

Codex CLI 的核心设计判断是：Agent 框架的安全层应该尽可能薄，把真正的隔离交给操作系统原语。Rust 内核确保了这层"胶水"足够快且攻击面足够小。

这个判断的收益是安全边界更硬——操作系统的沙箱比任何应用层检查都难绕过。代价是平台耦合（只支持 macOS/Linux 的沙箱机制）和复杂度分层（Rust + TypeScript 双层带来的构建和调试成本）。

理解这个 tradeoff，比记住 Codex 有什么功能更重要。

---

下一篇：[配置与权限系统：TOML 层级与三种审批策略](../02-config-permission/index.html)
