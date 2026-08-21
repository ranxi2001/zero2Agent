---
layout: default
title: Context Compaction：压缩、计量与缓存
description: 从压力触发、替换消息到 token meter 和 spill，建立可解释的上下文成本模型
eyebrow: DeepSeek Harness / 09
---

# Context Compaction：压缩、计量与缓存

上下文超限不是简单截断字符串。截断可能丢掉工具调用和用户约束，摘要也可能引入模型幻觉。可恢复的 Harness 需要把压缩当成日志事件和可观测状态迁移。

## 两种触发方式

官方 `ctx.compaction.compactIfNeeded(agent, trigger, signal)` 支持压力触发和上下文溢出触发；`compactNow(agent, signal)` 用于显式压缩。触发类型是 `'pressure' | 'context-overflow'`，调用方应传入取消信号。

压缩不会覆写历史。系统记录压缩相关事件，并在派生消息中使用替换的 `user/message`。因此需要同时关注 generation、被 shadow 的 seq，以及压缩前后的 token 计量。

## 成本不只是一项 token

`ctx.tokenMeter` 应至少区分输入、输出、缓存命中和工具结果；大结果可写入 `ctx.spillStore`，上下文只保留稳定摘要与引用。稳定的 System Prompt、工具定义和 Skills 元数据放在前缀，动态轨迹放在后部，更有利于 Provider 的前缀缓存。

## 验证压缩质量

为每类任务准备压缩前后的回放测试：目标、约束、未完成工具调用、审批状态和错误原因都不能丢。不要只比较摘要长度；要比较下一步决策是否改变，以及改变是否可解释。

参考：[Compaction](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.1.0-rc.8/docs/subsystems/compaction.zh.md) 与 [Capability Seams](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.1.0-rc.8/docs/capability-seams.zh.md)。
