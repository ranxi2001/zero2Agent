---
layout: default
title: Codex vs Claude Code vs DSH：三种终端 Agent 的工程对比
description: 从架构、安全、MCP 和生态四个维度对比三种 Coding Agent 的工程 tradeoff
eyebrow: Codex CLI / 07
---

# Codex vs Claude Code vs DSH：三种终端 Agent 的工程对比

## 为什么这个问题值得关注

2025-2026 年，三个主要的终端 Coding Agent 形成了清晰的竞争格局：

- **OpenAI Codex CLI**：Rust + TypeScript，平台原生沙箱，TOML 配置
- **Anthropic Claude Code**：TypeScript 全栈，应用层权限，CLAUDE.md 指令
- **DeepSeek Harness**：TypeScript + Cordis 插件系统，策略平面，可组合运行时

三者功能高度重叠（都能读写文件、执行命令、调用 MCP 工具），但做了根本不同的工程判断。这些判断不是"谁对谁错"，而是不同环境假设下的合理选择。

理解这些差异，能帮你在具体场景中做出选择——不是"哪个最好"，而是"哪个的假设和我的环境最匹配"。

## 架构哲学对比

### Codex CLI：性能优先 + 平台依赖

```text
核心判断：Agent 的热路径（沙箱检查、MCP 通信、配置解析）必须足够快
实现方式：Rust 内核处理性能敏感路径，TypeScript 处理 UI 和扩展
代价：双层构建、跨语言调试、平台耦合
```

### Claude Code：一致性优先 + 应用层控制

```text
核心判断：整个系统用一种语言能减少边界处的 bug 和认知负担
实现方式：TypeScript 全栈，权限检查在应用层，沙箱在框架内部实现
代价：性能天花板（Node.js GC、JSON 解析），安全边界相对软
```

### DeepSeek Harness：可组合优先 + 插件万物

```text
核心判断：没有任何组件应该是不可替换的
实现方式：Cordis 插件树，所有功能（包括 Agent Loop 本身）都是插件
代价：复杂度最高，学习曲线陡峭，社区生态依赖
```

### 一张表对比

| 维度 | Codex CLI | Claude Code | DeepSeek Harness |
| --- | --- | --- | --- |
| 核心语言 | Rust + TypeScript | TypeScript | TypeScript (Cordis) |
| 架构风格 | 分层（性能层 + 交互层） | 单体（全栈 TS） | 插件树（万物可替换） |
| Agent Loop | Turn-based | Continuous | 可替换（插件） |
| 复杂度 | 中 | 低 | 高 |
| 性能天花板 | 高（Rust 热路径） | 中（Node.js） | 中（依赖插件实现） |
| 可替换性 | 低（Rust 核心固定） | 低（框架核心固定） | 高（Loop 都可换） |

## 安全模型对比

这是三者分歧最大的维度。

### Codex：操作系统强制

```text
安全假设：操作系统的沙箱机制比任何应用代码都可靠
实现：macOS Seatbelt + Linux Bubblewrap
边界：内核级——绕过需要内核漏洞
粒度：路径级（文件系统）+ syscall 级（网络、进程）
```

### Claude Code：应用层审批

```text
安全假设：用户交互式审批 + 框架逻辑检查能覆盖风险
实现：TypeScript 中的权限检查 + 用户 prompt
边界：应用级——框架 bug 可能绕过
粒度：操作级（读/写/执行分别控制）
```

### DSH：策略平面

```text
安全假设：安全策略本身需要可编程、可替换
实现：Approval 插件 + 策略平面
边界：取决于策略实现——可以硬也可以软
粒度：完全自定义（可以根据上下文决策）
```

### 安全对比表

| 维度 | Codex | Claude Code | DSH |
| --- | --- | --- | --- |
| 绕过难度 | 极高 | 中 | 取决于策略 |
| 子进程安全 | 自动继承 | 需显式处理 | 取决于插件 |
| 动态策略 | 不支持 | 有限 | 完全支持 |
| 审计友好 | 是（TOML 可审计） | 中（规则分散） | 取决于实现 |
| 平台限制 | macOS/Linux only | 跨平台 | 跨平台 |
| 配置复杂度 | 中（TOML 层级） | 低（交互式） | 高（需写插件） |
| Prompt Injection 防护 | 无（不理解语义） | 有限 | 可编程 |

### 安全选择指南

```text
需要最硬的安全边界 → Codex（OS 沙箱，绕过需要内核漏洞）
需要开箱即用的安全 → Claude Code（无需配置，交互式审批）
需要可编程的安全策略 → DSH（策略是插件，可以根据上下文决策）
不需要框架级安全 → Pi（安全交给容器化基础设施）
```

## MCP 集成对比

| 维度 | Codex | Claude Code | DSH |
| --- | --- | --- | --- |
| 实现层 | Rust 原生 crate | TypeScript 内置 | Cordis 插件 |
| 传输支持 | STDIO + Streamable HTTP | STDIO + SSE | STDIO |
| 审批粒度 | Per-tool（4 种模式） | 统一权限模型 | 取决于 Approval 插件 |
| Token 优化 | 不做 | 不做 | 不内置（Pi 做了） |
| 安全隔离 | Guardian 隔离 | 无专门隔离 | 取决于策略 |
| 生态投入 | 1,100+ PR | 不公开 | 不公开 |

