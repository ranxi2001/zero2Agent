---
layout: default
title: Task System：统一任务框架
description: 6 种 TaskType、不可变状态更新、磁盘输出流、自动驱逐——从源码揭示 Claude Code 的任务引擎
eyebrow: Claude Code / s07
---

# Task System：统一任务框架

s03 的 TaskCreate/Update/Get/List 是面向用户的 **V2 Tool 接口**——模型通过它们创建和查询任务。

但接口背后，驱动一切的是一个 **内部任务框架**：统一的类型体系、不可变状态更新、磁盘输出流、轮询通知、自动驱逐。

这一节先用源码实证看清真实架构，再从零实现一个持久化 DAG。

---

## 源码实证：真实的任务框架

### 6 种 TaskType

Claude Code 不是只有一种"任务"。它有 **7 种 TaskType**，每种有唯一的 ID 前缀：

```typescript
// src/Task.ts
export type TaskType =
  | 'local_bash'          // 前缀 'b' — 本地 shell 命令
  | 'local_agent'         // 前缀 'a' — 本地 agent 子会话
  | 'remote_agent'        // 前缀 'r' — 远程 agent
  | 'in_process_teammate' // 前缀 't' — 进程内协作者
  | 'local_workflow'      // 前缀 'w' — 本地工作流脚本
  | 'monitor_mcp'         // 前缀 'm' — MCP 监控
  | 'dream'               // 前缀 'd' — 后台推测任务
```

ID 生成算法：**前缀 + 8 位随机字符**（36 进制，约 2.8 万亿组合）：

```typescript
// src/Task.ts
export function generateTaskId(type: TaskType): string {
  const prefix = getTaskIdPrefix(type)
  const bytes = randomBytes(8)
  let id = prefix
  for (let i = 0; i < 8; i++) {
    id += TASK_ID_ALPHABET[bytes[i]! % TASK_ID_ALPHABET.length]
  }
  return id
}
// 示例：local_bash → "b3k7f9x2a"，local_agent → "ahj4m8n1p"
```

### 统一的状态生命周期

所有任务共享一个 5 态生命周期：

```typescript
// src/Task.ts
export type TaskStatus =
  | 'pending'    // 已创建，等待启动
  | 'running'    // 执行中
  | 'completed'  // 成功完成
  | 'failed'     // 失败
  | 'killed'     // 被用户或系统终止
```

<div class="mermaid">
stateDiagram-v2
    [*] --> pending
    pending --> running
    running --> completed
    running --> failed
    running --> killed
    completed --> [*]
    failed --> [*]
    killed --> [*]
</div>

终态守卫——防止对已死任务做状态转换：

```typescript
// src/Task.ts
export function isTerminalTaskStatus(status: TaskStatus): boolean {
  return status === 'completed' || status === 'failed' || status === 'killed'
}
```

### TaskStateBase：所有任务的公共骨架

```typescript
// src/Task.ts
export type TaskStateBase = {
  id: string           // 带前缀的唯一 ID
  type: TaskType       // 任务类型
  status: TaskStatus   // 当前状态
  description: string  // 人类可读描述
  toolUseId?: string   // 关联的 tool_use ID
  startTime: number    // 创建时间戳
  endTime?: number     // 结束时间戳
  outputFile: string   // 磁盘输出文件路径
  outputOffset: number // 已读取的字节偏移量
  notified: boolean    // 父级是否已被通知
}

export function createTaskStateBase(
  id: string, type: TaskType,
  description: string, toolUseId?: string,
): TaskStateBase {
  return {
    id, type, status: 'pending', description, toolUseId,
    startTime: Date.now(),
    outputFile: getTaskOutputPath(id),
    outputOffset: 0,
    notified: false,
  }
}
```

每种具体任务在此基础上扩展自己的字段。类型联合体确保类型安全：

