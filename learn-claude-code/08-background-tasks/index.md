---
layout: default
title: Background Tasks：非阻塞工具执行
description: 慢命令不卡循环——守护线程 + 通知队列，Agent 可以边等边干别的
eyebrow: Claude Code / s08
---

# Background Tasks：非阻塞工具执行

`npm install`、`pytest`、`docker build`——这些命令可能跑几分钟。

如果直接在 Agent 循环里同步等待，模型什么都干不了，用户体验糟糕，而且浪费时间。

这一节实现后台任务：启动慢命令，Agent 循环继续，完成时通知结果。

---

## 问题

```python
# 同步执行：卡住整个循环，等待 3 分钟
output = run_bash("npm install && npm run build")
# 3 分钟后才能继续...
```

Agent 被迫等待，什么都干不了。

---

## 源码实证：Claude Code 的 6 种后台任务

Claude Code 不只能后台跑 shell 命令。它的 `src/tasks/` 目录下有 **6 种任务类型**，覆盖了从 bash 到自动记忆的全部后台场景：

| 类型 | type 标识 | 用途 | ID 前缀 |
|------|----------|------|---------|
| `LocalShellTask` | `local_bash` | 后台 shell 命令（npm、pytest、docker） | — |
| `LocalAgentTask` | `local_agent` | AgentTool 派生的子 Agent | `a` |
| `RemoteAgentTask` | `remote_agent` | 云端 session（ultraplan/ultrareview） | — |
| `InProcessTeammateTask` | `in_process_teammate` | 同进程内队友 Agent | — |
| `DreamTask` | `dream` | 自动记忆整合（auto-dream） | `dream` |
| `LocalMainSessionTask` | `local_agent` | Ctrl+B 将主会话放入后台 | `s` |

所有任务共享同一个注册和生命周期框架：`registerTask()` + `updateTaskState()` + `enqueuePendingNotification()`。

---

## 源码实证：LocalShellTask 的完整生命周期

`LocalShellTask` 是最核心的后台任务。它管理后台 shell 进程，追踪输出，发送完成通知。

### 状态结构

源码 `guards.ts` 定义了任务状态：

```typescript
// src/tasks/LocalShellTask/guards.ts
export type LocalShellTaskState = TaskStateBase & {
  type: 'local_bash'
  command: string
  result?: {
    code: number         // 进程退出码
    interrupted: boolean // 是否被中断
  }
  shellCommand: ShellCommand | null
  isBackgrounded: boolean   // false=前台运行, true=已放入后台
  agentId?: AgentId         // 哪个 agent 启动的，用于孤儿清理
  kind?: 'bash' | 'monitor' // UI 显示变体
}
```

关键点：`isBackgrounded` 区分前台和后台。一个命令可以先在前台运行，跑久了再切到后台。

### 启动流程

```typescript
// src/tasks/LocalShellTask/LocalShellTask.tsx (简化)
export async function spawnShellTask(input, context): Promise<TaskHandle> {
  const { command, description, shellCommand, toolUseId, agentId } = input
  const taskId = shellCommand.taskOutput.taskId

  // 1. 注册清理回调（进程退出时自动 kill）
  const unregisterCleanup = registerCleanup(async () => {
    killTask(taskId, setAppState)
  })

  // 2. 创建任务状态，注册到全局 tasks 表
  const taskState: LocalShellTaskState = {
    ...createTaskStateBase(taskId, 'local_bash', description, toolUseId),
    type: 'local_bash',
    status: 'running',
    command,
    shellCommand,
    isBackgrounded: true,
    agentId,
  }
  registerTask(taskState, setAppState)

  // 3. 切换到后台模式——TaskOutput 自动持续接收数据
  shellCommand.background(taskId)

  // 4. 启动 Stall Watchdog（检测交互式卡住）
  const cancelStallWatchdog = startStallWatchdog(taskId, description, ...)

  // 5. 等待结果，完成时更新状态并发送通知
  void shellCommand.result.then(async result => {
    cancelStallWatchdog()
    await flushAndCleanup(shellCommand)
    updateTaskState(taskId, setAppState, task => ({
      ...task,
      status: result.code === 0 ? 'completed' : 'failed',
      result: { code: result.code, interrupted: result.interrupted },
      shellCommand: null,
      endTime: Date.now(),
    }))
    enqueueShellNotification(taskId, description, status, result.code, ...)
    void evictTaskOutput(taskId)
  })

  return { taskId, cleanup: () => unregisterCleanup() }
}
```

