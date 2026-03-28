---
layout: default
title: 接入 LLM：OpenAI 与 HuggingFace
description: 在 LangGraph 节点里调用 ChatOpenAI 和 HuggingFaceEndpoint，构建完整的 LLM-powered Workflow
eyebrow: learn-langgraph · 07
---

# 接入 LLM：OpenAI 与 HuggingFace

前几篇的节点函数里，LLM 调用都用占位符代替了。这一篇把真实的 LLM 接进来，展示 ChatOpenAI 和 HuggingFace 两种方案在 LangGraph 节点里的完整写法。

## 安装依赖

```bash
# OpenAI
pip install langchain-openai

# HuggingFace
pip install langchain-huggingface huggingface_hub

# 两者都需要
pip install langgraph langchain-core
```

## OpenAI 方案

### 基础用法

```python
import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

# 初始化（建议在节点外部初始化，避免每次调用都重新创建）
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    api_key=os.environ.get("OPENAI_API_KEY"),
)

def summarize_node(state: dict) -> dict:
    """在节点里调用 ChatOpenAI"""
    text = state["input_text"]

    response = llm.invoke([
        SystemMessage(content="你是一个专业的文本摘要助手。"),
        HumanMessage(content=f"请用 2-3 句话总结以下内容：\n\n{text}"),
    ])

    return {"summary": response.content}
```

### 用 PromptTemplate 管理 Prompt

```python
from langchain_core.prompts import ChatPromptTemplate

prompt_template = ChatPromptTemplate.from_messages([
    ("system", "你是一个专业的{role}。"),
    ("human", "{task}"),
])

chain = prompt_template | llm

def analyze_node(state: dict) -> dict:
    response = chain.invoke({
        "role": "代码审查专家",
        "task": f"审查以下代码：\n{state['code']}",
    })
    return {"review": response.content}
```

### 结构化输出

```python
from pydantic import BaseModel, Field
from typing import List

class CodeReview(BaseModel):
    score: int = Field(description="代码质量评分 1-10")
    issues: List[str] = Field(description="发现的问题列表")
    suggestions: List[str] = Field(description="改进建议")

structured_llm = llm.with_structured_output(CodeReview)

def review_node(state: dict) -> dict:
    result: CodeReview = structured_llm.invoke(
        f"审查这段代码并给出评分：\n{state['code']}"
    )
    return {
        "score": result.score,
        "issues": result.issues,
        "suggestions": result.suggestions,
    }
```

## HuggingFace 方案

### 基础用法

```python
import os
from langchain_huggingface import HuggingFaceEndpoint

llm = HuggingFaceEndpoint(
    repo_id="mistralai/Mistral-7B-Instruct-v0.2",
    huggingfacehub_api_token=os.environ["HUGGINGFACEHUB_API_TOKEN"],
    task="text-generation",
    max_new_tokens=512,
    temperature=0.1,
    do_sample=True,
)

def generate_node(state: dict) -> dict:
    """HuggingFace 节点"""
    topic = state["topic"]

    # Mistral 用 [INST] 标记
    prompt = f"[INST] 用中文简要介绍：{topic} [/INST]"

    response = llm.invoke(prompt)
    return {"output": response}
```

### 不同模型的 Prompt 格式

不同模型有不同的指令格式，调用时要匹配：

```python
# Mistral / Mixtral
prompt = f"[INST] {instruction} [/INST]"

# Llama 2
prompt = f"<s>[INST] <<SYS>>\n{system}\n<</SYS>>\n\n{user} [/INST]"

# Llama 3
prompt = f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n{user}<|eot_id|><|start_header_id|>assistant<|end_header_id|>"

# ChatML（Qwen, Yi 等）
prompt = f"<|im_start|>system\n{system}<|im_end|>\n<|im_start|>user\n{user}<|im_end|>\n<|im_start|>assistant\n"
```

### 用 ChatHuggingFace 统一接口

`ChatHuggingFace` 用 `HumanMessage`/`SystemMessage` 接口，自动处理 prompt 格式：

```python
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain_core.messages import HumanMessage, SystemMessage

endpoint = HuggingFaceEndpoint(
    repo_id="mistralai/Mistral-7B-Instruct-v0.2",
    huggingfacehub_api_token=os.environ["HUGGINGFACEHUB_API_TOKEN"],
    task="text-generation",
    max_new_tokens=512,
)

chat_llm = ChatHuggingFace(llm=endpoint)

def chat_node(state: dict) -> dict:
    response = chat_llm.invoke([
        SystemMessage(content="你是一个助手。"),
        HumanMessage(content=state["user_input"]),
    ])
    return {"response": response.content}
```

