---
layout: default
title: Autonomous Agents：自组织团队
description: Coordinator Mode、Dream Task、Memory Extraction —— 源码实证 + 从零实现
eyebrow: Claude Code / s11
---

# Autonomous Agents：自组织团队

s09-s10 的团队需要 Leader 手动分配任务。这一节移除这个限制：**让 Agent 自己扫描任务、自己认领工作、自己记忆经验**。

Claude Code 在这个方向上已经走得很远：Coordinator Mode 让主 Agent 自动调度 Worker；Dream Task 在后台整理记忆；Memory Extraction 在每轮对话后自动提取经验。

本文分两条线：

- **源码实证** --- 直接读 Claude Code 源码，看真实架构怎么做
- **从零实现** --- 用 Python 从头搭建一个自治 Agent 系统

---

## 一、Coordinator Mode 源码实证

> 源文件：`src/coordinator/coordinatorMode.ts`

### 1.1 Feature Flag 双重门控

Coordinator Mode 不是默认开启的。它需要两道门：

```typescript
// coordinatorMode.ts
export function isCoordinatorMode(): boolean {
  if (feature('COORDINATOR_MODE')) {
    return isEnvTruthy(process.env.CLAUDE_CODE_COORDINATOR_MODE)
  }
  return false
}
```

第一道：编译时 feature flag `COORDINATOR_MODE`（Bun bundle 阶段决定）。第二道：运行时环境变量 `CLAUDE_CODE_COORDINATOR_MODE`。两道都通过才开启。

这种 **编译时 + 运行时** 双重门控在大型 Agent 系统中很常见 --- 编译时决定代码是否打包进产物，运行时决定是否激活。

### 1.2 Session Mode 恢复

恢复一个旧 session 时，当前环境变量可能和 session 创建时不同：

```typescript
export function matchSessionMode(
  sessionMode: 'coordinator' | 'normal' | undefined,
): string | undefined {
  const currentIsCoordinator = isCoordinatorMode()
  const sessionIsCoordinator = sessionMode === 'coordinator'

  if (currentIsCoordinator === sessionIsCoordinator) {
    return undefined
  }

  // 翻转环境变量，让 isCoordinatorMode() 实时匹配
  if (sessionIsCoordinator) {
    process.env.CLAUDE_CODE_COORDINATOR_MODE = '1'
  } else {
    delete process.env.CLAUDE_CODE_COORDINATOR_MODE
  }
  // ...
}
```

关键设计：**session 的模式优先于当前环境变量**。恢复 session 时直接改 `process.env`，因为 `isCoordinatorMode()` 是实时读取的，没有缓存。

### 1.3 Coordinator 的 System Prompt

`getCoordinatorSystemPrompt()` 返回一个完整的系统提示词，定义了 Coordinator 的行为规范：

**角色定义**：

> You are a **coordinator**. Your job is to help the user achieve their goal, direct workers to research/implement/verify code changes, synthesize results and communicate with the user.

**核心工具**：

| 工具 | 用途 |
|------|------|
| `Agent` | 创建新 Worker |
| `SendMessage` | 给已有 Worker 发后续指令 |
| `TaskStop` | 终止一个 Worker |

**Worker 结果如何回来**：

Worker 完成后，结果作为 **user-role 消息** 回来，包裹在 `<task-notification>` XML 中：

```xml
<task-notification>
  <task-id>{agentId}</task-id>
  <status>completed|failed|killed</status>
  <summary>{human-readable status summary}</summary>
  <result>{agent's final text response}</result>
  <usage>
    <total_tokens>N</total_tokens>
    <tool_uses>N</tool_uses>
    <duration_ms>N</duration_ms>
  </usage>
</task-notification>
```

**最重要的一条规则 --- “先理解再委派”**：

> When workers report research findings, **you must understand them before directing follow-up work**. Never write “based on your findings” or “based on the research.” You never hand off understanding to another worker.

