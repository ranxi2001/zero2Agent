---
layout: default
title: "Pi vs Claude Code vs DSH：按约束选择 Harness"
description: 用同一任务和失败实验比较三种 Agent Harness
eyebrow: Pi / 07
---

# Pi vs Claude Code vs DSH：按约束选择 Harness

## 为什么这个问题值得关注

Harness 选型不是比较谁的功能列表更长，而是选择模型适配、Session、上下文、安全策略和扩展代码分别由谁负责。只看宣传语或某次 Demo，容易把“存在某功能”误判成“该功能满足你的工程约束”。

Pi、Claude Code 和 DeepSeek Harness 代表三种不同的产品边界。比较它们的目的不是给出通用排名，而是设计一套可以在你的仓库里重复运行的验证方法。

## 比较基线

工具迭代很快，先固定证据版本：

- **Pi**：官方仓库 commit [`a470b121`](https://github.com/badlogic/pi-mono/tree/a470b121bf683b4c2b9fc0b3a7c807de7e0cfe9c)，以及 [latest 文档](https://pi.dev/docs/latest/)。
- **Claude Code**：2026-08-24 核验的官方 [Permissions](https://code.claude.com/docs/en/permissions)、[Sandboxing](https://code.claude.com/docs/en/sandboxing) 和 [Sessions](https://code.claude.com/docs/en/sessions) 文档。
- **DeepSeek Harness**：本项目固定参考官方 [`dsh-v0.1.0-rc.8`](https://github.com/deepseek-ai/deepseek-harness/tree/dsh-v0.1.0-rc.8)，具体设计见 [DeepSeek Harness 模块](../../learn-deepseek-harness/index.html)。

正式选型前应重新核验当前版本。下面矩阵只描述这些基线，不承诺未来版本不变。

## 三种产品边界

### Pi：基元和自定义优先

Pi 提供多 Provider、Agent Loop、工具、树形 Session、Compaction、TUI、JSON、RPC 和 SDK。它刻意不内置 MCP、subagent、权限弹窗、plan mode 和 background bash，鼓励用户通过 Extension、Package 或外部工具选择实现。

优点是定制路径直接，同一运行时可以服务多种宿主。代价是团队必须对第三方 Package、权限门禁和外部隔离负责。

### Claude Code：产品化工作流优先

Claude Code 围绕 Claude 模型提供完整产品体验，内置权限规则、权限模式、OS 级 bash sandbox、Session 恢复、checkpoint、Skills、Hooks、MCP 和多种交互入口。

优点是常见开发工作流与安全控制开箱可用。代价是深度行为受产品接口和 Claude 模型策略约束，无法像维护开源 Harness 那样直接修改核心实现。

### DeepSeek Harness：可组合运行时优先

DSH 把 Provider、工具、文件系统、Shell、sandbox、Session、UI 和 Agent Loop 等能力拆到插件与 capability seam 中，由 Profile 组合成具体产品。

优点是控制面与执行能力可以重组，适合研究或平台化。代价是插件依赖、策略组合和运行时所有权更复杂，团队需要承担更高的理解与维护成本。

## 可验证的决策矩阵

| 问题 | Pi | Claude Code | DeepSeek Harness |
| --- | --- | --- | --- |
| 主要入口 | TUI、Print/JSON、RPC、SDK | CLI、编辑器、桌面与产品入口 | Profile 组合的 Web、headless 等宿主 |
| 模型策略 | `pi-ai` 管理多 Provider 与模型目录 | 围绕 Claude 深度集成 | LLM seam 与插件组合 |
| Session | JSONL 树、resume、tree、fork、clone、compaction | 本地 Session、resume、branch、checkpoint、compaction | Session Log 与投影插件 |
| 定制 | Skill、Extension、Package、Prompt、Theme | Skill、Hook、MCP、Plugin、Subagent | Cordis 插件、capability seam、Profile |
| 项目资源保护 | project trust 控制高影响资源加载 | settings scope、权限与项目配置 | 由 Profile 和插件策略组合 |
| 工具审批 | 可由 Extension 或 Package 实现 | 内置 allow、ask、deny 和多种模式 | approval seam 与工具流水线 |
| 系统隔离 | 无内置 sandbox；使用容器、VM、Gondolin、OpenShell | bash sandbox + 文件工具权限；可配置 fail closed | sandbox policy 与可替换执行后端 |
| 控制流改造 | Extension API 内定制，必要时维护源码 Fork | 受公开产品接口约束 | Agent Loop 和策略均可插件化 |
| 维护责任 | 组合选择和第三方包责任较多 | 产品行为由厂商维护，组织负责配置 | 插件图、Profile 与兼容责任较多 |

这不是评分表。每一格都应该转成实验和证据，不能从“支持”两个字直接推出生产能力。

## 安全比较要拆成三问

### 谁决定某次动作是否允许

- Pi：Extension 可以在 `tool_call` 前拒绝或询问，默认内置工具没有统一权限弹窗。
- Claude Code：权限规则按 deny、ask、allow 等逻辑处理，并提供多种 permission mode。
- DSH：工具调用经过可组合的 policy 与 approval 流水线，由当前 Profile 决定实际策略。

### 谁限制最坏影响范围

- Pi：外部容器、VM、micro-VM、远程 sandbox 或低权限账号。
- Claude Code：bash 可使用 OS 级 sandbox，内置文件工具仍通过权限系统控制；不同工具边界需要分别理解。
- DSH：sandbox policy 可由本地平台后端或其他 capability provider 执行，具体强度取决于组合和平台。

### 控制失败时会不会继续执行

真正重要的是 fail-closed 行为：sandbox 不可用、审批 UI 不存在、策略插件缺失或规则解析失败时，是拒绝任务、降级提示，还是静默以完整权限运行。

这一点必须在目标平台上故障注入，不能只根据架构图推断。

## Session 比较不能只问“能不能恢复”

三者都具备会话能力，选型时应继续追问：

- transcript 的事实源是什么格式，是否可导出和独立解析？
- 分支是在同一文件中导航，还是创建新 Session？
- 文件 checkpoint 与对话分支是不是同一概念？
- compaction 后哪些目标、文件和工具证据会保留？
- 两个进程同时恢复同一 Session 会发生什么？
- Session 中是否包含密钥、工具大输出或隐私数据？
- 外部宿主怎样中止、flush、关闭和恢复？

Pi 的 `/tree`、`/fork`、`/clone` 语义不同；Claude Code 的 checkpoint 还涉及文件状态恢复；DSH 的 Session Log 与插件投影强调事件事实。只写“均支持 Session”没有决策价值。

## 扩展能力比较要看权限域

| 扩展方式 | 运行在哪里 | 能做什么 | 主要风险 |
| --- | --- | --- | --- |
| Pi Extension | Pi Node.js 进程 | 工具、事件、Session、Provider、TUI | 与 Pi 同权限，第三方代码需自审 |
| Claude Code Hook | 外部命令、HTTP、Prompt 或 Agent | 生命周期自动化与门禁 | hook 本身的命令、环境和输出需要治理 |
| Claude Code MCP | 独立 Server 或远端服务 | 标准化工具与数据连接 | 认证、Server 权限和工具 schema 成本 |
| DSH Plugin | Cordis 运行时与注册的 provider | 替换或组合控制面与能力 | 依赖图、所有权和插件交互复杂 |

“扩展很多”不等于“升级容易”。评估时要记录扩展 API 稳定性、失败隔离、reload 行为、版本固定和移除后的残留状态。

## 在三个 Harness 上运行同一组实验

准备一个临时仓库，包含两个源文件、一个会失败的测试和明确的项目规则。让三个候选工具完成同一任务：

```text
修复测试失败，只允许修改 src/a.ts 和 src/b.ts。
先解释失败原因，再修改并运行测试。禁止发布和外部写操作。
```

### 实验 1：项目上下文

检查是否读取项目规则，规则何时进入模型，以及不信任项目时哪些资源仍会加载。

### 实验 2：工具闭环

记录每个 tool call 与 result，确认失败的测试和工具错误都有结构化结果。

### 实验 3：用户插话

在工具执行中发送新指令，观察它是立即中止、当前 turn 后 steering，还是任务结束后的 follow-up。

### 实验 4：恢复与分支

中止任务后恢复，从同一历史点尝试两种实现，再确认活动分支和文件状态。

### 实验 5：上下文压力

制造大工具输出，触发 compaction，检查目标、约束、已修改文件、验证结果和未完成事项是否保留。

### 实验 6：危险操作

触发一次越界写入和一个外部命令，记录权限提示、sandbox 结果、实际文件状态和审计证据。

### 实验 7：扩展失败

让一个 Extension、Hook 或 Plugin 加载失败，观察无关功能是否仍可用，旧 handler 是否残留，系统是否明确报告降级。

## 记录可以比较的指标

| 维度 | 指标示例 |
| --- | --- |
| 任务结果 | 测试是否通过、diff 是否在允许范围、重复成功率 |
| 人工负担 | 审批次数、补充 Prompt 次数、恢复时人工重建上下文时间 |
| 模型成本 | 总请求轮数、input/output/cache token、延迟 |
| 失败恢复 | 工具错误恢复率、Session 恢复质量、compaction 信息保留 |
| 安全 | 最大文件与网络权限、默认拒绝行为、外部写操作可追踪性 |
| 维护 | 配置文件数、扩展代码量、升级后回归失败数量 |

不要只记录最佳一次。Agent 行为有随机性，至少要保留代表性的失败轨迹，才能知道系统靠什么恢复。

## 三类典型约束

### 已有隔离平台，需要多模型和深度定制

Pi 值得优先验证。多 Provider、公开源码、SDK/RPC 和 Extension 提供较直接的组合路径。前提是团队愿意承担 Package 审计和外部隔离。

### 主要使用 Claude，希望权限和产品体验开箱可用

Claude Code 值得优先验证。权限、sandbox、Session、Skills、Hooks 和 MCP 已形成产品化工作流。需要确认平台支持、组织策略和独有能力绑定是否符合长期计划。

### 研究控制平面、能力接缝或可替换 Loop

DSH 值得优先验证。它允许更深入地替换 provider、policy 和 runtime 组件，但这项灵活性只有在团队能够维护插件组合时才有价值。

## 可以共享什么，不能共享什么

较容易共享：

- 遵循共同约定的 `SKILL.md` 和参考资料；
- MCP Server 与服务端权限模型；
- 仓库规则、测试、Eval case 和任务 fixture；
- 结构化业务工具背后的领域逻辑。

通常需要重写或适配：

- Agent Loop 和消息队列语义；
- Session 分支、compaction 与恢复策略；
- 权限、审批、sandbox 和扩展 hook；
- TUI、状态栏和宿主生命周期；
- Framework-specific Extension、Hook 或 Plugin。

工具层互操作可以降低迁移成本，却不能消除控制层差异。

## 常见误判

### “Pi 没有 Session”

错误。Pi 原生提供持久化、恢复、树形分支、fork、clone 和 compaction。

### “Claude Code 有权限提示，所以不需要系统隔离”

错误。权限、bash sandbox、内置文件工具和外部服务各有边界，高风险任务仍要按资产设计隔离。

### “DSH 一切可替换，所以一定更灵活”

只有当目标 Profile 真正装配了所需 seam、provider 和 policy，并且团队能维护插件图时，这种灵活性才成立。

### “一个 MCP Server 可以抹平三个 Harness”

MCP 只统一部分工具连接。Context 构造、Session、审批和 Loop 仍由各自 Harness 决定。

## 小结

- 选 Harness 是选择责任边界，不是选择功能数量。
- Pi 偏向基元与自定义，Claude Code 偏向产品化工作流，DSH 偏向可组合运行时。
- 安全要分别比较动作决策、最坏影响范围和故障时是否 fail closed。
- Session、扩展和 MCP 都必须通过同一任务与失败实验验证。
- 最终决策应来自重复任务的证据矩阵，而不是 star、口号或一次成功 Demo。

---

下一篇建议继续看：[Session Runtime：树形历史、恢复与 Compaction](../08-session-runtime/index.html)
