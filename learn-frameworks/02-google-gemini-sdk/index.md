---
layout: default
title: "Google Gemini SDK：Function Calling 全解"
description: google-genai SDK 的完整用法——Function Calling、多模态输入、流式生成、系统指令与安全设置
eyebrow: learn-frameworks · 02
---

# Google Gemini SDK：Function Calling 全解

Google 的官方 Python SDK 是 `google-genai`（2024 年末重写，取代旧版 `google-generativeai`）。这一篇覆盖 Gemini 的核心用法：对话、Function Calling、流式输出和多模态。

## 安装与初始化

```bash
pip install google-genai
```

```python
import os
from google import genai
from google.genai import types

# 初始化客户端
client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
```

在 [Google AI Studio](https://aistudio.google.com/apikey) 获取 API key，免费额度够学习使用。

## 基础对话

```python
response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents="用中文介绍一下 LangGraph",
)
print(response.text)
```

### 多轮对话

```python
# 用 contents 列表维护历史
contents = [
    types.Content(
        role="user",
        parts=[types.Part(text="我叫张三，你好")]
    ),
    types.Content(
        role="model",
        parts=[types.Part(text="你好，张三！有什么可以帮你的？")]
    ),
    types.Content(
        role="user",
        parts=[types.Part(text="我叫什么名字？")]
    ),
]

response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents=contents,
)
print(response.text)  # 应输出：你叫张三
```

或者用 `chats` 接口更方便：

```python
chat = client.chats.create(model="gemini-2.0-flash")

r1 = chat.send_message("我叫张三")
print(r1.text)

r2 = chat.send_message("我叫什么名字？")
print(r2.text)
```

## 系统指令

```python
response = client.models.generate_content(
    model="gemini-2.0-flash",
    config=types.GenerateContentConfig(
        system_instruction="你是一个专业的 Python 代码审查员。只回答代码相关问题，对非代码问题礼貌拒绝。",
        temperature=0,
    ),
    contents="def add(a, b): return a+b，这段代码有什么问题？",
)
print(response.text)
```

## Function Calling

Gemini 的 Function Calling 分三步：**声明工具 → 模型决定调用 → 执行并回传结果**。

### 声明工具

```python
from google.genai import types

# 用 Python 函数定义工具
def get_weather(city: str) -> dict:
    """获取城市当前天气信息"""
    data = {
        "北京": {"temp": 25, "condition": "晴天", "humidity": 40},
        "上海": {"temp": 22, "condition": "多云", "humidity": 65},
        "广州": {"temp": 30, "condition": "雷阵雨", "humidity": 85},
    }
    return data.get(city, {"error": f"暂无 {city} 数据"})

def get_stock_price(symbol: str) -> dict:
    """获取股票价格（模拟数据）"""
    prices = {
        "GOOGL": {"price": 175.23, "change": "+1.2%"},
        "MSFT":  {"price": 420.10, "change": "-0.5%"},
        "AAPL":  {"price": 192.45, "change": "+0.8%"},
    }
    return prices.get(symbol, {"error": f"找不到 {symbol}"})
```

### 手动 Function Calling 循环

```python
import json

# 工具映射
tools_map = {
    "get_weather": get_weather,
    "get_stock_price": get_stock_price,
}

# 把 Python 函数转成 Gemini 工具描述
tools = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="get_weather",
            description="获取指定城市的当前天气信息，包括温度、天气状况和湿度",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "city": types.Schema(
                        type=types.Type.STRING,
                        description="城市名称，例如：北京、上海",
                    ),
                },
                required=["city"],
            ),
        ),
        types.FunctionDeclaration(
            name="get_stock_price",
            description="获取指定股票的当前价格和涨跌幅",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "symbol": types.Schema(
                        type=types.Type.STRING,
                        description="股票代码，例如：GOOGL、MSFT、AAPL",
                    ),
                },
                required=["symbol"],
            ),
        ),
    ]
)

def run_agent(user_input: str) -> str:
    """带 Function Calling 的 Agent 循环"""
    contents = [types.Content(role="user", parts=[types.Part(text=user_input)])]

    while True:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=contents,
            config=types.GenerateContentConfig(tools=[tools]),
        )

        # 检查是否有工具调用
        candidate = response.candidates[0]
        part = candidate.content.parts[0]

        if hasattr(part, "function_call") and part.function_call:
            fc = part.function_call
            print(f"  [调用工具] {fc.name}({dict(fc.args)})")

            # 执行工具
            tool_result = tools_map[fc.name](**dict(fc.args))

            # 把模型的调用请求 + 工具结果追加到 contents
            contents.append(types.Content(
                role="model",
                parts=[types.Part(function_call=fc)],
            ))
            contents.append(types.Content(
                role="user",
                parts=[types.Part(
                    function_response=types.FunctionResponse(
                        name=fc.name,
                        response={"result": tool_result},
                    )
                )],
            ))
            # 继续循环，让模型处理工具结果
        else:
            # 模型给出最终文字回复
            return response.text

# 测试
print(run_agent("北京和上海今天天气怎么样？另外 GOOGL 股价多少？"))
```

### 自动 Function Calling

新版 SDK 支持自动执行工具调用，不用手写循环：

```python
import json

# 直接传 Python 函数列表
response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents="北京今天天气怎么样？",
    config=types.GenerateContentConfig(
        tools=[get_weather, get_stock_price],  # 直接传函数
        automatic_function_calling=types.AutomaticFunctionCallingConfig(
            disable=False  # 启用自动调用
        ),
    ),
)
print(response.text)
```

SDK 会自动识别函数签名和 docstring，生成工具描述。

## 流式生成

```python
# 流式文本
for chunk in client.models.generate_content_stream(
    model="gemini-2.0-flash",
    contents="写一篇关于 AI Agent 的短文",
):
    print(chunk.text, end="", flush=True)
print()
```

## 多模态：图片输入

Gemini 原生支持图片、PDF、音频等多模态输入：

```python
import httpx
from google.genai import types

# 从 URL 加载图片
image_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/PNG_transparency_demonstration_1.png/280px-PNG_transparency_demonstration_1.png"
image_data = httpx.get(image_url).content

response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents=[
        types.Part(
            inline_data=types.Blob(
                mime_type="image/png",
                data=image_data,
            )
        ),
        types.Part(text="描述这张图片里有什么"),
    ],
)
print(response.text)
```

本地图片：

```python
with open("image.jpg", "rb") as f:
    image_bytes = f.read()

response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents=[
        types.Part(
            inline_data=types.Blob(mime_type="image/jpeg", data=image_bytes)
        ),
        types.Part(text="图片里有什么？"),
    ],
)
```

## 安全设置

Gemini 有内置的内容安全过滤，可以调整阈值：

```python
response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents="...",
    config=types.GenerateContentConfig(
        safety_settings=[
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            ),
        ]
    ),
)
```

阈值选项：`BLOCK_NONE`、`BLOCK_LOW_AND_ABOVE`、`BLOCK_MEDIUM_AND_ABOVE`、`BLOCK_ONLY_HIGH`。

## 参数配置

```python
config = types.GenerateContentConfig(
    temperature=0.7,        # 创意度 0-2
    top_p=0.95,             # nucleus sampling
    top_k=40,               # top-k sampling
    max_output_tokens=1024, # 最大输出 token
    stop_sequences=["END"], # 停止词
    system_instruction="...",
)
```

## 可用模型

| 模型 | 特点 | 适用场景 |
|------|------|---------|
| `gemini-2.0-flash` | 速度快，成本低 | 日常对话、快速迭代 |
| `gemini-2.0-flash-thinking` | 推理能力强 | 复杂分析、数学推理 |
| `gemini-1.5-pro` | 长上下文 1M tokens | 长文档分析 |
| `gemini-1.5-flash` | 平衡速度和质量 | 通用场景 |

## 小结

Gemini SDK 的核心特点：

- **Function Calling 手动控制**：完整暴露 `function_call` / `function_response` 循环，控制粒度细
- **自动调用**：新版支持传 Python 函数直接运行，省去手写循环
- **多模态原生支持**：图片、音频直接放进 `contents`，不需要特殊处理
- **系统指令独立**：在 `GenerateContentConfig` 里传，不占对话历史位置

下一篇：[Claude Anthropic SDK：Messages API 与 Tool Use](../03-claude-anthropic-sdk/index.html)。