这是区分好 Coordinator 和差 Coordinator 的分水岭。差的 Coordinator 是传话筒（“根据你的发现去修”）；好的 Coordinator 先消化结果，再给出精确指令（“修 src/auth/validate.ts:42 的空指针，Session.expired 为 true 时 user 字段是 undefined”）。

### 1.4 Worker 的工具上下文注入

```typescript
export function getCoordinatorUserContext(
  mcpClients: ReadonlyArray<{ name: string }>,
  scratchpadDir?: string,
): { [k: string]: string } {
  if (!isCoordinatorMode()) return {}

  const workerTools = isEnvTruthy(process.env.CLAUDE_CODE_SIMPLE)
    ? [BASH_TOOL_NAME, FILE_READ_TOOL_NAME, FILE_EDIT_TOOL_NAME]
        .sort().join(', ')
    : Array.from(ASYNC_AGENT_ALLOWED_TOOLS)
        .filter(name => !INTERNAL_WORKER_TOOLS.has(name))
        .sort().join(', ')

  let content = `Workers spawned via the Agent tool have access to these tools: ${workerTools}`

  if (scratchpadDir && isScratchpadGateEnabled()) {
    content += `\n\nScratchpad directory: ${scratchpadDir}\n`
      + 'Workers can read and write here without permission prompts.'
  }

  return { workerToolsContext: content }
}
```

三个关键点：

1. **SIMPLE 模式**：只给 Worker 最基础的 Bash + Read + Edit
2. **正常模式**：给 Worker 全部异步工具，但过滤掉内部工具（TeamCreate、TeamDelete、SendMessage、SyntheticOutput）--- Worker 不能自己创建或管理其他 Worker
3. **Scratchpad**：一个共享目录，Worker 可以无权限读写，用于跨 Worker 传递知识

---

## 二、Dream Task 源码实证

> 源文件：`src/tasks/DreamTask/DreamTask.ts`

Dream Task 是 Claude Code 的 **后台记忆整理** 机制 --- 像人睡觉时整理白天记忆一样（所以叫 “Dream”）。

### 2.1 状态模型

```typescript
export type DreamPhase = 'starting' | 'updating'

export type DreamTaskState = TaskStateBase & {
  type: 'dream'
  phase: DreamPhase
  sessionsReviewing: number          // 正在回顾多少个 session
  filesTouched: string[]             // 被修改的文件路径（不完整）
  turns: DreamTurn[]                 // 最近 30 轮的摘要
  abortController?: AbortController  // 用于取消
  priorMtime: number                 // 用于 kill 时回滚锁
}
```

两个阶段非常简单：`starting`（刚启动）和 `updating`（第一次 Edit/Write 工具调用落地后切换）。注释明确说了 **不解析** dream agent 的 4 阶段内部结构（orient/gather/consolidate/prune），只看有没有实际写文件。

### 2.2 增量转弯记录

```typescript
const MAX_TURNS = 30

export function addDreamTurn(
  taskId: string,
  turn: DreamTurn,
  touchedPaths: string[],
  setAppState: SetAppState,
): void {
  updateTaskState<DreamTaskState>(taskId, setAppState, task => {
    const seen = new Set(task.filesTouched)
    const newTouched = touchedPaths.filter(p => !seen.has(p) && seen.add(p))
    // 空 turn 且没有新文件 → 跳过，避免无意义重渲染
    if (turn.text === '' && turn.toolUseCount === 0 && newTouched.length === 0) {
      return task
    }
    return {
      ...task,
      phase: newTouched.length > 0 ? 'updating' : task.phase,
      filesTouched: newTouched.length > 0
        ? [...task.filesTouched, ...newTouched]
        : task.filesTouched,
      turns: task.turns.slice(-(MAX_TURNS - 1)).concat(turn),
    }
  })
}
```

滑动窗口只保留最近 30 轮。`filesTouched` 用 Set 去重。注释特别强调这只是 **“至少碰了这些文件”**，因为 Bash 命令里的写操作无法被 pattern-match 捕获。

### 2.3 Kill 与锁回滚

