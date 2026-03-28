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

## 有限状态机

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

---

## ProtocolManager 实现

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

## 关机协议流程

<div class="mermaid">
sequenceDiagram
    Leader->>Coder: request_shutdown
    Note over Coder: 检查当前状态
    Coder->>Leader: approve 或 reject
    alt approved
        Leader->>Coder: 执行关机
    else rejected
        Leader->>Leader: 等待稍后重试
    end
</div>

---

## 计划审批协议流程

<div class="mermaid">
sequenceDiagram
    Coder->>Leader: request_plan_approval
    Note over Leader: 审查计划是否安全
    Leader->>Coder: approve 或 reject
    alt approved
        Coder->>Coder: 执行操作
    else rejected
        Coder->>Leader: 说明原因请求指导
    end
</div>

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

## 协议的本质

协议就是**带确认的异步消息**。

三个要素：
1. **唯一 ID**：追踪每个请求的生命周期
2. **有限状态**：pending → approved/rejected（不可逆）
3. **双向通知**：请求时通知目标，响应时通知发起方

这个模式可以扩展到任何需要审批的操作：资源申请、代码合并、外部 API 调用……

---

下一篇：[Autonomous Agents：自组织团队](../11-autonomous-agents/index.html)
