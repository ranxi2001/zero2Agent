---
layout: default
title: Code Mode：把代码执行当作受控工具
description: 解释 run_code、结构化绑定、预算与失败分类，避免把隔离误当安全
eyebrow: DeepSeek Harness / 08
---

# Code Mode：把代码执行当作受控工具

当工具数量达到几十或上百个时，让模型逐个选择工具会增加上下文和调度成本。Code Mode 让模型编写一段代码，再由运行时提供结构化绑定完成批量调用。但它只是另一种工具入口，不是权限模型的替代品。

## DSH 的两个边界

`run_code` 会把代码中的子调用重新送入普通 Tool Pipeline，因此每个真实工具仍要经过参数校验、审批和审计。Code dispatch 记录为 `tool/code-dispatch`，为了避免重复上下文，不把 `additionalContexts` 当作普通相邻工具结果追加。

`ctx.codeRuntime.run(request)` 是运行时接缝。当前文档列出 `typescript` 和 `python` 语言，但官方发布的后端能力要以当前 Profile 为准；语言字段存在不代表每个发行包都已提供对应执行器。

## 必须限制的资源

- CPU、墙钟时间、输出字节数和并发子调用数
- 可访问的文件、网络、环境变量和凭据
- 绑定输入与返回值的 JSON 可序列化边界
- `exception`、`timeout`、`abort`、`worker-exit`、`invalid-output`、`output-limit` 等失败分类

隔离标签只是运行时描述，不是安全保证。若代码执行需要受限环境，应通过 `ctx.sandbox` 和 `ctx.sandboxPolicy` 明确选择策略；策略解析失败必须 fail closed，而不是悄悄退回宿主进程。

参考：[Code Runtime](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.1.0-rc.8/docs/subsystems/code-runtime.zh.md)、[Sandbox](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.1.0-rc.8/docs/subsystems/sandbox.zh.md)。
