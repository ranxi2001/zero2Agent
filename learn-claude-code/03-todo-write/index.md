---
layout: default
title: TodoWrite：让 Agent 不再迷路
description: 规划层——追踪任务状态，防止模型在多步任务中重复或遗漏
eyebrow: Claude Code / s03
---

# TodoWrite：让 Agent 不再迷路

s01/s02 的 Agent 能执行工具，但在多步任务里容易迷路——重复做已完成的事，跳过某个步骤，或者中途忘记目标。

这一节加一个规划层：**TodoManager**。

**重要更新**：Claude Code 内部已经将 TodoWrite 标记为 **V1（已弃用）**，新版本使用基于文件持久化的 **Task 工具族（V2）**。本文会先讲 V1 的设计思路，再深入 V2 的真实源码实现。

---

## 问题

没有规划层时，模型靠对话历史“记住”任务进度。这有几个问题：

- **重复工作**：读了文件 A 又读一遍
- **跳过步骤**：忘记某个子任务
- **上下文漂移**：多轮工具调用后，最初的任务目标被淹没

人在做复杂任务时会列清单。Agent 也需要。

---

## V1 设计：TodoWrite + TodoManager

### Python 实现

```python
from dataclasses import dataclass, field
from typing import List, Literal
import json

Status = Literal["pending", "in_progress", "completed"]

@dataclass
class TodoItem:
    id: str
    content: str
    status: Status = "pending"

class TodoManager:
    def __init__(self):
        self.todos: List[TodoItem] = []
        self._rounds_since_update = 0

    def add(self, content: str) -> str:
        item = TodoItem(id=str(len(self.todos) + 1), content=content)
        self.todos.append(item)
        return item.id

    def update(self, todo_id: str, status: Status):
        for item in self.todos:
            if item.id == todo_id:
                # 同时只能有一个 in_progress
                if status == "in_progress":
                    for other in self.todos:
                        if other.status == "in_progress":
                            other.status = "pending"
                item.status = status
                self._rounds_since_update = 0
                return f"Updated {todo_id} → {status}"
        return f"Todo {todo_id} not found"

    def view(self) -> str:
        if not self.todos:
            return "No todos."
        lines = []
        for item in self.todos:
            icon = {"pending": "○", "in_progress": "◐", "completed": "●"}[item.status]
            lines.append(f"{icon} [{item.id}] {item.content}")
        return "\n".join(lines)

    def attention_check(self) -> str | None:
        """3 轮没有更新 todo → 注入提醒"""
        self._rounds_since_update += 1
        if self._rounds_since_update >= 3:
            pending = [t for t in self.todos if t.status != "completed"]
            if pending:
                return f"\n[提醒] 还有 {len(pending)} 个未完成的任务，记得更新 todo 状态。"
        return None
```

**关键设计：同时只能有一个 `in_progress` 任务。** 这强迫模型专注于当前任务，而不是同时标记多个任务为进行中。

### V1 的局限

V1 是纯内存方案——所有 todo 存在 `appState.todos` 里：

```typescript
// TodoWriteTool.ts — V1 的核心逻辑
async call({ todos }, context) {
    const appState = context.getAppState()
    const todoKey = context.agentId ?? getSessionId()
    const oldTodos = appState.todos[todoKey] ?? []
    const allDone = todos.every(_ => _.status === 'completed')
    const newTodos = allDone ? [] : todos

    context.setAppState(prev => ({
        ...prev,
        todos: {
            ...prev.todos,
            [todoKey]: newTodos,
        },
    }))
    // ...
}
```

每次调用时，模型要传入**整个 todo 列表**的完整快照来覆盖旧列表。这意味着：

- **无法跨会话持久化**——进程退出，任务列表消失
- **无法多 Agent 共享**——内存状态无法被其他进程读取
- **操作粒度粗**——不能单独更新一个任务，必须传整个列表

---

## todo 工具

```python
todo_manager = TodoManager()

def run_todo(action: str, content: str = None,
             todo_id: str = None, status: str = None) -> str:
    if action == "add":
        return f"Added: {todo_manager.add(content)}"
    elif action == "update":
        return todo_manager.update(todo_id, status)
    elif action == "view":
        return todo_manager.view()
    return f"Unknown action: {action}"

TOOL_HANDLERS["todo"] = lambda **kw: run_todo(**kw)
```

加进 TOOLS schema：

