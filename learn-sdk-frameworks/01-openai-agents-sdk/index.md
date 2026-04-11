---
layout: default
title: "OpenAI Agents SDK：Agent、Tool、Handoff"
description: OpenAI 官方 Agents SDK 的核心抽象——Agent 对象、工具注册、Runner 执行循环、多 Agent Handoff
eyebrow: learn-frameworks · 01
---

# OpenAI Agents SDK：Agent、Tool、Handoff

OpenAI 在 2025 年初开源了 [Agents SDK](https://github.com/openai/openai-agents-python)，这是他们对“怎么构建 Agent”给出的官方答案。它比直接调 Chat Completions API 多了一层抽象，但比 LangChain 轻得多。

## 安装

```bash
pip install openai-agents
```

需要设置 API key：

```bash
export OPENAI_API_KEY=sk-...
```

## 核心概念

OpenAI Agents SDK 的三个核心对象：

| 对象 | 作用 |
|------|------|
| `Agent` | 定义一个 Agent 的行为（模型、指令、工具、可转交的子 Agent） |
| `Runner` | 执行 Agent，管理运行循环直到完成 |
| `Tool` | Agent 可以调用的函数，用装饰器注册 |

## 最小示例

```python
from agents import Agent, Runner

# 定义 Agent
agent = Agent(
    name="助手",
    instructions="你是一个有帮助的助手。用中文回答。",
    model="gpt-4o-mini",
)

# 运行
result = Runner.run_sync(agent, "你好，介绍一下自己")
print(result.final_output)
```

`Runner.run_sync` 是同步版本，适合脚本。`Runner.run` 是异步版本，适合 FastAPI 等异步框架。

## 注册工具

用 `@function_tool` 装饰器把普通函数变成工具：

```python
from agents import Agent, Runner, function_tool

@function_tool
def get_weather(city: str) -> str:
    """获取指定城市的天气"""
    # 实际调用天气 API
    weather_data = {
        "北京": "晴天，25°C",
        "上海": "多云，22°C",
        "广州": "小雨，28°C",
    }
    return weather_data.get(city, f"暂无 {city} 的天气数据")

@function_tool
def calculate(expression: str) -> str:
    """计算数学表达式，例如 '2 + 3 * 4'"""
    try:
        result = eval(expression)  # 生产环境用 safer 的方案
        return str(result)
    except Exception as e:
        return f"计算错误: {e}"

# 把工具传给 Agent
agent = Agent(
    name="工具助手",
    instructions="你可以查天气和做数学计算。",
    model="gpt-4o-mini",
    tools=[get_weather, calculate],
)

result = Runner.run_sync(agent, "北京今天天气怎么样？另外 15 * 8 等于多少？")
print(result.final_output)
```

SDK 会自动从函数的**类型注解**和**docstring** 提取工具描述，生成发给模型的 JSON Schema。这意味着：
- 参数类型要写清楚
- docstring 是工具的说明，直接影响模型怎么调用它

## Pydantic 结构化输出

如果想让 Agent 输出结构化结果而不是纯文本：

```python
from pydantic import BaseModel
from agents import Agent, Runner

class WeatherReport(BaseModel):
    city: str
    temperature: float
    condition: str
    suggestion: str

agent = Agent(
    name="天气分析师",
    instructions="分析天气数据，提供出行建议。",
    model="gpt-4o-mini",
    output_type=WeatherReport,  # 指定输出类型
)

result = Runner.run_sync(agent, "北京今天 25 度晴天，明天 10 度下雨")
report: WeatherReport = result.final_output
print(f"城市: {report.city}")
print(f"建议: {report.suggestion}")
```

## Handoff：多 Agent 协作

Handoff 是 OpenAI Agents SDK 的核心特性：一个 Agent 可以把任务**转交**给另一个 Agent。

```
用户 --> [分诊 Agent] --> 判断类型
                         |
                         +-- 技术问题 --> [技术 Agent]
                         |
                         +-- 账单问题 --> [账单 Agent]
                         |
                         +-- 投诉    --> [客服 Agent]
```

```python
from agents import Agent, Runner

# 专门的子 Agent
tech_agent = Agent(
    name="技术支持",
    instructions="你是技术支持专员，专门解决软件和硬件问题。",
    model="gpt-4o-mini",
)

billing_agent = Agent(
    name="账单支持",
    instructions="你是账单专员，处理付款、退款和发票问题。",
    model="gpt-4o-mini",
)

complaint_agent = Agent(
    name="客服专员",
    instructions="你是高级客服，处理投诉和升级案例，保持耐心和同理心。",
    model="gpt-4o-mini",
)

# 分诊 Agent，可以把任务转交给子 Agent
triage_agent = Agent(
    name="分诊助手",
    instructions="""你是客服分诊助手。根据用户问题类型，将其转交给对应专员：
    - 技术/软件/硬件问题 -> 技术支持
    - 付款/退款/发票 -> 账单支持
    - 投诉/不满 -> 客服专员
    如果无法判断，先了解更多信息。""",
    model="gpt-4o-mini",
    handoffs=[tech_agent, billing_agent, complaint_agent],  # 可转交的 Agent
)

# 运行
result = Runner.run_sync(triage_agent, "我的软件无法启动，一直报错")
print(result.final_output)
```

Handoff 发生时，SDK 会自动切换执行上下文到子 Agent，历史消息会传递过去。

## 异步运行

```python
import asyncio
from agents import Agent, Runner

agent = Agent(
    name="助手",
    instructions="你是一个助手。",
    model="gpt-4o-mini",
)

async def main():
    result = await Runner.run(agent, "你好")
    print(result.final_output)

asyncio.run(main())
```

## 流式输出

```python
import asyncio
from agents import Agent, Runner

agent = Agent(name="助手", instructions="你是一个助手。", model="gpt-4o-mini")

async def stream_example():
    async with Runner.run_streamed(agent, "写一首短诗") as stream:
        async for event in stream.stream_events():
            if hasattr(event, 'delta') and event.delta:
                print(event.delta, end="", flush=True)
    print()

asyncio.run(stream_example())
```

## 运行结果的结构

`Runner.run_sync` 返回的 `result` 包含：

```python
result.final_output      # 最终输出（字符串或 Pydantic 对象）
result.new_messages      # 本次运行产生的新消息
result.last_agent        # 最终执行的 Agent（Handoff 后可能不同）
result.input             # 输入
```

## 完整示例：研究助手

```python
from agents import Agent, Runner, function_tool

@function_tool
def search_web(query: str) -> str:
    """搜索网络，返回相关结果摘要"""
    # 实际项目接入真实搜索 API
    return f"关于 '{query}' 的搜索结果：这是一些相关信息..."

@function_tool
def save_notes(content: str, filename: str = "notes.txt") -> str:
    """保存研究笔记到文件"""
    with open(filename, "a", encoding="utf-8") as f:
        f.write(content + "\n---\n")
    return f"已保存到 {filename}"

researcher = Agent(
    name="研究员",
    instructions="""你是一个研究助手。步骤：
1. 搜索用户要求的主题
2. 整理关键信息
3. 保存到笔记文件
4. 给出简洁总结""",
    model="gpt-4o",
    tools=[search_web, save_notes],
)

result = Runner.run_sync(researcher, "研究一下 LangGraph 和 OpenAI Agents SDK 的区别")
print(result.final_output)
```

## 小结

OpenAI Agents SDK 的设计哲学：

- **Agent 是配置**：用 `Agent` 对象声明行为，不用手写执行循环
- **工具即函数**：`@function_tool` 装饰器，类型注解自动生成 schema
- **Handoff 原生支持**：多 Agent 协作不需要手写路由
- **Runner 管理循环**：工具调用、结果处理、循环终止全部自动

适合快速搭建多 Agent 系统，尤其是有明确任务分工的客服、研究、分析场景。

下一篇：[Google Gemini SDK：Function Calling 全解](../02-google-gemini-sdk/index.html)。
