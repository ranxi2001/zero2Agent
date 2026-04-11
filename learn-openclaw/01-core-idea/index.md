---
layout: default
title: 为什么要自己写 Agent
description: 从主流框架的局限，到 60 行代码的核心架构
eyebrow: OpenClaw / 01
---

# 为什么要自己写 Agent

你大概已经用过 LangChain、Dify 或者 Coze。

上手快，效果看起来不错，Demo 做出来很顺。

然后你试图把它真正部署起来，遇到了一些问题：

- 行为不稳定，但不知道内部发生了什么
- 想改一个细节，发现要翻三层抽象
- 查一个 bug，堆栈里全是框架代码
- 上了生产，偶尔出 CVE 漏洞（比如 LangChain 的 CVE-2025-68664）

这不是你用得不好。是框架的结构决定的。

## 真正跑在生产的 Coding Agent 用什么

Claude Code、Cursor、Kimi-cli、pi-mono——这些目前公认最好的 Coding Agent——都没有用 LangChain 或 Dify。

它们用的是**轻量级的自定义实现**。核心部分大概几十到几百行。

原因不复杂：

- 过度抽象 → 行为难预测
- 大依赖链 → 安全面更大
- 框架逻辑 → 你无法完全控制流程

OpenClaw 的方案从这里出发：**把 Agent 拆到最小单位，理解每一层在做什么，然后用你自己的代码搭出来。**

---

## Agent 的本质：三行公式

把 Agent 一层层拆开，会得到这样一个推导：

```
workflow = node + node
chatbot  = workflow + loop
agent    = chatbot + tools
```

这三行描述了从最简单的管道，到一个能自己决策、调用工具的 Agent，所需要的全部概念。

逐层看一下：

### Workflow：有向图里的节点

一个 Workflow 就是若干 Node 按顺序或按条件连接起来。每个 Node 做一件事：接收输入，返回输出和动作名称（action）。Flow 根据 action 决定下一个执行哪个 Node。

<div class="mermaid">
flowchart LR
    A([输入]) --> B[Node A] -->|action: search| C[Node B] -->|action: summarize| D[Node C] --> E([输出])
</div>

没有循环。执行路径由开发者提前定义好。这是 Workflow。

### Chatbot：加一个循环

把 Workflow 放进一个 while 循环，每轮读用户输入、执行一次 Flow、输出结果。

<div class="mermaid">
flowchart TD
    A([用户输入]) --> B[ChatNode]
    B -->|output| C([输出])
    C --> A
</div>

还是没有工具。只是一个能多轮对话的系统。这是 Chatbot。

### Agent：加工具调用的回路

当 ChatNode 判断需要调用工具时，不直接输出，而是把流程路由到 ToolCallNode。ToolCallNode 执行工具，把结果写回对话上下文，再把流程还给 ChatNode。

<div class="mermaid">
flowchart TD
    A[ChatNode] -->|tool_call| B[ToolCallNode]
    B -->|chat| A
    A -->|output| C([输出结果])
</div>

这个循环就是 Agent 和 Chatbot 的本质区别。

---

## 60 行代码的核心框架

实现上面这个结构，不需要 LangChain。核心代码大概 60 行：

```python
# core/node.py

shared = {}  # 全局状态，所有 Node 共享

class Node:
    def __init__(self, max_retries=1, wait=0):
        self.successors = {}      # action -> 下一个 Node
        self._action = "default"
        self.max_retries = max_retries
        self.wait = wait

    def exec(self, payload):
        # 子类实现：返回 (action, next_payload)
        raise NotImplementedError

    def __rshift__(self, other):
        # node >> other_node  —— 连接节点
        self.successors[self._action] = other
        self._action = "default"
        return other

    def __sub__(self, action):
        # node - "action"  —— 给边打标签
        self._action = action
        return self

class Flow:
    def __init__(self, start=None):
        self.start = start

    def run(self, payload=None):
        node = self.start
        while node:
            action, payload = node._exec(payload)
            node = node.successors.get(action)
```

用 Python 运算符重载让节点连接的语法很干净：

```python
# 构图
chat_node - "tool_call" >> tool_call_node
tool_call_node - "chat"  >> chat_node
chat_node - "output"     >> output_node

# 执行
flow = Flow(chat_node)
flow.run()
```