```typescript
async kill(taskId, setAppState) {
  let priorMtime: number | undefined
  updateTaskState<DreamTaskState>(taskId, setAppState, task => {
    if (task.status !== 'running') return task
    task.abortController?.abort()
    priorMtime = task.priorMtime
    return { ...task, status: 'killed', endTime: Date.now(), notified: true }
  })
  // 回滚锁的 mtime，让下次 session 可以重试
  if (priorMtime !== undefined) {
    await rollbackConsolidationLock(priorMtime)
  }
}
```

Dream 被 kill 时，不仅终止 agent，还要回滚 consolidation lock 的 mtime。这确保了 **kill 不会导致记忆整理永久跳过** --- 下个 session 检测锁时间戳时，会认为上次整理没完成，重新触发。

### 2.4 仅 UI 通知

```typescript
export function completeDreamTask(taskId, setAppState): void {
  // notified: true immediately — dream 没有 model-facing 通知路径
  // 它是纯 UI 展示，eviction 需要 terminal + notified
  updateTaskState<DreamTaskState>(taskId, setAppState, task => ({
    ...task, status: 'completed', endTime: Date.now(), notified: true,
  }))
}
```

Dream 完成时 **不通知模型**，只更新 UI。主 agent 不需要知道后台整理的结果 --- 下次读 memory 文件时自然会看到更新。

---

## 三、Memory Extraction 源码实证

> 源文件：`src/services/extractMemories/extractMemories.ts` + `prompts.ts`
> 类型定义：`src/memdir/memoryTypes.ts`

Memory Extraction 是 Claude Code 在 **每轮对话结束后** 自动提取有价值信息并写入持久化记忆的机制。

### 3.1 四种记忆类型

```typescript
// memoryTypes.ts
export const MEMORY_TYPES = ['user', 'feedback', 'project', 'reference'] as const
```

| 类型 | 内容 | 示例 |
|------|------|------|
| `user` | 用户角色、目标、偏好 | “用户是数据科学家，关注可观测性” |
| `feedback` | 用户对工作方式的指导 | “不要 mock 数据库，上次 mock 通过但线上挂了” |
| `project` | 项目进展、决策、截止日期 | “周四后冻结非关键合并，移动端在切分支” |
| `reference` | 外部系统指针 | “pipeline bug 追踪在 Linear 项目 INGEST 里” |

注意 **什么不存**：代码模式、架构、文件结构、git 历史 --- 这些可以从当前代码直接推导出来。记忆只存 **不可推导** 的信息。

### 3.2 Forked Agent 模式

Memory Extraction 使用 `runForkedAgent` --- 主对话的一个完美分叉，**共享 prompt cache**：

```typescript
const result = await runForkedAgent({
  promptMessages: [createUserMessage({ content: userPrompt })],
  cacheSafeParams,
  canUseTool,
  querySource: 'extract_memories',
  forkLabel: 'extract_memories',
  skipTranscript: true,   // 不记录到 transcript，避免和主线程竞争
  maxTurns: 5,            // 硬上限，防止验证兔子洞
})
```

分叉 agent 的关键约束：

- **工具权限**：Read/Grep/Glob 不受限；Bash 只允许只读命令；Edit/Write 只允许写 auto-memory 路径
- **轮次上限**：最多 5 轮。正常模式是 2-4 轮（第 1 轮并行读所有要改的文件，第 2 轮并行写）
- **不记录 transcript**：避免和主线程的写操作竞争

### 3.3 Cursor-based 增量处理

提取不是每次处理全部消息，而是用游标追踪上次处理到哪：

```typescript
// 闭包内的可变状态
let lastMemoryMessageUuid: string | undefined

function countModelVisibleMessagesSince(
  messages: Message[],
  sinceUuid: string | undefined,
): number {
  if (sinceUuid === null || sinceUuid === undefined) {
    return count(messages, isModelVisibleMessage)
  }
  let foundStart = false
  let n = 0
  for (const message of messages) {
    if (!foundStart) {
      if (message.uuid === sinceUuid) { foundStart = true }
      continue
    }
    if (isModelVisibleMessage(message)) { n++ }
  }
  // 游标 UUID 不存在（被 context compaction 删除）→ 回退到全量计数
  if (!foundStart) {
    return count(messages, isModelVisibleMessage)
  }
  return n
}
```

