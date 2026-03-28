---
layout: default
title: Worktree 隔离：多 Agent 并行不踩踏
description: 每个任务独立 Git worktree——控制平面与执行平面分离
eyebrow: Claude Code / s12
---

# Worktree 隔离：多 Agent 并行不踩踏

多个 Agent 同时修改同一个目录会出什么问题？

- Agent A 创建了 `temp.py`，Agent B 也创建了 `temp.py`，互相覆盖
- Agent A 的未提交修改和 Agent B 的修改混在一起，git status 一团乱
- 一个 Agent 的失败导致另一个 Agent 的工作也出问题

解决方案：**每个任务得到一个独立的 Git worktree**，物理隔离，互不干扰。

---

## Git Worktree 基础

Git worktree 让同一个仓库在多个目录中同时 checkout，每个目录有独立的工作区和 index：

```bash
# 为 task_001 创建独立 worktree
git worktree add .worktrees/task_001 -b task/task_001

# 目录结构：
# .worktrees/
#   task_001/    ← 完整的仓库副本，独立工作区
#   task_002/    ← 另一个任务的独立空间
# src/           ← 主工作区，不被任务修改
```

每个 worktree 指向同一个 `.git` 对象存储，但有独立的 HEAD、index 和工作文件。

---

## 两平面架构

```
控制平面（主目录）：
  .tasks/        ← 任务定义和状态
  .team/         ← 团队成员信息
  .transcripts/  ← 对话历史归档

执行平面（worktree 目录）：
  .worktrees/
    task_001/    ← task_001 的代码修改在这里
    task_002/    ← task_002 的代码修改在这里
```

控制平面只有任务数据，执行平面只有代码变更。两者物理隔离，互不污染。

---

## WorktreeManager 实现

```python
import subprocess, json
from pathlib import Path
from datetime import datetime

WORKTREES_DIR = Path(".worktrees")
EVENTS_LOG = WORKTREES_DIR / "events.jsonl"
WORKTREES_DIR.mkdir(exist_ok=True)

class WorktreeManager:
    def create(self, task_id: str) -> str:
        """为任务创建独立 worktree"""
        worktree_path = WORKTREES_DIR / task_id
        branch_name = f"task/{task_id}"

        if worktree_path.exists():
            return f"Worktree already exists: {worktree_path}"

        # 从当前 HEAD 创建新分支和 worktree
        result = subprocess.run(
            ["git", "worktree", "add", str(worktree_path), "-b", branch_name],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            return f"Failed to create worktree: {result.stderr}"

        # 更新任务状态
        task_manager.update_status(task_id, "in_progress",
                                   worktree=str(worktree_path))

        self._log_event(task_id, "worktree_created", {"path": str(worktree_path)})
        return f"Created worktree: {worktree_path}\nBranch: {branch_name}"

    def run_in(self, task_id: str, command: str) -> str:
        """在任务的 worktree 里执行命令"""
        worktree_path = WORKTREES_DIR / task_id
        if not worktree_path.exists():
            return f"Worktree not found for task {task_id}. Create it first."

        result = subprocess.run(
            command, shell=True, capture_output=True, text=True,
            cwd=str(worktree_path), timeout=60
        )
        output = (result.stdout + result.stderr)[:50000]
        self._log_event(task_id, "command_run", {"command": command, "returncode": result.returncode})
        return output

    def read_in(self, task_id: str, path: str) -> str:
        """读取任务 worktree 里的文件"""
        worktree_path = WORKTREES_DIR / task_id
        file_path = (worktree_path / path).resolve()

        # 安全检查
        if not file_path.is_relative_to(worktree_path.resolve()):
            return f"Path escapes worktree: {path}"
        if not file_path.exists():
            return f"File not found: {path}"
        return file_path.read_text()

    def write_in(self, task_id: str, path: str, content: str) -> str:
        """写文件到任务 worktree"""
        worktree_path = WORKTREES_DIR / task_id
        file_path = (worktree_path / path).resolve()

        if not file_path.is_relative_to(worktree_path.resolve()):
            return f"Path escapes worktree: {path}"

        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
        return f"Written: {path}"

    def finish(self, task_id: str, commit_message: str = None) -> str:
        """完成任务：提交变更，移除 worktree"""
        worktree_path = WORKTREES_DIR / task_id

        if commit_message:
            # 提交所有变更
            subprocess.run(["git", "add", "-A"], cwd=str(worktree_path))
            subprocess.run(
                ["git", "commit", "-m", commit_message or f"Complete {task_id}"],
                cwd=str(worktree_path)
            )

        # 移除 worktree
        subprocess.run(["git", "worktree", "remove", str(worktree_path), "--force"])
        task_manager.complete(task_id)
        self._log_event(task_id, "worktree_finished", {"committed": bool(commit_message)})
        return f"Task {task_id} finished. Worktree removed."

    def list(self) -> str:
        result = subprocess.run(
            ["git", "worktree", "list"], capture_output=True, text=True
        )
        return result.stdout

    def _log_event(self, task_id: str, event: str, data: dict):
        entry = json.dumps({
            "task_id": task_id,
            "event": event,
            "data": data,
            "timestamp": datetime.now().isoformat(),
        })
        with open(EVENTS_LOG, "a") as f:
            f.write(entry + "\n")
```

