---
layout: default
title: Subagent：上下文隔离的正确姿势
description: 大任务拆小，子智能体用独立 messages[]，不污染主对话
eyebrow: Claude Code / s04
---

# Subagent：上下文隔离的正确姿势

> *"大任务拆小，每个小任务干净的上下文"*

这一节加一个 `task` 工具。调用它会启动一个子 Agent，子 Agent 有完整的工具能力，但它的上下文完全隔离——父 Agent 只看到最终摘要。

---

## 问题

Agent 工作越久，messages 数组越胖。读文件、跑命令的每条输出都永久留在上下文里。

"这个项目用什么测试框架？"可能要读 5 个文件，但父 Agent 只需要一个词："pytest"。

如果直接在父 Agent 里做，这 5 次 read_file 的完整输出都会留在 messages 里，占用宝贵的上下文空间，干扰模型对后续任务的判断。

---

## 解决方案

<div class="mermaid">
flowchart LR
    A[父 Agent\nmessages 保持干净] -->|task prompt| B[子 Agent\nmessages=空]
    B --> C[读文件 × 5]
    B --> D[跑命令]
    B --> E[分析结果]
    E -->|仅摘要文本| A
</div>

子 Agent 可能跑了 30 次工具调用，但整个消息历史直接丢弃。父 Agent 收到的只是一段摘要文本。

---

## 源码实证：Claude Code 真实的 AgentTool

以下内容均来自 Claude Code 泄露源码，不是猜测。

### AgentTool 完整参数 schema

`AgentTool.tsx` 定义了两层 schema。**基础参数**（`baseInputSchema`）：

```typescript
// src/tools/AgentTool/AgentTool.tsx
const baseInputSchema = lazySchema(() => z.object({
  description: z.string()
    .describe('A short (3-5 word) description of the task'),
  prompt: z.string()
    .describe('The task for the agent to perform'),
  subagent_type: z.string().optional()
    .describe('The type of specialized agent to use for this task'),
  model: z.enum(['sonnet', 'opus', 'haiku']).optional()
    .describe("Optional model override for this agent."),
  run_in_background: z.boolean().optional()
    .describe('Set to true to run this agent in the background.')
}));
```

**完整参数**（`fullInputSchema`）在基础上扩展了多 Agent 协作与隔离：

```typescript
// 多 Agent 参数
name:      z.string().optional()   // 让 Agent 可通过 SendMessage({to: name}) 被寻址
team_name: z.string().optional()   // 团队名称
mode:      permissionModeSchema()  // 权限模式，如 "plan" 需要审批

// 隔离模式
isolation: z.enum(['worktree', 'remote']).optional()
  // "worktree" — 创建临时 git worktree，Agent 在代码副本上工作
  // "remote"  — 在远程 CCR 环境中启动（始终后台运行）

// 工作目录覆盖
cwd: z.string().optional()
  // 绝对路径，覆盖 Agent 的工作目录，与 worktree 互斥
```

这意味着 Claude Code 的 Agent 不是简单的"子任务执行器"，而是支持 **模型选择 / 后台执行 / 团队协作 / 代码隔离** 的完整多 Agent 系统。

### runAgent.ts 执行流程

`runAgent.ts` 是子 Agent 的核心运行逻辑。简化后的流程：

```
runAgent({agentDefinition, promptMessages, toolUseContext, ...})
  │
  ├── 1. 解析模型：getAgentModel(定义model, 主循环model, 调用指定model)
  ├── 2. 生成 agentId：createAgentId()（UUID）
  ├── 3. 构建初始消息：contextMessages + promptMessages
  ├── 4. 构建 system prompt：agent 定义 → 增强环境信息
  ├── 5. 解析工具集：resolveAgentTools() 或直接继承父工具
  ├── 6. 初始化 agent 专属 MCP servers（叠加到父 MCP 之上）
  ├── 7. 执行 SubagentStart hooks
  ├── 8. 预加载 frontmatter 中指定的 skills
  ├── 9. 创建隔离的 ToolUseContext（createSubagentContext）
  │
  ├── 10. 进入 query() 主循环 ─────────────────────┐
  │       for await (message of query({...}))       │
  │         ├── stream_event → 转发 metrics 给父    │
  │         ├── attachment   → 直接 yield           │
  │         └── recordable   → 记录 + yield         │
  │                                                  │
  └── 11. finally 清理 ────────────────────────────┘
          ├── 清理 agent MCP servers
          ├── 清理 session hooks
          ├── 释放 fileStateCache 内存
          ├── 释放 Perfetto trace 注册
          └── kill agent 产生的后台 bash 任务
```

