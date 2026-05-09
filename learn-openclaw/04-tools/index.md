---
layout: default
title: 工具系统：MCP 协议与并行执行
description: pi-mono 的工具架构——从本地函数到 MCP Server 的完整工具链
eyebrow: OpenClaw / 04
---

# 工具系统：MCP 协议与并行执行

Agent 的能力边界由工具决定。pi-mono / OpenClaw 的工具系统有三个层次：

1. **内置工具**（本地函数，进程内执行）
2. **MCP Server**（跨进程通信，标准协议）
3. **Skills**（结构化能力包，可组合）

---

## 内置工具：少即是多

pi-mono 的内置工具数量刻意控制得很少：

| 工具 | 功能 | 关键设计 |
|------|------|---------|
| `Read` | 读文件 | 支持 offset/limit（只读需要的行） |
| `Write` | 写文件 | 整文件覆写 |
| `Edit` | 精确替换 | old_string → new_string，失败时报错 |
| `Bash` | 执行 shell | 超时控制 + 输出截断 |
| `Grep` | 正则搜索 | 返回匹配行 + 上下文 |
| `Find` | 文件查找 | Glob 模式匹配 |
| `WebFetch` | HTTP 请求 | SSRF 防护 |
| `Agent` | 子 Agent | 上下文隔离的子任务 |

**为什么不是 20 个工具？**

实验数据表明：工具从 20+ 削减到 8 个时，任务完成率提升约 15%。原因：

- 工具越多，模型在"选哪个"上消耗的推理能力越多
- 职责重叠的工具会导致模型犹豫或误选
- `Bash` 本身就是万能工具，大多数操作都能用 shell 完成

**设计原则：能用 Bash 解决的，不要单独做工具。**

---

## 工具定义：TypeScript Schema

pi-mono 中每个工具的定义格式：

```typescript
// packages/agent/src/tools/read.ts
export const readTool: ToolDefinition = {
  name: 'Read',
  description: '读取文件内容。支持 offset 和 limit 参数读取大文件的部分内容。',
  parameters: {
    type: 'object',
    properties: {
      file_path: { type: 'string', description: '文件的绝对路径' },
      offset: { type: 'integer', description: '起始行号（可选）' },
      limit: { type: 'integer', description: '读取行数（可选）' }
    },
    required: ['file_path']
  },
  execute: async (args: { file_path: string; offset?: number; limit?: number }) => {
    const content = await fs.readFile(args.file_path, 'utf-8')
    const lines = content.split('\n')
    const start = args.offset || 0
    const end = args.limit ? start + args.limit : lines.length
    return lines.slice(start, end).map((l, i) => `${start + i + 1}\t${l}`).join('\n')
  }
}
```

关键点：
- `description` 是给 LLM 看的——写得越清晰，模型越能正确使用
- `parameters` 用 JSON Schema 格式，LLM 输出结构化参数
- `execute` 是实际执行函数，返回字符串结果

---

## 并行执行：默认行为

当模型一次请求多个工具时，pi-mono 默认并行执行：

```typescript
// agent-loop.ts 中的工具执行逻辑
async function executeToolCalls(toolCalls: ToolCall[]): Promise<ToolResult[]> {
  if (config.sequentialTools) {
    // 顺序模式：有依赖关系时使用
    const results: ToolResult[] = []
    for (const call of toolCalls) {
      results.push(await executeSingle(call))
    }
    return results
  }

  // 默认：并行执行
  return Promise.all(toolCalls.map(call => executeSingle(call)))
}
```

**什么时候需要顺序执行？**

- 工具 B 依赖工具 A 的结果（如：先 Write 再 Read 同一文件验证）
- 需要严格的副作用顺序（如：先创建目录再写文件）

但这种情况在实际中很少——模型通常会在不同轮次分开请求有依赖的工具。

---

## MCP：Model Context Protocol

MCP 是 Anthropic 2024 年提出的跨进程工具通信标准。核心思想：**工具不必在 Agent 进程内，可以是独立服务。**