```typescript
// src/tasks/types.ts
export type TaskState =
  | LocalShellTaskState
  | LocalAgentTaskState
  | RemoteAgentTaskState
  | InProcessTeammateTaskState
  | LocalWorkflowTaskState
  | MonitorMcpTaskState
  | DreamTaskState
```

---

### framework.ts：任务引擎的四大核心函数

所有任务类型共用 `src/utils/task/framework.ts` 中的统一框架。

#### 1. registerTask() — 注册任务到全局状态

```typescript
// src/utils/task/framework.ts
export function registerTask(task: TaskState, setAppState: SetAppState): void {
  let isReplacement = false
  setAppState(prev => {
    const existing = prev.tasks[task.id]
    isReplacement = existing !== undefined
    // 恢复时保留 UI 状态（retain, startTime, messages）
    const merged = existing && 'retain' in existing
      ? { ...task, retain: existing.retain, startTime: existing.startTime,
          messages: existing.messages, diskLoaded: existing.diskLoaded,
          pendingMessages: existing.pendingMessages }
      : task
    return { ...prev, tasks: { ...prev.tasks, [task.id]: merged } }
  })

  // 替换（恢复）不是新启动，跳过避免重复发送
  if (isReplacement) return

  enqueueSdkEvent({
    type: 'system', subtype: 'task_started',
    task_id: task.id, description: task.description,
    task_type: task.type, ...
  })
}
```

关键设计：
- **不可变更新**：用 `setAppState(prev => ...)` 函数式更新，永远不直接修改
- **恢复感知**：如果任务 ID 已存在（resume 场景），保留 UI 状态，不重复发 SDK 事件
- **SDK 事件**：首次注册时发射 `task_started` 事件，驱动外部集成

#### 2. updateTaskState() — 类型安全的状态更新

```typescript
export function updateTaskState<T extends TaskState>(
  taskId: string,
  setAppState: SetAppState,
  updater: (task: T) => T,
): void {
  setAppState(prev => {
    const task = prev.tasks?.[taskId] as T | undefined
    if (!task) return prev
    const updated = updater(task)
    // 同引用 → 无变化 → 跳过 spread，避免不必要的 re-render
    if (updated === task) return prev
    return { ...prev, tasks: { ...prev.tasks, [taskId]: updated } }
  })
}
```

泛型 `<T extends TaskState>` 让每种任务实现在更新时拿到自己的具体类型，而不是宽泛的联合体。

#### 3. evictTerminalTask() — 完成后驱逐释放内存

```typescript
export function evictTerminalTask(
  taskId: string, setAppState: SetAppState,
): void {
  setAppState(prev => {
    const task = prev.tasks?.[taskId]
    if (!task) return prev
    if (!isTerminalTaskStatus(task.status)) return prev  // 非终态，不驱逐
    if (!task.notified) return prev  // 还没通知父级，不驱逐
    // 面板宽限期：local_agent 有 retain 字段，需要等 evictAfter
    if ('retain' in task && (task.evictAfter ?? Infinity) > Date.now()) {
      return prev
    }
    const { [taskId]: _, ...remainingTasks } = prev.tasks
    return { ...prev, tasks: remainingTasks }
  })
}
```

驱逐有三道守卫：终态 → 已通知 → 宽限期过期。

#### 4. generateTaskAttachments() — 轮询输出增量

```typescript
export async function generateTaskAttachments(state: AppState): Promise<{
  attachments: TaskAttachment[]
  updatedTaskOffsets: Record<string, number>
  evictedTaskIds: string[]
}> {
  for (const taskState of Object.values(tasks)) {
    if (taskState.notified && isTerminalTaskStatus(taskState.status)) {
      evictedTaskIds.push(taskState.id)  // 已消费的终态任务 → GC
      continue
    }
    if (taskState.status === 'running') {
      const delta = await getTaskOutputDelta(
        taskState.id, taskState.outputOffset)
      if (delta.content) {
        updatedTaskOffsets[taskState.id] = delta.newOffset
      }
    }
  }
  return { attachments, updatedTaskOffsets, evictedTaskIds }
}
```

