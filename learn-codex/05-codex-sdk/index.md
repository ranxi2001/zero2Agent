---
layout: default
title: Codex SDK：Thread-based 编程式 Agent 接口
description: 从 thread.run/thread.turn 理解 Codex 的 per-turn 沙箱粒度控制
eyebrow: Codex CLI / 05
---

# Codex SDK：Thread-based 编程式 Agent 接口

## 为什么这个问题值得关注

CLI 工具解决的是交互式使用场景——人坐在终端前，逐步引导 Agent 完成任务。但很多 Agent 应用场景不是交互式的：

- CI/CD 中自动修复 lint 问题
- 代码审查自动化（PR 提交后自动检查）
- 批量代码迁移（100 个文件同样的重构）
- 自定义工作流编排（多步任务自动串联）

这些场景需要编程式接口——通过代码调用 Agent，而不是通过终端交互。Codex SDK 就是这个接口。

SDK 的核心抽象是 **Thread**（线程/会话），每个 Thread 由多个 **Turn** 组成。关键创新是 **per-turn 沙箱粒度**：同一个 Thread 中，不同 Turn 可以有不同的权限级别。这意味着你可以在一个会话中先用只读模式分析代码，再升级到写模式修改代码——权限按需提升，不需要重启。

## Thread 和 Turn 的概念

```text
Thread（会话）
├── Turn 1: "分析 src/ 目录结构"  [sandbox: read_only]
├── Turn 2: "找出所有 TODO 注释"  [sandbox: read_only]
├── Turn 3: "修复第一个 TODO"     [sandbox: workspace_write]
└── Turn 4: "运行测试验证"        [sandbox: workspace_write]
```

**Thread** 是一个持久化的会话，有唯一 ID，可以恢复。所有 Turn 共享同一个上下文（对话历史、文件状态）。

**Turn** 是 Thread 中的一个执行单元——一次用户指令到模型完成响应。每个 Turn 可以独立指定沙箱模式。

### Thread 的生命周期

```text
创建 → 运行 Turn 1 → 运行 Turn 2 → ... → 归档/恢复
```

Thread 可以被暂停、恢复。通过 Thread ID 可以在不同进程甚至不同机器上恢复同一个会话（需要共享状态存储）。

## SDK 基本用法

```javascript
import { Codex } from "@openai/codex-sdk";

const codex = new Codex({ apiKey: process.env.OPENAI_API_KEY });

// 创建 Thread
const thread = codex.threads.create({
  model: "o3",
  instructions: "你是一个代码审查助手",
});

// 执行一个 read-only Turn（分析阶段）
const analysis = await thread.turn({
  message: "分析 src/api/ 目录中的错误处理模式",
  sandbox: "read_only",
});

// 基于分析结果，执行一个 workspace-write Turn（修复阶段）
const fix = await thread.turn({
  message: "用统一的 AppError 类型替换所有裸 throw",
  sandbox: "workspace_write",
});
```

### Per-turn 沙箱的工程意义

传统做法：整个会话用同一个权限级别。如果任务需要"先分析后修改"，你要么一开始就给写权限（分析阶段有不必要的风险），要么中途重启切换权限（丢失上下文）。

Codex SDK 的做法：权限跟着 Turn 走。分析时 read_only，修改时 workspace_write，验证时可以再收回 read_only。

```javascript
// 渐进式权限升级
const t1 = await thread.turn({ message: "列出所有安全漏洞", sandbox: "read_only" });
const t2 = await thread.turn({ message: "修复严重级别的漏洞", sandbox: "workspace_write" });
const t3 = await thread.turn({ message: "验证修复没有引入新问题", sandbox: "read_only" });
```

这让最小权限原则在 Agent 工作流中可操作化——不是"给一个宽松权限跑完全程"，而是"每一步只给这一步需要的权限"。

## Thread 恢复

Thread ID 支持跨会话恢复：

```javascript
// 第一次运行
const thread = codex.threads.create({ model: "o3" });
const threadId = thread.id; // 保存这个 ID
await thread.turn({ message: "开始重构 auth 模块" });

// 下次运行（可能在另一个进程中）
const resumed = codex.threads.resume(threadId);
await resumed.turn({ message: "继续，修改第二个文件" });
```

这对长时间运行的任务很有价值——你可以在一天内分多次推进同一个重构任务，每次恢复时模型保留之前的上下文。

### 与 Claude Code 的会话恢复对比

Claude Code 也支持会话恢复（`--resume`），但恢复粒度是整个会话。Codex SDK 的恢复粒度是 Thread（也是整个会话），没有本质区别。

