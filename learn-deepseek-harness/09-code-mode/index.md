---
layout: default
title: Code Mode：上下文压缩不等于安全隔离
description: 理解 Code Mode 的压缩价值与真实安全边界
eyebrow: DeepSeek Harness / 09
---

# Code Mode：上下文压缩不等于安全隔离

当工具数量变多，模型需要在上下文中阅读大量名称、Schema 和中间结果。Code Mode 的设计动机不是“让模型拥有一个 Shell”，而是把一组结构化工具压缩成可组合的程序接口，让模型用更少的上下文表达一段计划。

## 设计理念：压缩接口，不放弃治理

Code Mode 同时带来两件事：

1. 模型可以在一次代码片段中组合多个绑定，减少工具列表和往返次数。
2. 模型生成的代码变成新的不确定输入，必须拥有更严格的预算、取消和权限边界。

所以 `run_code` 里的子调用仍然要重新进入普通 Tool Pipeline。Code dispatch 只是调度形态变化，不是审批和审计的旁路。

## 三层边界

| 层次 | 要解决的问题 |
| --- | --- |
| Binding | 哪些工具和数据可以被代码看到 |
| Runtime | CPU、时间、输出、并发和返回值如何受限 |
| Sandbox / Policy | 进程、文件、网络和凭据的真实权限 |

隔离标签不等于安全保证。语言字段存在也不代表当前 Profile 提供同样的后端。策略解析失败时必须 fail closed，否则一次配置错误就可能把受限执行降级为宿主进程执行。

## 设计取舍

Code Mode 提高了表达密度和批量调度能力，也增加了调试难度：错误可能来自代码、绑定、子工具或执行器。解决办法不是取消 Code Mode，而是为 `exception`、`timeout`、`abort`、`worker-exit`、`invalid-output` 和 `output-limit` 建立可区分的失败语义。

参考 [Code Runtime](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.1.0-rc.8/docs/subsystems/code-runtime.zh.md) 与 [Sandbox](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.1.0-rc.8/docs/subsystems/sandbox.zh.md)。

下一篇建议继续看：[Context Compaction：把上下文当作工作集管理](../10-context-compaction-cost/index.html)