关键常量：

```typescript
export const POLL_INTERVAL_MS = 1000     // 轮询间隔
export const STOPPED_DISPLAY_MS = 3_000  // killed 后显示时长
export const PANEL_GRACE_MS = 30_000     // 面板宽限期（30 秒）
```

---

### 任务注册表：tasks.ts

所有任务类型在 `src/tasks.ts` 注册，形成统一分发：

```typescript
// src/tasks.ts
export function getAllTasks(): Task[] {
  const tasks: Task[] = [
    LocalShellTask,
    LocalAgentTask,
    RemoteAgentTask,
    DreamTask,
  ]
  if (LocalWorkflowTask) tasks.push(LocalWorkflowTask)
  if (MonitorMcpTask) tasks.push(MonitorMcpTask)
  return tasks
}

export function getTaskByType(type: TaskType): Task | undefined {
  return getAllTasks().find(t => t.type === type)
}
```

每个 `Task` 实现必须提供 `name`、`type`、`kill()` 方法。spawn 和 render 是各类型自行实现的，不走多态分发。

---

### 架构全景图

<div class="mermaid">
flowchart TB
    subgraph "V2 Tool 接口 (s03)"
        TC[TaskCreate] --> |"用户调用"| FW
        TU[TaskUpdate] --> FW
        TG[TaskGet] --> FW
        TL[TaskList] --> FW
    end

    subgraph FW["内部框架 framework.ts"]
        RT["registerTask()"]
        UT["updateTaskState()"]
        ET["evictTerminalTask()"]
        GA["generateTaskAttachments()"]
    end

    subgraph "AppState.tasks"
        S["Record&lt;string, TaskState&gt;"]
    end

    subgraph "具体任务类型"
        LS["LocalShellTask (b*)"]
        LA["LocalAgentTask (a*)"]
        RA["RemoteAgentTask (r*)"]
        IP["InProcessTeammateTask (t*)"]
        LW["LocalWorkflowTask (w*)"]
        DR["DreamTask (d*)"]
    end

    RT --> S
    UT --> S
    ET --> S
    GA --> |"轮询 1s"| S

    LS --> RT
    LA --> RT
    RA --> RT
    IP --> RT
    LW --> RT
    DR --> RT
</div>

---

### 磁盘输出流

任务不把输出存在内存里——它们写到磁盘文件，框架按偏移量增量读取：

```
~/.claude/task-output/
  b3k7f9x2a.output    ← local_bash 任务的完整 stdout/stderr
  ahj4m8n1p.output    ← local_agent 任务的输出
```

- `initTaskOutput(taskId)`：安全创建输出文件（`O_NOFOLLOW | O_EXCL` 防符号链接攻击）
- `getTaskOutputDelta(taskId, fromOffset)`：从偏移量读增量内容
- `evictTaskOutput(taskId)`：任务结束后清理磁盘文件

这解释了 `TaskStateBase` 里 `outputFile` 和 `outputOffset` 的用途——它们构成一个**磁盘上的流式读取协议**。

---

## 从零实现：持久化任务 DAG

理解了真实框架后，我们来实现一个教学版的任务图（DAG）——加入依赖关系和磁盘持久化，这是 s07–s12 的基础骨架。

### 任务图的三个问题

1. **什么任务可以现在开始？**（没有未完成的前置任务）
2. **什么任务在等待？**（有未完成的前置任务）
3. **什么任务已经完成？**

<div class="mermaid">
flowchart TD
    T1["task_1 ✓ completed"]
    T2["task_2 ○ ready"]
    T3["task_3 ○ ready"]
    T4["task_4 ⏸ blocked"]

    T1 --> T2
    T1 --> T3
    T2 --> T4
    T3 --> T4
</div>

### 磁盘结构

每个任务是 `.tasks/` 目录下的一个 JSON 文件：

```
.tasks/
  task_001.json
  task_002.json
  task_003.json
```