### Stall Watchdog：检测交互式阻塞

Claude Code 有个精妙的机制——当后台命令停止输出 45 秒，且输出尾部看起来像交互式提示符时，主动通知模型：

```typescript
// 每 5 秒检查一次
const STALL_CHECK_INTERVAL_MS = 5_000
const STALL_THRESHOLD_MS = 45_000

// 匹配的模式：(y/n)、Continue?、Press Enter 等
const PROMPT_PATTERNS = [
  /\(y\/n\)/i,
  /\(yes\/no\)/i,
  /Continue\?/i,
  /Press (any key|Enter)/i,
  /Overwrite\?/i,
]
```

watchdog 通过 `fs.stat()` 监控输出文件大小变化。文件大小不增长 + 尾部匹配 prompt 模式 = 发出通知，告诉模型 "这个命令可能卡在交互提示上，kill 掉重试吧"。

### 通知格式

完成通知以 XML 格式注入到消息流：

```xml
<task-notification>
  <task-id>bash_abc123</task-id>
  <tool-use-id>toolu_xyz</tool-use-id>
  <output-file>/tmp/.../tasks/bash_abc123.output</output-file>
  <status>completed</status>
  <summary>Background command "npm install" completed (exit code 0)</summary>
</task-notification>
```

通知通过 `enqueuePendingNotification()` 放入队列，在下一轮 LLM 调用前注入到对话中。

### Kill 与孤儿清理

`killShellTasks.ts` 处理两种场景：

```typescript
// 1. 手动 kill 单个任务
export function killTask(taskId, setAppState): void {
  updateTaskState(taskId, setAppState, task => {
    task.shellCommand?.kill()
    task.shellCommand?.cleanup()
    task.unregisterCleanup?.()
    return { ...task, status: 'killed', notified: true, shellCommand: null }
  })
  void evictTaskOutput(taskId)
}

// 2. Agent 退出时清理所有它启动的 shell 任务（防止僵尸进程）
export function killShellTasksForAgent(agentId, getAppState, setAppState): void {
  const tasks = getAppState().tasks ?? {}
  for (const [taskId, task] of Object.entries(tasks)) {
    if (isLocalShellTask(task) && task.agentId === agentId && task.status === 'running') {
      killTask(taskId, setAppState)
    }
  }
  // 清除该 agent 的待处理通知
  dequeueAllMatching(cmd => cmd.agentId === agentId)
}
```

`killShellTasksForAgent` 是关键——没有它，子 Agent 退出后启动的 `npm run dev` 会变成僵尸进程，跑到天荒地老。

---

## 源码实证：Ctrl+B 放入后台与前后台切换

Claude Code 支持一个命令从前台无缝切换到后台。流程分三步：

```
registerForeground()     命令开始时注册前台任务（isBackgrounded=false）
     ↓ 用户按 Ctrl+B 或自动超时
backgroundExistingForegroundTask()   翻转 isBackgrounded=true，安装结果处理器
     ↓ 命令完成
enqueueShellNotification()   发送完成通知
```

`backgroundAll()` 在用户按 Ctrl+B 时，同时处理所有前台的 bash 任务和 agent 任务：