```python
{
    "name": "todo",
    "description": "管理任务列表。在开始多步任务时先创建 todo，每完成一步更新状态。",
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["add", "update", "view"],
                "description": "add: 添加任务, update: 更新状态, view: 查看列表"
            },
            "content": {"type": "string", "description": "任务内容（add 时必填）"},
            "todo_id": {"type": "string", "description": "任务 ID（update 时必填）"},
            "status": {
                "type": "string",
                "enum": ["pending", "in_progress", "completed"],
                "description": "新状态（update 时必填）"
            }
        },
        "required": ["action"]
    }
}
```

---

## attention_check：注意力机制

模型有时会忘记更新 todo。在每次 LLM 调用前检查：

```python
def agent_loop(query: str):
    messages = [{"role": "user", "content": query}]

    while True:
        # 检查是否需要注入提醒
        reminder = todo_manager.attention_check()
        if reminder:
            messages[-1]["content"] += reminder  # 附加到最新消息

        response = client.messages.create(...)
        # ... 正常循环 ...
```

3 轮没有更新 todo 时，提醒会附加到当前消息末尾，让模型重新关注任务进度。

---

## V2：Task 工具族

Claude Code 在内部用 `isTodoV2Enabled()` 做功能开关，将 TodoWrite（V1）替换为一组细粒度的 Task 工具。V2 的核心差异：**文件持久化 + 单任务操作 + hooks 生命周期**。

### 切换机制：isTodoV2Enabled

```typescript
// src/utils/tasks.ts
export function isTodoV2Enabled(): boolean {
  // 通过环境变量强制启用（供 SDK 用户使用）
  if (isEnvTruthy(process.env.CLAUDE_CODE_ENABLE_TASKS)) {
    return true
  }
  // 交互式会话默认启用 V2；非交互式（SDK）默认用 V1
  return !getIsNonInteractiveSession()
}
```

这个函数同时控制两侧：

```typescript
// TodoWriteTool.ts — V1 只在 V2 未启用时生效
isEnabled() {
    return !isTodoV2Enabled()
}

// TaskCreateTool.ts — V2 只在启用时生效
isEnabled() {
    return isTodoV2Enabled()
}
```

在 `src/tools.ts` 中，工具列表根据开关动态组装：

```typescript
// src/tools.ts
TodoWriteTool,                          // V1，始终注册但 isEnabled 受控
...(isTodoV2Enabled()
  ? [TaskCreateTool, TaskGetTool, TaskUpdateTool, TaskListTool]
  : []),
```

### Task 数据模型

V2 的任务不再是内存对象，而是磁盘上的 JSON 文件：

```typescript
// src/utils/tasks.ts — Task schema
export const TaskSchema = lazySchema(() =>
  z.object({
    id: z.string(),
    subject: z.string(),               // 任务标题（祈使句）
    description: z.string(),            // 任务描述
    activeForm: z.string().optional(),  // 进行中的展示文案（现在分词形式）
    owner: z.string().optional(),       // 负责的 Agent ID
    status: TaskStatusSchema(),         // pending | in_progress | completed
    blocks: z.array(z.string()),        // 本任务阻塞了哪些任务
    blockedBy: z.array(z.string()),     // 哪些任务阻塞了本任务
    metadata: z.record(z.string(), z.unknown()).optional(),
  }),
)
```

存储路径：`~/.claude/tasks/{taskListId}/{taskId}.json`。每个任务一个文件，支持文件锁（`proper-lockfile`）防止并发冲突。

### 五个 Task 工具

#### TaskCreate：创建任务

```typescript
// src/tools/TaskCreateTool/TaskCreateTool.ts
inputSchema: z.strictObject({
    subject: z.string(),          // 任务标题
    description: z.string(),      // 任务描述
    activeForm: z.string().optional(),  // spinner 展示文案
    metadata: z.record(z.string(), z.unknown()).optional(),
})
```

创建时自动触发 `executeTaskCreatedHooks`——如果 hook 返回 `blockingError`，任务会被立即删除：

```typescript
async call({ subject, description, activeForm, metadata }, context) {
    const taskId = await createTask(getTaskListId(), {
        subject, description, activeForm,
        status: 'pending',
        owner: undefined,
        blocks: [], blockedBy: [],
        metadata,
    })

    // 执行 TaskCreated hooks
    const generator = executeTaskCreatedHooks(taskId, subject, description, ...)
    for await (const result of generator) {
        if (result.blockingError) {
            blockingErrors.push(getTaskCreatedHookMessage(result.blockingError))
        }
    }
    if (blockingErrors.length > 0) {
        await deleteTask(getTaskListId(), taskId)
        throw new Error(blockingErrors.join('\n'))
    }
    // ...
}
```

