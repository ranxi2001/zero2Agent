---
layout: default
title: Task System：持久化任务图
description: 磁盘 DAG——任务依赖、阻塞关系、进程重启后自动恢复
eyebrow: Claude Code / s07
---

# Task System：持久化任务图

s03 的 TodoManager 是内存里的平铺列表——进程一重启就没了，也无法表达任务依赖关系。

这一节升级为磁盘持久化的 **任务图（DAG）**：任务有依赖，依赖完成时自动解锁，重启后从磁盘恢复。

这是 s07–s12 的基础骨架。

---

## 任务图的三个问题

一个任务图需要回答三个问题：

1. **什么任务可以现在开始？**（没有未完成的前置任务）
2. **什么任务在等待？**（有未完成的前置任务）
3. **什么任务已经完成？**

```
task_1 (completed)
    ↓
task_2 (ready)  ←→  task_3 (ready)
         ↘      ↙
          task_4 (blocked: 等待 2 和 3)
```

---

## 磁盘结构

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

---

## TaskManager 实现

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

---

## 工具接口

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

---

## DAG 执行流程

<div class="mermaid">
flowchart TD
    A[create task_1: 分析代码] --> B[create task_2: 重构\nblockedBy: task_1]
    B --> C[create task_3: 写测试\nblockedBy: task_1]
    C --> D[create task_4: 集成测试\nblockedBy: task_2, task_3]

    D --> E[list_ready → task_1]
    E --> F[执行 task_1]
    F --> G[complete task_1\n→ 解锁 task_2, task_3]
    G --> H[并行处理 task_2, task_3]
    H --> I[complete task_2 + task_3\n→ 解锁 task_4]
</div>

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
