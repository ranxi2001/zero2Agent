---
layout: default
title: 安全边界：Approval、Sandbox 与凭据
description: 用审批、沙箱、策略和 fail-closed 设计阻止 Agent 把便利变成越权
eyebrow: DeepSeek Harness / 10
---

# 安全边界：Approval、Sandbox 与凭据

工具和 Code Mode 让 Agent 能修改文件、执行进程和访问网络，也让“模型说了算”变成真实风险。安全边界必须位于模型输出之外，由运行时策略强制执行。

## Approval 是有状态的协议

`ctx.approval.request(req)` 只能在打开的 Turn 中请求审批。当前结果枚举包括 `allowed-once`、`rejected`、`cancelled`、`unavailable`。请求和决定分别记录为 `approval/asked` 与 `approval/decided`，审批服务不可用时应 fail closed。

审批不是一个 UI 弹窗就结束了，还需要绑定：请求对应的工具调用、参数摘要、操作者、有效期和决定来源。重试同一个危险调用时，不能默认复用上一次的允许。

## Sandbox 负责进程边界

`ctx.sandbox` 是进程执行接缝，`ctx.sandboxPolicy.resolve()` 决定采用哪种策略。受限执行失败时必须明确报错；静默退回 unconfined 会把配置错误升级成权限漏洞。`danger-full-access` 属于显式旁路，不能伪装成普通受限模式。

## 凭据和日志

真实模型凭据只从环境变量或宿主的密钥管理器读取，不写入会话日志、工具结果或代码绑定。日志保留审计所需的元数据，但对 token、Cookie、Authorization header 和用户隐私做结构化脱敏。

参考：[Approval](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.1.0-rc.8/docs/subsystems/approval.zh.md)、[Sandbox](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.1.0-rc.8/docs/subsystems/sandbox.zh.md)。