#### TaskUpdate：更新任务

可更新的字段最多：

```typescript
inputSchema: z.strictObject({
    taskId: z.string(),
    subject: z.string().optional(),
    description: z.string().optional(),
    activeForm: z.string().optional(),
    status: TaskUpdateStatusSchema.optional(),  // 包含 'deleted' 特殊状态
    addBlocks: z.array(z.string()).optional(),   // 添加阻塞关系
    addBlockedBy: z.array(z.string()).optional(),
    owner: z.string().optional(),
    metadata: z.record(z.string(), z.unknown()).optional(),
})
```

设置 `status: 'deleted'` 会物理删除任务文件。标记为 `completed` 时触发 `executeTaskCompletedHooks`。

一个重要细节：当 Agent Swarm 模式开启时，标记 `in_progress` 会自动设置 `owner`：

```typescript
// 自动设置 owner
if (isAgentSwarmsEnabled() && status === 'in_progress'
    && owner === undefined && !existingTask.owner) {
    const agentName = getAgentName()
    if (agentName) {
        updates.owner = agentName
    }
}
```

#### TaskGet：查询单个任务

```typescript
inputSchema: z.strictObject({
    taskId: z.string(),
})
// 返回: { id, subject, description, status, blocks, blockedBy }
```

只读操作，标记了 `isReadOnly: true` 和 `isConcurrencySafe: true`。

#### TaskList：列出所有任务

```typescript
inputSchema: z.strictObject({})  // 无参数
```

会过滤掉 `metadata._internal` 为 true 的内部任务，并且从 `blockedBy` 中去除已完成任务的引用——让模型看到的阻塞关系始终是有效的。

#### TaskStop：停止后台任务

```typescript
inputSchema: z.strictObject({
    task_id: z.string().optional(),
    shell_id: z.string().optional(),  // 向后兼容已废弃的 KillShell
})
```

这个工具停止的是后台运行的进程任务（如长时间运行的 shell 命令），不是 Task 列表中的逻辑任务。它保留了 `KillShell` 作为别名以兼容旧的 transcript。

### V2 的文件存储与并发控制

```typescript
// src/utils/tasks.ts

// 任务存储目录
export function getTasksDir(taskListId: string): string {
    return join(getClaudeConfigHomeDir(), 'tasks', sanitizePathComponent(taskListId))
}

// 创建任务 — 带文件锁
export async function createTask(taskListId, taskData): Promise<string> {
    const lockPath = await ensureTaskListLockFile(taskListId)
    let release = await lockfile.lock(lockPath, LOCK_OPTIONS)
    try {
        const highestId = await findHighestTaskId(taskListId)
        const id = String(highestId + 1)
        const task = { id, ...taskData }
        await writeFile(getTaskPath(taskListId, id), JSON.stringify(task, null, 2))
        return id
    } finally {
        await release()
    }
}
```

锁的参数为 swarm 场景优化——最多支持 10+ 个并发 Agent，重试 30 次，退避 5-100ms：

```typescript
const LOCK_OPTIONS = {
    retries: { retries: 30, minTimeout: 5, maxTimeout: 100 }
}
```

删除任务时还会维护 high water mark 文件（`.highwatermark`），确保已删除的任务 ID 不会被复用。

### Verification Nudge：防止跳过验证

V1 和 V2 都有一个相同的安全机制——当 3 个以上任务全部标记为 completed，且没有任何一个包含 “verif” 关键词时，工具返回中会注入一段提醒：

```typescript
// V2 中的实现（TaskUpdateTool.ts）
if (updates.status === 'completed') {
    const allTasks = await listTasks(taskListId)
    const allDone = allTasks.every(t => t.status === 'completed')
    if (allDone && allTasks.length >= 3
        && !allTasks.some(t => /verif/i.test(t.subject))) {
        verificationNudgeNeeded = true
    }
}
```

注入的提醒会要求模型在写总结之前先 spawn 一个 verification agent。这是对“所有任务完成 -> 循环退出 -> 跳过验证”这个常见失败模式的结构性防御。

---

## V1 vs V2 对比

