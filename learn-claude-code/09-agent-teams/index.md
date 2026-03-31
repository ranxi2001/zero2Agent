---
layout: default
title: Agent Teams：多 Agent 协作
description: 文件消息总线——持久化身份、收件箱、跨对话通信
eyebrow: Claude Code / s09
---

# Agent Teams：多 Agent 协作

s04 的 Subagent 是一次性的：没有持久身份，不能跨对话通信，任务结束就消失。

这一节实现真正的 Agent 团队：每个成员有固定身份，有自己的收件箱，成员之间可以发消息，团队状态持久化在磁盘上。

---

## 1 | TeamCreate：团队是怎么诞生的

### 源码实证

`TeamCreateTool` 是整个团队系统的入口。看它的 `call()` 方法：

```typescript
// src/tools/TeamCreateTool/TeamCreateTool.ts

// 输入 schema — 只需要三个字段
const inputSchema = z.strictObject({
  team_name: z.string(),
  description: z.string().optional(),
  agent_type: z.string().optional(),
})

// call() 核心流程 ——
async call(input, context) {
  const { setAppState, getAppState } = context

  // ① 一个 leader 只能管一个 team
  const existingTeam = appState.teamContext?.teamName
  if (existingTeam) {
    throw new Error(
      `Already leading team "${existingTeam}". Use TeamDelete first.`
    )
  }

  // ② 如果名字冲突，自动生成唯一名
  const finalTeamName = generateUniqueTeamName(team_name)

  // ③ 确定性 agent ID：格式 "team-lead@{teamName}"
  const leadAgentId = formatAgentId(TEAM_LEAD_NAME, finalTeamName)

  // ④ 写 TeamFile — 初始只有 lead 一个成员
  const teamFile: TeamFile = {
    name: finalTeamName,
    createdAt: Date.now(),
    leadAgentId,
    leadSessionId: getSessionId(),
    members: [{
      agentId: leadAgentId,
      name: TEAM_LEAD_NAME,
      agentType: leadAgentType,
      model: leadModel,
      joinedAt: Date.now(),
      cwd: getCwd(),
      subscriptions: [],
    }],
  }
  await writeTeamFileAsync(finalTeamName, teamFile)

  // ⑤ 注册 session 清理（防止磁盘残留，gh-32730 修复）
  registerTeamForSessionCleanup(finalTeamName)

  // ⑥ 重置任务列表：Team = Project = TaskList
  await resetTaskList(sanitizeName(finalTeamName))

  // ⑦ 更新全局 AppState
  setAppState(prev => ({
    ...prev,
    teamContext: {
      teamName: finalTeamName,
      teamFilePath,
      leadAgentId,
      teammates: { [leadAgentId]: { name: TEAM_LEAD_NAME, ... } },
    },
  }))
}
```

关键设计决策：

| 决策 | 原因 |
|------|------|
| 确定性 ID（`team-lead@teamName`） | leader 的 ID 可以被任意 teammate 推算出来，不需要查询 |
| `leadSessionId` 存真实 session ID | 用于跨 session 团队发现 |
| `registerTeamForSessionCleanup` | gh-32730 修复：之前团队文件永远留在磁盘上 |
| `resetTaskList` | 每个新团队任务编号从 1 开始 |
| leader 不设 `CLAUDE_CODE_AGENT_ID` 环境变量 | `isTeammate()` 对 leader 应返回 false，否则会错误触发收件箱轮询 |

### 从零实现

