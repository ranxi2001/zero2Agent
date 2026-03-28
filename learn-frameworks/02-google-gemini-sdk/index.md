---
layout: default
title: "Google genai SDK：Gemini + Vertex AI 多模型"
description: google-genai SDK 有两个后端——Google AI Studio（Gemini）和 Vertex AI（Claude、Llama、Mistral 等）；本篇覆盖两种模式、Function Calling 与多模态
eyebrow: learn-frameworks · 02
---

# Google genai SDK：Gemini + Vertex AI 多模型

Google 的官方 Python SDK 是 `google-genai`（2024 年末重写，取代旧版 `google-generativeai`）。

**它不只能调 Gemini。** SDK 支持两种后端，切换方式只是初始化参数不同：

| 后端 | 初始化方式 | 可用模型 |
|------|-----------|---------|
| Google AI Studio | `api_key=...` | 只有 Gemini 系列 |
| Vertex AI | `vertexai=True, project=..., location=...` | Gemini + Claude + Llama + Mistral + 更多 |

## 安装

```bash
pip install google-genai
```

Vertex AI 还需要 Google Cloud 认证：

```bash
pip install google-cloud-aiplatform
gcloud auth application-default login
```

## 两种初始化方式

### 方式一：Google AI Studio（Gemini 专用）

```python
import os
from google import genai

# 只能用 Gemini 模型
client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
```

