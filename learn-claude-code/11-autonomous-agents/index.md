---
layout: default
title: Autonomous Agents：自组织团队
description: 成员自己扫任务板、自己认领、WORK/IDLE 双态循环
eyebrow: Claude Code / s11
---

# Autonomous Agents：自组织团队

s09–s10 的团队需要 Leader 手动分配任务。这一节移除这个限制：**成员自己扫描任务板，自己认领工作**。

Leader 变成任务发布者，不再是调度者。

---

## 问题

手动调度的瓶颈：

- Leader 需要知道每个成员的能力和当前状态
- 成员越多，调度逻辑越复杂
- Leader 的上下文被调度细节填满

更好的方式：把任务放到任务板上，让成员自己去认领。这才是真正的自治。

---

## 两阶段生命周期

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

---

## 核心：idle 和 claim_task 工具

**idle 工具**：Agent 完成任务后主动调用，告诉框架"我空了，可以接新任务"。

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

---

## IDLE 轮询循环

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

---

## WORK 循环

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

---

## 完整 Agent 入口

```python
def autonomous_agent(name: str, system_prompt: str, initial_task: str = None):
    """自治 Agent 的完整生命周期"""
    _set_agent_status(name, "WORKING")

    if initial_task:
        work_loop(name, system_prompt, initial_task)

    # 进入 IDLE 循环，等待新任务
    idle_loop(name, system_prompt)
```

---

## 自组织的完整流程

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

下一篇：[Worktree 隔离：多 Agent 并行不踩踏](../12-worktree-isolation/index.html)