---

## 工具接口

```python
wt = WorktreeManager()

TOOL_HANDLERS.update({
    "worktree_create":  lambda **kw: wt.create(kw["task_id"]),
    "worktree_bash":    lambda **kw: wt.run_in(kw["task_id"], kw["command"]),
    "worktree_read":    lambda **kw: wt.read_in(kw["task_id"], kw["path"]),
    "worktree_write":   lambda **kw: wt.write_in(kw["task_id"], kw["path"], kw["content"]),
    "worktree_finish":  lambda **kw: wt.finish(kw["task_id"], kw.get("commit_message")),
    "worktree_list":    lambda **kw: wt.list(),
})
```

---

## 完整任务执行流程

<div class="mermaid">
flowchart TD
    A[claim_task: task_001] --> B[worktree_create: task_001]
    B --> C[worktree_read: task_001, src/auth.py]
    C --> D[worktree_write: task_001, src/auth.py]
    D --> E[worktree_bash: task_001, pytest tests/]
    E --> F{测试通过?}
    F -->|是| G[worktree_finish: task_001\n"实现 JWT 验证"]
    F -->|否| D
    G --> H[idle: 等待新任务]
</div>

---

## 崩溃恢复

`.worktrees/events.jsonl` 记录了所有操作：

```json
{"task_id": "task_001", "event": "worktree_created", "timestamp": "..."}
{"task_id": "task_001", "event": "command_run", "data": {"command": "pytest"}, ...}
{"task_id": "task_001", "event": "worktree_finished", ...}
```

如果进程崩溃，从日志里可以知道：哪些任务已经建了 worktree（可以继续），哪些完成了（可以跳过），哪些在中途（需要清理）。

```python
def recover_from_crash() -> list[str]:
    """从事件日志恢复未完成的任务"""
    events = {}
    if not EVENTS_LOG.exists():
        return []
    for line in EVENTS_LOG.read_text().splitlines():
        ev = json.loads(line)
        events[ev["task_id"]] = ev["event"]  # 只保留最新事件

    incomplete = [
        task_id for task_id, last_event in events.items()
        if last_event == "worktree_created"  # 创建了但没完成
    ]
    return incomplete
```

---

## 这套系统的全貌

至此，12 节课的所有机制组合在一起：

```
s01: while True loop       → Agent 的心跳
s02: dispatch map          → 工具系统的骨架
s03: TodoManager           → 单 Agent 的规划
s04: Subagent              → 上下文隔离
s05: Skill loading         → 知识按需加载
s06: Context compact       → 无限会话长度

s07: Task graph            → 任务依赖和持久化
s08: Background tasks      → 非阻塞执行
s09: Agent teams           → 多 Agent 通信
s10: Protocols             → 结构化协作
s11: Autonomous agents     → 自组织
s12: Worktree isolation    → 并行安全
```

从一个 30 行的循环，到一个能并行处理真实工程任务的自治 Agent 团队。

每一层都有具体的问题驱动，每一层的代码都可以独立理解和修改。

---

[← 返回 Claude Code 模块首页](../index.html)
