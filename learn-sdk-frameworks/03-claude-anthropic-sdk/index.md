---
layout: default
title: "Claude Anthropic SDK：Messages API 与 Tool Use"
description: Anthropic 官方 Python SDK 的核心用法——Messages API、Tool Use、流式生成、视觉能力与 thinking 模式
eyebrow: learn-frameworks · 03
---

# Claude Anthropic SDK：Messages API 与 Tool Use

Anthropic 的官方 Python SDK 是 `anthropic`，提供对 Claude 系列模型的完整访问。这一篇覆盖 Messages API、Tool Use（工具调用）、流式输出和视觉能力。

## 安装

```bash
pip install anthropic
```

```python
import os
import anthropic

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
```

在 [Anthropic Console](https://console.anthropic.com/) 创建 API key。

## Messages API 基础

### 单次对话

```python
message = client.messages.create(
    model="claude-opus-4-5",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "用中文解释什么是 Agent"}
    ]
)
print(message.content[0].text)
```

### 系统提示

```python
message = client.messages.create(
    model="claude-opus-4-5",
    max_tokens=1024,
    system="你是一个专业的 Python 代码审查员。只回答代码相关问题，保持简洁。",
    messages=[
        {"role": "user", "content": "def add(a, b): return a + b 这个函数有什么问题？"}
    ]
)
print(message.content[0].text)
```

### 多轮对话

```python
conversation = []

def chat(user_input: str) -> str:
    conversation.append({"role": "user", "content": user_input})

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system="你是一个友好的助手。",
        messages=conversation,
    )

    assistant_message = response.content[0].text
    conversation.append({"role": "assistant", "content": assistant_message})
    return assistant_message

print(chat("我叫张三"))
print(chat("我叫什么名字？"))
```

## 响应结构

```python
message = client.messages.create(...)

message.id           # 消息 ID
message.type         # "message"
message.role         # "assistant"
message.content      # List[ContentBlock]
message.model        # 使用的模型名
message.stop_reason  # "end_turn" / "max_tokens" / "tool_use" / "stop_sequence"
message.usage        # Usage(input_tokens=..., output_tokens=...)

# 获取文本
text = message.content[0].text
```

## Tool Use（工具调用）

Claude 的 Tool Use 遵循严格的请求-响应循环，显式暴露每一步。

### 定义工具

```python
tools = [
    {
        "name": "get_weather",
        "description": "获取指定城市的当前天气信息，包括温度、天气状况",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "城市名称，例如：北京、上海、广州"
                }
            },
            "required": ["city"]
        }
    },
    {
        "name": "search_web",
        "description": "搜索互联网，返回相关结果",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索关键词"
                }
            },
            "required": ["query"]
        }
    }
]
```

### 工具调用循环

```python
import json

def get_weather(city: str) -> str:
    data = {"北京": "晴天 25°C", "上海": "多云 22°C", "广州": "雷阵雨 30°C"}
    return data.get(city, f"暂无 {city} 天气数据")

def search_web(query: str) -> str:
    return f"关于 '{query}' 的搜索结果：这是一些相关信息（模拟数据）"

tools_map = {"get_weather": get_weather, "search_web": search_web}

def run_agent(user_input: str) -> str:
    """Claude Tool Use 循环"""
    messages = [{"role": "user", "content": user_input}]

    while True:
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=1024,
            tools=tools,
            messages=messages,
        )

        # 检查停止原因
        if response.stop_reason == "tool_use":
            # 收集本次所有工具调用
            tool_calls = [b for b in response.content if b.type == "tool_use"]
            tool_results = []

            for tc in tool_calls:
                print(f"  [调用工具] {tc.name}({tc.input})")
                result = tools_map[tc.name](**tc.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tc.id,
                    "content": result,
                })

            # 把模型的回复（含工具调用）和工具结果追加到 messages
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})

        else:
            # stop_reason == "end_turn"，提取最终文本回复
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text

# 测试
print(run_agent("北京今天天气怎样？同时帮我搜索一下 Claude Sonnet 的最新消息"))
```

### stop_reason 是核心

Claude Tool Use 的关键：`stop_reason == "tool_use"` 意味着模型想调用工具，你需要执行并回传结果；`stop_reason == "end_turn"` 意味着模型已给出最终答案。

## 流式生成

```python
# 基础流式
with client.messages.stream(
    model="claude-haiku-4-5-20251001",
    max_tokens=1024,
    messages=[{"role": "user", "content": "写一首关于 AI 的短诗"}],
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
print()
```

流式 + Tool Use：

```python
with client.messages.stream(
    model="claude-opus-4-5",
    max_tokens=1024,
    tools=tools,
    messages=messages,
) as stream:
    for event in stream:
        if hasattr(event, "type"):
            if event.type == "content_block_delta":
                if hasattr(event.delta, "text"):
                    print(event.delta.text, end="", flush=True)
    final_message = stream.get_final_message()
```

## 视觉能力

Claude 支持图片输入（base64 或 URL）：

```python
import base64

# 读取本地图片
with open("chart.png", "rb") as f:
    image_data = base64.standard_b64encode(f.read()).decode("utf-8")

message = client.messages.create(
    model="claude-opus-4-5",
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": image_data,
                    },
                },
                {
                    "type": "text",
                    "text": "分析这张图表，告诉我主要趋势"
                }
            ],
        }
    ],
)
print(message.content[0].text)
```

URL 方式（Claude 3.5+ 支持）：

```python
message = client.messages.create(
    model="claude-opus-4-5",
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {"type": "url", "url": "https://example.com/image.jpg"},
                },
                {"type": "text", "text": "这张图片里有什么？"},
            ],
        }
    ],
)
```

## Extended Thinking（扩展思考）

Claude 3.7+ 支持在回答前“思考”，适合复杂推理任务：

```python
response = client.messages.create(
    model="claude-opus-4-5",
    max_tokens=16000,
    thinking={
        "type": "enabled",
        "budget_tokens": 10000  # 思考可用的最大 token
    },
    messages=[{"role": "user", "content": "设计一个 Agent 系统的架构，要求支持多 Agent 协作、持久化状态和错误恢复"}]
)

for block in response.content:
    if block.type == "thinking":
        print("=== 思考过程 ===")
        print(block.thinking[:500])  # 打印思考过程的前 500 字
    elif block.type == "text":
        print("=== 回答 ===")
        print(block.text)
```

## 异步客户端

```python
import asyncio
import anthropic

async_client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

async def async_chat():
    message = await async_client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[{"role": "user", "content": "你好"}],
    )
    return message.content[0].text

print(asyncio.run(async_chat()))
```

## 完整示例：代码助手 Agent

```python
import anthropic

client = anthropic.Anthropic()

code_tools = [
    {
        "name": "run_python",
        "description": "在沙箱中运行 Python 代码并返回输出",
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "要运行的 Python 代码"}
            },
            "required": ["code"]
        }
    },
    {
        "name": "write_file",
        "description": "将内容写入文件",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "文件路径"},
                "content": {"type": "string", "description": "文件内容"}
            },
            "required": ["path", "content"]
        }
    }
]

def run_python(code: str) -> str:
    """模拟代码执行"""
    try:
        import io, sys
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        exec(code, {})
        output = sys.stdout.getvalue()
        sys.stdout = old_stdout
        return output or "（无输出）"
    except Exception as e:
        return f"错误: {e}"

def write_file(path: str, content: str) -> str:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"已写入 {path}"

tools_fn = {"run_python": run_python, "write_file": write_file}

def code_agent(task: str) -> str:
    messages = [{"role": "user", "content": task}]
    system = "你是一个 Python 编程助手。可以运行代码验证结果，也可以写文件保存代码。"

    while True:
        resp = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=2048,
            system=system,
            tools=code_tools,
            messages=messages,
        )

        if resp.stop_reason == "tool_use":
            tool_results = []
            for block in resp.content:
                if block.type == "tool_use":
                    result = tools_fn[block.name](**block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })
            messages.append({"role": "assistant", "content": resp.content})
            messages.append({"role": "user", "content": tool_results})
        else:
            for block in resp.content:
                if hasattr(block, "text"):
                    return block.text

print(code_agent("用 Python 计算前 10 个斐波那契数，然后把代码保存到 fib.py"))
```

## 可用模型

| 模型 | 特点 | 适用场景 |
|------|------|---------|
| `claude-opus-4-5` | 最强能力，支持 thinking | 复杂推理、代码、分析 |
| `claude-sonnet-4-6` | 速度与质量平衡 | 日常生产场景 |
| `claude-haiku-4-5-20251001` | 最快、成本最低 | 高并发、简单任务 |

## 小结

Anthropic SDK 的核心特点：

- **Messages API 设计简洁**：`system` 独立，`messages` 是对话历史，结构清晰
- **Tool Use 显式控制**：`stop_reason == "tool_use"` 触发工具执行，没有隐式自动调用
- **content 是 List**：一个回复可以同时包含文本块和工具调用块
- **Extended Thinking**：Claude 3.7+ 原生支持思维链推理，不需要手动 CoT

下一篇：[三大 SDK 横向对比：怎么选](../04-sdk-comparison/index.html)。
