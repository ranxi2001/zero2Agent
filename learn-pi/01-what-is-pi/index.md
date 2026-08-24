---
layout: default
title: Pi 是什么：从一次工具往返理解运行时
description: 用真实工具闭环理解 Pi 的职责边界
eyebrow: Pi / 01
---

# Pi 是什么：从一次工具往返理解运行时

Pi 不只是终端聊天界面，也不宜被概括成固定的“四包架构”。它是一个可组合的 Coding Agent 系统：模型适配、Agent 状态与工具循环、会话管理、终端交互和扩展加载分别承担不同职责。包会演进，**职责边界**比包数量更稳定。

> 事实基线：2026-08-24，官方仓库 [`badlogic/pi-mono`](https://github.com/badlogic/pi-mono) commit `a470b121`。

## 一次请求为什么会调用模型两次

[《动手学 Pi》序章](https://chasen-liao.github.io/pi-textbook-page/learn/prologue/)用“读取 README 并概括项目”展示七个可见里程碑。下面的 `model_start`、`tool_start` 是教材抽象事件名，不是官方 JSON 事件 API 名称：

```text
user_message
→ model_start（第一轮）
→ assistant_message（提出 read，toolCallId=call_1）
→ tool_start（Loop 开始调度）
→ tool_result（返回文件事实，仍是 call_1）
→ model_start（第二轮）
→ assistant_message（最终回答）
```

这里有三条不能混淆的事实：

1. 模型提出 `read`，不等于文件已经读取。
2. `toolCallId` 把请求和结果配成一对，缺少结果就无法证明动作成功。
3. `model_start`、`tool_start` 适合显示进度；长期 transcript 保存的是后续推理仍需要的结构化消息与工具结果。真实 session JSONL 还会保存模型切换、compaction、分支摘要和 Extension entry 等记录，不能把会话简化成三种消息。

一次用户输入因此可能触发多轮模型调用。工具错误、中止和超时也属于 Loop 的状态，而不是 UI 上的一句提示。

## 用职责层理解 Pi

- **Provider 层**：把不同模型 API 转成统一的消息、流式事件、工具调用和用量语义。
- **Agent runtime**：保存状态，调用模型，调度工具，再把工具结果送回下一轮。
- **Coding agent**：组装项目上下文、内置工具、会话、资源加载和交互行为。
- **交互层**：TUI 只是一个入口；Pi 还可通过 print/JSON、RPC 和 SDK 被其他程序控制。
- **定制层**：Skill 提供按需知识，Extension 改变运行时，Package 负责分发。

这也解释了为什么“终端原生”不等于“只能在终端里用”。同一条结构化事件流可以被 TUI、日志系统或外部应用消费。

## Pi 原生拥有会话能力

Pi 并非“没有会话恢复”。官方实现提供持久化会话、恢复、树形导航、分支、克隆与 compaction。真正需要评估的不是“有没有”，而是：

- 哪些消息是事实源；
- 分支后当前路径如何选择；
- 压缩后哪些约束必须保留；
- 外部系统如何通过 SDK/RPC 管理生命周期。

这些内容会在第 08 篇集中展开。

## 最小内核不等于默认安全

Pi 的工具和 Extension 以当前进程权限运行。项目 trust 控制项目级资源何时加载，但它不是文件系统或网络沙箱。Prompt 中写“不要执行危险操作”也不是权限控制。

实践中至少要做到：

- 在临时仓库或低权限环境开始；
- 修改前保存 Git 基线，修改后检查 diff；
- 对发布、删除、凭据和外部写操作设置确认；
- 审查第三方 Skill 中的脚本以及 Extension 的可执行代码；
- 高风险任务放进正确配置的容器或沙箱。

## 小结

理解 Pi 的最好入口不是记包名，而是追踪一次完整工具往返：谁提出动作、谁执行动作、哪条结果成为下一轮事实、哪些记录进入会话。这个模型稳定以后，Provider、Skill、Extension、MCP 和 Session 才不会混成一团。

---

下一篇建议继续看：[pi-ai：统一 Provider 的边界](../02-pi-ai-provider/index.html)