游标找不到时（context compaction 后消息被删除），回退到全量计数 --- **宁可多处理也不漏**。

### 3.4 互斥机制

主 agent 和提取 agent 不会同时写记忆：

```typescript
if (hasMemoryWritesSince(messages, lastMemoryMessageUuid)) {
  // 主 agent 已经写了 → 跳过，推进游标
  lastMemoryMessageUuid = lastMessage.uuid
  return
}
```

`hasMemoryWritesSince` 扫描游标之后的 assistant 消息，检查是否有 Edit/Write 工具调用写了 auto-memory 路径。如果主 agent 自己写了记忆，后台提取就跳过这个范围。

### 3.5 Overlap Guard + Trailing Run

防止并发，但不丢消息：

```typescript
let inProgress = false
let pendingContext: { context: REPLHookContext; ... } | undefined

// 如果正在运行，暂存最新上下文
if (inProgress) {
  pendingContext = { context, appendSystemMessage }
  return
}

// runExtraction 的 finally 块
finally {
  inProgress = false
  const trailing = pendingContext
  pendingContext = undefined
  if (trailing) {
    // trailing run 使用推进后的游标，只处理新增消息
    await runExtraction({ ...trailing, isTrailingRun: true })
  }
}
```

设计要点：`pendingContext` 只保留 **最新的**（覆盖旧的），因为最新上下文包含最多消息。trailing run 用的是更新过的游标，所以只处理两次调用之间新增的消息，不会重复。

### 3.6 提取 Prompt 的结构

```typescript
function opener(newMessageCount: number, existingMemories: string): string {
  return [
    `You are now acting as the memory extraction subagent.`,
    `Analyze the most recent ~${newMessageCount} messages above...`,
    `Available tools: Read, Grep, Glob, read-only Bash, Edit/Write for memory dir only.`,
    `You have a limited turn budget. Efficient strategy:`,
    `  turn 1 — parallel Read all files you might update`,
    `  turn 2 — parallel Write/Edit all changes`,
    // 预注入已有记忆目录清单
    existingMemories.length > 0
      ? `## Existing memory files\n${existingMemories}\nCheck before writing — update, don't duplicate.`
      : '',
  ].join('\n')
}
```

预注入 memory 目录清单（文件名 + frontmatter 摘要），省掉一轮 `ls` 调用。

### 3.7 记忆存储格式

每条记忆是一个独立 Markdown 文件，带 frontmatter：

```markdown
---
name: 用户偏好-简洁回复
description: 用户不喜欢冗长总结，直接给 diff
type: feedback
---

不要在回复末尾总结刚做了什么，用户可以自己看 diff。

**Why:** 用户明确说过 "stop summarizing, I can read the diff"
**How to apply:** 所有回复都省略末尾总结段落
```

存储路径：`~/.claude/projects/<sanitized-git-root>/memory/`

MEMORY.md 是索引文件（不是记忆本身），每行一个指针：`- [Title](file.md) — one-line hook`，200 行截断。

---

## 四、从零实现：自治 Agent 系统

理解了 Claude Code 的架构后，用 Python 搭一个简化版。核心思路保持一致：WORK/IDLE 双态循环 + 任务板自动认领。

### 4.1 两阶段生命周期

每个自治 Agent 有两个状态：

```
WORK 阶段：
  像普通 Agent 一样：LLM 调用工具，直到任务完成

IDLE 阶段：
  每 5 秒轮询一次：
    1. 检查收件箱（有新消息 → 进入 WORK）
    2. 扫描任务板（有可认领任务 → claim → 进入 WORK）
    3. 60 秒无活动 → SHUTDOWN
