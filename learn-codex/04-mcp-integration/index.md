---
layout: default
title: MCP 深度集成：1,100+ PR 背后的设计决策
description: 从 Rust 原生 MCP crate 和 per-tool 审批理解 Codex 的工具生态策略
eyebrow: Codex CLI / 04
---

# MCP 深度集成：1,100+ PR 背后的设计决策

## 为什么这个问题值得关注

MCP (Model Context Protocol) 是 Agent 工具生态的标准协议。每个主流 Coding Agent 都支持 MCP，但支持深度差异很大：

- **Claude Code**：内置支持，TypeScript SDK 集成
- **Pi**：通过 pi-mcp-adapter 做 token 压缩适配
- **DeepSeek Harness**：作为 Cordis 插件接入

Codex CLI 的 MCP 支持走了一条独特的路径：**Rust 原生实现，从第一天就在内核层面而非扩展层面集成。** GitHub 记录显示，从 2025 年 5 月（PR #787 引入 mcp-types crate）到 2026 年 8 月，共有 1,100+ 个 MCP 相关 PR 被合并。

这个投入量级说明 MCP 不是 Codex 的"附加功能"，而是核心工程重心之一。理解它的设计选择，能帮你判断 MCP 在 Agent 框架中应该被当作"工具插件"还是"基础设施"来对待。

## 架构：Rust 层的 MCP

Codex 的 MCP 实现分布在多个 Rust crate 中：

```text
codex-mcp          ← MCP 服务集成入口
├── rmcp-client    ← MCP 客户端（调用外部 MCP server）
├── mcp-server     ← MCP 服务端（暴露 Codex 自身工具）
└── mcp-types      ← MCP 协议类型定义
```

### 为什么在 Rust 层而非 TypeScript 层

**安全审查点。** MCP 工具调用是外部代码执行——来自第三方 MCP server 的响应可能包含恶意内容。把 MCP 客户端放在 Rust 层意味着：安全检查（tool approval、response 验证）和沙箱策略在同一层执行，不需要跨进程通信。

**性能。** MCP 的 STDIO 传输需要频繁的 JSON 序列化/反序列化。Rust 的 serde 在这类操作上比 Node.js 的 JSON.parse/stringify 快 3-5 倍。对于高频工具调用的 Agent，这个差距会累积。

**类型安全。** MCP 协议有复杂的消息格式（JSON-RPC 2.0 + 自定义扩展）。Rust 的类型系统在编译时就能捕获协议违反，不需要等到运行时。

## 双通道传输：STDIO + Streamable HTTP

Codex 支持两种 MCP server 连接方式：

### STDIO 模式

MCP server 作为子进程启动，通过 stdin/stdout 通信。

```toml
[mcp.servers.github]
transport = "stdio"
command = "npx"
args = ["-y", "@modelcontextprotocol/server-github"]
env = { GITHUB_TOKEN = "${GITHUB_TOKEN}" }
```

适合：本地工具、需要访问本地文件系统的 server、开发调试。

### Streamable HTTP 模式

MCP server 作为远程服务运行，通过 HTTP 通信。

```toml
[mcp.servers.remote-db]
transport = "streamable-http"
url = "https://mcp.example.com/db"
headers = { Authorization = "Bearer ${DB_TOKEN}" }
```

适合：远程服务、多用户共享的工具、需要独立部署和扩缩的场景。

### 选择逻辑

| 维度 | STDIO | Streamable HTTP |
| --- | --- | --- |
| 延迟 | 低（本地 IPC） | 中（网络往返） |
| 部署 | 随 Codex 启动 | 独立部署 |
| 安全 | 继承 Codex 沙箱 | 需要独立认证 |
| 扩展性 | 单实例 | 可水平扩展 |
| 生命周期 | Codex 退出时终止 | 持续运行 |

## Per-tool 审批机制

Codex 对 MCP 工具的审批不是全有全无的——你可以对每个 MCP server 甚至每个 tool 设置不同的审批模式：

```toml
[mcp.servers.github]
transport = "stdio"
command = "npx"
args = ["-y", "@modelcontextprotocol/server-github"]

# 这个 server 的所有工具默认需要审批
approval = "prompt"

# 但 read 类操作自动允许
enabled_tools = ["get_file_contents", "search_repositories"]

# 禁止执行这些工具
disabled_tools = ["delete_repository", "force_push"]
```

四种审批模式：

| 模式 | 行为 |
| --- | --- |
| `auto` | 自动执行，不提示 |
| `prompt` | 每次执行前提示用户 |
| `writes` | 只在写操作时提示 |
| `approve` | 需要显式预先批准 |

### 与 Claude Code 的 MCP 审批对比

Claude Code 的 MCP 工具审批是统一的——所有 MCP 工具调用走同一套权限检查逻辑（和内置工具一样的 allow/deny 规则）。