关键设计：**sync Agent 共享父的 abortController（Ctrl+C 同时停掉），async Agent 用独立的 AbortController。**

### QueryChainTracking：嵌套 Agent 是支持的

```typescript
// src/Tool.ts
export type QueryChainTracking = {
  chainId: string   // UUID，同一条调用链共享
  depth: number     // 0 = 顶层 Agent，每嵌套一层 +1
}
```

在 `query.ts` 中，每次进入 query 循环时：

```typescript
// src/query.ts — 初始化或递增
const queryTracking = toolUseContext.queryTracking
  ? {
      chainId: toolUseContext.queryTracking.chainId,
      depth: toolUseContext.queryTracking.depth + 1,  // 嵌套时 +1
    }
  : {
      chainId: deps.uuid(),   // 顶层生成新 UUID
      depth: 0,               // 顶层从 0 开始
    }
```

这意味着 **Claude Code 支持 Agent 嵌套调用**：Agent A 调用 Agent B，Agent B 再调用 Agent C，depth 从 0 → 1 → 2 递增。`chainId` 保持不变，用于遥测和调试时追踪整条调用链。

### 120 秒自动转后台

```typescript
// src/tools/AgentTool/AgentTool.tsx
function getAutoBackgroundMs(): number {
  if (isEnvTruthy(process.env.CLAUDE_AUTO_BACKGROUND_TASKS)
    || getFeatureValue_CACHED_MAY_BE_STALE(
         'tengu_auto_background_agents', false)) {
    return 120_000;  // 120 秒
  }
  return 0;
}
```

如果一个同步 Agent 执行超过 120 秒，会自动转为后台任务。这解决了"子任务意外耗时很长，阻塞父 Agent 交互"的问题。

### LocalAgentTask / RemoteAgentTask

后台 Agent 有完整的进度跟踪机制：

```typescript
// src/tasks/LocalAgentTask/LocalAgentTask.tsx
export type AgentProgress = {
  toolUseCount: number;      // 已执行的工具调用次数
  tokenCount: number;        // 消耗的 token 总数
  lastActivity?: ToolActivity;
  recentActivities?: ToolActivity[];  // 最近 5 条活动
  summary?: string;          // 周期性摘要
};
```

`LocalAgentTask` 负责本地后台 Agent，`RemoteAgentTask` 负责远程 CCR 环境中的 Agent。两者都通过 `registerAsyncAgent` / `registerRemoteAgentTask` 注册到 AppState，父 Agent 可以随时查看进度。

---

## 简化 Python 实现

理解了真实架构后，我们用 Python 实现核心机制。

### Subagent 运行器

```python
import uuid

# 模拟 QueryChainTracking
def make_tracking(parent_tracking=None):
    """生成调用链追踪信息"""
    if parent_tracking:
        return {
            "chain_id": parent_tracking["chain_id"],
            "depth": parent_tracking["depth"] + 1
        }
    return {"chain_id": str(uuid.uuid4()), "depth": 0}

def run_subagent(prompt: str, parent_tracking=None,
                 model=None) -> str:
    """启动子 Agent，返回最终摘要文本

    与 Claude Code 的关键对应：
    - parent_tracking → QueryChainTracking（支持嵌套）
    - model → AgentTool 的 model 参数
    - CHILD_TOOLS 包含 task → 允许递归（靠 depth 追踪）
    """
    tracking = make_tracking(parent_tracking)
    use_model = model or MODEL

    sub_messages = [{"role": "user", "content": prompt}]

    for _ in range(30):  # 安全限制
        response = client.messages.create(
            model=use_model,
            system=SUBAGENT_SYSTEM,
            messages=sub_messages,
            tools=PARENT_TOOLS,  # 子 Agent 也有 task 工具，允许嵌套
            max_tokens=8000,
        )
        sub_messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            break

        results = []
        for block in response.content:
            if block.type == "tool_use":
                if block.name == "task":
                    # 递归调用子 Agent，传递 tracking
                    output = run_subagent(
                        block.input["prompt"],
                        parent_tracking=tracking,
                        model=block.input.get("model"),
                    )
                else:
                    handler = TOOL_HANDLERS.get(block.name)
                    output = (handler(**block.input) if handler
                              else f"Unknown tool: {block.name}")
                results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": str(output)[:50000]
                })
        sub_messages.append({"role": "user", "content": results})

    return "".join(
        b.text for b in response.content if hasattr(b, "text")
    ) or "(no summary)"
```

