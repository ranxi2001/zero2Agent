---
layout: default
title: Subagent 编排：可选能力而不是第二个 Loop
description: 通过 provider registry、capability 检查和 workflow 边界理解 Subagent 组合
eyebrow: DeepSeek Harness / 11
---

# Subagent 编排：可选能力而不是第二个 Loop

多 Agent 不是把一个 Loop 复制几份。每个子 Agent 都会带来新的会话、权限、预算、失败传播和上下文边界。DeepSeek Harness 将这些能力放在 `ctx.subagents` 接缝中，让核心 Agent Loop 不必知道具体供应商。

## Provider registry

`ctx.subagents.registerProvider(provider)` 注册 provider，`getProvider(name)` 读取 provider。官方文档列出 in-process、fork、ACP、Codex、Claude Code 和 DSH SDK 等实现方向；实际可用能力由 Profile 和 provider 声明决定。

调用前先检查 capability：是否支持流式输出、取消、工具、工作目录、审批转发和上下文隔离。能力不满足时应在启动前拒绝，而不是运行到中途才发现无法恢复。

## 谁负责编排

- `ctx.subagents` 负责发现、启动和回收子 Agent。
- `ctx.workflowEngine` 负责显式的工作流、依赖和并行关系。
- `ctx.jobs` 负责脱离当前 Turn 的后台任务和状态查询。

这三个服务都是可选接缝，不等于核心 Loop。一个简单任务可以只使用单 Agent；只有当隔离、并行或不同模型能力带来可测收益时才引入 Subagent。

参考：[Subagent](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.1.0-rc.8/docs/subsystems/subagent.zh.md)、[Workflow](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.1.0-rc.8/docs/subsystems/workflow.zh.md) 和 [Jobs](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.1.0-rc.8/docs/subsystems/jobs.zh.md)。