```json
{
  "id": "task_002",
  "title": "重构 auth.py",
  "description": "提取 JWT 验证逻辑到独立函数",
  "status": "ready",
  "blockedBy": ["task_001"],
  "blocks": ["task_004"],
  "created_at": "2025-01-01T10:00:00",
  "completed_at": null
}
```

`blockedBy`：这个任务需要等哪些任务先完成。
`blocks`：这个任务完成后，会解锁哪些任务。

### TaskManager 实现

```python
import json, uuid
from pathlib import Path
from datetime import datetime
from typing import Literal

TASKS_DIR = Path(".tasks")
TASKS_DIR.mkdir(exist_ok=True)

Status = Literal["pending", "ready", "in_progress", "completed", "failed"]

class TaskManager:
    def create(self, title: str, description: str = "",
               blocked_by: list[str] = None) -> str:
        task_id = f"task_{uuid.uuid4().hex[:6]}"
        status = "pending" if blocked_by else "ready"
        task = {
            "id": task_id,
            "title": title,
            "description": description,
            "status": status,
            "blockedBy": blocked_by or [],
            "blocks": [],
            "created_at": datetime.now().isoformat(),
            "completed_at": None,
        }
        # 把这个任务注册到前置任务的 blocks 列表
        for dep_id in (blocked_by or []):
            self._add_block(dep_id, task_id)
        self._save(task)
        return task_id

    def complete(self, task_id: str) -> str:
        task = self._load(task_id)
        if not task:
            return f"Task {task_id} not found"
        task["status"] = "completed"
        task["completed_at"] = datetime.now().isoformat()
        self._save(task)
        # 检查并解锁下游任务
        unlocked = self._unlock_downstream(task_id)
        msg = f"Completed: {task_id}"
        if unlocked:
            msg += f"\nUnlocked: {', '.join(unlocked)}"
        return msg

    def _unlock_downstream(self, completed_id: str) -> list[str]:
        """检查所有被 completed_id 阻塞的任务，看是否可以解锁"""
        unlocked = []
        for path in TASKS_DIR.glob("*.json"):
            task = json.loads(path.read_text())
            if completed_id in task.get("blockedBy", []):
                # 检查所有前置任务是否都已完成
                all_done = all(
                    self._get_status(dep) == "completed"
                    for dep in task["blockedBy"]
                )
                if all_done:
                    task["status"] = "ready"
                    self._save(task)
                    unlocked.append(task["id"])
        return unlocked

    def list_ready(self) -> list[dict]:
        return [t for t in self._all() if t["status"] == "ready"]

    def list_all(self) -> str:
        tasks = self._all()
        if not tasks:
            return "No tasks."
        lines = []
        for t in tasks:
            icon = {"ready": "○", "in_progress": "◐", "completed": "●",
                    "pending": "⏸", "failed": "✗"}.get(t["status"], "?")
            dep = f" [blocked by: {', '.join(t['blockedBy'])}]" if t["blockedBy"] and t["status"] == "pending" else ""
            lines.append(f"{icon} {t['id']}: {t['title']}{dep}")
        return "\n".join(lines)

    def _save(self, task: dict):
        (TASKS_DIR / f"{task['id']}.json").write_text(json.dumps(task, indent=2))

    def _load(self, task_id: str) -> dict | None:
        path = TASKS_DIR / f"{task_id}.json"
        return json.loads(path.read_text()) if path.exists() else None

    def _get_status(self, task_id: str) -> str:
        task = self._load(task_id)
        return task["status"] if task else "not_found"

    def _all(self) -> list[dict]:
        return [json.loads(p.read_text()) for p in sorted(TASKS_DIR.glob("*.json"))]

    def _add_block(self, task_id: str, blocked_task_id: str):
        task = self._load(task_id)
        if task and blocked_task_id not in task["blocks"]:
            task["blocks"].append(blocked_task_id)
            self._save(task)
```

### 工具接口