---

## task 工具定义

```python
PARENT_TOOLS = BASE_TOOLS + [
    {
        "name": "task",
        "description": (
            "启动子 Agent 处理子任务，返回摘要。"
            "子 Agent 有独立的上下文和完整的工具能力（包括再次调用 task）。"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "3-5 个词的任务简述"
                },
                "prompt": {
                    "type": "string",
                    "description": "子任务的完整描述，需自包含"
                },
                "model": {
                    "type": "string",
                    "enum": ["sonnet", "opus", "haiku"],
                    "description": "可选的模型覆盖"
                }
            },
            "required": ["description", "prompt"]
        }
    }
]

TOOL_HANDLERS["task"] = lambda **kw: run_subagent(
    kw["prompt"], model=kw.get("model")
)
```

**注意：子 Agent 拥有 `task` 工具。** 与我们最初以为的"禁止递归"不同，Claude Code 通过 `QueryChainTracking.depth` 追踪嵌套深度而非禁止嵌套。实际的安全边界是 `maxTurns` 限制和 token 预算，而不是剥夺工具。

---

## 子任务 prompt 要自包含

父 Agent 给子 Agent 的 prompt 必须包含所有必要的上下文，因为子 Agent 看不到父 Agent 的对话历史。

```python
# 错误：子 Agent 不知道"这个项目"是什么
"找出这个项目使用的测试框架"

# 正确：自包含的任务描述
"读取 /workspace/learn-claude-code 项目根目录下的文件，
 找出使用的测试框架（查看 requirements.txt、setup.py、pyproject.toml 等），
 返回测试框架名称和版本。"
```

---

## 相对 s03 的变化

| 组件 | s03 | s04 |
|------|-----|-----|
| 工具数量 | 5 | 5 + task（所有层级共享） |
| 上下文 | 单一共享 | 父/子隔离 |
| 子 Agent | 无 | `run_subagent()` |
| 嵌套调用 | — | 支持，depth 追踪 |
| 返回值 | — | 仅摘要文本 |

---

## 什么时候用 task

适合用子 Agent 的场景：

- 需要读大量文件但只关心结论（"这个模块有什么问题？"）
- 需要独立验证（一个子 Agent 写代码，另一个子 Agent 审查）
- 独立的子任务，结果互不依赖
- 需要不同模型（用 haiku 做简单搜索，用 opus 做复杂推理）

不适合用子 Agent 的场景：

- 子任务之间有依赖（A 的输出是 B 的输入）
- 任务简单，单次工具调用就能完成
- 需要父 Agent 全程参与推理

---

## 设计哲学：隔离即安全

设计指南将 Claude Code 的多 Agent 模式总结为三个递进的隔离级别：

| 模式 | 隔离级别 | 共享范围 |
|------|---------|---------|
| 子代理（AgentTool） | 上下文隔离 | 共享文件系统 |
| 后台代理（run_in_background） | 上下文 + 时间隔离 | 共享文件系统 |
| Worktree 代理（isolation: worktree） | 上下文 + 文件系统隔离 | 独立 Git 分支 |

隔离级别越高，安全性越强，但协调成本也越高。这是一个经典的工程权衡。

源码中 `QueryChainTracking` 的 depth 机制体现了**为失败设计**的原则——不是禁止嵌套，而是追踪深度，在达到限制时优雅停止。120 秒自动转后台也是同样的思路：不是限制子 Agent 的执行时间，而是在超时后自动切换到不阻塞用户的模式。

另一个设计洞察：**子 Agent 返回的是文本摘要，不是原始数据**。这不是技术限制，而是刻意的设计——父 Agent 只需要结论，不需要子 Agent 的完整上下文。这和管理的委托原则一致：委派任务时，你要的是结果报告，不是执行日志。

---

下一篇：[Skill Loading：按需加载领域知识](../05-skill-loading/index.html)
