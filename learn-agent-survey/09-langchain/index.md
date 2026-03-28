---
layout: default
title: "LangChain：最流行的 LLM 框架"
description: LangChain 核心概念精讲——LCEL、Chain、Agent、Tool、Memory，以及什么时候不该用它
eyebrow: 框架调研 · 09
---

# LangChain：最流行的 LLM 框架

LangChain 是目前 GitHub star 最多的 LLM 框架，几乎是 LLM 应用开发的代名词。但它也是被吐槽最多的框架之一——过度抽象、文档混乱、API 频繁变动。

这篇不是 LangChain 的完整教程，而是帮你快速判断：**LangChain 能解决什么问题，什么时候换其他方案更好**。

GitHub：[langchain-ai/langchain](https://github.com/langchain-ai/langchain)

## 安装

```bash
pip install langchain langchain-openai langchain-community
```

## 核心概念演进

LangChain 经历了两个时代：

**v0.1 时代（Chain 为核心）**

```python
# 旧写法：显式链条
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

chain = LLMChain(
    llm=ChatOpenAI(),
    prompt=PromptTemplate.from_template("翻译成英文：{text}"),
)
result = chain.run(text="你好世界")
```

**v0.2+ 时代（LCEL 为核心）**

```python
# 新写法：LCEL 管道
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

llm = ChatOpenAI(model="gpt-4o-mini")
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个翻译助手"),
    ("human", "翻译成英文：{text}"),
])

chain = prompt | llm | StrOutputParser()
result = chain.invoke({"text": "你好世界"})
print(result)  # Hello World
```

`|` 是 LCEL（LangChain Expression Language）的管道操作符，把组件串联成链。

## LCEL：管道组合

LCEL 的核心思路是**函数组合**：

```python
from langchain_core.runnables import RunnableLambda, RunnablePassthrough

# 每个 Runnable 都实现 .invoke() / .stream() / .batch()
step1 = RunnableLambda(lambda x: x.upper())
step2 = RunnableLambda(lambda x: f"结果：{x}")

chain = step1 | step2
print(chain.invoke("hello"))  # 结果：HELLO

# 并行执行
from langchain_core.runnables import RunnableParallel
parallel = RunnableParallel(
    upper=RunnableLambda(str.upper),
    lower=RunnableLambda(str.lower),
)
print(parallel.invoke("Hello"))  # {"upper": "HELLO", "lower": "hello"}
```

## RAG：检索增强生成

LangChain 在 RAG 场景最成熟：

```python
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# 1. 加载文档
loader = TextLoader("knowledge.txt", encoding="utf-8")
docs = loader.load()

# 2. 切分
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = splitter.split_documents(docs)

# 3. 向量化存储
vectorstore = Chroma.from_documents(chunks, OpenAIEmbeddings())
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# 4. RAG Chain
prompt = ChatPromptTemplate.from_template("""
根据以下上下文回答问题：

上下文：{context}

问题：{question}

回答：""")

rag_chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | ChatOpenAI(model="gpt-4o-mini")
    | StrOutputParser()
)

result = rag_chain.invoke("什么是 LangGraph？")
print(result)
```

## Agent（工具调用）

```python
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate

@tool
def get_weather(city: str) -> str:
    """获取城市天气信息"""
    data = {"北京": "晴天 25°C", "上海": "多云 22°C"}
    return data.get(city, "暂无数据")

@tool
def calculate(expression: str) -> str:
    """计算数学表达式"""
    try:
        return str(eval(expression))
    except:
        return "计算错误"

llm = ChatOpenAI(model="gpt-4o-mini")
tools = [get_weather, calculate]

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个助手，可以查天气和做数学计算。"),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),  # Agent 的中间思考过程
])

agent = create_tool_calling_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

result = executor.invoke({"input": "北京天气怎样？另外 100 * 3.14 等于多少？"})
print(result["output"])
```

## 流式输出

```python
for chunk in chain.stream({"text": "你好世界"}):
    print(chunk, end="", flush=True)
```

```python
# Agent 流式
for event in executor.stream({"input": "北京天气？"}):
    if "output" in event:
        print(event["output"])
```

## Memory（历史记忆）

```python
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain

memory = ConversationBufferMemory()
conversation = ConversationChain(
    llm=ChatOpenAI(model="gpt-4o-mini"),
    memory=memory,
    verbose=False,
)

conversation.predict(input="我叫张三")
response = conversation.predict(input="我叫什么名字？")
print(response)  # 应记得张三
```

## LangSmith：可观测性

LangChain 的配套工具 LangSmith 提供 trace：

```python
import os
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = "your-langsmith-key"
os.environ["LANGCHAIN_PROJECT"] = "my-project"

# 之后所有 LangChain 调用都会自动记录到 LangSmith
result = rag_chain.invoke("问题")
# 在 LangSmith 控制台可以看到完整执行链路
```

## LangChain 的问题

坦白说，LangChain 有几个真实存在的痛点：

**1. 过度抽象**

```python
# 简单任务被包装得很重
# 实际上只是：response = llm.invoke(prompt)
# 但 LangChain 要写很多行
```

**2. API 频繁变动**

2023 年的代码在 2024 年版本里基本都要改写。

**3. 调试困难**

三层抽象之间的错误，stack trace 很难读。

**4. 性能开销**

轻量任务不需要这么重的框架。

## 什么时候用 LangChain

**适合：**
- RAG 场景：文档加载、切分、向量化、检索有大量现成实现
- 快速原型：大量预置 Loader、Splitter、Retriever
- 社区工具丰富：需要某个特定 API 集成时，langchain-community 可能已经有了

**不适合：**
- 生产环境的核心 Agent 逻辑（优先考虑原厂 SDK 或 LangGraph）
- 简单的 LLM 调用（直接用 openai/anthropic 包更清晰）
- 需要精细控制工具调用流程（用 Anthropic SDK 手动写更可控）

## 和 LangGraph 的关系

LangGraph 是 LangChain 团队开发的图执行框架，两者可以混用：

```python
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI

# LangGraph 直接支持 LangChain 的 Tool
agent = create_react_agent(
    model=ChatOpenAI(model="gpt-4o-mini"),
    tools=[get_weather, calculate],
)
result = agent.invoke({"messages": [("user", "北京天气")]})
```

**建议：** 用 LangGraph 做 Agent 控制流，用 LangChain 的工具/加载器/向量数据库做周边集成，不要用 LangChain 的 Agent 抽象。