```typescript
export function backgroundAll(getAppState, setAppState): void {
  // 后台化所有前台 bash 任务
  for (const taskId of foregroundBashTaskIds) {
    backgroundTask(taskId, getAppState, setAppState)
  }
  // 后台化所有前台 agent 任务
  for (const taskId of foregroundAgentTaskIds) {
    backgroundAgentTask(taskId, getAppState, setAppState)
  }
}
```

---

## 源码实证：DreamTask 自动记忆整合

`DreamTask` 是一种特殊的后台任务——不执行用户命令，而是自动整理对话记忆。它的状态结构很独特：

```typescript
// src/tasks/DreamTask/DreamTask.ts
export type DreamTaskState = TaskStateBase & {
  type: 'dream'
  phase: 'starting' | 'updating'  // starting→reading sessions, updating→writing CLAUDE.md
  sessionsReviewing: number       // 正在复习多少个 session
  filesTouched: string[]          // 修改了哪些文件（不完全，仅工具调用可见的）
  turns: DreamTurn[]              // 最多保留 30 轮助手文本
  abortController?: AbortController
  priorMtime: number              // 用于 kill 时回滚 consolidation lock
}
```

DreamTask 的特殊之处：

1. **没有模型通知**——完成后不发 `<task-notification>`，因为它是纯 UI 层面的展示
2. **phase 检测简单**——不解析 dream prompt 的 4 阶段结构，只看是否有 Edit/Write 调用来切换 phase
3. **kill 时回滚 lock**——用户中止 dream 后，回滚 consolidation lock 的 mtime，让下次 session 可以重试

```typescript
export const DreamTask: Task = {
  name: 'DreamTask',
  type: 'dream',
  async kill(taskId, setAppState) {
    let priorMtime: number | undefined
    updateTaskState<DreamTaskState>(taskId, setAppState, task => {
      if (task.status !== 'running') return task
      task.abortController?.abort()
      priorMtime = task.priorMtime
      return { ...task, status: 'killed', notified: true }
    })
    // 回滚 lock，让下次 session 可以重新 dream
    if (priorMtime !== undefined) {
      await rollbackConsolidationLock(priorMtime)
    }
  },
}
```

---

## 源码实证：LocalMainSessionTask 主会话后台化

当用户按两次 Ctrl+B，当前对话本身会被放入后台。这是最"重量级"的后台任务——整个 query 循环在后台继续：

```typescript
// src/tasks/LocalMainSessionTask.ts
export function registerMainSessionTask(
  description: string,
  setAppState: SetAppState,
  mainThreadAgentDefinition?: AgentDefinition,
  existingAbortController?: AbortController,
): { taskId: string; abortSignal: AbortSignal } {
  // ID 用 's' 前缀，区分于 agent 任务的 'a' 前缀
  const taskId = generateMainSessionTaskId()  // 例如 "s7k2m9x1"

  // 输出指向独立的 transcript 文件（不能写主 session 文件，否则 /clear 后会损坏）
  void initTaskOutputAsSymlink(
    taskId,
    getAgentTranscriptPath(asAgentId(taskId)),
  )

  const taskState: LocalMainSessionTaskState = {
    ...createTaskStateBase(taskId, 'local_agent', description),
    type: 'local_agent',
    agentType: 'main-session',  // 标识这是主会话，不是子 agent
    status: 'running',
    isBackgrounded: true,
  }
  registerTask(taskState, setAppState)

  return { taskId, abortSignal: abortController.signal }
}
```

`startBackgroundSession()` 则是完整的后台 query 运行器：它克隆当前消息列表，在后台 `for await` 一个新的 `query()` 调用，实时更新 progress（toolUseCount、tokenCount、recentActivities），并逐条写入独立的 sidechain transcript。

---

## 源码实证：输出流与面板驱逐

### TaskOutput 磁盘流

所有后台任务的输出都通过 `TaskOutput` 写入磁盘文件。TaskOutput 支持两种模式：