### MCP 选择逻辑

- **需要细粒度 per-tool 审批**：Codex 最强
- **需要和内置工具统一的权限体验**：Claude Code
- **需要可编程的工具路由和动态加载**：DSH
- **需要 token 经济学优化**：Pi 的 pi-mcp-adapter

## 扩展性与生态对比

| 维度 | Codex | Claude Code | DSH |
| --- | --- | --- | --- |
| 扩展机制 | MCP + 配置 | Skills + Hooks + MCP | Cordis 插件（万物可替换）|
| 扩展语言 | TOML 配置 + MCP server | TypeScript/Markdown + MCP | TypeScript (Cordis API) |
| 扩展粒度 | MCP server 级 | Skill/Hook 级 | 函数级 |
| 社区生态 | 发展中 | 成熟 | 依赖 DSH 社区 |
| 跨框架兼容 | 通过 MCP 标准 | 通过 MCP + Skills | 通过 MCP 标准 |

### 扩展选择逻辑

- **最低门槛（写 Markdown 就能扩展）**：Claude Code Skills
- **最大灵活性（连 Loop 都可替换）**：DSH Cordis 插件
- **标准化集成（MCP 协议）**：三者都支持，Codex 最深

## 开发者体验对比

| 维度 | Codex | Claude Code | DSH |
| --- | --- | --- | --- |
| 安装 | npm install | npm install | npm install |
| 首次配置 | 需要配 TOML | 开箱即用 | 需要理解插件系统 |
| 交互模式 | Turn-based（审查式） | Continuous（自动式） | 取决于 Profile |
| IDE 集成 | 无 | VS Code | Web + headless |
| 会话恢复 | 支持 | 支持 | 内置（Session Log） |
| 学习曲线 | 中 | 低 | 高 |
| Breaking changes | 频繁 | 中等 | 频繁 |
| ThoughtWorks | Trial | Adopt | 未评级 |

## 场景推荐矩阵

| 场景 | 推荐 | 原因 |
| --- | --- | --- |
| 个人日常开发 | Claude Code | 开箱即用，学习曲线最低 |
| 安全敏感环境 | Codex | OS 沙箱最硬 |
| 企业合规要求 | DSH | 策略可审计、可编程 |
| CI/CD 自动化 | Codex SDK | per-turn 权限 + 编程接口 |
| 需要可编程策略 | DSH | 策略即插件 |
| 多模型切换 | DSH / Pi | Provider 适配最灵活 |
| 团队协作 | Claude Code | Skills 共享 + CLAUDE.md 统一 |
| MCP 重度使用 | Codex | 原生 Rust 实现 + per-tool 审批 |
| 快速原型 | Claude Code | Continuous loop + 低配置 |
| 需要容器隔离 | Pi | 设计哲学最匹配 |

## 三者的收敛趋势

尽管路线不同，三个框架在某些方向上正在收敛：

**MCP 标准化。** 三者都支持 MCP，且投入在增加。工具生态正在通过 MCP 标准实现跨框架兼容。

**多角色安全。** Codex 的 Guardian 隔离、DSH 的策略平面、Claude Code 的 Hooks——都在向"同一系统内不同角色不同权限"的方向演进。

**SDK/编程接口。** 三者都在提供编程式调用能力，支持 CI/CD 和自动化集成。

**会话恢复。** 长任务断点续传成为标配。

收敛不意味着趋同——它们在收敛的方向上仍然用不同的方式实现，保持各自的架构特色。

## 决策框架

选择时问自己三个问题：

**1. 你的安全需求能提前声明吗？**
- 能 → Codex（TOML 配置 + OS 沙箱）
- 不能，需要动态决策 → DSH（策略平面）
- 不需要精细控制 → Claude Code（交互式审批够用）

**2. 你的主要工作模式是什么？**
- 交互式、每步审查 → Codex（Turn-based）
- 自动化、批量处理 → Codex SDK
- 快速迭代、信任模型 → Claude Code（Continuous）
- 高度定制 → DSH（可替换的 Loop）

**3. 你能承受多大的学习曲线？**
- 最小 → Claude Code
- 中等 → Codex CLI
- 最大（但最灵活）→ DSH

## 小结

三种终端 Coding Agent 代表了三种工程哲学：

- **Codex CLI**：安全交给操作系统，性能交给 Rust，配置交给 TOML——静态、可预测、硬边界
- **Claude Code**：一切在应用层解决——简单、一致、易上手，但边界相对软
- **DeepSeek Harness**：一切都是插件——最大灵活性，但最高复杂度

没有绝对的优劣。关键变量是你的环境：安全需求、自动化程度、团队技术栈、学习预算。

理解三者的设计判断和 tradeoff，比记住功能对比表更有价值。当下一个 Coding Agent 出现时，你能快速判断它在这个光谱上的位置。

---

返回：[模块目录](../index.html)
