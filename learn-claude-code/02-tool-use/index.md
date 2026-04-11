---
layout: default
title: Tool Use：扩展模型能触达的边界
description: dispatch map 设计——加一个工具，只加一个 handler，循环永远不变
eyebrow: Claude Code / s02
---

# Tool Use：扩展模型能触达的边界

> *“加一个工具，只加一个 handler”*

s01 只有一个 `bash` 工具。这一节加 3 个专用工具，同时引入一个关键设计：**dispatch map**。

加工具不需要改循环。循环永远不变。

---

## 问题

只有 `bash` 时，所有操作都走 shell：

- `cat` 输出可能被截断，不可预测
- `sed` 遇到特殊字符就崩
- 每次 bash 调用都是不受约束的安全面，没有路径沙箱

专用工具（`read_file`、`write_file`、`edit_file`）可以在工具层做路径验证，防止模型意外访问工作区外的文件。

**关键洞察：加工具不需要改循环。**

---

## dispatch map 设计

s01 的工具执行是硬编码的：

```python
# s01：硬编码，每加一个工具就要改循环
if block.name == "bash":
    output = run_bash(block.input["command"])
```

s02 换成 dispatch map：

```python
# s02：字典查找，加工具只加 handler
TOOL_HANDLERS = {
    "bash":       lambda **kw: run_bash(kw["command"]),
    "read_file":  lambda **kw: run_read(kw["path"], kw.get("limit")),
    "write_file": lambda **kw: run_write(kw["path"], kw["content"]),
    "edit_file":  lambda **kw: run_edit(kw["path"], kw["old_text"], kw["new_text"]),
}

# 循环中：一行查找替代 if/elif 链
handler = TOOL_HANDLERS.get(block.name)
output = handler(**block.input) if handler else f"Unknown tool: {block.name}"
```

循环体本身和 s01 完全一样，只是工具执行那行变成了字典查找。

这个 Python 字典正是 Claude Code 真实架构的简化映射——在 Claude Code 源码中，同样的思路被推到了工业级规模。

---

## 源码实证：Claude Code 的工具注册表

以下内容来自 Claude Code 泄露源码的真实分析。

### 工具注册：`src/tools.ts`

Claude Code 在 `getAllBaseTools()` 函数中返回一个 `Tools` 数组——这就是它的 “dispatch map”。核心工具直接注册，实验性工具通过 feature flag 条件注册：

```typescript
// src/tools.ts — 工具注册表（简化）
export function getAllBaseTools(): Tools {
  return [
    AgentTool,
    TaskOutputTool,
    BashTool,
    // 内嵌搜索工具时跳过 Glob/Grep
    ...(hasEmbeddedSearchTools() ? [] : [GlobTool, GrepTool]),
    FileReadTool,
    FileEditTool,
    FileWriteTool,
    NotebookEditTool,
    WebFetchTool,
    TodoWriteTool,
    WebSearchTool,
    SkillTool,
    AskUserQuestionTool,
    EnterPlanModeTool,
    ExitPlanModeV2Tool,
    // feature flag 条件注册
    ...(SleepTool ? [SleepTool] : []),
    ...cronTools,  // CronCreate, CronDelete, CronList
    ...(isWorktreeModeEnabled()
      ? [EnterWorktreeTool, ExitWorktreeTool] : []),
    ...(isTodoV2Enabled()
      ? [TaskCreateTool, TaskGetTool, TaskUpdateTool, TaskListTool] : []),
    ...(isToolSearchEnabledOptimistic() ? [ToolSearchTool] : []),
    // ... 共计 ~40 个工具
  ]
}
```

关键设计：**数组展开 + 条件三元运算符**。`feature('PROACTIVE')` 返回 `true` 时 `SleepTool` 才会进入数组；`process.env.USER_TYPE === 'ant'` 控制 Anthropic 内部工具。这让同一个二进制产物能服务不同用户群。

### 完整工具清单

`src/tools/` 目录下共 40+ 个工具目录：

| 类别 | 工具 | 作用 |
|------|------|------|
| **文件操作** | `FileReadTool`, `FileWriteTool`, `FileEditTool`, `NotebookEditTool` | 读、写、精确编辑、Jupyter 编辑 |
| **搜索** | `GlobTool`, `GrepTool`, `ToolSearchTool`, `LSPTool` | 文件名匹配、内容搜索、工具搜索、语言服务 |
| **执行** | `BashTool`, `PowerShellTool`, `REPLTool` | Shell 执行、PowerShell、REPL |
| **Agent/协作** | `AgentTool`, `SkillTool`, `SendMessageTool`, `TeamCreateTool`, `TeamDeleteTool` | 子 Agent、技能调用、消息传递、团队管理 |
| **任务管理** | `TodoWriteTool`, `TaskCreateTool`, `TaskGetTool`, `TaskUpdateTool`, `TaskListTool`, `TaskOutputTool`, `TaskStopTool` | 待办事项、任务 CRUD、输出采集 |
| **Web** | `WebFetchTool`, `WebSearchTool`, `WebBrowserTool` | URL 抓取、搜索引擎、浏览器 |
| **计划/模式** | `EnterPlanModeTool`, `ExitPlanModeV2Tool`, `EnterWorktreeTool`, `ExitWorktreeTool` | 计划模式、Git worktree 隔离 |
| **调度/监控** | `CronCreateTool`, `CronDeleteTool`, `CronListTool`, `SleepTool`, `MonitorTool`, `RemoteTriggerTool` | 定时任务、休眠、监控 |
| **交互** | `AskUserQuestionTool`, `BriefTool`, `ConfigTool`, `PushNotificationTool` | 向用户提问、简报、配置、推送通知 |
| **MCP** | `ListMcpResourcesTool`, `ReadMcpResourceTool` | MCP 协议资源访问 |