```python
import json, threading, time, uuid
from pathlib import Path
from datetime import datetime

TEAM_DIR = Path(".team")
INBOX_DIR = TEAM_DIR / "inbox"
CONFIG_PATH = TEAM_DIR / "config.json"
TEAM_DIR.mkdir(exist_ok=True)
INBOX_DIR.mkdir(exist_ok=True)

class TeammateManager:
    def __init__(self):
        self._active_team: str | None = None   # 同 Claude Code：一个 leader 只管一个 team

    def create_team(self, team_name: str, description: str = "") -> str:
        """对应 TeamCreateTool.call()"""
        if self._active_team:
            return f"Already leading team '{self._active_team}'. Delete it first."

        config = self._load_config()
        if config.get("members"):
            # 名字冲突时自动加后缀（对应 generateUniqueTeamName）
            team_name = f"{team_name}-{uuid.uuid4().hex[:6]}"

        # 确定性 lead ID
        lead_id = f"team-lead@{team_name}"

        config = {
            "team_name": team_name,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "lead_agent_id": lead_id,
            "members": {
                "team-lead": {
                    "agent_id": lead_id,
                    "status": "IDLE",
                    "system_prompt": "你是团队 leader，负责分解任务并分配给成员。",
                    "started_at": datetime.now().isoformat(),
                }
            }
        }
        self._save_config(config)
        self._active_team = team_name

        # 确保 leader 收件箱存在
        (INBOX_DIR / "team-lead.jsonl").touch()
        return f"Team '{team_name}' created. Lead ID: {lead_id}"

    def spawn(self, name: str, system_prompt: str) -> str:
        """启动一个新 Agent 成员"""
        config = self._load_config()
        if name in config.get("members", {}):
            return f"Agent '{name}' already exists"

        team_name = config.get("team_name", "default")
        agent_id = f"{name}@{team_name}"  # 确定性 ID

        config.setdefault("members", {})[name] = {
            "agent_id": agent_id,
            "status": "WORKING",
            "system_prompt": system_prompt,
            "started_at": datetime.now().isoformat(),
        }
        self._save_config(config)

        inbox_path = INBOX_DIR / f"{name}.jsonl"
        if not inbox_path.exists():
            inbox_path.touch()

        thread = threading.Thread(
            target=self._run_agent,
            args=(name, system_prompt),
            daemon=True
        )
        thread.start()
        return f"Spawned agent: {name} (id: {agent_id})"

    def send(self, to: str, message: str, sender: str = "user",
             summary: str | None = None) -> str:
        """发送消息到指定 Agent 的收件箱"""
        inbox = INBOX_DIR / f"{to}.jsonl"
        if not inbox.exists():
            return f"Agent '{to}' not found"
        entry = json.dumps({
            "from": sender,
            "message": message,
            "summary": summary,          # 同源码：summary 用于 UI 预览
            "timestamp": datetime.now().isoformat(),
            "read": False,
        })
        with open(inbox, "a") as f:
            f.write(entry + "\n")
        return f"Message sent to {to}"

    def read_inbox(self, agent_name: str) -> str:
        """读取并标记收件箱中的未读消息"""
        inbox = INBOX_DIR / f"{agent_name}.jsonl"
        if not inbox.exists():
            return "No messages."
        lines = inbox.read_text().splitlines()
        unread = []
        updated = []
        for line in lines:
            if not line.strip():
                continue
            msg = json.loads(line)
            if not msg.get("read"):
                unread.append(f"[{msg['from']}]: {msg['message']}")
                msg["read"] = True
            updated.append(json.dumps(msg))
        inbox.write_text("\n".join(updated) + "\n" if updated else "")
        return "\n".join(unread) if unread else "No new messages."

    def status(self) -> str:
        config = self._load_config()
        members = config.get("members", {})
        if not members:
            return "No team members."
        lines = []
        for name, info in members.items():
            lines.append(f"- {name}: {info['status']}")
        return "\n".join(lines)

    def _run_agent(self, name: str, system_prompt: str):
        while True:
            new_msgs = self.read_inbox(name)
            if new_msgs != "No new messages.":
                self._process_as_agent(name, system_prompt, new_msgs)
                self._set_status(name, "IDLE")
            time.sleep(5)

    def _process_as_agent(self, name: str, system_prompt: str, inbox_content: str):
        self._set_status(name, "WORKING")
        messages = [{
            "role": "user",
            "content": f"你是 {name}。你的收件箱有新消息：\n\n{inbox_content}"
        }]
        # ... 标准 agent_loop 逻辑 ...

    def _load_config(self) -> dict:
        if CONFIG_PATH.exists():
            return json.loads(CONFIG_PATH.read_text())
        return {"members": {}}

    def _save_config(self, config: dict):
        CONFIG_PATH.write_text(json.dumps(config, indent=2))

    def _set_status(self, name: str, status: str):
        config = self._load_config()
        if name in config.get("members", {}):
            config["members"][name]["status"] = status
            self._save_config(config)
```

---

## 2 | InProcessTeammateTask：Teammate 的状态模型

### 源码实证

