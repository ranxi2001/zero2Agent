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

## 解决方案

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

## BackgroundManager 实现

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

## 集成到 Agent 循环

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

## 工具 Schema

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

## 线程安全说明

- **主线程**：Agent 循环，单线程，无需锁
- **守护线程**：每个后台任务一个线程，只写自己的 job 对象和 queue
- **queue.Queue**：线程安全，`put` 和 `get` 无需加锁
- **job 对象**：守护线程写完后才放入 queue，主线程通过 queue 感知——无竞争条件

---

下一篇：[Agent Teams：多 Agent 协作](../09-agent-teams/index.html)
