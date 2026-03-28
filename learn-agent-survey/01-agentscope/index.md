---
layout: default
title: "AgentScope：阿里的分布式多 Agent 框架"
description: 阿里巴巴开源的多 Agent 框架——基于消息的 Agent 通信、Pipeline 流程编排、分布式部署
eyebrow: 框架调研 · 01
---

# AgentScope：阿里的分布式多 Agent 框架

AgentScope 是阿里巴巴开源的多 Agent 框架，2024 年发布。核心设计思路是：把每个 Agent 都当成一个**消息处理节点**，通过消息传递来协调多 Agent 协作。

GitHub：[modelscope/agentscope](https://github.com/modelscope/agentscope)

## 安装

```bash
pip install agentscope
```

带全部可选依赖：

```bash
pip install agentscope[full]
```

## 核心概念

AgentScope 的三个核心抽象：

| 概念 | 说明 |
|------|------|
| `AgentBase` | 所有 Agent 的基类，继承它来创建自定义 Agent |
| `Msg` | Agent 之间传递的消息对象，包含 `name`、`role`、`content` |
| `Pipeline` | 把多个 Agent 串联或并联起来的流程控制器 |

## 最小示例：单 Agent 对话

```python
import agentscope
from agentscope.agents import DialogAgent
from agentscope.message import Msg

# 初始化（配置模型）
agentscope.init(
    model_configs={
        "config_name": "my_model",
        "model_type": "openai_chat",
        "model_name": "gpt-4o-mini",
        "api_key": "your-openai-key",
    }
)

# 创建对话 Agent
agent = DialogAgent(
    name="Assistant",
    sys_prompt="你是一个有帮助的助手，用中文回答。",
    model_config_name="my_model",
)

# 发送消息
msg = Msg(name="User", content="介绍一下 AgentScope", role="user")
response = agent(msg)
print(response.content)
```

## 多 Agent Pipeline

AgentScope 内置了多种 Pipeline 模式：

```python
from agentscope.agents import DialogAgent, UserAgent
from agentscope.pipelines import SequentialPipeline

# 用户 Agent（从终端读取输入）
user = UserAgent(name="User")

# 助手 Agent
assistant = DialogAgent(
    name="Assistant",
    sys_prompt="你是一个助手。",
    model_config_name="my_model",
)

# 顺序 Pipeline：User -> Assistant
pipeline = SequentialPipeline([user, assistant])

# 运行对话
msg = Msg(name="System", content="开始对话", role="system")
for _ in range(3):
    msg = pipeline(msg)
    print(f"{msg.name}: {msg.content}")
```

## 自定义 Agent

继承 `AgentBase` 实现自定义逻辑：

```python
from agentscope.agents import AgentBase
from agentscope.message import Msg

class WeatherAgent(AgentBase):
    """查询天气的专用 Agent"""

    def __init__(self, name: str, model_config_name: str):
        super().__init__(name=name, model_config_name=model_config_name)

    def reply(self, x: Msg) -> Msg:
        # x 是收到的消息
        city = x.content

        # 调用天气 API（模拟）
        weather = self._get_weather(city)

        # 用 LLM 生成自然语言回复
        prompt = f"城市 {city} 的天气是 {weather}，请用友好的语言告知用户。"
        response = self.model([{"role": "user", "content": prompt}])

        return Msg(
            name=self.name,
            content=response.text,
            role="assistant",
        )

    def _get_weather(self, city: str) -> str:
        data = {"北京": "晴天 25°C", "上海": "多云 22°C"}
        return data.get(city, "暂无数据")
```

## 工具调用（Service）

AgentScope 把工具调用称为 **Service**，内置了大量现成工具：

```python
from agentscope.service import (
    ServiceToolkit,
    execute_python_code,
    web_search,
    read_text_file,
)
from agentscope.agents import ReActAgent

# 注册工具
toolkit = ServiceToolkit()
toolkit.add(execute_python_code)
toolkit.add(web_search, api_key="your-serper-key")

# ReAct Agent 自动决定何时调用工具
agent = ReActAgent(
    name="ReActAssistant",
    model_config_name="my_model",
    service_toolkit=toolkit,
    sys_prompt="你是一个可以执行代码和搜索网络的助手。",
    max_iters=5,
)

msg = Msg(name="User", content="计算 2^10 然后告诉我结果", role="user")
response = agent(msg)
print(response.content)
```

## 分布式部署

AgentScope 原生支持把 Agent 分布到不同进程或机器：

```python
import agentscope
from agentscope.agents import DialogAgent

agentscope.init(
    model_configs=[...],
    project="my_project",
)

# 以分布式模式启动 Agent（运行在独立进程）
agent = DialogAgent(
    name="DistributedAgent",
    sys_prompt="...",
    model_config_name="my_model",
).to_dist()  # 关键：to_dist() 变成分布式 Agent

# 调用方式和普通 Agent 完全一样
msg = Msg(name="User", content="你好", role="user")
response = agent(msg)  # 内部通过 RPC 通信
```

## 模型配置

AgentScope 支持多种 LLM 后端：

```python
model_configs = [
    # OpenAI
    {
        "config_name": "gpt4",
        "model_type": "openai_chat",
        "model_name": "gpt-4o",
        "api_key": "sk-...",
    },
    # 通义千问（Dashscope）
    {
        "config_name": "qwen",
        "model_type": "dashscope_chat",
        "model_name": "qwen-max",
        "api_key": "your-dashscope-key",
    },
    # Ollama 本地模型
    {
        "config_name": "local",
        "model_type": "ollama_chat",
        "model_name": "llama3",
        "options": {"temperature": 0},
    },
]

agentscope.init(model_configs=model_configs)
```

## 优缺点

**优点：**
- 分布式支持是原生设计，不是事后叠加
- 内置大量工具（Service），开箱即用
- 通义千问等国内模型支持好
- 消息传递模型直观，多 Agent 协调自然

**缺点：**
- 文档以中文为主，英文社区较小
- 相比 LangGraph 社区生态弱
- 分布式功能有学习成本

## 适合什么场景

- 需要**分布式多 Agent**，Agent 跑在不同机器上
- 国内部署，用通义千问等模型
- 需要大量内置工具快速搭建原型
- 阿里云生态下的 AI 应用