```python
task_manager = TaskManager()

def run_task_tool(action: str, **kwargs) -> str:
    if action == "create":
        return task_manager.create(
            title=kwargs["title"],
            description=kwargs.get("description", ""),
            blocked_by=kwargs.get("blocked_by", [])
        )
    elif action == "complete":
        return task_manager.complete(kwargs["task_id"])
    elif action == "list":
        return task_manager.list_all()
    elif action == "list_ready":
        ready = task_manager.list_ready()
        return "\n".join(f"- {t['id']}: {t['title']}" for t in ready) or "No ready tasks."
    return f"Unknown action: {action}"
```

### DAG 执行流程

<div class="mermaid">
flowchart TD
    A[task_1: 分析代码] --> B[task_2: 重构]
    A --> C[task_3: 写测试]
    B --> D[task_4: 集成测试]
    C --> D

    D --> E[list_ready: task_1 可用]
    E --> F[执行 task_1]
    F --> G[complete task_1\n解锁 task_2 和 task_3]
    G --> H[并行处理 task_2 和 task_3]
    H --> I[complete task_2 + task_3\n解锁 task_4]
</div>

---

## 真实框架 vs 从零实现

| 维度 | Claude Code 真实框架 | 我们的 DAG 实现 |
|------|---------------------|----------------|
| 任务类型 | 7 种 TaskType，各有专属状态 | 单一类型 |
| 状态管理 | 不可变函数式更新 `setAppState(prev => ...)` | 直接写 JSON 文件 |
| ID 生成 | 类型前缀 + 8 位密码学随机 | `uuid.hex[:6]` |
| 输出存储 | 磁盘流式文件 + 偏移量增量读 | 无输出流 |
| 依赖关系 | 无（各任务独立，由模型编排） | blockedBy/blocks DAG |
| 生命周期管理 | 终态守卫 + 通知 + 宽限期驱逐 | 手动 complete |
| 轮询 | 1 秒间隔 + 增量 delta | 无轮询 |

核心洞察：Claude Code 的任务**没有 DAG 依赖**——它让模型自行决定执行顺序。框架只负责注册、状态更新、输出流、驱逐。这是一种"**模型即调度器**"的设计哲学。

## 设计哲学：从同步助手到异步协作者

设计指南将任务系统视为 Agent 进化的关键转折点：

> 后台任务是 Agent 从"同步助手"进化为"异步协作者"的关键。

早期 AI 助手是完全同步的——用户问，AI 答，用户等待。任务系统打破了这个限制，让 Agent 能够：
1. **并行执行**多个长时间任务
2. **不阻塞用户**继续其他工作
3. **持久化进度**，崩溃后可恢复

源码中"模型即调度器"的设计选择也值得深思：Claude Code 的任务系统**没有 DAG 依赖**，它让模型自行决定执行顺序。框架只负责注册、状态更新、输出流、驱逐。这体现了设计指南的第三原则——**单一职责，组合完成复杂任务**：框架管生命周期，模型管调度逻辑，各司其职。

另一个设计亮点是**可观察性是一等公民**。任务 ID 的类型前缀（`b` = bash, `a` = agent, `d` = dream）让运维人员一眼就能区分任务类型。输出持久化到磁盘文件 + 偏移量增量读取，既支持实时追踪又不占用内存。这些不是事后添加的功能，而是从设计之初就内置的。

---

## 为什么比 TodoManager 更好

| 特性 | TodoManager (s03) | TaskSystem (s07) |
|------|-------------------|-----------------|
| 持久化 | 无（内存） | 磁盘 JSON |
| 依赖关系 | 无 | blockedBy / blocks |
| 重启恢复 | 丢失 | 自动恢复 |
| 自动解锁 | 无 | 完成时自动解锁下游 |
| 并发支持 | 无 | 基础（s08+ 扩展） |

---

下一篇：[Background Tasks：非阻塞工具执行](../08-background-tasks/index.html)
