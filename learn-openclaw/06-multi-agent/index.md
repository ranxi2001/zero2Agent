---
layout: default
title: Multi-Agent 与 Agent Teams
description: 为什么主从调度不好用，以及上下文隔离和并行团队的正确姿势
eyebrow: OpenClaw / 06
---

# Multi-Agent 与 Agent Teams

多 Agent 架构在 2024 年变得很流行，但大多数实现踩了同一个坑：**主从调度**。

这一节说清楚为什么主从调度经常失败，以及真正有效的两种多 Agent 模式。

---

## 主从调度的问题

"Orchestrator + Worker" 的经典架构：

<div class="mermaid">
flowchart TD
    A[Orchestrator Agent] -->|子任务 1| B[Worker Agent 1]
    A -->|子任务 2| C[Worker Agent 2]
    A -->|子任务 3| D[Worker Agent 3]
    B --> A
    C --> A
    D --> A
</div>

理论上很美。实际问题：

1. **上下文污染**：Worker 的执行细节（大量工具调用、中间结果）全部流回 Orchestrator，它的上下文迅速膨胀
2. **错误传播**：Worker 的错误或幻觉会影响 Orchestrator 的后续判断
3. **调度复杂性**：Orchestrator 需要理解所有子任务的格式和协议，自身也容易出错
4. **串行瓶颈**：Worker 按顺序执行，任务越多越慢

Google、Anthropic 的内部工程经验都指向同一个结论：**主从调度在复杂任务上不稳定**。

---

## 模式 1：上下文隔离

最实用的多 Agent 用法不是调度，而是**隔离**。

每个子任务启动一个独立的 Agent，各自有独立的 `shared` 和 `messages`。它们互不知道彼此的存在，只处理分配给自己的那块任务。

```python
# 主流程：拆分任务，各自独立运行
import subprocess
import json

def run_subagent(task: str) -> str:
    """启动一个新进程运行子 Agent"""
    result = subprocess.run(
        ["uv", "run", "agent_runner.py", "--task", task],
        capture_output=True, text=True, timeout=300
    )
    return result.stdout

# 主 Agent 只负责拆任务和收结果，不参与执行细节
tasks = [
    "分析 src/auth.py，列出所有安全问题",
    "分析 src/api.py，检查输入验证",
    "分析 tests/，找出覆盖率不足的模块",
]

results = [run_subagent(t) for t in tasks]
final_report = merge_results(results)
```

**核心优势**：子 Agent 的上下文不会污染主流程。主流程只看最终结果，不关心中间过程。

---

## 模式 2：并行 Agent 团队

上下文隔离通常是串行的（等一个做完再做下一个）。更进一步是**并行执行**：

```python
import concurrent.futures

def run_subagent(task: str) -> str:
    # 同上
    ...

tasks = [
    "分析 auth 模块",
    "分析 api 模块",
    "分析测试覆盖率",
]

# 并行执行，不等待
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
    futures = [executor.submit(run_subagent, t) for t in tasks]
    results = [f.result() for f in futures]

final = merge_results(results)
```

<div class="mermaid">
flowchart LR
    A([任务]) --> B[Agent 1\n子任务 A]
    A --> C[Agent 2\n子任务 B]
    A --> D[Agent 3\n子任务 C]
    B --> E([合并结果])
    C --> E
    D --> E
</div>

这是当前 Coding Agent 领域的前沿方向。pi-mono 的实验数据显示：对可并行的任务（如代码分析、多文件处理），并行 Agent 团队比单 Agent 快 3-5 倍，且稳定性更高。

---

## Tmux 多窗格：调试多 Agent 的利器

在本地运行多个 Agent 时，Tmux 是最好的观察工具：

```bash
# 创建 4 窗格布局
tmux new-session -s agents
tmux split-window -h
tmux split-window -v
tmux select-pane -t 0
tmux split-window -v

# 各窗格分别运行不同的 Agent
# 窗格 0: 主 Agent
# 窗格 1: 子 Agent 1 (auth 分析)
# 窗格 2: 子 Agent 2 (api 分析)
# 窗格 3: 日志监控
```

能同时看到所有 Agent 的实时输出，问题一眼就能发现。

---

## 任务拆分的原则

不是所有任务都适合并行。好的拆分需要满足：

**1. 任务之间无依赖**

```
✅ 可并行：
   - 分析文件 A
   - 分析文件 B
   - 分析文件 C

❌ 不能并行（有依赖）：
   - 先读取配置文件
   - 再根据配置决定执行哪些分析
```

**2. 结果可以独立验证**

每个子任务的输出应该是自包含的，主流程不需要上下文就能判断质量。

**3. 子任务粒度适中**

太细（每个函数一个 Agent）：调度开销大于收益。
太粗（整个项目一个 Agent）：等于没有拆分。

经验值：单个子任务的预估执行时间在 30 秒 ~ 5 分钟之间最合适。

---

## 结果合并策略

子 Agent 的输出往往格式不统一，合并时需要处理：

```python
def merge_results(results: list[str]) -> str:
    """用 LLM 把多个子 Agent 的报告合并成一份"""
    combined = "\n\n---\n\n".join(
        f"[子任务 {i+1}]\n{r}" for i, r in enumerate(results)
    )
    return call_llm_simple(
        f"请把以下多个分析报告合并成一份结构清晰的综合报告：\n\n{combined}"
    )
```

---

## 什么时候用多 Agent

不要为了用多 Agent 而用。多 Agent 的引入会增加复杂度，只在以下情况才值得：

| 场景 | 原因 |
|------|------|
| 任务可分解为独立子任务 | 并行加速、上下文隔离 |
| 单 Agent 上下文会溢出 | 子任务各自维护小 context |
| 子任务需要不同的 system prompt | 专业化 Agent |
| 需要独立验证（一个 Agent 生成，另一个检查）| 减少幻觉 |

如果单 Agent 能搞定，不要引入多 Agent。

---

下一篇：[读懂 pi-mono](../07-pi-mono/index.html)
