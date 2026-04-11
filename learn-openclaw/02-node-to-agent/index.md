---
layout: default
title: Node → Workflow → Agent 推导
description: 从 60 行核心代码出发，手写出一个完整的 Agent 框架
eyebrow: OpenClaw / 02
---

# Node → Workflow → Agent 推导

这一节做一件事：从最简单的 Node 开始，一步步推导出 Workflow、Chatbot、Agent，每一步都有完整可运行的代码。

读完之后你会发现，所谓“框架”就是这些代码加在一起。

---

## 核心结构：60 行代码

先看完整的 `core/node.py`，整个框架就在这里：

```python
# core/node.py
import time
from typing import Any, Dict, Optional, Tuple

shared = {}  # 全局状态，所有 Node 之间共享

class Node:
    def __init__(self, max_retries: int = 1, wait: float = 0):
        self.successors: Dict[str, "Node"] = {}
        self._action: str = "default"
        self.max_retries = max_retries
        self.wait = wait

    def exec(self, payload: Any) -> Tuple[str, Any]:
        """子类实现：返回 (action, next_payload)"""
        raise NotImplementedError

    def _exec(self, payload: Any) -> Tuple[str, Any]:
        """内部调用：处理重试逻辑"""
        for attempt in range(self.max_retries):
            try:
                return self.exec(payload)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(self.wait)

    def __rshift__(self, other: "Node") -> "Node":
        """node >> other  —— 连接到下一个节点"""
        self.successors[self._action] = other
        self._action = "default"
        return other

    def __sub__(self, action: str) -> "Node":
        """node - "action"  —— 给连接边打标签"""
        self._action = action
        return self


class Flow:
    def __init__(self, start: Optional[Node] = None):
        self.start = start

    def run(self, payload: Any = None) -> Any:
        """沿有向图走到没有后继节点为止"""
        node = self.start
        while node:
            action, payload = node._exec(payload)
            node = node.successors.get(action)
        return payload
```

两个核心设计：

1. **`exec()` 返回 `(action, next_payload)`** ——  action 决定路由，next_payload 是下一个 Node 的输入
2. **运算符重载** —— `node - "action" >> next_node` 让图的构建语法极度简洁

---

## 第一步：Workflow

Workflow 是一条有向路径，每个 Node 做一件具体的事。

目标：`接收输入 → 联网搜索 → 大模型总结`

```python
# examples/workflow/main.py
from core.node import Node, Flow, shared
from core.llm import call_llm_simple
from tools.builtins.search import search_web

class InputNode(Node):
    def exec(self, query):
        shared["query"] = query
        return "search", query

class SearchNode(Node):
    def exec(self, query):
        results = search_web(query)
        shared["search_results"] = results
        return "summarize", results

class SummarizeNode(Node):
    def exec(self, results):
        prompt = f"请总结以下搜索结果：\n{results}\n\n原始问题：{shared['query']}"
        answer = call_llm_simple(prompt)
        return "default", answer

# 构图
input_node  = InputNode()
search_node = SearchNode()
summary_node = SummarizeNode()

input_node  - "search"    >> search_node
search_node - "summarize" >> summary_node

# 执行
flow = Flow(input_node)
result = flow.run("Python asyncio 最佳实践")
print(result)
```

<div class="mermaid">
flowchart LR
    A([用户输入]) --> B[InputNode]
    B -->|search| C[SearchNode]
    C -->|summarize| D[SummarizeNode]
    D --> E([输出总结])
</div>

没有循环，执行路径写死，这就是 Workflow。

---

## 第二步：Chatbot

把 Workflow 套进 `while True` 循环，加上多轮对话历史，就变成了 Chatbot。

```python
# examples/chatbot/main.py
from core.node import Node, Flow, shared
from core.llm import call_llm

shared["messages"] = []

class ChatNode(Node):
    def exec(self, _):
        response = call_llm(shared["messages"])
        shared["messages"].append(response)
        return "output", response["content"]

class OutputNode(Node):
    def exec(self, text):
        print(f"\nAssistant: {text}\n")
        return "default", None

# 构图
chat_node   = ChatNode()
output_node = OutputNode()
chat_node - "output" >> output_node

# 循环
while True:
    user_input = input("You: ").strip()
    if not user_input:
        continue
    shared["messages"].append({"role": "user", "content": user_input})
    Flow(chat_node).run()
```