Teammate 不是一个独立进程，而是同一个 Node.js 进程内的一个 Task。它的完整状态定义在 `types.ts`：

```typescript
// src/tasks/InProcessTeammateTask/types.ts

// Teammate 的身份——存在 AppState 里，不依赖 AsyncLocalStorage
type TeammateIdentity = {
  agentId: string          // "researcher@my-team"
  agentName: string        // "researcher"
  teamName: string
  color?: string
  planModeRequired: boolean
  parentSessionId: string  // leader 的 session ID
}

type InProcessTeammateTaskState = TaskStateBase & {
  type: 'in_process_teammate'

  identity: TeammateIdentity

  // 执行相关
  prompt: string
  model?: string
  selectedAgent?: AgentDefinition
  abortController?: AbortController   // 杀死整个 teammate
  currentWorkAbortController?: AbortController  // 只中断当前 turn

  // Plan mode
  awaitingPlanApproval: boolean
  permissionMode: PermissionMode

  // 对话历史（仅用于 zoomed view）
  messages?: Message[]

  // 消息队列——mid-turn 到达的消息先入队
  pendingUserMessages: string[]

  // 生命周期
  isIdle: boolean
  shutdownRequested: boolean
  onIdleCallbacks?: Array<() => void>  // leader 等待 teammate idle 的回调

  // 进度追踪（用于通知增量）
  lastReportedToolCount: number
  lastReportedTokenCount: number
}
```

**50 条消息 UI 上限**——这个数字背后有一个真实事故：

```typescript
// src/tasks/InProcessTeammateTask/types.ts

/**
 * BQ analysis (round 9, 2026-03-20):
 * ~20MB RSS per agent at 500+ turn sessions
 * ~125MB per concurrent agent in swarm bursts
 * Whale session 9a990de8 launched 292 agents in 2 minutes → 36.8GB
 * The dominant cost is this array holding a second full copy of every message.
 */
export const TEAMMATE_MESSAGES_UI_CAP = 50

export function appendCappedMessage<T>(
  prev: readonly T[] | undefined,
  item: T,
): T[] {
  if (prev === undefined || prev.length === 0) return [item]
  if (prev.length >= TEAMMATE_MESSAGES_UI_CAP) {
    const next = prev.slice(-(TEAMMATE_MESSAGES_UI_CAP - 1))
    next.push(item)
    return next
  }
  return [...prev, item]
}
```

这段注释本身就是一份事故报告：某用户在 2 分钟内创建了 292 个 agent，每个 agent 的 `messages[]` 数组保存了完整对话历史的副本，总内存飙到 36.8GB。修复方案是只在 UI 层保留最近 50 条消息，完整对话存在磁盘上。

关键状态字段解读：

| 字段 | 作用 |
|------|------|
| `pendingUserMessages[]` | mid-turn 消息队列：teammate 正在执行工具时收到的消息，等当前 tool round 结束后再处理 |
| `isIdle` | 空闲标志。空闲 ≠ 死亡，空闲的 teammate 收到消息会自动恢复 |
| `shutdownRequested` | 收到 shutdown_request 后置 true，teammate 完成当前工作再退出 |
| `onIdleCallbacks` | leader 不轮询，而是注册回调等待 teammate 变空闲 |
| `abortController` vs `currentWorkAbortController` | 两级中断：前者杀死整个 teammate，后者只中断当前 turn |
| `parentSessionId` | leader 的 session ID，用于跨 session 消息路由 |

---

## 3 | SendMessage：消息路由的三条路径

### 源码实证

`SendMessageTool` 是团队通信的枢纽。它的 `call()` 方法根据 `to` 字段的值走三条完全不同的路径：

```
to = "researcher"       → 同进程路由（writeToMailbox / queuePendingMessage）
to = "*"                → 广播（遍历 teamFile.members）
to = "uds:/path.sock"   → Unix Domain Socket 跨 session
to = "bridge:session_…" → Remote Control 跨机器
```

**路径 1：同进程 teammate**