Codex 的 per-tool 审批更细粒度：你可以说"GitHub 的读操作自动允许，写操作需要审批，delete 操作直接禁止"。但代价是配置更复杂——每个 MCP server 都需要单独考虑审批策略。

### 与 Pi 的 MCP 方案对比

Pi 的 pi-mcp-adapter 关注的是不同的问题：**token 压缩**。它把 MCP 工具描述从 10k+ token 压缩到 ~200 token，解决的是上下文窗口经济学问题。

Codex 不做 token 压缩——它假设模型的上下文窗口够大（GPT-4o、o3 都有 128k+ 窗口）。Pi 的压缩方案在窗口有限的场景更有价值。

三者的关注点差异：

| 框架 | MCP 关注重点 |
| --- | --- |
| Codex | 安全（per-tool 审批）+ 性能（Rust 原生）|
| Claude Code | 一致性（MCP 工具和内置工具统一权限模型）|
| Pi | 经济性（token 压缩）+ 兼容性（多框架 Skill）|

## 安全硬化：Guardian 隔离

2026 年 8 月，Codex 合并了一系列安全相关 PR，其中最值得关注的是 **Guardian review 与 executor MCP server 的隔离**（PR #39962）。

这解决的问题是：当 Codex 有一个"审查者"角色（Guardian）负责检查 Agent 的操作是否安全时，Guardian 不应该能访问 Agent 正在使用的 MCP server——否则恶意 MCP server 可能通过审查者的上下文注入攻击。

```text
┌──────────────┐     ┌──────────────┐
│ Executor     │     │ Guardian     │
│ 执行 Agent   │     │ 审查 Agent   │
├──────────────┤     ├──────────────┤
│ MCP Server A │     │ 无 MCP 访问  │
│ MCP Server B │     │ 只看执行记录 │
└──────────────┘     └──────────────┘
```

这是多租户安全模型的雏形：同一系统内不同角色有不同的工具访问边界。DSH 通过策略平面实现类似功能；Codex 通过进程级隔离实现。

同一时期合并的其他安全 PR：

- OAuth issuer binding：防止 MCP OAuth token 被重放到其他 server
- Bearer token over WebSocket：WebSocket 连接的认证加固
- Credential write hardening：凭据写入的额外保护

## MCP 生态的量化观察

1,100+ PR 的分布可以反映 Codex 团队在 MCP 上的工程优先级：

- **2025.5 - 2025.10**：基础建设期。mcp-types crate、STDIO 传输、基本工具调用
- **2025.10 - 2026.4**：功能完善期。Streamable HTTP、per-tool 审批、allowlist/denylist
- **2026.4 - 2026.8**：安全硬化期。OAuth、Guardian 隔离、credential protection

这个时间线说明 MCP 在 Codex 中经历了"能用 → 好用 → 安全"的三阶段演进。当前处于安全硬化阶段，暗示基础功能已经稳定。

## 实操：添加 MCP Server

在项目配置中添加一个 MCP server 的最小步骤：

```toml
# .codex/config.toml
[mcp.servers.filesystem]
transport = "stdio"
command = "npx"
args = ["-y", "@modelcontextprotocol/server-filesystem", "./"]
approval = "writes"
```

这声明了一个 filesystem MCP server，读操作自动允许，写操作需要审批。

验证是否生效：

```bash
codex mcp list          # 列出已配置的 MCP servers
codex mcp test filesystem  # 测试连接
```

## 什么时候 Codex 的 MCP 方案更优

- 你需要对不同 MCP server 设置不同的安全策略
- 你有高频工具调用的场景，需要 Rust 层面的解析性能
- 你需要 STDIO 和 HTTP 双通道支持（本地 + 远程混合部署）
- 你需要多角色安全隔离（Guardian + Executor 分离）

## 什么时候其他方案更优

- **Claude Code**：如果你希望 MCP 工具和内置工具有完全一致的权限体验
- **Pi**：如果你的上下文窗口有限，需要 token 压缩
- **DSH**：如果你需要可编程的工具路由逻辑（比如"根据任务类型自动选择 MCP server"）

## 小结

Codex 的 MCP 集成不是"支持 MCP"这么简单——它是一个从 Rust 层面原生实现、经过 1,100+ PR 打磨、正在向多租户安全模型演进的完整子系统。Per-tool 审批、双通道传输、Guardian 隔离——这些设计选择反映了一个判断：**MCP 工具是 Agent 的主要攻击面之一，安全投入应该和功能投入匹配。**

这个判断在企业环境（多 MCP server、多角色、合规要求）下尤其成立。对于个人开发者的简单场景，这些安全机制可能是过度工程——但这恰好说明了 Codex 的目标用户群：不是"快速跑个 demo"的场景，而是"需要细粒度安全控制"的场景。

---

下一篇：[Codex SDK：Thread-based 编程式 Agent 接口](../05-codex-sdk/index.html)