| 维度 | V1 (TodoWrite) | V2 (Task 工具族) |
|------|----------------|-----------------|
| 存储 | 内存 (`appState.todos`) | 文件 (`~/.claude/tasks/`) |
| 操作粒度 | 整个列表覆盖 | 单任务 CRUD |
| 工具数量 | 1 个 | 4 个 (Create/Update/Get/List) |
| 并发安全 | 无 | 文件锁 (`proper-lockfile`) |
| 多 Agent 共享 | 不支持 | 支持 (通过 `taskListId`) |
| Hooks 集成 | 无 | TaskCreated / TaskCompleted |
| 依赖关系 | 无 | blocks / blockedBy |
| 任务所有权 | 无 | owner 字段 |
| 持久化 | 进程内 | 跨会话 |

---

## 源码实证

以下是文中引用的关键源码文件，均来自 Claude Code 仓库：

| 文件路径 | 说明 |
|----------|------|
| `src/tools/TodoWriteTool/TodoWriteTool.ts` | V1 工具实现，`isEnabled` 返回 `!isTodoV2Enabled()` |
| `src/tools/TodoWriteTool/prompt.ts` | V1 的完整 prompt，定义使用场景和任务状态规则 |
| `src/tools/TaskCreateTool/TaskCreateTool.ts` | V2 创建任务，触发 `executeTaskCreatedHooks` |
| `src/tools/TaskUpdateTool/TaskUpdateTool.ts` | V2 更新任务，支持 `deleted` 状态和 hooks |
| `src/tools/TaskGetTool/TaskGetTool.ts` | V2 查询任务，只读 + 并发安全 |
| `src/tools/TaskListTool/TaskListTool.ts` | V2 列出任务，过滤内部任务和已完成的阻塞引用 |
| `src/tools/TaskStopTool/TaskStopTool.ts` | 停止后台运行任务（兼容旧 KillShell） |
| `src/utils/tasks.ts` | 核心：`isTodoV2Enabled()`、文件存储、锁、Task schema |
| `src/tools.ts` | 工具注册入口，根据 `isTodoV2Enabled()` 动态切换 |

---

## 典型执行过程

对于“重构 src/ 目录下的所有模块”这样的任务：

```
模型第 1 轮：
  todo(add, "分析现有代码结构")
  todo(add, "重构 auth.py")
  todo(add, "重构 api.py")
  todo(add, "运行测试")
  todo(update, "1", "in_progress")

模型第 2 轮：
  bash("find src/ -name '*.py'")
  read_file("src/auth.py")
  todo(update, "1", "completed")
  todo(update, "2", "in_progress")

模型第 3 轮：
  edit_file("src/auth.py", ...)
  todo(update, "2", "completed")
  todo(update, "3", "in_progress")
  ...
```

<div class="mermaid">
flowchart TD
    A([任务开始]) --> B[todo: 分解任务]
    B --> C[todo: 标记 in_progress]
    C --> D[执行工具]
    D --> E[todo: 标记 completed]
    E --> F{还有任务?}
    F -->|是| C
    F -->|否| G([任务完成])
</div>

---

## 设计哲学：渐进式复杂度

TodoWrite 的 V1→V2 演化是 Claude Code 设计指南提到的**渐进式复杂度原则**的典型案例：

**入门用户**：不需要知道任务系统的存在，Claude 自动管理工作流程。

**进阶用户**：V1 的 TodoWrite 提供了简单的任务跟踪——一个字典，几个操作，足够应付大多数场景。

**专家用户**：V2 的 Task 工具族提供了完整的后台执行、磁盘持久化、并发控制，支持复杂的多任务工作流。

每个层次都是完整可用的，不需要理解下一层才能使用当前层。这和 Claude Code 整体的设计理念一致——对新手友好，对专家强大。

设计指南还强调了**代码即文档**原则。V2 源码中 `isTodoV2Enabled()` 的命名就是一个例子：函数名本身就解释了它的用途，注释只补充“为什么”（feature flag + 客户端版本检查），不重复“做什么”。

---

## 相对 s02 的变化

| 组件 | s02 | s03 |
|------|-----|-----|
| 工具数量 | 4 | 5（新增 todo） |
| 任务规划 | 无 | TodoManager |
| 注意力机制 | 无 | 3 轮无更新自动提醒 |
| Agent loop | — | **不变** |

---

下一篇：[Subagent：上下文隔离的正确姿势](../04-subagent/index.html)
