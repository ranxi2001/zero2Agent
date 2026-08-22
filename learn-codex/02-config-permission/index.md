---
layout: default
title: 配置与权限系统：TOML 层级与三种审批策略
description: 从 TOML 三层配置理解 Codex CLI 如何把权限决策编码为静态规则
eyebrow: Codex CLI / 02
---

# 配置与权限系统：TOML 层级与三种审批策略

## 为什么这个问题值得关注

每个 Coding Agent 都需要回答一个问题：模型想做某件事时，谁来决定允不允许？

Claude Code 的答案是：运行时动态判断，权限规则编码在框架内部，用户通过交互式 prompt 授权。DeepSeek Harness 的答案是：策略平面 + Approval 插件，权限规则本身是可替换的插件。

Codex CLI 的答案是第三种：**权限规则编码在 TOML 配置文件中，层级覆盖，解析在 Rust 层完成，运行时只做查表。** 没有复杂的策略引擎，没有可编程的审批逻辑——就是配置文件。

这个设计选择的工程含义是：权限行为完全可预测（读配置就知道结果），但灵活性有限（不能根据上下文动态调整策略）。

## TOML 三层配置

Codex CLI 的配置系统分三层，优先级从低到高：

```text
~/.codex/config.toml          ← 用户级（全局默认）
$CODEX_HOME/profile.config.toml ← Profile 级（命名配置集）
.codex/config.toml             ← 项目级（仓库内，需信任）
```

### 用户级：全局默认

`~/.codex/config.toml` 定义你的全局偏好。比如：

```toml
[model]
default = "o3"

[sandbox]
mode = "workspace-write"

[approval]
policy = "on-request"
```

这意味着：默认用 o3 模型，沙箱允许写当前工作区，工具调用按需审批。

### Profile 级：命名配置集

当你有多个工作场景（比如"开发时宽松"和"生产环境严格"），可以创建命名 Profile：

```toml
# $CODEX_HOME/strict.config.toml
[sandbox]
mode = "read-only"

[approval]
policy = "untrusted"
```

启动时通过 `--profile strict` 加载。Profile 覆盖用户级配置的对应字段，未指定的字段继承用户级。

### 项目级：仓库内配置

`.codex/config.toml` 放在项目根目录，和代码一起版本控制。这层的特殊之处在于需要信任：Codex 不会自动加载未信任项目的项目级配置——防止恶意仓库通过配置文件提权。

```toml
# .codex/config.toml
[sandbox]
writable_roots = ["src/", "tests/", "docs/"]

[mcp.servers.github]
transport = "stdio"
command = "npx"
args = ["-y", "@modelcontextprotocol/server-github"]
```

### 覆盖规则

层级覆盖的逻辑是：更具体的配置覆盖更通用的。项目级 > Profile 级 > 用户级。但有一条硬规则：**deny 始终覆盖 write，更具体的路径覆盖更通用的路径。**

```toml
[sandbox.filesystem]
# 允许写 src/ 但禁止写 src/generated/（即使 src/ 整体可写）
"src/" = "write"
"src/generated/" = "deny"
```

这条规则的工程意义是：安全约束只能收紧不能放宽——子目录的 deny 不会被父目录的 write 覆盖。

## 三种沙箱模式

Codex CLI 提供三种预设的沙箱模式：

| 模式 | 文件系统 | 网络 | 进程 | 适合场景 |
| --- | --- | --- | --- | --- |
| `read-only` | 只读全部 | 受限 | 受限 | 代码审查、问答 |
| `workspace-write` | 工作区可写 | 受限 | 受限 | 日常开发（默认） |
| `danger-full-access` | 全部可写 | 不限 | 不限 | 系统管理（危险） |

### read-only

模型不能修改任何文件。可以读代码、分析结构、回答问题，但不能写入。适合代码 review 或探索性对话。

### workspace-write

模型只能在当前工作目录及其子目录内写文件。不能写 `~/.ssh/`、不能写 `/etc/`、不能写其他项目。这是默认模式，覆盖了 90% 的日常开发场景。

你可以通过 `writable_roots` 进一步收窄：

```toml
[sandbox]
mode = "workspace-write"
writable_roots = ["src/", "tests/"]
# 只允许写 src/ 和 tests/，连项目根目录的其他文件都不能改
```

### danger-full-access

没有任何限制。名字中的 `danger-` 前缀是故意的——强制用户意识到这是高风险操作。适合系统管理任务（修改系统配置、安装全局包），不适合日常编码。

### 与 Claude Code 的权限模式对比