```

<div class="mermaid">
stateDiagram-v2
    [*] --> WORK: spawn
    WORK --> IDLE: 完成任务
    IDLE --> WORK: 收到消息或认领任务
    IDLE --> [*]: 60s 无活动
</div>

### 4.2 核心工具：idle 和 claim_task

**idle 工具**：Agent 完成任务后主动调用，告诉框架“我空了，可以接新任务”。

```python
def run_idle(agent_name: str) -> str:
    """进入 IDLE 状态，开始轮询"""
    _set_agent_status(agent_name, "IDLE")
    return f"Agent {agent_name} is now IDLE. Polling for new tasks..."
```

**claim_task 工具**：从任务板认领一个可用任务。

```python
def run_claim_task(agent_name: str) -> str:
    """从任务板认领一个 ready 状态的未认领任务"""
    ready_tasks = task_manager.list_ready()
    unclaimed = [t for t in ready_tasks if not t.get("claimed_by")]

    if not unclaimed:
        return "No unclaimed tasks available."

    # 认领第一个可用任务
    task = unclaimed[0]
    task["claimed_by"] = agent_name
    task["status"] = "in_progress"
    task_manager._save(task)

    return (f"Claimed task: {task['id']}\n"
            f"Title: {task['title']}\n"
            f"Description: {task['description']}")
```

### 4.3 IDLE 轮询循环

```python
import time

def idle_loop(agent_name: str, system_prompt: str):
    """IDLE 阶段：轮询收件箱和任务板"""
    idle_start = time.time()
    IDLE_TIMEOUT = 60  # 60 秒无活动则关机

    while True:
        # 1. 检查收件箱
        new_msgs = team.read_inbox(agent_name)
        if new_msgs != "No new messages.":
            print(f"[{agent_name}] Got messages, entering WORK")
            work_loop(agent_name, system_prompt,
                      f"收件箱新消息：\n{new_msgs}")
            idle_start = time.time()  # 重置超时计时
            continue

        # 2. 扫描任务板
        unclaimed = [t for t in task_manager.list_ready() if not t.get("claimed_by")]
        if unclaimed:
            task = unclaimed[0]
            print(f"[{agent_name}] Found unclaimed task {task['id']}, claiming")
            result = run_claim_task(agent_name)
            work_loop(agent_name, system_prompt,
                      f"认领到新任务：\n{result}")
            idle_start = time.time()
            continue

        # 3. 检查超时
        if time.time() - idle_start > IDLE_TIMEOUT:
            print(f"[{agent_name}] Idle timeout, shutting down")
            _set_agent_status(agent_name, "SHUTDOWN")
            return

        time.sleep(5)
```

### 4.4 WORK 循环

```python
def work_loop(agent_name: str, system_prompt: str, initial_message: str):
    """WORK 阶段：标准 Agent 循环"""
    _set_agent_status(agent_name, "WORKING")

    # 注入身份信息（防止 context compact 后遗忘身份）
    full_system = f"{system_prompt}\n\n你的名字是 {agent_name}。完成任务后调用 idle 工具进入待机状态。"

    messages = [{"role": "user", "content": initial_message}]

    for _ in range(50):  # 安全限制
        # 上下文压缩
        micro_compact(messages)
        if estimate_tokens(messages) > THRESHOLD:
            messages[:] = auto_compact(messages)
            # 压缩后重新注入身份
            messages.insert(0, {
                "role": "user",
                "content": f"[身份恢复] 你是 {agent_name}。{system_prompt}"
            })

        response = client.messages.create(
            model=MODEL, system=full_system,
            messages=messages, tools=AGENT_TOOLS, max_tokens=8000,
        )
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            break

        results = []
        idle_called = False
        for block in response.content:
            if block.type == "tool_use":
                if block.name == "idle":
                    idle_called = True
                    results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": run_idle(agent_name)
                    })
                else:
                    output = TOOL_HANDLERS.get(block.name, lambda **kw: "Unknown")(**block.input)
                    results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(output)
                    })
        messages.append({"role": "user", "content": results})

        if idle_called:
            break  # 退出 WORK，进入 IDLE