真正的区别在于 API 形态：Claude Code 的恢复是 CLI 参数，Codex SDK 的恢复是编程接口。后者对自动化场景更友好——你可以在代码中管理多个 Thread 的生命周期。

## 自动化工作流编排

SDK 的编程特性让复杂工作流成为可能：

### 批量迁移

```javascript
const files = glob.sync("src/**/*.ts");

for (const file of files) {
  const thread = codex.threads.create({ model: "o3" });
  await thread.turn({
    message: `将 ${file} 中的 moment.js 调用替换为 dayjs`,
    sandbox: "workspace_write",
    writable_roots: [file], // 只允许写这一个文件
  });
}
```

每个文件一个 Thread，互不干扰。writable_roots 限制到单文件粒度——即使模型尝试修改其他文件也会被沙箱拦截。

### CI/CD 集成

```javascript
// PR 自动审查
const thread = codex.threads.create({ model: "o3" });
const review = await thread.turn({
  message: `审查以下 diff 的安全问题：\n${diff}`,
  sandbox: "read_only",
});

if (review.includes("安全风险")) {
  await github.createComment(prId, review);
  process.exit(1); // 阻止合入
}
```

read_only 确保审查过程不会意外修改代码——即使模型"想修复"发现的问题，沙箱也会阻止。

### 条件式权限升级

```javascript
const analysis = await thread.turn({
  message: "检查是否有死代码",
  sandbox: "read_only",
});

if (analysis.deadCodeFound && userApproved) {
  await thread.turn({
    message: "删除标记的死代码",
    sandbox: "workspace_write",
  });
}
```

程序逻辑决定何时升级权限——不是模型决定，是你的代码决定。这把人类（或自动化逻辑）放在了权限决策的控制位。

## 与其他编程式 Agent 接口的对比

### OpenAI Assistants API

Assistants API 也有 Thread + Run 的概念，但没有沙箱——它是纯云端执行，不接触本地文件系统。Codex SDK 是本地执行 + 沙箱隔离。

### Claude Code SDK (claude --sdk)

Claude Code 可以通过 `--output-format json` 实现编程式调用，但不是正式的 SDK——没有 Thread/Turn 的显式抽象，没有 per-turn 权限控制。

### Codex SDK 的独特价值

| 维度 | Codex SDK | OpenAI Assistants | Claude Code (CLI) |
| --- | --- | --- | --- |
| 执行环境 | 本地 + 沙箱 | 云端 | 本地 + 权限检查 |
| per-turn 权限 | 支持 | 不适用 | 不支持 |
| Thread 恢复 | 支持 | 支持 | 支持 |
| 文件系统访问 | 直接 | 通过 Code Interpreter | 直接 |
| 适合场景 | 本地自动化 + 安全 | 云端对话 | 交互式开发 |

## SDK 的限制

**模型绑定。** Codex SDK 默认用 OpenAI 模型。虽然配置上可能支持其他 Provider，但优化和测试重心在 GPT 系列。

**文档成熟度。** 部分 SDK 功能（如 per-turn writable_roots 的精确语义）在官方文档中有描述，但未在开源代码中完全确认。产品版本可能和开源版本有差异。

**生态配套。** Claude Code 围绕 SDK 有 hooks、skills、CLAUDE.md 等配套机制。Codex SDK 的配套生态相对年轻。

**错误处理。** 当 per-turn 沙箱限制导致工具调用失败时，模型的恢复行为不总是可预测的——它可能反复尝试被禁止的操作，浪费 token。

## 什么时候该用 Codex SDK

- 需要在自动化流程中调用 Coding Agent（CI/CD、批处理）
- 需要细粒度的权限控制（不同阶段不同权限）
- 需要管理多个并行 Thread（批量任务）
- 需要会话恢复（长时间任务分多次完成）
- 你的技术栈已经基于 OpenAI API

## 什么时候不该用

- 只需要交互式使用——直接用 CLI 更简单
- 你的主模型不是 OpenAI 的——SDK 对其他模型的支持不如 CLI 灵活
- 你需要稳定的 API 合约——SDK 还在快速迭代
- 你需要跨框架兼容——Pi 的 Skill 机制在多个框架间通用，Codex SDK 只在 Codex 生态内

## 小结

Codex SDK 的核心创新是 **per-turn 沙箱粒度**：同一个会话中，不同执行步骤可以有不同的权限级别。这让最小权限原则从"配置时声明"变为"运行时精确控制"。

编程式接口 + 细粒度权限 + Thread 恢复——这三者组合让 Codex SDK 适合"需要自动化但不能放弃安全控制"的场景。代价是 OpenAI 生态绑定和 API 成熟度不足。

---

下一篇：[开发者体验与生态评估：Trial 环的原因](../06-developer-experience/index.html)