## 完整示例：多步内容生成 Workflow

用 OpenAI 实现一个完整的三步内容生成流程：

```python
import os
from typing import TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END

# ===== State =====
class ContentState(TypedDict):
    topic: str
    keywords: str
    outline: str
    article: str

# ===== LLM（只初始化一次）=====
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.7,
    api_key=os.environ.get("OPENAI_API_KEY"),
)

# ===== 节点 =====

def extract_keywords(state: ContentState) -> dict:
    """提取关键词"""
    response = llm.invoke([
        HumanMessage(content=f"从主题'{state['topic']}'中提取 5 个核心关键词，用逗号分隔，只输出关键词：")
    ])
    return {"keywords": response.content.strip()}

def create_outline(state: ContentState) -> dict:
    """根据关键词生成大纲"""
    response = llm.invoke([
        HumanMessage(content=(
            f"基于主题'{state['topic']}'和关键词'{state['keywords']}'，"
            f"生成一个 4 节的文章大纲，每节一行，格式为：数字. 标题"
        ))
    ])
    return {"outline": response.content.strip()}

def write_article(state: ContentState) -> dict:
    """根据大纲写文章"""
    response = llm.invoke([
        HumanMessage(content=(
            f"根据以下大纲，写一篇关于'{state['topic']}'的短文（约 300 字）：\n\n"
            f"{state['outline']}"
        ))
    ])
    return {"article": response.content.strip()}

# ===== 图 =====

graph = StateGraph(ContentState)
graph.add_node("keywords", extract_keywords)
graph.add_node("outline", create_outline)
graph.add_node("write", write_article)

graph.set_entry_point("keywords")
graph.add_edge("keywords", "outline")
graph.add_edge("outline", "write")
graph.add_edge("write", END)

app = graph.compile()

# ===== 运行 =====
if __name__ == "__main__":
    result = app.invoke({
        "topic": "LangGraph 状态图编程",
        "keywords": "",
        "outline": "",
        "article": "",
    })

    print("关键词:", result["keywords"])
    print("\n大纲:\n", result["outline"])
    print("\n文章:\n", result["article"])
```

## 在节点里处理 LLM 错误

```python
import time
from langchain_core.exceptions import OutputParserException

def robust_llm_node(state: dict) -> dict:
    """带重试的 LLM 节点"""
    max_retries = 3

    for attempt in range(max_retries):
        try:
            response = llm.invoke([HumanMessage(content=state["prompt"])])
            return {"result": response.content}
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # 指数退避
                continue
            else:
                return {"result": f"错误：{str(e)}", "error": True}
```

## 环境变量管理

```python
# 推荐用 .env 文件 + python-dotenv
from dotenv import load_dotenv
load_dotenv()

# .env 文件内容：
# OPENAI_API_KEY=sk-...
# HUGGINGFACEHUB_API_TOKEN=hf_...

import os
openai_key = os.environ["OPENAI_API_KEY"]
hf_token = os.environ["HUGGINGFACEHUB_API_TOKEN"]
```

## OpenAI vs HuggingFace 选哪个

| 维度 | OpenAI (GPT-4o) | HuggingFace (Mistral 等) |
|------|-----------------|------------------------|
| 质量 | 更高，特别是复杂推理 | 中等，小模型差距明显 |
| 成本 | 按 token 计费 | 推理 API 免费（有限额） |
| 速度 | 快 | 免费 Endpoint 较慢 |
| 离线部署 | 不支持 | 支持（本地推理） |
| 结构化输出 | 原生支持 | 需要自己解析 |
| 适合场景 | 生产环境，高质量需求 | 学习实验，成本敏感 |

学习阶段：用 HuggingFace 免费额度跑通流程，不需要花钱。

生产阶段：换 OpenAI/Claude，只改节点里的 LLM 初始化代码，图结构不变。

## 小结

- LLM 在节点函数里调用，图结构与模型选择完全解耦
- OpenAI：`ChatOpenAI` + `HumanMessage`/`SystemMessage`，支持 `with_structured_output`
- HuggingFace：`HuggingFaceEndpoint` + `ChatHuggingFace`，注意 prompt 格式
- LLM 对象在图外部初始化，节点函数闭包引用
- 生产代码记得加重试和错误处理

到这里，LangGraph 的核心模式都覆盖到了：顺序图、条件分支、并行执行、Prompt Chaining、LLM 集成。

接下来可以去看 [OpenClaw 模块](../../learn-openclaw/index.html) 或 [Claude Code 模块](../../learn-claude-code/index.html)，把 LangGraph 和手写框架的思路结合起来。
