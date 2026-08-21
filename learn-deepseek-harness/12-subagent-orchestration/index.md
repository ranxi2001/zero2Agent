---
layout: default
title: Subagent 编排：扩展能力而不是复制 Loop
description: 用可选接缝组织子代理、工作流与后台任务
eyebrow: DeepSeek Harness / 12
---

# Subagent 编排：扩展能力而不是复制 Loop

多 Agent 常被描述成“再启动几个 Agent”。这会快速放大会话、权限、预算、失败传播和上下文隔离问题。更稳妥的设计是把 Subagent 当作一种可选能力，由主运行时决定何时使用，而不是让每个子进程重新发明一套控制规则。

## 设计理念：一切皆插件，但不是一切都必须启用

从官方架构和社区实践看，可以把 DSH 理解成一个插件化 Agent Runtime：模型、工具、文件系统、Shell、沙箱、会话存储、Subagent、UI，甚至 Loop 本身，都可以成为可替换的能力模块。官方 Web 和 headless 是一套预置 Profile；外部 Profile 和插件可以拼出不同的宿主形态。

这是一种很强的组合能力，也是一种很高的复杂度转移。插件越自由，依赖、权限和版本兼容越难治理，所以“可插拔”不等于“随便加载”。

## 三种编排责任

| 接缝 | 负责的问题 | 不应取代什么 |
| --- | --- | --- |
| `ctx.subagents` | 发现 provider、检查能力、启动和回收子 Agent | 核心 Agent Loop |
| `ctx.workflowEngine` | 表达依赖、并行和显式工作流 | 隐式的消息拼接 |
| `ctx.jobs` | 管理脱离当前 Turn 的后台任务 | 当前 Turn 的完成状态 |

Provider 的能力应该在启动前检查：是否支持流式、取消、工具、工作目录、审批转发和上下文隔离。能力不满足时提前拒绝，比运行到中途再处理半成品更容易恢复。

## 自进化的实验性边界

一个值得关注的方向是：Agent 检查当前 runtime，现场编写一个插件并挂载，随后在任务中使用新能力。这已经接近“自进化软件”的雏形，但当前更适合看作实验性能力：动态插件可能只存在于内存，重启后消失，也还没有自动沉淀为经过审查的永久插件。

真正可靠的自进化还需要版本化、权限审批、测试门禁、回滚和来源追踪。能现场写出代码只是能力生成，不等于能力已经获得生产信任。

参考 [Subagent](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.1.0-rc.8/docs/subsystems/subagent.zh.md)、[Workflow](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.1.0-rc.8/docs/subsystems/workflow.zh.md) 和 [Jobs](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.1.0-rc.8/docs/subsystems/jobs.zh.md)。

下一篇建议继续看：[Runtime Surfaces：一套运行时如何服务多个宿主](../13-runtime-surfaces/index.html)
