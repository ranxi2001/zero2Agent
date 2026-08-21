---
layout: default
title: Context Compaction：把上下文当作工作集管理
description: 理解上下文压缩背后的信息选择、缓存与成本设计
eyebrow: DeepSeek Harness / 10
---

# Context Compaction：把上下文当作工作集管理

长对话的问题不是“模型记性不好”，而是每一轮决策都要在有限预算里选择信息。把完整历史原样塞回请求，会浪费 token、破坏缓存，还会让旧工具结果和当前目标争夺注意力；简单截断则可能删掉约束和未完成副作用。

## 设计理念：Context 是工作集，不是聊天记录

Session Log 保存完整事实，Context Builder 只为当前决策准备工作集。这个工作集应该稳定地保留目标、约束、未完成动作和必要证据，同时把低价值细节压缩、外置或延迟加载。

## 压缩必须保持哪些语义

官方 `compactIfNeeded` 和 `compactNow` 的 API 只是入口，真正的设计要求是压缩前后不能丢掉：

- 用户当前目标和不可违反的约束
- 已经发生的工具副作用与失败原因
- 未完成的调用、审批状态和取消状态
- 下一步决策需要的证据来源

压缩应该产生可审计的替换事件，而不是覆写旧日志。这样恢复时可以知道哪一代上下文被 shadow，调试时也能比较压缩前后的决策差异。

## 成本和缓存是同一个设计问题

稳定的 System Prompt、工具定义和 Skills 元数据适合放在前缀；动态轨迹、检索结果和工具输出放在后部。`tokenMeter` 负责解释输入、输出和缓存命中，`spillStore` 负责把大结果移出工作集。这样做不是单纯省钱，而是减少无关信息对模型注意力的干扰。

## 设计取舍

摘要越短不代表越好。压缩会引入新的模型判断，因此需要回放测试：压缩前后是否仍会选择相同的工具、是否仍记得审批边界、是否能解释结论来源。可恢复性、缓存命中和信息完整性之间没有免费的最优解。

参考 [Compaction](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.1.0-rc.8/docs/subsystems/compaction.zh.md) 与 [Capability Seams](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.1.0-rc.8/docs/capability-seams.zh.md)。

下一篇建议继续看：[安全边界：把信任放到模型之外](../11-security-boundary/index.html)