### Tool 类型定义：`src/Tool.ts`

每个工具都实现 `Tool<Input, Output, Progress>` 类型：

```typescript
// src/Tool.ts — 核心类型（简化）
export type Tool<Input, Output, P> = {
  readonly name: string
  readonly inputSchema: Input           // Zod schema
  call(
    args: z.infer<Input>,
    context: ToolUseContext,
    canUseTool: CanUseToolFn,
    parentMessage: AssistantMessage,
    onProgress?: ToolCallProgress<P>,
  ): Promise<ToolResult<Output>>
  description(input, options): Promise<string>
  isEnabled(): boolean                  // 是否在当前环境可用
  isReadOnly(input): boolean            // 只读操作？
  isDestructive?(input): boolean        // 不可逆操作？
  isConcurrencySafe(input): boolean     // 可并发执行？
  maxResultSizeChars: number            // 结果超限时持久化到磁盘
  readonly shouldDefer?: boolean        // 延迟加载（需 ToolSearch 发现）
}
```

### 工具返回值：`ToolResult<T>`

```typescript
export type ToolResult<T> = {
  data: T                    // 工具输出内容
  newMessages?: Message[]    // 可选：注入额外消息到上下文
  contextModifier?: (ctx: ToolUseContext) => ToolUseContext  // 可选：修改后续上下文
}
```

`data` 是返回给 LLM 的主体内容。`newMessages` 让工具可以向消息历史注入系统提示。`contextModifier` 让工具（如 `EnterPlanModeTool`）可以改变后续循环的行为。

### ToolUseContext：工具运行时上下文

```typescript
export type ToolUseContext = {
  messages: Message[]               // 完整对话历史
  abortController: AbortController  // 中断控制
  getAppState(): AppState           // 读全局状态
  setAppState(f): void              // 写全局状态
  queryTracking?: QueryChainTracking  // 查询链追踪
  options: {
    tools: Tools                    // 可用工具列表
    mcpClients: MCPServerConnection[]
    mainLoopModel: string
    // ...
  }
}

export type QueryChainTracking = {
  chainId: string   // 同一轮对话的链 ID
  depth: number     // 嵌套深度（Agent 中的 Agent）
}
```

### 权限模型：`ToolPermissionContext`

每次工具调用前都经过权限检查：

```typescript
export type ToolPermissionContext = DeepImmutable<{
  mode: PermissionMode                    // 'default' | 'plan' | 'bypass'
  alwaysAllowRules: ToolPermissionRulesBySource   // 始终允许
  alwaysDenyRules: ToolPermissionRulesBySource     // 始终拒绝
  alwaysAskRules: ToolPermissionRulesBySource      // 始终询问
  additionalWorkingDirectories: Map<string, AdditionalWorkingDirectory>
  isBypassPermissionsModeAvailable: boolean
  shouldAvoidPermissionPrompts?: boolean  // 后台 Agent 自动拒绝
}>
```

权限检查的结果是三选一：**allow**（直接执行）、**deny**（拒绝并返回错误）、**ask**（弹出对话框请求用户授权）。工具还通过 `isReadOnly()` 和 `isDestructive()` 标记自身的危险等级，`filterToolsByDenyRules()` 在工具列表发送给模型之前就过滤掉被禁止的工具。

---

## 路径沙箱

```python
from pathlib import Path

WORKDIR = Path(".").resolve()

def safe_path(p: str) -> Path:
    """防止路径逃逸工作区"""
    path = (WORKDIR / p).resolve()
    if not path.is_relative_to(WORKDIR):
        raise ValueError(f"Path escapes workspace: {p}")
    return path
```

所有文件操作都通过 `safe_path()` 验证，模型无法读写工作区外的文件。

在 Claude Code 的真实实现中，`ToolPermissionContext` 中的 `additionalWorkingDirectories` 字段允许配置额外的合法工作目录，实现更灵活的沙箱策略。

---

## 四个工具的实现

```python
import subprocess
from pathlib import Path

def run_bash(command: str) -> str:
    result = subprocess.run(
        command, shell=True, capture_output=True, text=True, timeout=30
    )
    return (result.stdout + result.stderr)[:50000]

def run_read(path: str, limit: int = None) -> str:
    text = safe_path(path).read_text()
    lines = text.splitlines()
    if limit and limit < len(lines):
        lines = lines[:limit]
    return "\n".join(lines)[:50000]

def run_write(path: str, content: str) -> str:
    p = safe_path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return f"Written: {path}"

def run_edit(path: str, old_text: str, new_text: str) -> str:
    p = safe_path(path)
    content = p.read_text()
    if old_text not in content:
        return f"Error: old_text not found in {path}"
    p.write_text(content.replace(old_text, new_text, 1))
    return f"Edited: {path}"
```

