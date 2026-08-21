---
layout: default
title: DeepSeek Harness
description: 从 Cordis 插件内核、会话日志和 Agent Loop，到工具、安全、压缩与 Subagent 的系统拆解
eyebrow: DeepSeek Harness / Core
---

# DeepSeek Harness

**把一个可运行的 Agent，拆成可以验证、替换和治理的运行时。**

很多教程把 Harness 当成一段更长的 System Prompt，或把 Agent Loop 简化成一个 `while` 循环。DeepSeek Harness 提供了另一种观察角度：模型只是决策组件，真正决定系统能否长期运行的，是会话日志、上下文构造、工具边界、权限审批、沙箱、压缩和可观测事件组成的运行时。

本模块以讲解为主，围绕官方仓库 `deepseek-harness` 的 `dsh-v0.1.0-rc.8` 文档和源码建立主线。社区教程、电子书、白皮书与 NanoCordis 用来补充背景和教学实现；遇到 API 差异时，以官方版本化文档为准。

## 阅读主线

```mermaid
flowchart LR
  A[配置与插件] --> B[会话日志]
  B --> C[Agent Loop]
  C --> D[工具与 Code Mode]
  D --> E[压缩与成本]
  E --> F[审批与沙箱]
  F --> G[Subagent 与运行面]
```

建议按顺序阅读。前 05 篇建立最小运行时模型，06–10 篇解释控制、工具、上下文和安全边界，最后两篇再讨论多 Agent 和不同宿主。

## 文章目录

1. [Harness 到底解决什么问题](./01-what-is-harness/index.html)
2. [Cordis 插件内核：服务、事件与生命周期](./02-cordis-plugin-kernel/index.html)
3. [Profile、Bundle 与 Patch：运行时如何组装](./03-profile-bundle-patch/index.html)
4. [Session Log：为什么日志就是事实源](./04-session-log/index.html)
5. [Agent Loop：Turn、Step 与请求边界](./05-agent-loop/index.html)
6. [Inbox 控制：followup、steer、inject 的差别](./06-inbox-control/index.html)
7. [Tool Pipeline：一次工具调用经过哪些门](./07-tool-pipeline/index.html)
8. [Code Mode：把代码执行当作受控工具](./08-code-mode/index.html)
9. [Context Compaction：压缩、计量与缓存](./09-context-compaction-cost/index.html)
10. [安全边界：Approval、Sandbox 与凭据](./10-security-boundary/index.html)
11. [Subagent 编排：可选能力而不是第二个 Loop](./11-subagent-orchestration/index.html)
12. [Runtime Surfaces：Web、Headless、ACP 与 SDK](./12-runtime-surfaces/index.html)

## 资料与版本

| 资料 | 用途 | 版本或许可 |
| --- | --- | --- |
| [DeepSeek Harness 官方仓库](https://github.com/deepseek-ai/deepseek-harness/tree/dsh-v0.1.0-rc.8) | API、服务契约、架构事实 | `dsh-v0.1.0-rc.8`，MIT |
| [Cordis](https://github.com/shigma/Cordis/tree/8cc9e33) | 插件内核与依赖注入背景 | MIT |
| [DeepSeek Harness 从零到一](https://github.com/yanhua1010/dsh-harness-tutorial/tree/2a29d03) | 中文 Demo 与教学实现 | MIT，社区资料 |
| [从开机到拆开](https://github.com/alchaincyf/deepseek-harness-orange-book/tree/887f4b4) | 系统提示词、启动清单与原始会话日志 | 社区电子书，按上游声明使用 |
| [解剖 DeepSeek Harness](https://xueai.app/slides/learn.html#dsh-1.html) | 交互式源码专题 | 在线资料 |
| [Cordis 在做什么](https://blog.antinomie.org) | 从插件作者视角补充 Cordis 心智模型 | 在线短文 |
| [DeepSeek Harness 白皮书](https://github.com/Electricitysheep/dsh-handbook/tree/6dafa52) | 安装、插件与安全的补充叙述 | CC BY-NC-SA 4.0，基于 `0.1.0-rc.6` |
| [NanoCordis](https://github.com/SheltonLiu-N/nano-cordis/tree/caea7b0) | 可运行的简化框架 | MIT |

社区材料基于较早的 `rc.6` 或教学 API，不能直接当作 `rc.8` 的接口说明。本文会明确标出推导、实现建议和仍需在本地验证的部分。