```

### 4.5 完整 Agent 入口

```python
def autonomous_agent(name: str, system_prompt: str, initial_task: str = None):
    """自治 Agent 的完整生命周期"""
    _set_agent_status(name, "WORKING")

    if initial_task:
        work_loop(name, system_prompt, initial_task)

    # 进入 IDLE 循环，等待新任务
    idle_loop(name, system_prompt)
```

### 4.6 自组织的完整流程

```
Leader：
  创建任务板：
    task_manager.create("实现登录 API", blocked_by=[])
    task_manager.create("实现注册 API", blocked_by=[])
    task_manager.create("集成测试", blocked_by=["task_001", "task_002"])

  启动团队：
    spawn("coder_1", "专注后端 API 开发")
    spawn("coder_2", "专注后端 API 开发")

自动发生：
  coder_1 → 认领 task_001（登录 API）→ 开始 WORK
  coder_2 → 认领 task_002（注册 API）→ 开始 WORK

  coder_1 完成 → 调用 idle() → 扫描任务板
  coder_2 完成 → 调用 idle() → 扫描任务板

  task_003 被自动解锁（task_001 + task_002 都完成）
  coder_1 认领 task_003（集成测试）→ 开始 WORK

  coder_2：60 秒无任务 → 自动关机
```

---

## 五、架构对比

| 维度 | Claude Code 真实架构 | 从零实现 |
|------|---------------------|---------|
| 调度模型 | Coordinator 主动分派 + Worker 异步回报 | IDLE 轮询 + 自动认领 |
| Worker 管理 | Agent/SendMessage/TaskStop 三件套 | spawn + 任务板 |
| 结果传递 | `<task-notification>` XML user-role 消息 | 收件箱消息 |
| 记忆提取 | forked agent + cursor-based 增量 + 互斥 | 无（可扩展） |
| 记忆整理 | Dream Task 后台运行 | 无（可扩展） |
| 工具权限 | canUseTool 函数精细控制 | 全量工具 |
| 并发控制 | overlap guard + trailing run | 轮询串行 |
| Prompt 管理 | 完整的合成指令（coordinator 理解后再委派） | 直接传递任务描述 |

Claude Code 的核心设计哲学：**Coordinator 不是传话筒，是理解者**。它读完 Worker 的研究报告后，要自己理解，然后写出包含具体文件路径、行号、修改方案的精确指令。

从零实现的版本更简单 --- Agent 自己扫任务板、自己认领 --- 适合理解自治 Agent 的基本机制。但要做到生产级别，需要补上 Claude Code 源码中展示的这些机制：增量处理、互斥写入、权限控制、优雅终止。

## 六、设计哲学：协调器是指挥家，不是演奏者

设计指南用一个精妙的比喻描述 Coordinator 模式：

> 协调器是多 Agent 系统的“指挥家”——它不演奏，但决定谁演奏什么。

这个比喻揭示了 Coordinator 的三个核心职责：

1. **理解全局**：读完所有 Worker 的报告后，Coordinator 自己消化理解，然后生成包含具体文件路径、行号、修改方案的精确指令——而不是简单转发用户的原始请求
2. **选择合适的演奏者**：Explore Agent 做只读分析，Plan Agent 做方案设计，general-purpose Agent 做实际修改——不同任务分配给不同专业能力的 Agent
3. **整合最终结果**：收集各 Agent 的输出，综合成用户需要的完整答案

设计指南将这种模式提升为一个通用工程原则：**复杂系统的管理本身也需要专门的角色**。不是每个团队成员都应该做调度，也不是调度者应该亲自执行。这和软件架构中的“关注点分离”一脉相承。

从源码中还能看到一个重要的设计决策：Coordinator 通过 **feature flag 双重门控** 启用，而且有 **session mode 恢复** 机制。这意味着：
- 新功能默认关闭，验证充分后再开放（安全是默认）
- 用户中途切换模式时，系统能优雅地恢复到正确状态（为失败设计）

---

下一篇：[Worktree 隔离：多 Agent 并行不踩踏](../12-worktree-isolation/index.html)
