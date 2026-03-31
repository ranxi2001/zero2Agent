---
layout: default
title: Team Protocols：结构化通信协议
description: 请求-响应握手——关机协议和计划审批协议，防止 Agent 自行其是
eyebrow: Claude Code / s10
---

# Team Protocols：结构化通信协议

s09 的 Agent 团队可以互发消息，但消息是非结构化的——任意文本，没有固定格式，没有确认机制。

这一节在消息总线上加协议：**请求-响应握手**，用唯一 request_id 追踪每个请求的状态。

---

## 为什么需要协议

两个场景暴露了非结构化通信的问题：

**场景 1：关机**

Leader 发 "请关机" → Coder 可能正在执行重要任务，直接关掉会丢失工作。需要一个询问-确认流程。

**场景 2：危险操作**

Coder 要执行 `rm -rf src/`。这种危险操作需要 Leader 审批，不能自行决定。

这两个场景都需要：发出请求 → 等待批准/拒绝 → 根据结果执行。

---

## 源码实证：SendMessageTool 的结构化消息

Claude Code 的 `SendMessage` 工具不只是发文本——它用 Zod discriminated union 定义了三种**结构化消息类型**，这就是内置的协议层。

### 消息类型定义

源码位于 `src/tools/SendMessageTool/SendMessageTool.ts`：

```typescript
// SendMessageTool.ts — StructuredMessage schema
const StructuredMessage = lazySchema(() =>
  z.discriminatedUnion('type', [
    z.object({
      type: z.literal('shutdown_request'),
      reason: z.string().optional(),
    }),
    z.object({
      type: z.literal('shutdown_response'),
      request_id: z.string(),
      approve: semanticBoolean(),  // true/false 语义布尔
      reason: z.string().optional(),
    }),
    z.object({
      type: z.literal('plan_approval_response'),
      request_id: z.string(),
      approve: semanticBoolean(),
      feedback: z.string().optional(),
    }),
  ]),
)
```

关键设计：`message` 字段是 `z.union([z.string(), StructuredMessage])`——普通文本和协议消息走同一个工具，用类型区分。

### 输入验证规则

源码中有严格的验证约束：

```typescript
// validateInput 片段
if (input.message.type === 'shutdown_response' && input.to !== TEAM_LEAD_NAME) {
  return { result: false, message: `shutdown_response must be sent to "team-lead"` }
}
if (input.message.type === 'shutdown_response' && !input.message.approve
    && (!input.message.reason || input.message.reason.trim().length === 0)) {
  return { result: false, message: 'reason is required when rejecting a shutdown request' }
}
if (input.to === '*') {
  return { result: false, message: 'structured messages cannot be broadcast (to: "*")' }
}
```

三条硬约束：
1. **shutdown_response 必须发给 team-lead**——不能发给其他 agent
2. **拒绝关机必须给出理由**——空理由被拒绝
3. **结构化消息不能广播**——只能点对点

---

## 源码实证：协议的路由分发

`SendMessageTool.call()` 中用 switch 分发结构化消息：

```typescript
// SendMessageTool.ts — call() 路由逻辑
switch (input.message.type) {
  case 'shutdown_request':
    return handleShutdownRequest(input.to, input.message.reason, context)
  case 'shutdown_response':
    if (input.message.approve) {
      return handleShutdownApproval(input.message.request_id, context)
    }
    return handleShutdownRejection(input.message.request_id, input.message.reason!)
  case 'plan_approval_response':
    if (input.message.approve) {
      return handlePlanApproval(input.to, input.message.request_id, context)
    }
    return handlePlanRejection(
      input.to, input.message.request_id,
      input.message.feedback ?? 'Plan needs revision', context,
    )
}
```

每种消息类型映射到独立的 handler 函数。这就是协议的核心——**类型驱动分发**。

---

## 关机协议的完整流程

### 请求阶段

`handleShutdownRequest` 生成唯一 request_id，写入 mailbox：

```typescript
async function handleShutdownRequest(targetName, reason, context) {
  const requestId = generateRequestId('shutdown', targetName)
  const shutdownMessage = createShutdownRequestMessage({
    requestId, from: senderName, reason,
  })
  await writeToMailbox(targetName, {
    from: senderName,
    text: jsonStringify(shutdownMessage),
    timestamp: new Date().toISOString(),
  }, teamName)
  return {
    data: { success: true, request_id: requestId, target: targetName,
            message: `Shutdown request sent to ${targetName}. Request ID: ${requestId}` }
  }
}
```

