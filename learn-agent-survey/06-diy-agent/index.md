---
layout: default
title: "手搓 Agent：从原理到实现"
description: 不用任何框架，从 LLM API 出发，用 200 行 Python 实现一个完整的 Tool-Use Agent
eyebrow: 框架调研 · 06
---

# 手搓 Agent：从原理到实现

框架是别人手搓的 Agent。理解了底层原理，框架才是透明的。

这一篇不依赖任何 Agent 框架，只用 LLM 的原始 API，从零实现一个支持 Tool Calling、多工具并发、循环执行的 Agent。

## Agent 的本质

一个 Agent 就是一个循环：

```
while True:
    decision = llm(history + system_prompt)

    if decision.wants_tool:
        result = execute_tool(decision.tool_name, decision.args)
        history.append(result)
    else:
        return decision.text  # 最终回答，结束循环
```

所有框架做的事，都是在这个循环上加抽象。

## 完整实现（约 200 行）

```python
import json
import os
from typing import Any, Callable
from anthropic import Anthropic

client = Anthropic()


# ===== 工具注册系统 =====

class ToolRegistry:
    """工具注册表：管理所有可调用的工具"""

    def __init__(self):
        self._tools: dict[str, dict] = {}          # name -> schema
        self._functions: dict[str, Callable] = {}  # name -> function

    def register(self, name: str, description: str, parameters: dict, func: Callable):
        self._tools[name] = {
            "name": name,
            "description": description,
            "input_schema": parameters,
        }
        self._functions[name] = func

    def tool(self, name: str, description: str, parameters: dict):
        """装饰器方式注册"""
        def decorator(func: Callable):
            self.register(name, description, parameters, func)
            return func
        return decorator

    def schemas(self) -> list[dict]:
        return list(self._tools.values())

    def call(self, name: str, args: dict) -> Any:
        if name not in self._functions:
            return f"错误：工具 {name} 不存在"
        try:
            return self._functions[name](**args)
        except Exception as e:
            return f"工具执行失败：{e}"


registry = ToolRegistry()


# ===== 工具定义 =====

@registry.tool(
    name="get_weather",
    description="获取指定城市的当前天气",
    parameters={
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "城市名称"},
        },
        "required": ["city"],
    },
)
def get_weather(city: str) -> str:
    data = {"北京": "晴天 25°C", "上海": "多云 22°C", "广州": "小雨 30°C"}
    return data.get(city, f"{city}：暂无天气数据")


@registry.tool(
    name="calculate",
    description="计算数学表达式",
    parameters={
        "type": "object",
        "properties": {
            "expression": {"type": "string", "description": "数学表达式，如 '2 + 3 * 4'"},
        },
        "required": ["expression"],
    },
)
def calculate(expression: str) -> str:
    try:
        # 限制只允许数学表达式
        allowed = set("0123456789+-*/()., ")
        if not all(c in allowed for c in expression):
            return "不支持的表达式"
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"计算错误: {e}"


@registry.tool(
    name="search_knowledge",
    description="在知识库中搜索信息",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "搜索关键词"},
        },
        "required": ["query"],
    },
)
def search_knowledge(query: str) -> str:
    # 模拟知识库搜索
    kb = {
        "langchain": "LangChain 是最流行的 LLM 框架，提供 Chain、Agent、Tool 抽象。",
        "langgraph": "LangGraph 是基于图的 Agent 框架，支持状态管理和条件分支。",
        "agentscope": "AgentScope 是阿里巴巴开源的分布式多 Agent 框架。",
    }
    for key, value in kb.items():
        if key.lower() in query.lower():
            return value
    return f"未找到关于 '{query}' 的相关信息"


# ===== Agent 核心 =====

class Agent:
    def __init__(
        self,
        system_prompt: str,
        model: str = "claude-opus-4-5",
        max_iterations: int = 10,
        verbose: bool = True,
    ):
        self.system_prompt = system_prompt
        self.model = model
        self.max_iterations = max_iterations
        self.verbose = verbose
        self.history: list[dict] = []

    def _log(self, msg: str):
        if self.verbose:
            print(msg)

    def run(self, user_input: str) -> str:
        self.history.append({"role": "user", "content": user_input})

        for iteration in range(self.max_iterations):
            self._log(f"\n[迭代 {iteration + 1}]")

            # 调用 LLM
            response = client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=self.system_prompt,
                tools=registry.schemas(),
                messages=self.history,
            )

            if response.stop_reason == "tool_use":
                # 收集工具调用
                tool_calls = [b for b in response.content if b.type == "tool_use"]
                tool_results = []

                for tc in tool_calls:
                    self._log(f"  → 调用工具: {tc.name}({tc.input})")
                    result = registry.call(tc.name, tc.input)
                    self._log(f"  ← 结果: {result}")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tc.id,
                        "content": str(result),
                    })

                # 把工具调用和结果追加到历史
                self.history.append({"role": "assistant", "content": response.content})
                self.history.append({"role": "user", "content": tool_results})

            elif response.stop_reason == "end_turn":
                # 提取最终文本回复
                for block in response.content:
                    if hasattr(block, "text"):
                        self.history.append({
                            "role": "assistant",
                            "content": block.text
                        })
                        return block.text

        return "已达到最大迭代次数，任务未完成"

    def reset(self):
        """清空对话历史"""
        self.history = []


# ===== 使用 =====

if __name__ == "__main__":
    agent = Agent(
        system_prompt="""你是一个智能助手，可以查询天气、做数学计算和搜索知识库。
根据用户需求，合理调用工具来完成任务。""",
        verbose=True,
    )

    # 测试 1：单工具
    print("=" * 40)
    result = agent.run("北京今天天气怎样？")
    print(f"\n最终回答：{result}")

    # 测试 2：多工具
    agent.reset()
    print("\n" + "=" * 40)
    result = agent.run("上海天气怎样？另外 15 * 8 + 6 等于多少？再帮我搜索一下 LangGraph 是什么。")
    print(f"\n最终回答：{result}")
```