- **文件直写模式**（shell 任务）：stdout 直接写入文件 fd，不经过 JS
- **管道模式**（hooks）：通过 `writeStdout()`/`writeStderr()` 缓冲后写入

读取端通过 `getTaskOutputDelta(taskId, fromOffset)` 增量读取，只从偏移量开始读，不加载整个文件。

### PANEL_GRACE_MS 面板驱逐

```typescript
// src/utils/task/framework.ts
export const PANEL_GRACE_MS = 30_000  // 30 秒
```

任务完成后，在状态栏 pill 和 Shift+Down 面板中保留 30 秒，然后驱逐。这给用户足够时间看到完成状态，又不会让面板堆满历史任务。

### AgentProgress 追踪

`LocalAgentTask` 追踪子 Agent 的进度，用于 UI 展示：

```typescript
export type AgentProgress = {
  toolUseCount: number         // 工具调用次数
  tokenCount: number           // token 消耗量
  lastActivity?: ToolActivity  // 最近一次工具调用
  recentActivities?: ToolActivity[]  // 最近 5 次活动
}
```

token 计数有个细节：API 的 `input_tokens` 是每轮累计的（包含所有历史 context），所以只取最新值；`output_tokens` 是每轮独立的，需要累加。

---

## 解决方案

理解了 Claude Code 的架构，我们来看核心设计模式：

<div class="mermaid">
flowchart LR
    A[Agent 循环\n主线程] -->|background_run| B[BackgroundManager\n启动守护线程]
    B --> C[子进程\nnpm install]
    B -->|立即返回 job_id| A
    A --> D[继续干别的工作]
    C -->|完成| E[结果入队列]
    E -->|下轮 LLM 调用前\ndraining| A
</div>

关键设计：主线程始终单线程，只有子进程 I/O 是并行的。

---

## 从零实现：BackgroundManager

```python
import threading, subprocess, queue, time, uuid
from dataclasses import dataclass

@dataclass
class BackgroundJob:
    job_id: str
    command: str
    status: str = "running"   # running | completed | failed
    output: str = ""
    started_at: float = 0.0
    completed_at: float = 0.0

class BackgroundManager:
    def __init__(self):
        self.jobs: dict[str, BackgroundJob] = {}
        self.notifications: queue.Queue = queue.Queue()

    def run(self, command: str) -> str:
        """启动后台命令，立即返回 job_id"""
        job_id = f"job_{uuid.uuid4().hex[:6]}"
        job = BackgroundJob(
            job_id=job_id,
            command=command,
            started_at=time.time()
        )
        self.jobs[job_id] = job

        # 守护线程执行子进程
        thread = threading.Thread(
            target=self._execute,
            args=(job,),
            daemon=True  # 主进程退出时自动清理
        )
        thread.start()
        return f"Started background job: {job_id}\nCommand: {command}"

    def _execute(self, job: BackgroundJob):
        try:
            result = subprocess.run(
                job.command, shell=True,
                capture_output=True, text=True, timeout=600
            )
            job.output = (result.stdout + result.stderr)[:50000]
            job.status = "completed" if result.returncode == 0 else "failed"
        except subprocess.TimeoutExpired:
            job.output = "Timeout after 600 seconds"
            job.status = "failed"
        except Exception as e:
            job.output = str(e)
            job.status = "failed"

        job.completed_at = time.time()
        # 完成时放入通知队列
        self.notifications.put({
            "job_id": job.job_id,
            "status": job.status,
            "output": job.output,
            "duration": f"{job.completed_at - job.started_at:.1f}s"
        })

    def check(self, job_id: str) -> str:
        """查询特定任务状态"""
        job = self.jobs.get(job_id)
        if not job:
            return f"Job {job_id} not found"
        elapsed = time.time() - job.started_at
        if job.status == "running":
            return f"Job {job_id}: still running ({elapsed:.1f}s elapsed)"
        return f"Job {job_id}: {job.status}\nOutput:\n{job.output}"

    def drain_notifications(self) -> list[dict]:
        """取出所有待处理的完成通知（每次 LLM 调用前调用）"""
        notifications = []
        while not self.notifications.empty():
            try:
                notifications.append(self.notifications.get_nowait())
            except queue.Empty:
                break
        return notifications
```