---

## 工具 Schema

每个工具需要一个 schema 告诉 LLM 怎么调用：

```python
TOOLS = [
    {
        "name": "bash",
        "description": "执行 shell 命令",
        "input_schema": {
            "type": "object",
            "properties": {"command": {"type": "string"}},
            "required": ["command"]
        }
    },
    {
        "name": "read_file",
        "description": "读取文件内容，支持 limit 参数限制行数",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "limit": {"type": "integer", "description": "最多读取的行数（可选）"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "write_file",
        "description": "写入文件，自动创建父目录",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"}
            },
            "required": ["path", "content"]
        }
    },
    {
        "name": "edit_file",
        "description": "精确查找替换文件中的内容",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "old_text": {"type": "string", "description": "要替换的原文本"},
                "new_text": {"type": "string", "description": "替换后的新文本"}
            },
            "required": ["path", "old_text", "new_text"]
        }
    }
]
```

在 Claude Code 中，schema 使用 Zod 定义（`inputSchema` 字段），运行时自动转换为 JSON Schema 发送给 API。每个工具还有动态 `description()` 方法，可以根据当前权限上下文生成不同的描述文本。

---

## 相对 s01 的变化

| 组件 | s01 | s02 |
|------|-----|-----|
| 工具数量 | 1（仅 bash） | 4（bash + read + write + edit） |
| 工具分发 | 硬编码 if | `TOOL_HANDLERS` 字典 |
| 路径安全 | 无 | `safe_path()` 沙箱 |
| Agent loop | — | **不变** |

<div class="mermaid">
flowchart LR
    A[LLM tool_use] --> B{TOOL_HANDLERS}
    B -->|bash| C[run_bash]
    B -->|read_file| D[run_read]
    B -->|write_file| E[run_write]
    B -->|edit_file| F[run_edit]
    C & D & E & F --> G[tool_result]
</div>

---

## 为什么 edit_file 比 bash sed 更好

```bash
# bash sed：遇到特殊字符（/、&、\n）就崩
sed -i 's/old_text/new_text/' file.py

# edit_file：Python 字符串替换，无特殊字符问题
run_edit("file.py", old_text="def foo():", new_text="def bar():")
```

`edit_file` 还有一个额外好处：如果 `old_text` 不存在，会返回明确的错误信息，而不是静默成功（sed 的常见陷阱）。

---

## 从 4 个工具到 40 个：架构启示

我们的 s02 只有 4 个工具，但架构设计和 Claude Code 的 40+ 工具注册表是同构的：

| 维度 | s02 (Python) | Claude Code (TypeScript) |
|------|-------------|--------------------------|
| 注册表 | `TOOL_HANDLERS` 字典 | `getAllBaseTools()` 数组 |
| Schema | JSON dict | Zod → JSON Schema |
| 返回值 | `str` | `ToolResult { data, newMessages?, contextModifier? }` |
| 权限 | `safe_path()` | `ToolPermissionContext` (allow/deny/ask) |
| 条件注册 | 无 | `feature()` flag + 环境变量 |
| 工具发现 | 全量发送 | `ToolSearchTool` + `shouldDefer` 延迟加载 |

核心原则不变：**加一个工具，只加一个 handler，循环永远不变。**

---

## 设计哲学：Unix 哲学与工具设计

Claude Code 的工具系统深刻体现了 Unix 哲学：**每个工具做好一件事，复杂功能通过组合完成**。

- `FileReadTool` 只读文件
- `GrepTool` 只搜索内容
- `FileEditTool` 只做字符串替换
- `BashTool` 只执行命令

复杂任务（如“重构认证模块”）不是由一个大而全的 `RefactorTool` 完成的，而是由 LLM 的推理能力编排多个原子工具完成。这和 Unix 管道的思想一致——`cat file | grep pattern | sort | uniq` 每一环只做一件事。

设计指南还指出一个容易忽视的细节：**工具描述是“承重的艺术品”（load-bearing art form）**。Claude Code 的每个工具描述都经过精心设计，因为模型完全依赖描述来决定何时使用哪个工具。一个模糊的描述会导致工具被误用或忽略。这就是为什么源码中 `BashTool` 的描述长达数十行——它不只是文档，而是模型决策的核心输入。

另一个 Unix 启发的设计：**工具是无状态的**。每次调用独立执行，通过 `ToolUseContext` 显式接收所有依赖，而不是通过全局变量。这让工具可以被安全地并行执行、被不同 Agent 复用。

这个原则的实际意义：**加一个工具只需要加一个 handler 和一份 schema，Agent 循环永远不变。** 这就是我们在 s02 中实践的设计。

---

下一篇：[TodoWrite：让 Agent 不再迷路](../03-todo-write/index.html)
