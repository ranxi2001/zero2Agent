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

## 设计：文件消息总线

不用数据库，不用消息队列中间件——只用文件系统：

```
.team/
  config.json          ← 团队花名册 + 成员状态
  inbox/
    leader.jsonl       ← leader 的收件箱
    coder.jsonl        ← coder 的收件箱
    reviewer.jsonl     ← reviewer 的收件箱
```

JSONL 格式（每行一条消息）：天然支持追加，无需锁定整个文件。

---

## 团队配置

```json
{
  "team_name": "coding-team",
  "members": {
    "leader": {
      "status": "IDLE",
      "system_prompt": "你是团队 leader，负责分解任务并分配给成员。",
      "started_at": "2025-01-01T10:00:00"
    },
    "coder": {
      "status": "WORKING",
      "system_prompt": "你是 coder，专注于编写代码。",
      "started_at": "2025-01-01T10:00:05"
    },
    "reviewer": {
      "status": "IDLE",
      "system_prompt": "你是 reviewer，专注于代码审查。",
      "started_at": null
    }
  }
}
```

---

## TeammateManager 实现

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
    def spawn(self, name: str, system_prompt: str) -> str:
        """启动一个新 Agent 成员"""
        config = self._load_config()
        if name in config.get("members", {}):
            return f"Agent '{name}' already exists"

        config.setdefault("members", {})[name] = {
            "status": "WORKING",
            "system_prompt": system_prompt,
            "started_at": datetime.now().isoformat(),
        }
        self._save_config(config)

        # 确保收件箱文件存在
        inbox_path = INBOX_DIR / f"{name}.jsonl"
        if not inbox_path.exists():
            inbox_path.touch()

        # 在守护线程里运行 Agent 循环
        thread = threading.Thread(
            target=self._run_agent,
            args=(name, system_prompt),
            daemon=True
        )
        thread.start()
        return f"Spawned agent: {name}"

    def send(self, to: str, message: str, sender: str = "user") -> str:
        """发送消息到指定 Agent 的收件箱"""
        inbox = INBOX_DIR / f"{to}.jsonl"
        if not inbox.exists():
            return f"Agent '{to}' not found"
        entry = json.dumps({
            "from": sender,
            "message": message,
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
        """在独立线程里运行 Agent 的消息处理循环"""
        while True:
            # 检查收件箱
            new_msgs = self.read_inbox(name)
            if new_msgs != "No new messages.":
                # 有新消息，启动 Agent 处理
                self._process_as_agent(name, system_prompt, new_msgs)
                self._set_status(name, "IDLE")
            time.sleep(5)  # 轮询间隔

    def _process_as_agent(self, name: str, system_prompt: str, inbox_content: str):
        """用完整 Agent 循环处理收件箱消息"""
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

## 三个工具

```python
team = TeammateManager()

TOOL_HANDLERS["spawn"]      = lambda **kw: team.spawn(kw["name"], kw["system_prompt"])
TOOL_HANDLERS["send"]       = lambda **kw: team.send(kw["to"], kw["message"], kw.get("from", "leader"))
TOOL_HANDLERS["read_inbox"] = lambda **kw: team.read_inbox(kw["agent_name"])
```

---

## Agent 生命周期

<div class="mermaid">
stateDiagram-v2
    [*] --> WORKING: spawn
    WORKING --> IDLE: 任务完成
    IDLE --> WORKING: 收到消息
    WORKING --> IDLE: 等待回复
    IDLE --> [*]: SHUTDOWN
</div>

---

## 典型协作流程

```
Leader：
  spawn("coder", "专注于编写 Python 代码")
  spawn("reviewer", "专注于代码审查")

  send("coder", "实现 src/auth.py 中的 JWT 验证函数")

Coder（收到消息后激活）：
  read_file("src/auth.py")
  write_file("src/auth.py", "...")
  send("reviewer", "已完成 JWT 验证函数实现，请审查 src/auth.py")
  send("leader", "实现完成，已通知 reviewer 审查")

Reviewer（收到消息后激活）：
  read_file("src/auth.py")
  send("leader", "审查完成，发现 2 个问题：...")

Leader：
  read_inbox("leader")  # 获取 coder 和 reviewer 的汇报
  send("coder", "请修复以下问题：...")
```

---

## 与 Subagent 的区别

| 特性 | Subagent (s04) | Agent Teams (s09) |
|------|----------------|-------------------|
| 身份 | 一次性 | 持久（有名字） |
| 通信 | 无（只返回结果）| 双向消息 |
| 并发 | 否 | 是（守护线程） |
| 跨对话 | 否 | 是（文件持久化） |
| 协调 | 父 Agent | 消息驱动 |

---

下一篇：[Team Protocols：结构化通信协议](../10-team-protocols/index.html)
