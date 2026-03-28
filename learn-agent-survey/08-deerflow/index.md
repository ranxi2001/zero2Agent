---
layout: default
title: "DeerFlow：字节跳动的 Deep Research 框架"
description: 字节跳动开源的深度研究 Agent——多 Agent 协作、网络搜索、报告生成，基于 LangGraph 构建
eyebrow: 框架调研 · 08
---

# DeerFlow：字节跳动的 Deep Research 框架

DeerFlow 是字节跳动 2025 年初开源的 Deep Research 框架，用于自动化地进行深度信息调研并生成结构化报告。它底层基于 LangGraph，是"用框架搭框架"的典型案例。

GitHub：[bytedance/deer-flow](https://github.com/bytedance/deer-flow)

## 是什么

给定一个研究问题，DeerFlow 会：

1. **规划**：把问题拆解成多个子研究方向
2. **搜索**：并行搜索网络，收集信息
3. **分析**：对搜索结果进行摘要和筛选
4. **综合**：把所有子结果整合成结构化报告

类似 OpenAI Deep Research、Perplexity Deep Research，但完全开源可自部署。

## 架构

```
用户输入问题
    |
[Coordinator Agent]  ← 协调整个流程
    |
[Planner Agent]      ← 把问题拆成子任务
    |
    +-- [Researcher Agent 1]  ← 并行研究子任务
    +-- [Researcher Agent 2]
    +-- [Researcher Agent N]
    |
[Writer Agent]       ← 整合结果，生成最终报告
    |
最终研究报告
```

## 安装与配置

```bash
git clone https://github.com/bytedance/deer-flow.git
cd deer-flow
pip install -r requirements.txt
```

配置文件 `conf.yaml`：

```yaml
# LLM 配置
BASIC_MODEL:
  base_url: "https://api.openai.com/v1"
  model: "gpt-4o"
  api_key: "your-key"

REASONING_MODEL:
  base_url: "https://api.openai.com/v1"
  model: "o3-mini"
  api_key: "your-key"

# 搜索配置
SEARCH_API: "tavily"  # 或 "serper", "duckduckgo"
TAVILY_API_KEY: "your-tavily-key"
```

## 基本使用

```python
import asyncio
from src.workflow import run_agent_workflow

async def main():
    # 运行深度研究
    result = await run_agent_workflow(
        user_input="分析 2024-2025 年 AI Agent 框架生态的发展趋势",
        debug=True,
    )
    print(result["final_report"])

asyncio.run(main())
```

或者直接命令行：

```bash
python main.py --query "LangGraph vs AutoGen 技术对比分析"
```

## 核心流程代码（简化版）

DeerFlow 的核心是 LangGraph 的多 Agent 图，下面是简化后的关键逻辑：

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Annotated
import operator

class ResearchState(TypedDict):
    user_input: str
    research_plan: List[str]
    search_results: Annotated[List[str], operator.add]
    final_report: str

def coordinator_node(state: ResearchState) -> dict:
    """协调器：判断是直接回答还是需要深度研究"""
    # 简单问题直接回答，复杂问题启动研究流程
    return {}

def planner_node(state: ResearchState) -> dict:
    """规划器：把问题拆解成子研究任务"""
    question = state["user_input"]

    # 调用 LLM 生成研究计划
    plan_response = llm.invoke(f"""
把以下研究问题拆解成 3-5 个独立的子研究方向，每行一个：

问题：{question}

子任务：""")

    tasks = [line.strip() for line in plan_response.content.split("\n") if line.strip()]
    return {"research_plan": tasks}

def researcher_node(state: ResearchState) -> dict:
    """研究员：对一个子任务进行网络搜索和分析"""
    # 每个子任务调用搜索 API
    results = []
    for task in state["research_plan"]:
        search_result = search_web(task)  # 调用 Tavily/Serper
        analyzed = analyze_result(task, search_result)  # LLM 分析
        results.append(analyzed)
    return {"search_results": results}

def writer_node(state: ResearchState) -> dict:
    """写作者：整合所有研究结果，生成最终报告"""
    all_results = "\n\n".join(state["search_results"])

    report = llm.invoke(f"""
基于以下研究材料，为问题"{state['user_input']}"撰写一份深度分析报告：

{all_results}

报告格式：
# 标题
## 执行摘要
## 详细分析
## 结论与建议
""")
    return {"final_report": report.content}

# 组装图
graph = StateGraph(ResearchState)
graph.add_node("coordinator", coordinator_node)
graph.add_node("planner", planner_node)
graph.add_node("researcher", researcher_node)
graph.add_node("writer", writer_node)

graph.set_entry_point("coordinator")
graph.add_edge("coordinator", "planner")
graph.add_edge("planner", "researcher")
graph.add_edge("researcher", "writer")
graph.add_edge("writer", END)
```

## Web UI

DeerFlow 提供了 Next.js 前端：

```bash
cd web
npm install
npm run dev
# 访问 http://localhost:3000
```

前端展示：
- 实时查看每个 Agent 的执行过程
- 流式显示搜索结果和分析过程
- 最终报告的 Markdown 渲染

## 自定义搜索工具

```python
from src.tools.search import create_search_tool

# 接入自定义搜索源
def custom_search(query: str) -> list[dict]:
    """接入内部知识库或特定数据源"""
    results = your_internal_api.search(query)
    return [{"title": r.title, "content": r.content, "url": r.url} for r in results]

# 注册到 DeerFlow
search_tool = create_search_tool(custom_search)
```

## 与自己搭建的对比

| 维度 | DeerFlow | 自己用 LangGraph 搭 |
|------|----------|-------------------|
| 上手速度 | 快，clone 即用 | 慢，需要设计架构 |
| 灵活性 | 受限于 DeerFlow 结构 | 完全自由 |
| 生产可用 | 需要适配 | 根据需求定制 |
| 学习价值 | 读源码学多 Agent 设计 | 深度理解每个组件 |

## 优缺点

**优点：**
- 开源、可本地部署，数据不出境
- 基于 LangGraph，架构清晰可读
- 提供 Web UI，演示效果好
- 字节跳动生产验证

**缺点：**
- 需要搜索 API（Tavily/Serper 付费）
- 研究任务耗时较长（多轮搜索+分析）
- 定制需要改源码，不如自建灵活

## 适合什么场景

- 需要自动化深度研究报告的业务
- 竞品分析、市场调研自动化
- 企业内部知识库的深度问答
- 想学习多 Agent 系统设计（读源码）