<div class="mermaid">
flowchart LR
    A[Agent 进程] -->|JSON-RPC over stdio| B[MCP Server A\nGitHub 操作]
    A -->|JSON-RPC over HTTP| C[MCP Server B\n数据库查询]
    A -->|JSON-RPC over stdio| D[MCP Server C\n文件系统]
</div>

### MCP 的通信协议

```typescript
// Agent → MCP Server: 请求工具列表
{ "jsonrpc": "2.0", "method": "tools/list", "id": 1 }

// MCP Server → Agent: 返回工具定义
{ "jsonrpc": "2.0", "result": { "tools": [...] }, "id": 1 }

// Agent → MCP Server: 调用工具
{ "jsonrpc": "2.0", "method": "tools/call", "params": { "name": "query", "arguments": {...} }, "id": 2 }

// MCP Server → Agent: 返回结果
{ "jsonrpc": "2.0", "result": { "content": [...] }, "id": 2 }
```

### OpenClaw 的 MCP 集成

```typescript
// src/mcp/channel-bridge.ts
// OpenClaw 把每个 MCP Server 当作一个 "channel"，统一管理生命周期
export class McpChannelBridge {
  private servers: Map<string, McpServerProcess> = new Map()

  async connectServer(config: McpServerConfig): Promise<void> {
    const process = spawn(config.command, config.args)
    const transport = new StdioTransport(process.stdin, process.stdout)
    this.servers.set(config.name, { process, transport })
  }

  async listTools(): Promise<ToolDefinition[]> {
    const allTools: ToolDefinition[] = []
    for (const [name, server] of this.servers) {
      const { tools } = await server.transport.request('tools/list')
      allTools.push(...tools.map(t => ({ ...t, server: name })))
    }
    return allTools
  }
}
```

### 什么时候用 MCP，什么时候用内置工具

| 场景 | 选择 | 原因 |
|------|------|------|
| 读写本地文件 | 内置工具 | 无需跨进程开销 |
| 查询数据库 | MCP Server | 独立部署，可复用 |
| GitHub API 操作 | MCP Server | 社区已有成熟实现 |
| 简单文本处理 | Bash 工具 | 一行命令搞定 |
| 复杂多步流程 | Skill | 内部有子流程 |

---

## Skills：OpenClaw 的能力包

Skill 是 OpenClaw 特有概念——比单个工具复杂，比独立 Agent 轻量：

```
src/agents/skills/
  code-review/
    manifest.json    ← 技能描述、触发条件
    prompt.md        ← 技能专用的系统指令
    tools.ts         ← 技能专属工具（可选）
  security-audit/
    manifest.json
    prompt.md
```

```json
// manifest.json
{
  "name": "code-review",
  "description": "审查代码变更，检查安全问题和最佳实践",
  "triggers": ["review", "审查", "看看这段代码"],
  "requiredTools": ["Read", "Grep", "Bash"]
}
```

### SKILL.md 标准格式

pi-mono 生态（pi-skills，1.6k stars）定义了跨平台 Skill 格式——一个 SKILL.md 文件兼容 Claude Code、OpenClaw、Codex CLI、Amp、Droid 等多个 Agent：

```markdown
<!-- SKILL.md -->
---
name: security-review
description: 审查代码变更中的安全漏洞
triggers:
  - "review security"
  - "安全审查"
  - "check vulnerabilities"
tools_required:
  - Read
  - Grep
  - Bash
---

# Security Review Skill

你是安全审计专家。审查用户指定的代码文件，检查以下类别的问题：
1. 注入攻击（SQL、命令、XSS）
2. 认证/授权缺陷
3. 敏感信息泄露
4. 不安全的依赖

输出格式：
- 严重程度（Critical/High/Medium/Low）
- 位置（文件:行号）
- 问题描述
- 修复建议
```

Skill 的加载机制：

