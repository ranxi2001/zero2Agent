---
layout: default
title: "AgentUniverse：华为的企业级 Agent 平台"
description: 华为开源的多 Agent 协作框架——PEER 协作模式、知识组件、企业级可观测性
eyebrow: 框架调研 · 07
---

# AgentUniverse：华为的企业级 Agent 平台

AgentUniverse（aU）是华为开源的多 Agent 协作框架，2024 年发布。定位是帮助企业快速构建**专家级多 Agent 系统**，强调可观测性和企业集成能力。

GitHub：[alipay/agentUniverse](https://github.com/alipay/agentUniverse)（蚂蚁集团与华为合作开源）

## 核心设计：PEER 协作模式

AgentUniverse 提出了 **PEER** 多 Agent 协作模式：

| 角色 | 含义 | 职责 |
|------|------|------|
| **P**lanning | 规划 Agent | 把复杂任务拆分成子任务 |
| **E**xecuting | 执行 Agent | 完成具体的子任务 |
| **E**xpressing | 表达 Agent | 整合结果，生成最终输出 |
| **R**eviewing | 审查 Agent | 检查结果质量，决定是否需要重试 |

这是对"多 Agent 如何分工"的一种具体化方案。

## 安装

```bash
pip install agentUniverse
```

## 配置文件驱动

AgentUniverse 的核心是 YAML 配置文件。每个 Agent、工具、LLM 都用配置文件描述：

```yaml
# agent/research_agent.yaml
name: 'research_agent'
description: '专门进行信息收集和研究的 Agent'
profile:
  prompt_version: research_agent.cn
  llm_model:
    name: 'qwen_llm'
    temperature: 0.1
    max_tokens: 2000
plan:
  planner:
    name: 'react_planner'
action:
  tool:
    - 'web_search_tool'
    - 'read_file_tool'
memory:
  name: 'demo_memory'
```

```yaml
# llm/qwen_llm.yaml
name: 'qwen_llm'
description: '通义千问 LLM'
model_name: 'qwen-max'
max_tokens: 2000
temperature: 0.5
```

## 代码示例

```python
from agentuniverse.agent.agent_manager import AgentManager
from agentuniverse.base.agentuniverse import AgentUniverse

# 初始化框架（加载配置目录）
AgentUniverse().start(config_path='./config/config.toml')

# 获取 Agent
research_agent = AgentManager().get_instance_obj('research_agent')

# 运行
output = research_agent.run(
    input="分析 LangGraph 和 AgentScope 的技术差异"
)
print(output.get_data('output'))
```

## 自定义 Agent

```python
from agentuniverse.agent.agent import Agent
from agentuniverse.agent.input_object import InputObject
from agentuniverse.agent.output_object import OutputObject

class CustomResearchAgent(Agent):
    """自定义研究 Agent"""

    def input_keys(self) -> list[str]:
        return ['input']

    def output_keys(self) -> list[str]:
        return ['output', 'sources']

    def parse_input(self, input_object: InputObject, agent_input: dict) -> dict:
        agent_input['input'] = input_object.get_data('input')
        return agent_input

    def parse_result(self, agent_result: dict) -> OutputObject:
        return OutputObject({
            'output': agent_result.get('output', ''),
            'sources': agent_result.get('sources', []),
        })
```

## 工具定义

```python
from agentuniverse.agent.action.tool.tool import Tool
from agentuniverse.agent.action.tool.tool_manager import ToolManager

class WeatherTool(Tool):
    name: str = 'weather_tool'
    description: str = '获取城市天气信息'

    def execute(self, tool_input: str, **kwargs) -> str:
        """tool_input 是 LLM 传入的参数（字符串）"""
        data = {
            "北京": "晴天 25°C",
            "上海": "多云 22°C",
        }
        # 从输入中提取城市名
        for city in data:
            if city in tool_input:
                return f"{city}天气：{data[city]}"
        return "未找到城市天气数据"
```

对应 YAML：

```yaml
# tool/weather_tool.yaml
name: 'weather_tool'
description: '获取指定城市的天气信息'
tool_type: 'api'
input_keys:
  - 'city'
```

## PEER 多 Agent 协作示例

```python
from agentuniverse.agent.agent_manager import AgentManager

# PEER 模式：四个 Agent 协作完成一个复杂任务
peer_agent = AgentManager().get_instance_obj('peer_agent')

result = peer_agent.run(
    input="深度分析 2024 年中国 AI 大模型市场格局，给出投资建议"
)

# PEER Agent 内部：
# 1. Planning Agent 把任务拆分：市场规模、主要玩家、技术对比、政策环境
# 2. Executing Agent 分别执行每个子任务
# 3. Expressing Agent 整合所有结果生成报告
# 4. Reviewing Agent 检查报告质量，不满足则触发重新执行
```

## 可观测性

AgentUniverse 内置监控：

```python
# 开启 tracing
from agentuniverse.base.tracing import Tracer

tracer = Tracer()
tracer.start_trace(agent_name='research_agent', input=user_input)
# ... 执行 Agent ...
tracer.end_trace(output=result)

# 查看执行链路
trace_info = tracer.get_trace()
for step in trace_info.steps:
    print(f"{step.agent}: {step.duration_ms}ms")
```

## 知识组件（Knowledge）

```python
from agentuniverse.agent.action.knowledge.knowledge import Knowledge

# 接入知识库
knowledge = Knowledge(
    name='company_kb',
    description='公司内部知识库',
)

# 在 Agent 配置中引用
# agent.yaml:
# knowledge:
#   - 'company_kb'
```

## 优缺点

**优点：**
- PEER 模式是经过实践的多 Agent 协作方案
- 配置文件驱动，业务逻辑和代码解耦
- 内置可观测性，企业级 trace 支持
- 通义千问等国内模型集成好
- 企业知识库接入能力强

**缺点：**
- 配置文件学习成本高，灵活性相对低
- 文档以中文为主
- 社区规模小，开源时间不长
- 相比 LangGraph 在状态管理上不够灵活

## 适合什么场景

- 企业内部复杂分析任务（报告生成、市场研究）
- 需要 PEER 模式的多 Agent 协作
- 华为云 / 阿里云生态
- 对可观测性和审计要求高的企业项目