### 批准阶段

`handleShutdownApproval` 做两件事——通知 team-lead 并终止自身进程：

```typescript
async function handleShutdownApproval(requestId, context) {
  // 1. 发确认消息给 team-lead
  await writeToMailbox(TEAM_LEAD_NAME, {
    from: agentName,
    text: jsonStringify(approvedMessage),
    timestamp: new Date().toISOString(),
  }, teamName)

  // 2. 终止自身
  if (ownBackendType === 'in-process') {
    // 进程内 agent：abort controller
    task.abortController.abort()
  } else {
    // 独立进程 agent：graceful shutdown
    setImmediate(async () => { await gracefulShutdown(0, 'other') })
  }
}
```

### 拒绝阶段

拒绝时只通知 team-lead，不终止自身——继续工作：

```typescript
async function handleShutdownRejection(requestId, reason) {
  await writeToMailbox(TEAM_LEAD_NAME, {
    from: agentName,
    text: jsonStringify(rejectedMessage),
    timestamp: new Date().toISOString(),
  }, teamName)
  return {
    data: { success: true, request_id: requestId,
            message: `Shutdown rejected. Reason: "${reason}". Continuing to work.` }
  }
}
```

<div class="mermaid">
sequenceDiagram
    Leader->>Coder: shutdown_request (reason, request_id)
    Note over Coder: 检查当前状态
    alt approve
        Coder->>Leader: shutdown_response (approve: true)
        Note over Coder: abort / gracefulShutdown
    else reject
        Coder->>Leader: shutdown_response (approve: false, reason: "...")
        Note over Coder: 继续工作
    end
</div>

---

## 计划审批协议

### 权限控制

只有 team-lead 可以审批计划——源码有硬检查：

```typescript
async function handlePlanApproval(recipientName, requestId, context) {
  if (!isTeamLead(appState.teamContext)) {
    throw new Error('Only the team lead can approve plans.')
  }

  // 审批时继承 leader 的权限模式
  const leaderMode = appState.toolPermissionContext.mode
  const modeToInherit = leaderMode === 'plan' ? 'default' : leaderMode

  const approvalResponse = {
    type: 'plan_approval_response',
    requestId,
    approved: true,
    permissionMode: modeToInherit,  // 权限继承
    timestamp: new Date().toISOString(),
  }
  await writeToMailbox(recipientName, { ... }, teamName)
}
```

注意 `permissionMode: modeToInherit`——审批不只是 "同意"，还传递了执行权限级别。

<div class="mermaid">
sequenceDiagram
    Coder->>Leader: plan_approval_request (plan, request_id)
    Note over Leader: 审查计划 + isTeamLead 检查
    alt approve
        Leader->>Coder: plan_approval_response (approve: true, permissionMode)
        Note over Coder: 以继承的权限执行
    else reject
        Leader->>Coder: plan_approval_response (approve: false, feedback: "...")
        Note over Coder: 根据 feedback 修改计划
    end
</div>

---

## 源码实证：Task 完成通知的 XML 格式

协议不止 agent 间通信。Coordinator 模式下，Worker 完成后用 XML 格式通知 Coordinator——这是另一个协议。

源码位于 `src/tasks/LocalAgentTask/LocalAgentTask.tsx`：

```typescript
// enqueueAgentNotification — 构建 task-notification XML
const message = `<task-notification>
<task-id>${taskId}</task-id>${toolUseIdLine}
<output-file>${outputPath}</output-file>
<status>${status}</status>
<summary>${summary}</summary>${resultSection}${usageSection}${worktreeSection}
</task-notification>`

enqueuePendingNotification({ value: message, mode: 'task-notification' })
```

完整的 XML 结构：

```xml
<task-notification>
  <task-id>agent-a1b2c3</task-id>
  <tool-use-id>toolu_xyz</tool-use-id>
  <output-file>/path/to/output</output-file>
  <status>completed</status>               <!-- completed | failed | killed -->
  <summary>Agent "Fix auth bug" completed</summary>
  <result>Found and fixed null pointer...</result>  <!-- optional -->
  <usage>                                            <!-- optional -->
    <total_tokens>15000</total_tokens>
    <tool_uses>8</tool_uses>
    <duration_ms>45000</duration_ms>
  </usage>
  <worktree>                                         <!-- optional -->
    <worktreePath>/path/to/worktree</worktreePath>
    <worktreeBranch>fix/auth-bug</worktreeBranch>
  </worktree>
</task-notification>
```

