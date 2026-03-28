---
layout: default
title: 三大 SDK 横向对比：怎么选
description: OpenAI Agents SDK、Google Gemini SDK、Claude Anthropic SDK 的设计差异、Tool Calling 实现对比与选型建议
eyebrow: learn-frameworks · 04
---

# 三大 SDK 横向对比：怎么选

三家厂商的 SDK 设计哲学不同，适合的场景也不同。这一篇做系统对比，帮你建立选型判断。

## API 设计对比

### 对话接口

```python
# OpenAI Agents SDK
from agents import Agent, Runner

agent = Agent(name="助手", instructions="你是一个助手", model="gpt-4o-mini")
result = Runner.run_sync(agent, "你好")
print(result.final_output)

# Google Gemini SDK
from google import genai
client = genai.Client(api_key="...")
response = client.models.generate_content(model="gemini-2.0-flash", contents="你好")
print(response.text)

# Anthropic Claude SDK
import anthropic
client = anthropic.Anthropic(api_key="...")
msg = client.messages.create(
    model="claude-opus-4-5",
    max_tokens=1024,
    messages=[{"role": "user", "content": "你好"}]
)
print(msg.content[0].text)
```

**观察：**
- OpenAI Agents SDK 是**高层抽象**：有 Agent 对象概念，Runner 管理执行循环
- Gemini SDK 是**中层抽象**：客户端直接调用，但支持自动 Function Calling
- Anthropic SDK 是**低层控制**：完整暴露 Messages API，Tool Use 需要手动循环

### 系统提示

```python
# OpenAI
agent = Agent(instructions="系统提示内容", ...)

# Gemini
config = types.GenerateContentConfig(system_instruction="系统提示内容")
client.models.generate_content(..., config=config)

# Anthropic
client.messages.create(system="系统提示内容", ...)
```

三家都把系统提示和对话历史分开，这是共识。

## Tool Calling 对比

这是最关键的差异。

### OpenAI Agents SDK

```python
from agents import function_tool

@function_tool
def get_weather(city: str) -> str:
    """获取城市天气"""
    return f"{city}: 晴天 25°C"

agent = Agent(tools=[get_weather], ...)
result = Runner.run_sync(agent, "北京天气")
# Runner 自动处理工具调用循环，无需手动干预
```

**特点：装饰器注册，自动循环，用户不感知工具调用过程。**

### Google Gemini SDK

```python
# 方式一：手动定义 schema + 手动循环
tools = types.Tool(function_declarations=[
    types.FunctionDeclaration(name="get_weather", description="...", parameters=...)
])
response = client.models.generate_content(config=types.GenerateContentConfig(tools=[tools]))
# 检查 response.candidates[0].content.parts[0].function_call
# 手动执行，手动回传 function_response

# 方式二：自动 Function Calling（新版）
def get_weather(city: str) -> str:
    """获取城市天气"""  # docstring 自动变成工具描述
    return f"{city}: 晴天"

response = client.models.generate_content(
    tools=[get_weather],  # 直接传函数
    config=types.GenerateContentConfig(
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=False)
    )
)
```

**特点：两种模式，自动模式方便，手动模式控制粒度更细。**

### Anthropic Claude SDK

```python
tools = [{
    "name": "get_weather",
    "description": "获取城市天气",
    "input_schema": {
        "type": "object",
        "properties": {"city": {"type": "string", "description": "城市名"}},
        "required": ["city"]
    }
}]

# 必须手动写循环
while True:
    response = client.messages.create(tools=tools, messages=messages)
    if response.stop_reason == "tool_use":
        # 手动执行工具，构造 tool_result，追加到 messages
        ...
    else:
        return response.content[0].text
```

**特点：完全手动，完整控制，没有自动循环。**

### Tool Calling 对比汇总

| 维度 | OpenAI | Gemini | Anthropic |
|------|--------|--------|-----------|
| 工具注册方式 | `@function_tool` 装饰器 | 手动 schema 或传函数 | 手动 JSON schema |
| 循环控制 | 全自动（Runner） | 可自动可手动 | 完全手动 |
| 调试难度 | 较难（黑盒） | 中等 | 最容易（完全透明） |
| 适合场景 | 快速开发 | 灵活中间层 | 生产/精细控制 |

## 多 Agent 支持

| 维度 | OpenAI | Gemini | Anthropic |
|------|--------|--------|-----------|
| 原生多 Agent | Handoff（原生支持） | 需要自己实现 | 需要自己实现 |
| Agent 间通信 | 自动传递对话历史 | 手动管理 | 手动管理 |
| 适合模式 | 任务分派、专家路由 | 自定义编排 | 自定义编排 |

OpenAI 的 `handoffs` 是目前三家中唯一原生支持多 Agent 的 SDK 级能力。Gemini 和 Anthropic 需要自己实现路由和上下文传递（或者配合 LangGraph）。

