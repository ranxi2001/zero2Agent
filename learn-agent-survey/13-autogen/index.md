---
layout: default
title: "AutoGen：微软的多 Agent 对话框架"
description: 微软 AutoGen——ConversableAgent、GroupChat、代码执行、人机协作（Human-in-the-loop）
eyebrow: 框架调研 · 13
---

# AutoGen：微软的多 Agent 对话框架

AutoGen 是微软研究院开源的多 Agent 框架，核心理念是：**让 Agent 之间通过自然语言对话来协作完成任务**。它的代码执行能力和 Human-in-the-loop 支持是显著特色。

GitHub：[microsoft/autogen](https://github.com/microsoft/autogen)

> AutoGen 从 v0.2 到 v0.4 有重大架构变化。本文以 **AutoGen v0.4+**（新版 AgentChat API）为准。

## 安装

```bash
pip install "autogen-agentchat" "autogen-ext[openai]"
```

## 核心概念

| 概念 | 说明 |
|------|------|
| `AssistantAgent` | 调用 LLM 生成回复的 Agent |
| `UserProxyAgent` | 代理用户，可执行代码、获取人类输入 |
| `RoundRobinGroupChat` | 多 Agent 轮流发言的群聊 |
| `SelectorGroupChat` | 由 LLM 决定下一个发言的 Agent |
| `Team` | 一组协作的 Agent |

## 最小示例：两 Agent 对话

```python
import asyncio
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import MaxMessageTermination
from autogen_ext.models.openai import OpenAIChatCompletionClient

async def main():
    model_client = OpenAIChatCompletionClient(model="gpt-4o-mini")

    # 助手 Agent
    assistant = AssistantAgent(
        name="Assistant",
        model_client=model_client,
        system_message="你是一个有帮助的助手，用中文回答。",
    )

    # 批评者 Agent
    critic = AssistantAgent(
        name="Critic",
        model_client=model_client,
        system_message="你是一个批评者，检查助手的回答是否准确和完整，指出改进点。",
    )

    # 组成团队，轮流发言
    team = RoundRobinGroupChat(
        participants=[assistant, critic],
        termination_condition=MaxMessageTermination(max_messages=4),
    )

    # 运行
    result = await team.run(task="解释什么是 RAG（检索增强生成）")

    for message in result.messages:
        print(f"\n[{message.source}]")
        print(message.content)

asyncio.run(main())
```

## 带代码执行的 Agent

AutoGen 的代码执行是原生能力：

```python
import asyncio
from autogen_agentchat.agents import AssistantAgent, CodeExecutorAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.code_executors.local import LocalCommandLineCodeExecutor

async def main():
    model_client = OpenAIChatCompletionClient(model="gpt-4o")

    # 代码编写者
    coder = AssistantAgent(
        name="Coder",
        model_client=model_client,
        system_message="""你是一个 Python 程序员。
编写代码时用 ```python 代码块包裹，只写代码，不加解释。
代码解决问题后回复 TERMINATE。""",
    )

    # 代码执行者（在本地沙箱执行）
    executor = CodeExecutorAgent(
        name="Executor",
        code_executor=LocalCommandLineCodeExecutor(work_dir="./tmp"),
    )

    team = RoundRobinGroupChat(
        participants=[coder, executor],
        termination_condition=TextMentionTermination("TERMINATE"),
    )

    result = await team.run(
        task="计算前 20 个斐波那契数，并用 matplotlib 画出折线图，保存为 fib.png"
    )

    for msg in result.messages:
        print(f"\n[{msg.source}]: {msg.content[:200]}")

asyncio.run(main())
```

## 工具调用

```python
from autogen_agentchat.agents import AssistantAgent
from autogen_core.tools import FunctionTool
from autogen_ext.models.openai import OpenAIChatCompletionClient

def get_weather(city: str) -> str:
    """获取城市天气"""
    data = {"北京": "晴天 25°C", "上海": "多云 22°C"}
    return data.get(city, "暂无数据")

def search_web(query: str) -> str:
    """搜索网络"""
    return f"关于 '{query}' 的搜索结果（模拟）"

# 包装成 FunctionTool
tools = [
    FunctionTool(get_weather, description="获取城市天气"),
    FunctionTool(search_web, description="搜索网络信息"),
]

agent = AssistantAgent(
    name="ToolAgent",
    model_client=OpenAIChatCompletionClient(model="gpt-4o-mini"),
    tools=tools,
    system_message="你可以查天气和搜索信息来回答用户问题。",
)

import asyncio
async def main():
    result = await agent.run(task="北京天气怎样？同时搜索一下 AutoGen 是什么")
    print(result.messages[-1].content)

asyncio.run(main())
```

## SelectorGroupChat：LLM 决定发言顺序

```python
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.conditions import MaxMessageTermination

# 多个专家 Agent
planner = AssistantAgent(
    name="Planner",
    model_client=model_client,
    system_message="你是规划专家，负责把任务拆分成子任务。",
)

researcher = AssistantAgent(
    name="Researcher",
    model_client=model_client,
    system_message="你是研究专家，负责收集信息。",
)

writer = AssistantAgent(
    name="Writer",
    model_client=model_client,
    system_message="你是写作专家，负责整合信息生成报告。",
)

# SelectorGroupChat 让 LLM 决定下一步该谁说话
team = SelectorGroupChat(
    participants=[planner, researcher, writer],
    model_client=model_client,  # 用这个模型决定发言顺序
    termination_condition=MaxMessageTermination(max_messages=10),
)

async def main():
    result = await team.run(task="写一份关于 LangGraph 的技术分析报告")
    print(result.messages[-1].content)

asyncio.run(main())
```

## Human-in-the-loop

```python
from autogen_agentchat.agents import UserProxyAgent

# UserProxyAgent 在关键步骤请求人类确认
human = UserProxyAgent(
    name="Human",
    input_func=input,  # 从终端读取输入
)

assistant = AssistantAgent(
    name="Assistant",
    model_client=model_client,
    system_message="你是助手，需要人类审批后才能执行操作。",
)

team = RoundRobinGroupChat(
    participants=[assistant, human],
    termination_condition=TextMentionTermination("APPROVED"),
)

# Agent 会生成方案，等待人类输入 "APPROVED" 确认
```

## 流式输出

```python
async def stream_example():
    async for message in team.run_stream(task="写一首诗"):
        if hasattr(message, "content"):
            print(f"[{message.source}]: ", end="")
            print(message.content)
```

## AutoGen v0.2 vs v0.4

很多网上教程还是旧版 v0.2，两者 API 差异大：

| | v0.2（旧） | v0.4（新） |
|--|-----------|-----------|
| 包名 | `autogen` | `autogen-agentchat` |
| 初始化 | `AssistantAgent(llm_config=...)` | `AssistantAgent(model_client=...)` |
| 运行 | `agent.initiate_chat(...)` | `team.run(task=...)` |
| 异步 | 部分支持 | 完全异步 |

建议直接用 v0.4，不要被旧教程误导。

## 优缺点

**优点：**
- 代码执行是原生能力，代码 Agent 场景强
- Human-in-the-loop 支持完善
- 多 Agent 对话模式自然，适合需要"讨论"的任务
- 微软官方维护，Semantic Kernel 可集成

**缺点：**
- 多 Agent 对话难以预测，调试困难
- v0.2 到 v0.4 迁移成本高，历史教程混乱
- 不适合需要精确控制执行流程的场景
- 代码执行有安全风险（需要沙箱）

## 适合什么场景

- 代码生成和自动执行（Coder + Executor 模式）
- 需要多专家"讨论"得出结论的分析任务
- 有 Human-in-the-loop 审批需求的工作流
- 教育和研究：探索多 Agent 协作行为