```typescript
// src/tools/SendMessageTool/SendMessageTool.ts — call() 内部

if (typeof input.message === 'string' && input.to !== '*') {
  const registered = appState.agentNameRegistry.get(input.to)
  const agentId = registered ?? toAgentId(input.to)
  const task = appState.tasks[agentId]

  if (isLocalAgentTask(task) && !isMainSessionTask(task)) {
    if (task.status === 'running') {
      // ① 正在运行——消息入 pending 队列
      queuePendingMessage(agentId, input.message, context.setAppState)
      return { data: { success: true, message: 'Message queued...' } }
    }
    // ② 已停止——自动恢复
    const result = await resumeAgentBackground({
      agentId,
      prompt: input.message,
      ...
    })
    return { data: { success: true, message: `Agent resumed...` } }
  }
}
```

核心行为：给运行中的 teammate 发消息不会打断它，消息进 `pendingUserMessages[]` 队列；给已停止的 teammate 发消息会自动唤醒它。

**路径 2：广播**

```typescript
// handleBroadcast — 遍历 teamFile.members，跳过自己
const recipients: string[] = []
for (const member of teamFile.members) {
  if (member.name.toLowerCase() === senderName.toLowerCase()) continue
  recipients.push(member.name)
}
for (const recipientName of recipients) {
  await writeToMailbox(recipientName, { from: senderName, text: content, ... }, teamName)
}
```

广播开销与团队大小成正比（O(n)），所以 prompt 里明确标注"expensive, use only when everyone genuinely needs it"。

**结构化消息类型**

不是所有消息都是纯文本。`SendMessageTool` 定义了三种结构化消息类型：

```typescript
const StructuredMessage = z.discriminatedUnion('type', [
  z.object({
    type: z.literal('shutdown_request'),
    reason: z.string().optional(),
  }),
  z.object({
    type: z.literal('shutdown_response'),
    request_id: z.string(),
    approve: semanticBoolean(),    // "yes"/"no"/"true"/"false" 都能识别
    reason: z.string().optional(),
  }),
  z.object({
    type: z.literal('plan_approval_response'),
    request_id: z.string(),
    approve: semanticBoolean(),
    feedback: z.string().optional(),
  }),
])
```

验证规则也很严格：
- `shutdown_response` 必须发给 `team-lead`（不能发给其他 teammate）
- 拒绝 shutdown 时 `reason` 必填
- 结构化消息不能广播（`to: "*"` 不允许）
- 结构化消息不能跨 session 发送（只有纯文本可以走 UDS/bridge）
- 纯文本消息必须带 `summary`（5-10 字，用于 UI 预览）

**关机协议的完整流程**

```typescript
// handleShutdownApproval — teammate 同意关机

// ① 发确认消息给 team-lead
await writeToMailbox(TEAM_LEAD_NAME, {
  from: agentName,
  text: jsonStringify(approvedMessage),  // 包含 paneId, backendType
  ...
}, teamName)

// ② 根据后端类型选择退出方式
if (ownBackendType === 'in-process') {
  // 同进程：abort controller
  const task = findTeammateTaskByAgentId(agentId, appState.tasks)
  task.abortController.abort()
} else {
  // 外部进程：graceful shutdown
  setImmediate(async () => {
    await gracefulShutdown(0, 'other')
  })
}
```

### 从零实现

```python
team = TeammateManager()

TOOL_HANDLERS["create_team"] = lambda **kw: team.create_team(kw["team_name"], kw.get("description", ""))
TOOL_HANDLERS["spawn"]       = lambda **kw: team.spawn(kw["name"], kw["system_prompt"])
TOOL_HANDLERS["send"]        = lambda **kw: team.send(kw["to"], kw["message"],
                                                       kw.get("from", "leader"),
                                                       kw.get("summary"))
TOOL_HANDLERS["read_inbox"]  = lambda **kw: team.read_inbox(kw["agent_name"])
```

---

## 4 | Agent 生命周期

源码中的状态机比我们想象的简单——只有两个核心布尔值 `isIdle` 和 `shutdownRequested`：

<div class="mermaid">
stateDiagram-v2
    [*] --> WORKING: spawn（isIdle=false）
    WORKING --> IDLE: turn 结束（isIdle=true, 触发 onIdleCallbacks）
    IDLE --> WORKING: 收到消息（auto-resume）
    WORKING --> IDLE: 等待 plan approval（awaitingPlanApproval=true）
    IDLE --> SHUTDOWN_PENDING: shutdown_request（shutdownRequested=true）
    SHUTDOWN_PENDING --> [*]: shutdown_response approve=true（abortController.abort()）
    SHUTDOWN_PENDING --> WORKING: shutdown_response approve=false