Claude Code 的权限系统是基于操作类型的：

- 读文件：总是允许
- 写文件：需要审批（可配置自动允许特定路径）
- 执行命令：需要审批（可配置白名单）
- 网络访问：内置限制

Codex 的权限系统是基于沙箱模式的：

- 选择一个模式，模式决定所有权限边界
- 在模式内通过 writable_roots 微调
- 不是逐操作审批，是预先声明边界

两种方式的 tradeoff：

| 维度 | Codex (模式 + 路径) | Claude Code (逐操作审批) |
| --- | --- | --- |
| 可预测性 | 高——读配置就知道边界 | 中——需要运行才知道哪里会暂停 |
| 灵活性 | 低——不能根据上下文动态调整 | 高——可以根据操作内容决策 |
| 用户负担 | 低（配置一次）| 高（每次审批） |
| 安全粒度 | 路径级 | 操作级 |
| 绕过风险 | 低（OS 强制） | 中（应用层检查可能有漏洞） |

## 三种审批策略

配置文件中的 `[approval].policy` 控制模型工具调用时的审批行为：

### untrusted

每个工具调用都需要人工审批。最安全，但最慢。适合不熟悉的项目或高风险环境。

### on-request

模型可以执行读操作和已声明为安全的工具调用，只在写操作或潜在危险操作时请求审批。这是默认策略。

### never

不请求任何审批。模型自主决策所有操作。只在 `read-only` 或 `danger-full-access` 模式下有意义——前者因为反正不能写，后者因为用户已经显式接受了风险。

### 细粒度覆盖

除了全局策略，Codex 支持按类别覆盖审批行为（文档描述，部分未在开源代码中确认）：

```toml
[approval]
policy = "on-request"

# 覆盖：MCP 工具调用总是需要审批
mcp_elicitations = "untrusted"

# 覆盖：Skill 加载总是允许
skill_approval = "never"
```

这意味着你可以有一个"整体宽松但 MCP 工具严格"的策略组合。

## 配置即代码的工程含义

Codex 选择 TOML 配置（而非运行时策略引擎）的工程含义：

**收益：**

- 权限行为完全可预测——审计时读配置文件就够
- 配置文件可以版本控制、code review、CI 检查
- 解析在 Rust 中完成，没有运行时开销
- 团队可以通过项目级配置统一安全基线

**代价：**

- 不能根据操作内容动态决策（"这个 rm 命令删的是临时文件还是源码"无法区分）
- 不能实现复杂策略（"只允许在工作时间执行写操作"）
- 策略变更需要修改配置文件并重启——不能热更新
- 表达能力有限——TOML 不是图灵完备的

### 与 DSH 策略平面的对比

DeepSeek Harness 的 Approval 机制是插件——你可以写一个插件，根据操作的上下文（调用栈、历史记录、用户角色）动态决策。这比 TOML 灵活得多，但也复杂得多。

Codex 的选择适合"大多数情况下规则不变"的场景。如果你需要"根据操作内容做决策"，Codex 的配置系统不够用——你需要 DSH 的策略平面或者自己在 Codex 外层包一个策略层。

## 信任模型

项目级配置（`.codex/config.toml`）涉及一个安全问题：如果恶意仓库在配置里写 `mode = "danger-full-access"`，clone 后就能提权。

Codex 的解决方案是 **trust-on-first-use**：

1. 首次打开一个项目时，Codex 不加载项目级配置
2. 用户显式执行 `codex trust` 标记该项目为可信
3. 之后的会话加载项目级配置

这和 Git 的 `safe.directory` 机制类似——不是完美的安全方案（用户可能无脑 trust），但至少增加了一个显式确认步骤。

## 小结

Codex CLI 的配置和权限设计体现了一个清晰的工程判断：**权限规则应该是静态的、可预测的、可审计的。** TOML 层级系统、三种沙箱模式、三种审批策略——这些都是有限集合，不是无限灵活的策略引擎。

这个判断在"规则稳定、场景明确"的环境下表现很好——读配置就知道边界，不需要理解运行时逻辑。在"需要根据上下文动态决策"的环境下则显得僵硬。

选择 Codex 的配置模式还是 Claude Code 的动态审批，关键变量是你的安全需求有多少是可以提前声明的。如果 90% 的场景可以用"只写 src/ 和 tests/"覆盖，Codex 的方式更高效。如果每次操作都需要不同的判断标准，动态审批更合适。

---

下一篇：[沙箱与安全模型：平台原生隔离的工程边界](../03-sandbox-security/index.html)