status 的生成逻辑：

```typescript
const summary =
  status === 'completed' ? `Agent "${description}" completed`
  : status === 'failed'  ? `Agent "${description}" failed: ${error || 'Unknown error'}`
  : `Agent "${description}" was stopped`
```

这个通知会作为 user-role message 注入 coordinator 的对话中——coordinator 的 system prompt 明确说明了如何区分：

> Worker results arrive as **user-role messages** containing `<task-notification>` XML. They look like user messages but are not.

---

## 源码实证：Coordinator 的协议规则

`src/coordinator/coordinatorMode.ts` 中的 `getCoordinatorSystemPrompt()` 定义了 coordinator 的行为准则：

### 核心规则

```typescript
// coordinatorMode.ts — system prompt 片段

// 规则 1：必须先理解再指挥
"When workers report research findings, you must understand them
 before directing follow-up work."

// 规则 2：禁止懒惰委派
"Never write 'based on your findings' or 'based on the research.'
 These phrases delegate understanding to the worker."

// 规则 3：Continue vs Spawn 决策
// 高上下文重叠 → SendMessage continue
// 低上下文重叠 → 新建 Agent
"High overlap -> continue. Low overlap -> spawn fresh."

// 规则 4：并行是超能力
"Parallelism is your superpower. Launch independent workers
 concurrently whenever possible."
```

### Continue vs Spawn 决策表

来自 coordinator system prompt 原文：

| 场景 | 机制 | 原因 |
|------|------|------|
| 研究探索的文件正是要编辑的 | **Continue**（SendMessage） | worker 已有文件上下文 |
| 研究范围大但实现范围小 | **Spawn fresh**（Agent） | 避免探索噪声 |
| 纠正失败或扩展近期工作 | **Continue** | worker 有错误上下文 |
| 验证另一个 worker 的代码 | **Spawn fresh** | 验证者需要新鲜视角 |
| 首次实现用了错误方法 | **Spawn fresh** | 错误上下文会污染重试 |

---

## 从零实现：ProtocolManager

理解了源码中的协议设计后，我们用 Python 实现一个等价的协议管理器。

### 有限状态机

每个协议请求有三个状态：

```
pending → approved
       → rejected
```

用共享文件追踪：

```
.team/
  protocols/
    shutdown_req_abc123.json   ← 关机请求
    plan_req_def456.json       ← 计划审批请求
```

```json
{
  "request_id": "shutdown_req_abc123",
  "type": "shutdown",
  "from": "leader",
  "to": "coder",
  "status": "pending",
  "message": "任务完成，请准备关机",
  "created_at": "2025-01-01T10:00:00",
  "resolved_at": null,
  "resolution": null
}
```

### 完整实现

```python
import json, uuid
from pathlib import Path
from datetime import datetime

PROTOCOL_DIR = Path(".team/protocols")
PROTOCOL_DIR.mkdir(parents=True, exist_ok=True)

class ProtocolManager:
    def request_shutdown(self, target: str, requester: str, reason: str = "") -> str:
        req_id = f"shutdown_{uuid.uuid4().hex[:8]}"
        self._create_request(req_id, "shutdown", requester, target,
                             f"请求关机。原因：{reason}")
        # 发消息通知目标 Agent
        team.send(target, f"[协议请求] shutdown\nrequest_id: {req_id}\n{reason}",
                  sender=requester)
        return f"Shutdown request sent: {req_id}"

    def request_plan_approval(self, plan: str, requester: str, approver: str) -> str:
        req_id = f"plan_{uuid.uuid4().hex[:8]}"
        self._create_request(req_id, "plan_approval", requester, approver, plan)
        team.send(approver, f"[协议请求] plan_approval\nrequest_id: {req_id}\n计划内容：{plan}",
                  sender=requester)
        return f"Plan approval request sent: {req_id}"

    def approve(self, request_id: str, approver: str, comment: str = "") -> str:
        return self._resolve(request_id, "approved", approver, comment)

    def reject(self, request_id: str, rejector: str, reason: str = "") -> str:
        return self._resolve(request_id, "rejected", rejector, reason)

    def check_status(self, request_id: str) -> str:
        req = self._load(request_id)
        if not req:
            return f"Request {request_id} not found"
        return (f"Request: {request_id}\n"
                f"Type: {req['type']}\n"
                f"Status: {req['status']}\n"
                f"Resolution: {req.get('resolution', '')}")

    def _create_request(self, req_id: str, req_type: str,
                         from_: str, to: str, message: str):
        req = {
            "request_id": req_id,
            "type": req_type,
            "from": from_,
            "to": to,
            "status": "pending",
            "message": message,
            "created_at": datetime.now().isoformat(),
            "resolved_at": None,
            "resolution": None,
        }
        (PROTOCOL_DIR / f"{req_id}.json").write_text(json.dumps(req, indent=2))

    def _resolve(self, request_id: str, status: str, resolver: str, comment: str) -> str:
        req = self._load(request_id)
        if not req:
            return f"Request {request_id} not found"
        req["status"] = status
        req["resolved_at"] = datetime.now().isoformat()
        req["resolution"] = comment
        (PROTOCOL_DIR / f"{request_id}.json").write_text(json.dumps(req, indent=2))
        # 通知请求方
        team.send(req["from"],
                  f"[协议响应] {request_id}\n结果：{status}\n备注：{comment}",
                  sender=resolver)
        return f"Request {request_id} {status}"

    def _load(self, request_id: str) -> dict | None:
        path = PROTOCOL_DIR / f"{request_id}.json"
        return json.loads(path.read_text()) if path.exists() else None
```