</div>

---

## 5 | 典型协作流程

结合源码，一次完整的团队协作：

```
① TeamCreate("coding-team")
   → teamFile 写入 ~/.claude/teams/coding-team/config.json
   → lead_agent_id = "team-lead@coding-team"
   → resetTaskList("coding-team")

② Agent("researcher", team_name="coding-team")
   → InProcessTeammateTask 启动
   → identity.agentId = "researcher@coding-team"
   → identity.parentSessionId = leader 的 session ID

③ SendMessage(to="researcher", message="分析 auth 模块", summary="analyze auth")
   → appState.tasks["researcher@coding-team"].status === "running"
   → queuePendingMessage()（如果正在执行工具）
   → 或 writeToMailbox()（如果在等待消息）

④ researcher 完成工作
   → SendMessage(to="team-lead", message="分析完成，发现 3 个问题", summary="analysis done")
   → isIdle = true
   → onIdleCallbacks 通知 leader

⑤ SendMessage(to="researcher", message={"type": "shutdown_request"})
   → researcher 收到，shutdownRequested = true
   → SendMessage(to="team-lead", message={"type": "shutdown_response",
       "request_id": "...", "approve": true})
   → abortController.abort()
```

---

## 6 | 与 Subagent 的区别

| 特性 | Subagent (s04) | Agent Teams (s09) |
|------|----------------|-------------------|
| 身份 | 一次性 | 持久（`name@teamName` 确定性 ID） |
| 通信 | 无（只返回结果）| 双向消息（mailbox + pending queue） |
| 并发 | 否 | 是（同进程 Task / tmux / UDS） |
| 跨对话 | 否 | 是（TeamFile 持久化 + bridge） |
| 协调 | 父 Agent | 消息驱动 + TaskList |
| 内存保护 | 无 | 50 条 UI cap（36.8GB 事故后修复） |
| 关机 | 自动 | 协议驱动（request → response → abort） |

---

## 7 | 设计洞察

从源码中可以提炼出几个值得记住的架构决策：

**消息队列 vs 直接调用**——teammate 正在执行时收到的消息不会打断它，而是进入 `pendingUserMessages[]`。这避免了并发竞争，同时保证消息不丢失。

**两级 AbortController**——`abortController` 杀死整个 teammate，`currentWorkAbortController` 只中断当前 turn。这让"取消当前操作"和"彻底关闭"成为两个独立操作。

**leader 不是 teammate**——leader 故意不设置 `CLAUDE_CODE_AGENT_ID`，这样 `isTeammate()` 返回 false。leader 不参与收件箱轮询，它通过 `onIdleCallbacks` 被动接收通知。

**确定性 ID**——`formatAgentId(name, teamName)` 生成的 ID 是可推算的。任何 teammate 都能计算出 team-lead 的 ID 而不需要查询，减少了一次文件读取。

## 8 | 设计哲学：可观察性驱动的多 Agent 架构

设计指南指出，多 Agent 系统最大的挑战不是通信，而是**可观察性**——当多个 Agent 并行工作时，如何知道谁在做什么？

Claude Code 的解决方案层层叠加：

**颜色系统**：每个 Agent 分配唯一颜色（蓝、绿、黄、红、青、品红、白），UI 中不同 Agent 的输出一目了然。这个小细节对调试至关重要。

**确定性 ID**：`formatAgentId(name, teamName)` 生成可推算的 ID，不需要查询就能计算任意 teammate 的地址。减少了一次文件读取，也让日志更易追踪。

**资源限制**：`maxTurns`、`maxBudgetUsd`、50 条消息 UI cap——这些不只是安全措施，也是可观察性工具。当一个 Agent 达到限制时，系统知道出了问题。

**两级 AbortController**：区分"取消当前操作"和"彻底关闭"。这让人类操作员有精细的控制粒度，而不是只能全杀或全不杀。

设计指南总结的原则是：**在能力和控制之间取得平衡**。多 Agent 系统很强大，但如果人类无法理解和干预，强大就变成了危险。

---

下一篇：[Team Protocols：结构化通信协议](../10-team-protocols/index.html)
