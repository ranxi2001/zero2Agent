---
layout: default
title: Inbox 控制：followup、steer、inject 的差别
description: 理解下一轮、当前步和系统事件三种消息注入方式
eyebrow: DeepSeek Harness / 06
---

# Inbox 控制：followup、steer、inject 的差别

真实用户不会等 Agent 自己完成才发消息。用户可能补充约束、撤回危险操作，或者只想让系统记录一条内部状态。把这些情况都当成普通 `user` 消息，会让时序和审计变得模糊。

## 三种入口

| API | 语义 | 适合场景 |
| --- | --- | --- |
| `agent.followup(message)` | 排队到当前 Turn 结束后的下一轮 | 用户继续追问、追加任务 |
| `agent.steer(message)` | 插入当前执行的控制路径 | 用户要求改方向、取消后续工具 |
| `agent.inject(message)` | 写入内部事件或上下文，不冒充用户轮次 | 系统状态、外部 webhook、测试注入 |

这些方法的确切可用窗口由 Agent 生命周期约束。官方事件 `agent/inbox/inserted`、`agent/inbox/claimed` 和 `agent/inbox/discarded` 应作为状态迁移记录；仅在内存队列里改数组无法支持重启恢复。

## 取消不是删除

收到 steer 或取消请求时，正在运行的模型流和工具进程需要通过 `AbortSignal` 协作退出。已经发生的工具调用不能从历史抹去，应记录结果为取消或中断，再由下一 Step 决定是否继续。

## 设计检查表

- 消息何时被 claim，谁拥有处理权？
- 当前 Step 已经产生的副作用如何回滚或补偿？
- 多个客户端同时 steer 时，顺序和权限如何确定？
- inbox 事件是否能在 resume 后重建？

参考 [Core Subsystem](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.1.0-rc.8/docs/subsystems/core.zh.md)。
