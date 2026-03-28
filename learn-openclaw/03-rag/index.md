---
layout: default
title: RAG 的本质是 VectorDB
description: 把 RAG 拆到最小单位——一个向量数据库和一次近邻检索
eyebrow: OpenClaw / 03
---

# RAG 的本质是 VectorDB

RAG（Retrieval-Augmented Generation）听起来很复杂。但把它拆到最小单位，就是两件事：

1. 把文档存进向量数据库
2. 用户问问题时，检索最相关的几段，拼进 prompt

这一节从这里出发，把 RAG 的实现路径走一遍。

---

## 为什么需要 RAG

LLM 的上下文窗口有限。即使是 128K token 的模型，遇到大型代码库或者企业知识库，直接把所有内容塞进去也不现实。

RAG 的思路是：**只给模型看它需要看的那部分**。

```
用户提问
   ↓
向量检索：在知识库里找最相关的 K 段
   ↓
把这 K 段拼进 prompt
   ↓
模型生成回答
```

---

## 向量数据库是什么

向量数据库存的不是文本，而是文本对应的**嵌入向量（embedding）**——一个高维浮点数组，捕捉了文本的语义。

```python
# 同一个意思，向量应该相近
"Python 如何处理异常" → [0.12, -0.34, 0.91, ...]
"Python exception handling" → [0.11, -0.35, 0.89, ...]
```

检索时，把用户的问题也转成向量，找余弦距离最近的 K 个文档片段。

---

## 实现：三个步骤

### 步骤 1：分块（Chunking）

把文档切成适合模型阅读的片段。

```python
# tools/rag/chunker.py
def chunk_text(text: str, chunk_size: int = 512, overlap: int = 64) -> list[str]:
    """按字符数分块，支持重叠防止语义断裂"""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks
```

重叠（overlap）是关键：边界处的语义不应该被硬切断。

### 步骤 2：嵌入 + 存入向量库

```python
# tools/rag/store.py
import chromadb
from openai import OpenAI

client = OpenAI()
chroma = chromadb.PersistentClient(path="./rag_db")
collection = chroma.get_or_create_collection("docs")

def embed(text: str) -> list[float]:
    resp = client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    return resp.data[0].embedding

def add_document(doc_id: str, text: str, metadata: dict = None):
    chunks = chunk_text(text)
    for i, chunk in enumerate(chunks):
        collection.add(
            ids=[f"{doc_id}_{i}"],
            embeddings=[embed(chunk)],
            documents=[chunk],
            metadatas=[metadata or {}]
        )
```

### 步骤 3：检索

```python
def retrieve(query: str, k: int = 5) -> list[str]:
    results = collection.query(
        query_embeddings=[embed(query)],
        n_results=k
    )
    return results["documents"][0]
```

---

## 接进 Agent

把检索嵌进 Node 里：

```python
# examples/rag_agent/main.py
from core.node import Node, Flow, shared
from core.llm import call_llm
from tools.rag.store import retrieve

shared["messages"] = []

class RAGChatNode(Node):
    def exec(self, _):
        user_query = shared["messages"][-1]["content"]

        # 检索相关片段
        relevant_chunks = retrieve(user_query, k=5)
        context = "\n\n---\n\n".join(relevant_chunks)

        # 把检索结果注入 system prompt
        system_prompt = f"""你是一个知识库助手。回答时优先参考以下上下文：

{context}

如果上下文不足以回答，请如实说明。"""

        response = call_llm(shared["messages"], system_prompt=system_prompt)
        shared["messages"].append(response)
        return "output", response["content"]

class OutputNode(Node):
    def exec(self, text):
        print(f"\nAssistant: {text}\n")
        return "default", None

rag_node = RAGChatNode()
out_node = OutputNode()
rag_node - "output" >> out_node

while True:
    user_input = input("You: ").strip()
    if not user_input:
        continue
    shared["messages"].append({"role": "user", "content": user_input})
    Flow(rag_node).run()
```

<div class="mermaid">
flowchart TD
    A([用户输入]) --> B[RAGChatNode]
    B --> C[向量检索 top-K]
    C --> D[拼入 system_prompt]
    D --> E[调用 LLM]
    E --> F[OutputNode]
    F --> A
</div>

---

## 为什么选 Chroma，不选 Milvus 或 pgvector

| 工具 | 适用场景 |
|------|---------|
| **Chroma** | 本地开发、小型项目、嵌入式部署 |
| **pgvector** | 已有 PostgreSQL、数据量中等 |
| **Milvus** | 大规模生产（亿级向量） |
| **Pinecone** | 托管服务，不想自运维 |

大多数 Coding Agent 的知识库不需要亿级向量。Chroma 零配置、纯 Python、本地持久化，是原型和中小型生产最合适的选择。

---

## Embedding 模型选择

```bash
# 配置 embedding 模型（OpenAI 协议兼容）
export OPENAI_API_KEY="your-key"
export OPENAI_BASE_URL="https://api.moonshot.cn/v1"
```

国内常用选项：

| 模型 | 维度 | 备注 |
|------|------|------|
| `text-embedding-3-small` | 1536 | OpenAI，需代理 |
| 智谱 `embedding-3` | 2048 | 国内直连 |
| Moonshot（暂不支持 embedding）| — | 用 LLM 模型 |

如果用 Kimi 或智谱做 LLM，embedding 通常要单独调另一个接口。在 `tools/rag/store.py` 里单独配一个 embedding 用的 client 即可。

---

## 一个常见误区

**RAG 不是搜索引擎**。

全文搜索（BM25、Elasticsearch）匹配的是关键词。向量检索匹配的是**语义**。

两者互补，很多生产系统用混合检索（hybrid search）：先用关键词召回候选集，再用向量排序。Chroma 目前不原生支持 BM25，但你可以自己先用 `grep` 过滤，再用向量 rerank。

---

## 完整目录结构

```
rag_db/           ← Chroma 持久化目录
tools/
  rag/
    chunker.py    ← 文本分块
    store.py      ← embed + 向量库操作
examples/
  rag_agent/
    main.py       ← 接入 Flow 的完整示例
    ingest.py     ← 把文档批量写入向量库
```

`ingest.py` 示例：

```python
# examples/rag_agent/ingest.py
import os
from tools.rag.store import add_document

# 把 docs/ 目录下所有 .md 文件写入向量库
for fname in os.listdir("docs"):
    if fname.endswith(".md"):
        path = os.path.join("docs", fname)
        with open(path) as f:
            text = f.read()
        add_document(doc_id=fname, text=text, metadata={"source": fname})
        print(f"Indexed: {fname}")
```

---

下一篇：[Tool / MCP / Skill 全解析](../04-tools/index.html)
