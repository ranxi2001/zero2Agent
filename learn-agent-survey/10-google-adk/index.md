---
layout: default
title: "Google ADK：官方 Agent 开发套件"
description: Google 官方发布的 Agent Development Kit——多 Agent 编排、内置工具、与 Gemini 深度集成
eyebrow: 框架调研 · 10
---

# Google ADK：官方 Agent 开发套件

Google ADK（Agent Development Kit）是 Google 2025 年发布的官方 Agent 框架，PyPI 包名 `google-adk`。定位是让开发者用 Gemini 快速构建、测试和部署 Agent，类似 OpenAI 的 Agents SDK，但有更深的 Google 生态集成。

GitHub：[google/adk-python](https://github.com/google/adk-python)
文档：[google.github.io/adk-docs](https://google.github.io/adk-docs/)

## 安装

```bash
pip install google-adk
```

需要 Gemini API key（Google AI Studio）：

```bash
export GOOGLE_API_KEY=your-key
```

## 核心概念

| 概念 | 说明 |
|------|------|
| `Agent` | 核心实体，绑定模型、指令、工具 |
| `Tool` | 函数工具，Python 函数 + 类型注解 |
| `Runner` | 执行 Agent，管理 Session 和历史 |
| `Session` | 一次对话的上下文，持久化支持 |
| `MultiAgent` | 多 Agent 编排，支持顺序/并行/路由 |

## 最小示例

```python
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# 定义 Agent
root_agent = Agent(
    name="assistant",
    model="gemini-2.0-flash",
    description="一个通用助手",
    instruction="你是一个有帮助的助手，用中文回答所有问题。",
)

# 初始化 Runner
session_service = InMemorySessionService()
runner = Runner(agent=root_agent, session_service=session_service, app_name="demo")

# 创建 Session
session = session_service.create_session(app_name="demo", user_id="user1")

# 发送消息
response = runner.run(
    user_id="user1",
    session_id=session.id,
    new_message=types.Content(
        role="user",
        parts=[types.Part(text="介绍一下 Google ADK")]
    ),
)

for event in response:
    if event.is_final_response():
        print(event.content.parts[0].text)
```

## 定义工具

ADK 用 Python 函数的**类型注解和 docstring** 自动生成工具 schema：

```python
def get_weather(city: str) -> dict:
    """获取指定城市的当前天气信息。

    Args:
        city: 城市名称，例如：北京、上海、广州

    Returns:
        包含温度、天气状况的字典
    """
    data = {
        "北京": {"temperature": 25, "condition": "晴天"},
        "上海": {"temperature": 22, "condition": "多云"},
        "广州": {"temperature": 30, "condition": "小雨"},
    }
    return data.get(city, {"error": f"暂无 {city} 天气数据"})

def search_web(query: str) -> str:
    """搜索网络获取最新信息。

    Args:
        query: 搜索关键词

    Returns:
        搜索结果摘要
    """
    # 实际接入搜索 API
    return f"关于 '{query}' 的搜索结果：..."

# 把工具绑定到 Agent
weather_agent = Agent(
    name="weather_assistant",
    model="gemini-2.0-flash",
    instruction="你可以查询天气和搜索信息。",
    tools=[get_weather, search_web],
)
```

## 多 Agent 编排

ADK 原生支持多种 Agent 协作模式：

### 顺序执行

```python
from google.adk.agents import SequentialAgent

pipeline = SequentialAgent(
    name="research_pipeline",
    sub_agents=[
        fetch_agent,    # 第一步：获取数据
        analyze_agent,  # 第二步：分析
        report_agent,   # 第三步：生成报告
    ],
    description="顺序执行三步研究流程",
)
```

### 并行执行

```python
from google.adk.agents import ParallelAgent

parallel = ParallelAgent(
    name="parallel_research",
    sub_agents=[
        web_search_agent,
        db_search_agent,
        api_agent,
    ],
    description="并行从三个来源搜集信息",
)
```

### 路由（LLM 决定走哪个）

```python
from google.adk.agents import Agent

router = Agent(
    name="router",
    model="gemini-2.0-flash",
    instruction="""根据用户请求，转交给合适的专家 Agent：
- 技术问题 -> tech_agent
- 账单问题 -> billing_agent
- 投诉 -> support_agent""",
    sub_agents=[tech_agent, billing_agent, support_agent],
)
```

## 内置 Google 工具

ADK 提供了与 Google 服务的原生集成：

```python
from google.adk.tools import google_search, code_execution

# Google 搜索（grounding）
search_agent = Agent(
    name="search_agent",
    model="gemini-2.0-flash",
    tools=[google_search],  # 使用 Google 搜索的真实结果
)

# 代码执行
code_agent = Agent(
    name="code_agent",
    model="gemini-2.0-flash",
    tools=[code_execution],  # 在沙箱中执行 Python 代码
)
```

## 流式输出

```python
async for event in runner.run_async(
    user_id="user1",
    session_id=session.id,
    new_message=types.Content(role="user", parts=[types.Part(text="写一首诗")]),
):
    if hasattr(event, "content") and event.content:
        for part in event.content.parts:
            if hasattr(part, "text"):
                print(part.text, end="", flush=True)
```

## Web UI 调试

ADK 内置了一个 Web UI 用于本地调试：

```bash
adk web
# 启动后访问 http://localhost:8000
# 可以直接在浏览器里和 Agent 对话
# 查看完整的工具调用过程
```

## 部署到 Vertex AI

```python
from google.adk.runners import VertexAIRunner

# 直接部署到 Vertex AI Agent Engine
runner = VertexAIRunner(
    agent=root_agent,
    project="your-gcp-project",
    location="us-central1",
)
```

## 与 Gemini SDK 的关系

| 场景 | 用什么 |
|------|--------|
| 直接调用 Gemini API | `google-genai` SDK |
| 构建单个 Agent + 工具 | `google-adk` |
| 多 Agent 编排 | `google-adk`（MultiAgent） |
| 需要调用非 Gemini 模型 | `google-genai` + Vertex AI |
| 部署到 Vertex AI | `google-adk` |

## 优缺点

**优点：**
- Google 官方出品，与 Gemini 深度集成
- 内置 Google Search、Code Execution 等真实工具
- 多 Agent 编排原生支持（Sequential/Parallel/Router）
- `adk web` 本地调试界面方便
- 一键部署到 Vertex AI

**缺点：**
- 2025 年初发布，生态还在成长
- 主要绑定 Gemini 模型
- 相比 OpenAI Agents SDK 文档还不够完善

## 适合什么场景

- 主要用 Gemini 模型的项目
- 需要 Google Search grounding 的 Agent
- 计划部署到 Google Cloud / Vertex AI
- 需要多 Agent 编排但不想用 LangGraph