整个框架就是这样。没有魔法，没有隐藏逻辑。

---

## 工具系统：越少越好

OpenClaw 方案里只保留了 8 个工具：

| 工具 | 作用 |
|------|------|
| `read` | 读文件（支持 offset/limit）|
| `write` | 写文件（自动创建父目录）|
| `edit` | 精确查找替换 |
| `bash` | 执行 shell 命令 |
| `grep` | 正则搜索 |
| `find` | Glob 匹配查找文件 |
| `ls` | 列目录 |
| `search` | DuckDuckGo 搜索 |

**为什么这么少？**

实验数据：把工具数量从很多削减到 8 个，Agent 的任务完成率反而提升了。

原因在于：工具越多，模型选工具的决策空间越大，越容易选错或组合错。简单、职责清晰的工具更容易被模型正确使用。

一个实用原则：**能用 `bash` 解决的，不要单独做工具。**

### 工具的三种形式

OpenClaw 方案把“工具”分成三类，概念很清晰：

| 类型 | 本质 | 例子 |
|------|------|------|
| Tool | 本地函数调用 | `read_file()` |
| MCP | 远程进程调用（Anthropic 协议）| MCP Server |
| Skill | 本地进程调用（结构化能力）| `tools/skills/pdf/` |

---

## 上下文与内存

内存不复杂：

```
memory = 短期上下文 + 长期上下文
```

- **短期上下文**：最近几轮完整的对话历史，直接放进 `messages`
- **长期上下文**：对更早对话的摘要，压缩后追加到上下文头部

没有向量数据库，没有复杂的检索策略。大多数场景下这就够了。

---

## 多 Agent：上下文隔离，而不是主从调度

多 Agent 架构目前最实用的用法不是“一个主 Agent 调度一堆子 Agent”，而是**上下文隔离**。

每个子 Agent 处理一个独立的子任务，彼此的上下文互不干扰。主 Agent 的上下文不会因为某个子任务的细节被污染。

更进一步的方向是**并行 Agent 团队**——多个 Agent 同时处理不同子任务，最后合并结果。这是当前 Coding Agent 领域的前沿方向，比主从调度更高效，也更稳定。

<div class="mermaid">
flowchart LR
    A([任务]) --> B[Agent 1\n子任务 A]
    A --> C[Agent 2\n子任务 B]
    A --> D[Agent 3\n子任务 C]
    B --> E([合并结果])
    C --> E
    D --> E
</div>

---

## 构建你自己的 OpenClaw

这套思路落地的路径是：

1. **理解核心框架**：读懂 `core/node.py` 里的 60 行代码
2. **跑通 workflow → chatbot → agent** 的推导过程
3. **读 pi-mono**：这是目前公认最好的开源 Coding Agent，用 4 小时理解它的架构
4. **fork 改造**：把 pi-mono 改成你自己的 LLM、你自己的工具集、你自己的系统 Prompt
5. **部署**：用 PM2 后台运行，接入 Slack 或飞书，通过 IM 跟自己的 Agent 对话

```bash
# 克隆 pi-mono
git clone https://github.com/pi-mcp/pi-mono

# 配置 LLM（以 Kimi 为例）
export OPENAI_API_KEY="your-key"
export OPENAI_BASE_URL="https://api.moonshot.cn/v1"

# PM2 后台部署
npm install -g pm2
pm2 start your_agent.py --name "myclaw"
```

你的 Agent 可以叫 `YourNameClaw`——这就是 OpenClaw 命名约定的含义。

---

## 这条路适合什么人

这套方案对以下场景有价值：

- 你想真正理解 Agent 底层在做什么，不满足于黑盒调包
- 你要开发一个真正部署上线的 Agent，需要完整的可控性
- 你在准备 Agent 方向的技术面试，需要展示能从零搭系统的能力

它不适合：

- 只是想快速 Demo 一个功能
- 不需要深入理解原理，只需要结果

下一步建议：

- 克隆 [Learn-OpenClaw](https://github.com/lasywolf/Learn-OpenClaw)，跑通 `examples/` 里的三个示例
- 阅读 [pi-mono](https://github.com/pi-mcp/pi-mono)，用 Claude 帮你生成架构图