---

## 工具接口

```python
protocol = ProtocolManager()

TOOL_HANDLERS.update({
    "request_shutdown":      lambda **kw: protocol.request_shutdown(**kw),
    "request_plan_approval": lambda **kw: protocol.request_plan_approval(**kw),
    "approve_request":       lambda **kw: protocol.approve(**kw),
    "reject_request":        lambda **kw: protocol.reject(**kw),
    "check_protocol":        lambda **kw: protocol.check_status(kw["request_id"]),
})
```

---

## 源码 vs 我们的实现

| 维度 | Claude Code 源码 | 我们的 ProtocolManager |
|------|------------------|----------------------|
| 消息类型 | Zod discriminated union（编译时校验） | JSON 字符串 + 运行时检查 |
| 状态存储 | mailbox 文件 + AppState 内存 | 独立 JSON 文件 |
| 验证约束 | `validateInput` 硬编码规则 | `_resolve` 中简单检查 |
| 关机执行 | abort controller / gracefulShutdown | 外部逻辑处理 |
| 权限继承 | `permissionMode: modeToInherit` | 不支持 |
| 通知格式 | XML `<task-notification>` | 纯文本消息 |

核心差异：Claude Code 的协议和工具系统**深度集成**——结构化消息是工具输入的一部分，验证在工具层完成，终止通过 AbortController 实现。我们的实现用文件模拟了相同的状态机语义。

---

## 协议的本质

协议就是**带确认的异步消息**。

三个要素：
1. **唯一 ID**：追踪每个请求的生命周期（源码用 `generateRequestId`）
2. **有限状态**：pending → approved/rejected（不可逆）
3. **双向通知**：请求时写入 mailbox，响应时也写入 mailbox

从 Claude Code 源码中还可以提取一个关键设计原则：**协议消息不能广播**。结构化消息必须是点对点的——广播只用于非结构化文本通知。这避免了多个 agent 同时处理同一个协议请求的混乱。

## 设计哲学：显式优于隐式

协议系统是设计指南**第四原则——显式优于隐式**的最佳体现。

对比两种多 Agent 通信方式：

**隐式通信**（通过共享文件系统）：Agent A 写文件，Agent B 读文件。简单但危险——谁先写？谁覆盖了谁？文件损坏怎么办？没有确认机制，没有状态追踪。

**显式通信**（通过结构化协议）：Zod discriminated union 定义消息类型，`validateInput` 硬编码校验规则，`generateRequestId` 追踪每个请求的生命周期。一切都是明确的、可追溯的、可验证的。

设计指南还强调了**安全是默认，便利是可选**的原则在协议中的应用：
- 结构化消息**不能广播**——只能点对点，避免多个 Agent 同时处理同一请求
- 权限通过 `permissionMode: modeToInherit` 显式继承——子 Agent 不会自动获得父 Agent 的权限
- 关机需要**协议审批**——不是直接杀进程，而是走 request → response → abort 流程

这些设计看起来增加了复杂性，但实际上减少了生产环境中的混乱。隐式的"便利"在单 Agent 时没问题，在多 Agent 协作时就是灾难源。

---

下一篇：[Autonomous Agents：自组织团队](../11-autonomous-agents/index.html)
