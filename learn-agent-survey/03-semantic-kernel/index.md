---
layout: default
title: "Semantic Kernel：微软的企业级 AI SDK"
description: 微软开源的 AI SDK——Plugin/Function 抽象、Planner 自动规划、企业级记忆与 Kernel 架构
eyebrow: 框架调研 · 03
---

# Semantic Kernel：微软的企业级 AI SDK

Semantic Kernel（SK）是微软 2023 年开源的 AI SDK，支持 Python、C# 和 Java。设计目标是让企业把 LLM 能力集成进现有业务系统，主打**企业级**场景。

GitHub：[microsoft/semantic-kernel](https://github.com/microsoft/semantic-kernel)

## 安装

```bash
# Python
pip install semantic-kernel

# 可选：Azure OpenAI
pip install semantic-kernel[azure]
```

## 核心概念

| 概念 | 说明 |
|------|------|
| `Kernel` | 核心容器，管理 AI 服务、插件、记忆 |
| `Plugin` | 功能模块，包含若干 `KernelFunction` |
| `KernelFunction` | 可调用的原子能力，支持 LLM 调用或原生代码 |
| `Planner` | 根据用户目标自动编排插件，生成执行计划 |
| `Memory` | 向量化的语义记忆系统 |

## 最小示例

```python
import asyncio
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.contents import ChatHistory

async def main():
    # 创建 Kernel
    kernel = Kernel()

    # 添加 AI 服务
    kernel.add_service(
        OpenAIChatCompletion(
            service_id="chat",
            ai_model_id="gpt-4o-mini",
        )
    )

    # 获取 Chat 服务直接调用
    chat = kernel.get_service("chat")
    history = ChatHistory()
    history.add_user_message("你好，介绍一下 Semantic Kernel")

    result = await chat.get_chat_message_content(
        chat_history=history,
        settings=kernel.get_prompt_execution_settings_from_service_id("chat"),
    )
    print(result)

asyncio.run(main())
```

## Plugin（插件）

Plugin 是 SK 的核心抽象，用装饰器定义：

```python
from semantic_kernel.functions import kernel_function
from typing import Annotated

class WeatherPlugin:
    """天气查询插件"""

    @kernel_function(
        name="get_current_weather",
        description="获取指定城市的当前天气",
    )
    def get_current_weather(
        self,
        city: Annotated[str, "城市名称，例如：北京、上海"],
    ) -> Annotated[str, "天气描述"]:
        data = {"北京": "晴天 25°C", "上海": "多云 22°C"}
        return data.get(city, f"{city}：暂无数据")

    @kernel_function(
        name="get_forecast",
        description="获取未来三天天气预报",
    )
    def get_forecast(
        self,
        city: Annotated[str, "城市名称"],
    ) -> str:
        return f"{city} 未来三天：晴、多云、小雨"


class MathPlugin:
    """数学计算插件"""

    @kernel_function(description="计算两数之和")
    def add(self, a: float, b: float) -> float:
        return a + b

    @kernel_function(description="计算两数之积")
    def multiply(self, a: float, b: float) -> float:
        return a * b
```

注册并使用插件：

```python
kernel = Kernel()
kernel.add_service(OpenAIChatCompletion(service_id="chat", ai_model_id="gpt-4o-mini"))

# 注册插件
kernel.add_plugin(WeatherPlugin(), plugin_name="weather")
kernel.add_plugin(MathPlugin(), plugin_name="math")

# 直接调用插件函数
result = await kernel.invoke(
    kernel.get_function("weather", "get_current_weather"),
    city="北京",
)
print(result)  # 晴天 25°C
```

## 语义函数（Prompt Function）

SK 支持用 Prompt 模板定义"语义函数"：

```python
from semantic_kernel.functions import KernelFunctionFromPrompt

# 从 Prompt 模板创建函数
summarize = KernelFunctionFromPrompt(
    function_name="summarize",
    plugin_name="utils",
    prompt="""
请用 2-3 句话总结以下内容：

{{$input}}

摘要：""",
)

kernel.add_function("utils", summarize)

result = await kernel.invoke(
    summarize,
    input="LangChain 是一个用于构建 LLM 应用的框架，提供了链、Agent、工具等抽象..."
)
print(result)
```

## Function Calling（Auto Tool Selection）

让 LLM 自动决定调用哪些插件：

```python
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAIChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior

kernel = Kernel()
kernel.add_service(OpenAIChatCompletion(service_id="chat", ai_model_id="gpt-4o"))
kernel.add_plugin(WeatherPlugin(), "weather")
kernel.add_plugin(MathPlugin(), "math")

# 启用自动工具选择
settings = OpenAIChatPromptExecutionSettings(
    function_choice_behavior=FunctionChoiceBehavior.Auto(),
)

history = ChatHistory()
history.add_user_message("北京天气怎样？另外 15 乘以 8 等于多少？")

chat_service = kernel.get_service("chat")
result = await chat_service.get_chat_message_content(
    chat_history=history,
    settings=settings,
    kernel=kernel,  # 传入 kernel，让 LLM 能调用插件
)
print(result)
```

## 记忆（Memory）

SK 的语义记忆可以把文本存入向量数据库：

```python
from semantic_kernel.memory import SemanticTextMemory
from semantic_kernel.connectors.memory.chroma import ChromaMemoryStore
from semantic_kernel.connectors.ai.open_ai import OpenAITextEmbedding

# 初始化记忆
memory = SemanticTextMemory(
    storage=ChromaMemoryStore(persist_directory="./chroma_db"),
    embeddings_generator=OpenAITextEmbedding(ai_model_id="text-embedding-3-small"),
)

# 存储文本
await memory.save_information(
    collection="notes",
    id="note1",
    text="AgentScope 是阿里巴巴开源的多 Agent 框架",
)

# 语义搜索
results = await memory.search(collection="notes", query="阿里的 Agent 框架")
for r in results:
    print(r.text, r.relevance)
```

## Azure OpenAI

SK 与 Azure 生态无缝集成：

```python
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion

kernel.add_service(
    AzureChatCompletion(
        service_id="azure-chat",
        deployment_name="gpt-4o",
        endpoint="https://your-resource.openai.azure.com/",
        api_key="your-azure-key",
    )
)
```

## 优缺点

**优点：**
- 微软官方维护，企业支持完善
- C# 支持对 .NET 生态友好
- Plugin 系统组织清晰，便于大团队协作
- Azure 生态深度集成（Azure OpenAI、Azure AI Search）
- Planner 自动规划能力强

**缺点：**
- API 变动频繁，历史版本文档混乱
- Python 版功能有时落后于 C# 版
- 相对 LangChain 更重，学习曲线较陡
- 社区规模不如 LangChain

## 适合什么场景

- .NET / C# 技术栈的企业项目
- 已在 Azure 生态（Azure OpenAI、Azure AI Search）
- 需要 Plugin 体系管理大量工具
- 企业内部知识库 + 语义搜索场景
