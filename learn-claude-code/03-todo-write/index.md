---
layout: default
title: TodoWrite：让 Agent 不再迷路
description: 规划层——追踪任务状态，防止模型在多步任务中重复或遗漏
eyebrow: Claude Code / s03
---

# TodoWrite：让 Agent 不再迷路

s01/s02 的 Agent 能执行工具，但在多步任务里容易迷路——重复做已完成的事，跳过某个步骤，或者中途忘记目标。

这一节加一个规划层：**TodoManager**。

---

## 问题

没有规划层时，模型靠对话历史"记住"任务进度。这有几个问题：

- **重复工作**：读了文件 A 又读一遍
- **跳过步骤**：忘记某个子任务
- **上下文漂移**：多轮工具调用后，最初的任务目标被淹没

人在做复杂任务时会列清单。Agent 也需要。

---

## TodoManager 设计

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

## 典型执行过程

对于"重构 src/ 目录下的所有模块"这样的任务：

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

## 相对 s02 的变化

| 组件 | s02 | s03 |
|------|-----|-----|
| 工具数量 | 4 | 5（新增 todo） |
| 任务规划 | 无 | TodoManager |
| 注意力机制 | 无 | 3 轮无更新自动提醒 |
| Agent loop | — | **不变** |

---

下一篇：[Subagent：上下文隔离的正确姿势](../04-subagent/index.html)