## 流式输出

```python
# OpenAI
async with Runner.run_streamed(agent, "...") as stream:
    async for event in stream.stream_events():
        print(event.delta, end="")

# Gemini
for chunk in client.models.generate_content_stream(model="...", contents="..."):
    print(chunk.text, end="")

# Anthropic
with client.messages.stream(model="...", messages=[...]) as stream:
    for text in stream.text_stream:
        print(text, end="")
```

Gemini 和 Anthropic 都支持同步流式，OpenAI Agents SDK 的流式是异步的。

## 多模态能力

| 能力 | OpenAI GPT-4o | Gemini 2.0 | Claude 3.5+ |
|------|---------------|-----------|-------------|
| 图片输入 | 支持 | 支持 | 支持 |
| 音频输入 | 支持（Whisper） | 原生支持 | 不支持 |
| 视频输入 | 不支持 | 支持 | 不支持 |
| 文档 PDF | 不支持 | 支持 | 支持（Files API） |
| 图片生成 | DALL-E（独立） | Imagen（独立） | 不支持 |

Gemini 在多模态覆盖面上最广，特别是视频和音频的原生支持。

## 特色功能对比

| 功能 | OpenAI | Gemini | Anthropic |
|------|--------|--------|-----------|
| 长上下文 | 128K | 1M token | 200K |
| 推理/思维链 | o1/o3 系列 | Flash Thinking | Extended Thinking |
| 代码执行 | Code Interpreter | 原生代码执行 | 工具调用模拟 |
| 向量搜索 | 内置 Vector Store | Grounding（Google 搜索） | 无（需外接） |
| 细粒度速率 | 较低免费额度 | 较慷慨免费额度 | 中等 |

Gemini 的 **1M token 上下文**和 **Google 搜索 Grounding** 是独特优势；Anthropic 的 **Extended Thinking** 在复杂推理上有优势；OpenAI 的 **Agents SDK** 多 Agent 支持最完整。

## 定价参考（2025 年，仅供参考）

| 模型 | 输入价格 | 输出价格 | 特点 |
|------|---------|---------|------|
| GPT-4o mini | $0.15/1M | $0.60/1M | OpenAI 最便宜 |
| GPT-4o | $2.50/1M | $10/1M | OpenAI 主力 |
| Gemini Flash | $0.075/1M | $0.30/1M | 目前最便宜 |
| Gemini Pro | $1.25/1M | $5/1M | Gemini 主力 |
| Claude Haiku | $0.25/1M | $1.25/1M | Claude 最便宜 |
| Claude Sonnet | $3/1M | $15/1M | Claude 主力 |
| Claude Opus | $15/1M | $75/1M | 最强但最贵 |

**定价以官网为准，经常变动。**

## 选型建议

### 用 OpenAI Agents SDK，如果：

- 需要**原生多 Agent Handoff**，任务分派逻辑复杂
- 想快速搭原型，不想手写工具调用循环
- 团队已经在用 OpenAI，生态熟悉

```
适合场景：客服机器人、多专家协作系统、任务规划 Agent
```

### 用 Google Gemini SDK，如果：

- 需要处理**长文档**（超 100K token）
- 需要**视频/音频**多模态能力
- 想用 Google Search Grounding 接地气
- 在 Google Cloud 生态（Vertex AI）

```
适合场景：文档分析、多媒体内容处理、需要实时信息的 Agent
```

### 用 Anthropic Claude SDK，如果：

- 需要**精细控制** Tool Use 每一步
- 做**复杂推理**任务（Extended Thinking）
- 注重**代码质量**和**指令遵循**
- 生产环境要求高可靠性

```
适合场景：代码助手、分析报告、需要详细思考过程的决策系统
```

### 实际项目里怎么组合

**不要被 SDK 绑定。** 这三家 SDK 的 API 风格不同，但都支持通过工具调用接入外部系统。

一个常见的生产架构：

```
外层框架（LangGraph / 自定义）
  |
  +-- 任务A --> Claude（复杂推理）
  |
  +-- 任务B --> Gemini（长文档处理）
  |
  +-- 任务C --> GPT-4o（通用对话）
```

业务逻辑在框架层，模型是可替换的资源。把 LLM 调用封装成统一接口，切换模型只改配置。

## 最后一条建议

学习阶段：**用 Anthropic SDK 最合适**——它把 Tool Use 的每一步都暴露出来，你能清楚地看到"请求 → 模型决定调用工具 → 执行 → 回传结果 → 最终回复"的完整循环。其他 SDK 封装了这个过程，反而不利于理解底层机制。

理解了 Anthropic 的手动循环，再看 OpenAI 的自动 Runner，你就能明白它在背后帮你做了什么。

生产阶段：根据任务需求选模型，根据团队熟悉度选 SDK，不要教条。