在 [Google AI Studio](https://aistudio.google.com/apikey) 获取 API key，免费额度够学习使用。

### 方式二：Vertex AI（多模型）

```python
from google import genai

# 可以调 Gemini、Claude、Llama、Mistral 等
client = genai.Client(
    vertexai=True,
    project="your-gcp-project-id",
    location="us-central1",
)
```

**同一套 SDK，同一套 API，只换初始化参数。** 后面所有代码对两种后端都适用，只有 `model` 字符串不同。

## 用 Vertex AI 调非 Gemini 模型

Vertex AI 的 [Model Garden](https://cloud.google.com/vertex-ai/generative-ai/docs/model-garden/explore-models) 托管了很多第三方模型：

```python
client = genai.Client(vertexai=True, project="my-project", location="us-central1")

# 调 Claude（需要先在 Vertex AI 开通 Anthropic 模型）
response = client.models.generate_content(
    model="claude-3-5-sonnet-v2@20241022",
    contents="用中文介绍一下 Agent",
)
print(response.text)

# 调 Llama 3.1
response = client.models.generate_content(
    model="meta/llama-3.1-405b-instruct-maas",
    contents="What is LangGraph?",
)
print(response.text)

# 调 Mistral
response = client.models.generate_content(
    model="mistral-large@2407",
    contents="介绍 RAG 原理",
)
print(response.text)
```

Vertex AI 上的模型 ID 格式因厂商而异，但调用方式完全一样——`client.models.generate_content`，不用换 SDK。

## 基础对话（以 Gemini 为例）

```python
# 用 Google AI Studio
client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents="用中文介绍一下 LangGraph",
)
print(response.text)
```

### 多轮对话

```python
from google.genai import types

contents = [
    types.Content(role="user", parts=[types.Part(text="我叫张三，你好")]),
    types.Content(role="model", parts=[types.Part(text="你好，张三！有什么可以帮你的？")]),
    types.Content(role="user", parts=[types.Part(text="我叫什么名字？")]),
]

response = client.models.generate_content(model="gemini-2.0-flash", contents=contents)
print(response.text)
```

用 `chats` 接口更简洁：

```python
chat = client.chats.create(model="gemini-2.0-flash")
chat.send_message("我叫张三")
r = chat.send_message("我叫什么名字？")
print(r.text)
```

## 系统指令

```python
from google.genai import types

response = client.models.generate_content(
    model="gemini-2.0-flash",
    config=types.GenerateContentConfig(
        system_instruction="你是一个 Python 代码审查员。只回答代码相关问题。",
        temperature=0,
    ),
    contents="def add(a, b): return a+b 这段代码有什么问题？",
)
print(response.text)
```

## Function Calling

Function Calling 分三步：**声明工具 → 模型决定调用 → 执行并回传结果**。

### 手动循环（完整控制）

```python
from google.genai import types

def get_weather(city: str) -> dict:
    """获取城市当前天气信息"""
    data = {
        "北京": {"temp": 25, "condition": "晴天"},
        "上海": {"temp": 22, "condition": "多云"},
    }
    return data.get(city, {"error": f"暂无 {city} 数据"})

tools_map = {"get_weather": get_weather}

tools = types.Tool(function_declarations=[
    types.FunctionDeclaration(
        name="get_weather",
        description="获取指定城市的当前天气信息",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "city": types.Schema(type=types.Type.STRING, description="城市名称"),
            },
            required=["city"],
        ),
    ),
])

def run_agent(user_input: str) -> str:
    contents = [types.Content(role="user", parts=[types.Part(text=user_input)])]

    while True:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=contents,
            config=types.GenerateContentConfig(tools=[tools]),
        )

        part = response.candidates[0].content.parts[0]

        if hasattr(part, "function_call") and part.function_call:
            fc = part.function_call
            print(f"  [调用工具] {fc.name}({dict(fc.args)})")
            result = tools_map[fc.name](**dict(fc.args))

            contents.append(types.Content(role="model", parts=[types.Part(function_call=fc)]))
            contents.append(types.Content(
                role="user",
                parts=[types.Part(function_response=types.FunctionResponse(
                    name=fc.name,
                    response={"result": result},
                ))],
            ))
        else:
            return response.text

print(run_agent("北京今天天气怎么样？"))
```

### 自动 Function Calling（直接传函数）

```python
# 直接传 Python 函数，SDK 自动生成 schema + 执行循环
response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents="北京今天天气怎么样？",
    config=types.GenerateContentConfig(
        tools=[get_weather],  # 传函数，不用手写 FunctionDeclaration
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=False),
    ),
)
print(response.text)
```

SDK 从函数签名和 docstring 自动提取工具描述。

## 流式生成

```python
for chunk in client.models.generate_content_stream(
    model="gemini-2.0-flash",
    contents="写一篇关于 AI Agent 的短文",
):
    print(chunk.text, end="", flush=True)
print()
```

## 多模态：图片输入

```python
import base64
from google.genai import types

with open("image.png", "rb") as f:
    image_bytes = f.read()

response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents=[
        types.Part(inline_data=types.Blob(mime_type="image/png", data=image_bytes)),
        types.Part(text="描述这张图片里有什么"),
    ],
)
print(response.text)
```

Gemini 在多模态上支持最广：图片、PDF、音频、视频都可以直接放进 `contents`。

## 参数配置

```python
config = types.GenerateContentConfig(
    temperature=0.7,
    top_p=0.95,
    max_output_tokens=1024,
    stop_sequences=["END"],
    system_instruction="...",
)
```

## 可用模型速查

### Google AI Studio（api_key 模式）

| 模型 | 特点 |
|------|------|
| `gemini-2.0-flash` | 速度快，成本低，推荐日常使用 |
| `gemini-2.0-flash-thinking` | 推理能力强，支持思维链 |
| `gemini-1.5-pro` | 长上下文 1M tokens |

### Vertex AI 非 Gemini 模型（vertexai 模式）

| 模型 ID | 来源 |
|---------|------|
| `claude-3-5-sonnet-v2@20241022` | Anthropic |
| `claude-3-haiku@20240307` | Anthropic |
| `meta/llama-3.1-405b-instruct-maas` | Meta |
| `mistral-large@2407` | Mistral AI |
| `mistral-nemo@2407` | Mistral AI |

Vertex AI 模型需要在 Google Cloud 控制台开通对应厂商的授权，部分模型需要单独申请。

## 小结

- `google-genai` SDK 有两个后端：`api_key` 只用 Gemini，`vertexai=True` 可用 Claude、Llama、Mistral 等
- 切换后端只改初始化参数，后续 API 调用代码完全一样
- Function Calling 支持手动循环（完整控制）和自动模式（传函数直接跑）
- Gemini 的多模态覆盖最广（图片/音频/视频）
- 免费学习用 Google AI Studio，生产多模型需求用 Vertex AI

下一篇：[Claude Anthropic SDK：Messages API 与 Tool Use](../03-claude-anthropic-sdk/index.html)。
