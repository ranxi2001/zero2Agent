---
layout: default
title: 读懂 pi-mono
description: 目前最好的开源 Coding Agent 的架构拆解
eyebrow: OpenClaw / 07
---

# 读懂 pi-mono

pi-mono 是目前公认最好的开源 Coding Agent 之一，也是 OpenClaw 方案的参考实现。

它的架构设计直接影响了 Claude Code、Cursor 等商业产品的思路。理解 pi-mono，就理解了生产级 Coding Agent 的工程要点。

---

## 为什么读 pi-mono

大多数开源 Agent 项目是"Demo 级别的"——能演示，但不能真正部署。pi-mono 的代码是**可以直接跑在生产上的**，它解决了很多 Demo 项目回避的问题：

- 上下文窗口满了怎么办
- 工具调用出错怎么重试
- 多轮任务中途失败怎么恢复
- 怎么处理超大文件（只读需要的部分）
- 安全沙箱（防止模型乱删文件）

读完 pi-mono，这些问题都有答案。

---

## 仓库结构

```
pi-mono/
├── packages/
│   ├── core/          ← 核心框架（必读）
│   ├── agent/         ← Agent 逻辑（必读）
│   └── tools/         ← 工具实现（选读）
├── examples/          ← 上手示例
└── README.md
```

**建议读的顺序：**

1. `packages/core/` — Node/Flow 实现，对应前面章节的 60 行代码
2. `packages/agent/` — ChatNode / ToolCallNode / 压缩逻辑
3. `packages/tools/` — 8 个内置工具的具体实现

`packages/tools/` 读文件操作和 bash 的实现就够了，其他可以跳过。

---

## 用 AI 辅助阅读

pi-mono 约 3000 行代码。不要从头到尾顺序读——用 Claude 帮你快速建立架构图：

```bash
# 把项目结构和关键文件内容传给 Claude
cat packages/core/node.py packages/agent/chat.py | \
  claude "请画出这个系统的数据流图，说明消息如何在 Node 之间传递"
```

或者在 Claude Code 里直接问：

```
@packages/core 解释 Flow.run() 的完整执行路径
@packages/agent/chat.py ChatNode.exec() 里的路由逻辑是什么
```

生成 Mermaid 图之后粘贴进来看，比看代码直观得多。

---

## 核心架构图

pi-mono 的主流程（基于前面的知识你应该能认出来）：

<div class="mermaid">
flowchart TD
    A([用户输入]) --> B[ChatNode]
    B -->|tool_call| C[ToolCallNode]
    C -->|chat| B
    B -->|output| D[OutputNode]
    D --> A

    B --> E{上下文检查}
    E -->|超出阈值| F[CompressNode]
    F --> B
</div>

和前面章节的 Agent 结构一样，但多了 `CompressNode`——这是 pi-mono 的关键细节。

---

## pi-mono 的关键设计决策

### 1. 系统 Prompt 放在哪里

pi-mono 把系统 Prompt 单独维护在 `SYSTEM_PROMPT.md` 文件里，而不是硬编码在代码中。

原因：系统 Prompt 是要频繁调整的。用文件管理，改 Prompt 不需要改代码，CI/CD 也可以单独管理。

### 2. 工具输出的截断策略

pi-mono 的文件读取工具有一个 `offset/limit` 设计：

```python
read(path="main.py", offset=50, limit=30)  # 只读第 50-80 行
```

这让模型可以先读文件头，再根据需要读具体的行范围，而不是把整个文件都塞进上下文。

对大型代码库，这个设计让上下文使用量降低了约 60%。

### 3. 错误处理和重试

pi-mono 的 Node 基类实现了指数退避重试：

```python
class Node:
    def _exec(self, payload):
        for attempt in range(self.max_retries):
            try:
                return self.exec(payload)
            except RateLimitError:
                wait = self.wait * (2 ** attempt)  # 指数退避
                time.sleep(wait)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
```

API 限速是生产环境的常见问题，这个处理让 Agent 不会因为一次 429 就整体失败。

### 4. 进度持久化

对长任务，pi-mono 会定期把 `shared` 状态序列化到磁盘：

```python
import json, os

def save_checkpoint(shared: dict, path: str = ".agent_checkpoint.json"):
    with open(path, "w") as f:
        json.dump(shared, f, ensure_ascii=False, indent=2)

def load_checkpoint(path: str = ".agent_checkpoint.json") -> dict:
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}
```

进程崩溃或者手动中断后，可以从 checkpoint 恢复，而不需要从头跑。

---

## 一个练习：生成 pi-mono 的架构图

克隆仓库之后，试着做这件事：

```bash
git clone https://github.com/pi-mcp/pi-mono
cd pi-mono

# 用 Claude Code 生成架构图
claude "读取 packages/ 下的所有 Python 文件，生成一个 Mermaid 类图，展示主要类和它们的关系"
```

把生成的图粘贴进任意 Markdown 文件，用 `<div class="mermaid">` 包裹，就能在本地渲染出来。

这个练习的目的不是生成一张完美的图，而是**让你主动触碰代码，建立对整体结构的感知**。

---

## 4 小时阅读计划

| 时间 | 内容 |
|------|------|
| 第 1 小时 | 跑通 examples/，理解输入/输出行为 |
| 第 2 小时 | 读 core/node.py，画 Flow.run() 的执行路径 |
| 第 3 小时 | 读 agent/chat.py，理解 ChatNode 的路由逻辑 |
| 第 4 小时 | 改一个工具或者换一个 LLM，跑通修改后的版本 |

第 4 小时的"改"是关键——读懂代码最快的方式是改代码，不是读文档。

---

下一篇：[构建你的 OpenClaw](../08-build-openclaw/index.html)