<div class="mermaid">
flowchart TD
    A([用户输入]) --> B[ChatNode]
    B -->|output| C[OutputNode]
    C --> A
</div>

---

## 第三步：Agent

Agent 和 Chatbot 的区别只有一个：当模型想调工具时，把流程路由到 ToolCallNode，执行完再路由回 ChatNode。

这在图结构里就是**一个回路**。

```python
# examples/chatbot_with_tools/main.py
from core.node import Node, Flow, shared
from core.llm import call_llm
from tools.executor import ToolExecutor
from tools.builtins import ALL_TOOLS

shared["messages"] = []
executor = ToolExecutor(ALL_TOOLS)

class ChatNode(Node):
    def exec(self, _):
        response = call_llm(
            shared["messages"],
            tools=[t.to_llm_format() for t in ALL_TOOLS]
        )
        shared["messages"].append(response)

        # 有 tool_calls → 去执行工具
        if response.get("tool_calls"):
            return "tool_call", response["tool_calls"]
        # 没有 → 直接输出
        return "output", response["content"]

class ToolCallNode(Node):
    def exec(self, tool_calls):
        results = executor.execute(tool_calls)
        # 把工具结果追加到对话历史
        for result in results:
            shared["messages"].append(result.to_message())
        # 路由回 ChatNode
        return "chat", None

class OutputNode(Node):
    def exec(self, text):
        print(f"\nAssistant: {text}\n")
        return "default", None

# 构图（注意回路）
chat_node      = ChatNode()
tool_call_node = ToolCallNode()
output_node    = OutputNode()

chat_node      - "tool_call" >> tool_call_node
tool_call_node - "chat"      >> chat_node      # 回路
chat_node      - "output"    >> output_node

# 循环
while True:
    user_input = input("You: ").strip()
    if not user_input:
        continue
    shared["messages"].append({"role": "user", "content": user_input})
    Flow(chat_node).run()
```

<div class="mermaid">
flowchart TD
    A([用户输入]) --> B[ChatNode]
    B -->|tool_call| C[ToolCallNode]
    C -->|chat| B
    B -->|output| D[OutputNode]
    D --> A
</div>

这个回路就是 Agent 的核心结构。ToolCallNode 不决定任务，ChatNode（模型）决定。ToolCallNode 只负责执行，把结果交还给模型继续判断。

---

## 三行公式的完整含义

```
workflow = node + node           # 有向路径，无循环
chatbot  = workflow + loop       # 加外层循环，多轮对话
agent    = chatbot + tools       # 图内部有回路，模型驱动工具
```

这三行不是比喻，是图结构的精确描述。

理解了这个，你就理解了市面上所有 Agent 框架的本质——它们都是在这个结构上加了各种封装。

---

## LLM 调用层

`core/llm.py` 只暴露两个函数：

```python
def call_llm_simple(prompt: str) -> str:
    """单轮，string in，string out"""
    ...

def call_llm(
    messages: list,
    tools: list = None,
    system_prompt: str = None
) -> dict:
    """多轮，返回 assistant message dict（含 tool_calls 字段）"""
    ...
```

使用 OpenAI 兼容协议，通过环境变量配置接入点：

```bash
export OPENAI_API_KEY="your-key"
export OPENAI_BASE_URL="https://api.moonshot.cn/v1"  # Kimi
# 或
export OPENAI_BASE_URL="https://open.bigmodel.cn/api/paas/v4"  # 智谱
```

---

## 动手跑起来

```bash
# 1. 安装 uv（比 conda 快 10 倍，无商业授权风险）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. 克隆仓库
git clone https://github.com/lasywolf/Learn-OpenClaw
cd Learn-OpenClaw

# 3. 配置镜像源（国内）
cat >> ~/.config/uv/uv.toml << 'EOF'
[[index]]
url = "https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple"
default = true
EOF

# 4. 初始化项目
uv sync

# 5. 配置 API key
export OPENAI_API_KEY="sk-xxx"
export OPENAI_BASE_URL="https://api.moonshot.cn/v1"

# 6. 依次运行三个示例
uv run examples/workflow/main.py
uv run examples/chatbot/main.py
uv run examples/chatbot_with_tools/main.py
```

三个示例跑通之后，你已经完整理解了 Agent 的核心结构。

下一篇：[RAG 的本质是 VectorDB](../03-rag/index.html)
