---
layout: default
title: DeepSeek Harness
description: 从设计理念理解可组合 Agent Runtime 的工程边界
eyebrow: Module 07
---

# DeepSeek Harness

**不是把 Prompt 写得更长，而是把 Agent 变成一个可恢复、可控制、可演进的运行时。**

一个模型调用很容易写出来。难的是让它连续运行几十轮，允许用户中途改方向，能够从崩溃中恢复，在执行危险动作前停下来，并且能解释每一个副作用是怎样发生的。DeepSeek Harness 值得学习的地方，不是某个 CLI 或某组 TypeScript 类型，而是它对这些问题的系统性回答。

## 七个设计判断

| 设计问题 | 核心判断 | 运行时承载 |
| --- | --- | --- |
| 什么是核心 | 不保留不可替换的特权内核 | Cordis Plugin Tree |
| 状态从哪里来 | 事实应该追加保存，状态从事实派生 | Session Log |
| 模型差异怎么隔离 | 用统一词汇表约束消息、流式输出和失败事实 | LLM Seam / Adapter Registry |
| 能力如何扩展 | 用服务接缝组合能力，不把所有逻辑塞进 Loop | Cordis Plugin / Capability Seam |
| 模型如何产生副作用 | 决策和执行分离，模型输出不等于授权 | Agent Loop / Tool Pipeline |
| 长任务如何持续 | Context 是受管理的工作集，压缩要保持语义 | Compaction / Token Meter / Spill |
| 如何守住边界 | 审批、沙箱和凭据由运行时强制，失败默认拒绝 | Approval / Sandbox / Policy |

这些判断共同完成一次复杂度转移：用户只看到一个连续的任务体验，系统内部则把不确定的模型决策包在确定的日志、策略和生命周期里。代价是实现更复杂、服务契约更多、调试需要理解事件顺序；收益是系统可以恢复、审计、替换和测试。

## 阅读顺序

```mermaid
flowchart LR
  A["复杂度转移"] --> B["能力组合"]
  B --> C["事实源"]
  C --> D["控制循环"]
  D --> E["副作用边界"]
  E --> F["上下文与成本"]
  F --> G["安全与多运行面"]
```

1. [Agent Harness 与一切皆插件](./01-what-is-harness/index.html)：从无特权内核建立设计目标
2. [声明式与命令式：Cordis 的五个核心概念](./02-cordis-plugin-kernel/index.html)：理解 DSH 为何承担更重的运行时复杂度
3. [运行中的 DSH：插件树、组合层与能力接缝](./03-profile-bundle-patch/index.html)：理解产品如何从有序配置层启动
4. [LLM 接缝：把模型差异关在适配器里](./04-llm-seam/index.html)：理解统一词汇表、流式协议与失败策略
5. [Agent Loop：控制平面如何推进任务](./05-agent-loop/index.html)
6. [Tool Pipeline：能力为什么不能直接等于权限](./06-tool-pipeline/index.html)
7. [Session Log：为什么日志就是事实源](./07-session-log/index.html)：理解可恢复性的基础
8. [Inbox 控制：为什么用户插话必须有自己的语义](./08-inbox-control/index.html)
9. [Code Mode：上下文压缩不等于安全隔离](./09-code-mode/index.html)
10. [Context Compaction：把上下文当作工作集管理](./10-context-compaction-cost/index.html)
11. [安全边界：把信任放到模型之外](./11-security-boundary/index.html)
12. [Subagent 编排：扩展能力而不是复制 Loop](./12-subagent-orchestration/index.html)
13. [Runtime Surfaces：一个运行时如何服务多个宿主](./13-runtime-surfaces/index.html)

## 资料边界

文章以官方仓库 [dsh-v0.1.0-rc.8](https://github.com/deepseek-ai/deepseek-harness/tree/dsh-v0.1.0-rc.8) 的架构和子系统文档为事实基线。社区教程、电子书、白皮书和 NanoCordis 用来帮助理解设计背景与教学实现；它们描述的 `rc.6` 或简化 API 不直接代表当前接口。

本文更关心可迁移的设计问题：换成其他模型、Provider 或宿主后，为什么这些边界仍然成立。API 名称只在需要确认契约时出现。