---

## 从零实现：集成到 Agent 循环

```python
bg_manager = BackgroundManager()

TOOL_HANDLERS["background_run"] = lambda **kw: bg_manager.run(kw["command"])
TOOL_HANDLERS["check"] = lambda **kw: bg_manager.check(kw["job_id"])

def agent_loop(messages: list):
    while True:
        # 每次 LLM 调用前：把后台任务完成通知注入消息
        notifications = bg_manager.drain_notifications()
        if notifications:
            notice_text = "\n".join(
                f"[Background job completed]\n"
                f"job_id: {n['job_id']}\n"
                f"status: {n['status']}\n"
                f"duration: {n['duration']}\n"
                f"output: {n['output'][:1000]}"
                for n in notifications
            )
            messages.append({"role": "user", "content": notice_text})

        response = client.messages.create(...)
        # ... 正常循环 ...
```

通知以普通 user 消息注入，模型可以看到后台任务的结果并继续推理。

---

## 从零实现：工具 Schema

```python
{
    "name": "background_run",
    "description": "在后台运行慢命令，立即返回 job_id。适合 npm install、pytest、docker build 等耗时操作。",
    "input_schema": {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "要在后台执行的 shell 命令"}
        },
        "required": ["command"]
    }
},
{
    "name": "check",
    "description": "查询后台任务状态",
    "input_schema": {
        "type": "object",
        "properties": {
            "job_id": {"type": "string", "description": "background_run 返回的 job_id"}
        },
        "required": ["job_id"]
    }
}
```

---

## 典型使用场景

```
用户：安装依赖并运行测试

模型：
  background_run("pip install -r requirements.txt")
  → 返回 job_abc123，继续工作

  # 趁等待时做其他事
  read_file("tests/test_main.py")
  todo(update, "2", "in_progress")

  # 通知注入：job_abc123 completed，安装成功

  background_run("pytest tests/ -v")
  → 返回 job_def456

  # 继续其他工作...

  # 通知注入：job_def456 completed，10 passed 2 failed
  # 模型根据结果决定下一步
```

---

## 源码实证 vs 从零实现对比

| 维度 | Claude Code 真实实现 | 我们的 Python 实现 |
|------|---------------------|-------------------|
| 任务类型 | 6 种（shell/agent/dream/session...） | 1 种（shell only） |
| 输出存储 | 磁盘文件 + offset 增量读取 | 内存字符串 |
| 进程管理 | ShellCommand 封装 + kill/cleanup | subprocess.run 一把梭 |
| 通知格式 | XML `<task-notification>` 结构化 | 纯文本 user 消息 |
| Stall 检测 | 45s watchdog + prompt 模式匹配 | 无 |
| 前后台切换 | registerForeground → background | 只有后台 |
| 孤儿清理 | killShellTasksForAgent | 守护线程 daemon=True |
| 面板驱逐 | 30s grace period 后清除 | 无 |

我们的实现是 Claude Code 的最小可行子集。真实产品需要处理更多边界情况——交互式命令卡住、子 Agent 退出后的僵尸进程、磁盘输出的增量读取——但核心模式完全一致：**异步启动 + 队列通知 + 下轮注入**。

---

## 线程安全说明

- **主线程**：Agent 循环，单线程，无需锁
- **守护线程**：每个后台任务一个线程，只写自己的 job 对象和 queue
- **queue.Queue**：线程安全，`put` 和 `get` 无需加锁
- **job 对象**：守护线程写完后才放入 queue，主线程通过 queue 感知——无竞争条件

---

下一篇：[Agent Teams：多 Agent 协作](../09-agent-teams/index.html)