1. Agent 启动时扫描 Skills 目录，注册所有可用 Skill
2. 用户输入命中 trigger 时，动态加载对应 Skill 的 prompt 和工具
3. Skill 执行完毕后卸载，不污染主 Agent 上下文
4. SKILL.md 格式跨 Agent 通用——写一次，多处运行

这就是 Claude Code 中 `/review`、`/init` 等斜杠命令的实现原理。

### Skill 生态

OpenClaw 的 ClawHub 注册了 1,800+ 社区 Skill，覆盖：
- 代码质量（lint、review、refactor）
- DevOps（deploy、monitor、rollback）
- 数据分析（SQL 生成、可视化）
- 文档（API 文档生成、翻译）

---

## 安全策略

OpenClaw 对工具执行有多层安全防护：

```typescript
// src/security/command-auth.ts
export class CommandAuthorizer {
  private allowList: RegExp[] = []
  private denyList: RegExp[] = [
    /rm\s+-rf\s+\//,         // 禁止 rm -rf /
    /sudo/,                   // 禁止 sudo
    /curl.*\|.*sh/,          // 禁止管道执行远程脚本
    /chmod\s+777/,           // 禁止全权限
  ]

  authorize(command: string): AuthResult {
    for (const pattern of this.denyList) {
      if (pattern.test(command)) {
        return { allowed: false, reason: `Blocked by security policy: ${pattern}` }
      }
    }
    return { allowed: true }
  }
}
```

```typescript
// src/security/ssrf-policy.ts
// 防止工具访问内网地址
export function validateUrl(url: string): boolean {
  const parsed = new URL(url)
  const ip = await dns.resolve(parsed.hostname)
  return !isPrivateIP(ip) // 拒绝 10.x / 172.16.x / 192.168.x
}
```

生产环境还会加沙箱（Docker / SSH），把工具执行隔离在容器内。

### 分层安全模型（来自安全审计）

OpenClaw 的安全不是单一黑名单，而是**四层防御**：

```
Layer 1: 命令级过滤（正则黑名单）
Layer 2: Per-channel Ed25519 身份验证（每个渠道独立密钥）
Layer 3: 分层工具调度（不同权限级别可用不同工具子集）
Layer 4: 硬化容器（cap_drop ALL, read-only rootfs, 64MB tmpfs）
```

```typescript
// 工具权限分级
toolPermissions:
  level_0:  ['Read', 'Grep', 'Find']           // 只读，无风险
  level_1:  ['Read', 'Grep', 'Find', 'Edit', 'Write']  // 可修改文件
  level_2:  ['Read', 'Grep', 'Find', 'Edit', 'Write', 'Bash']  // 可执行命令
  level_3:  ['*']                               // 所有工具（需要显式授权）
```

用户首次使用时从 level_0 开始，逐步授权提升。这比"全部允许或全部拒绝"更精细。

---

## 面试高频题

**Q：为什么 Coding Agent 的工具不能太多？**

> 工具数量是模型决策空间的维度。8 个工具的选择空间是 8^n（n 为步骤数），20 个工具是 20^n。决策空间指数增长导致模型更容易选错工具或生成无效的参数组合。实验数据：从 20+ 削减到 8 个，任务完成率提升 ~15%。

**Q：MCP 相比直接函数调用的优劣？**

> 优势：语言无关（Go 写的 MCP Server 可被 TypeScript Agent 调用）、进程隔离（工具崩溃不影响 Agent）、可复用（社区共享）。劣势：序列化开销（JSON-RPC）、进程管理复杂度、调试困难（跨进程调用链）。

**Q：如何设计一个安全的 Bash 工具？**

> 三层防护：1) 命令黑名单（正则匹配危险模式）；2) 超时控制（防止无限循环）；3) 输出截断（防止大输出撑爆上下文）。生产环境额外加 Docker 沙箱隔离文件系统。

---

下一篇：[Context Engine：OpenClaw 的记忆架构](../05-memory/index.html)