## 扩展：支持多轮对话

```python
# 不 reset，直接继续对话
agent = Agent(system_prompt="你是一个助手。", verbose=False)

print("开始对话（输入 quit 退出）")
while True:
    user_input = input("\n用户: ").strip()
    if user_input.lower() == "quit":
        break
    if not user_input:
        continue

    response = agent.run(user_input)
    print(f"助手: {response}")
```

## 扩展：并发工具调用

当 LLM 同时请求多个工具时，可以并发执行提速：

```python
import concurrent.futures

def run_tools_concurrently(tool_calls):
    """并发执行多个工具调用"""
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {
            tc.id: executor.submit(registry.call, tc.name, tc.input)
            for tc in tool_calls
        }
        return [
            {
                "type": "tool_result",
                "tool_use_id": tc.id,
                "content": str(futures[tc.id].result()),
            }
            for tc in tool_calls
        ]
```

## 你真正学到了什么

手写一遍，会发现框架在背后做的事：

| 框架能力 | 对应的手写代码 |
|---------|--------------|
| 工具注册 | `ToolRegistry.register()` |
| 工具调用循环 | `while True` + `stop_reason == "tool_use"` |
| 对话历史管理 | `self.history.append(...)` |
| 最大迭代保护 | `for iteration in range(max_iterations)` |
| 工具结果回传 | `tool_results` + `messages.append` |

LangChain、OpenAI Agents SDK、AgentScope 做的都是这些——只是加了更多配置、更多工具、更多 Agent 间通信机制。

## 什么时候手搓而不是用框架

- **学习目的**：理解底层机制，看透框架
- **极简场景**：工具少，流程固定，不需要框架的复杂性
- **生产可控**：框架升级频繁，手写代码依赖稳定
- **性能敏感**：去掉框架抽象层，减少不必要开销
