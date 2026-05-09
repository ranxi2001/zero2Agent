---
layout: default
title: RAG：检索增强的工程实现
description: 从向量检索到混合召回，Coding Agent 场景下 RAG 的正确实现
eyebrow: OpenClaw / 03
---

# RAG：检索增强的工程实现

RAG（Retrieval-Augmented Generation）在 Agent 系统中有两种用法：

1. **知识库问答**：用户提问 → 检索相关文档 → 注入上下文 → 生成回答
2. **代码库导航**：Agent 需要理解大型代码库时，按需检索相关代码片段

这一节覆盖从基础实现到生产级优化的完整路径。

---

## 核心管线

```
文档 → 分块 → 编码（Embedding）→ 写入向量库
                                         ↓
用户查询 → 编码 → 向量检索 Top-K → Rerank → 注入 Prompt → LLM 生成
```

每个环节的选择直接影响最终效果。

---

## 分块策略

### 按语义边界分块（推荐）

```typescript
// 代码文件：按函数/类边界切分
function chunkByAST(code: string, language: string): Chunk[] {
  const tree = parser.parse(code, language)
  return tree.rootNode.children
    .filter(node => ['function', 'class', 'method'].includes(node.type))
    .map(node => ({
      content: node.text,
      metadata: { type: node.type, name: node.name, startLine: node.startPosition.row }
    }))
}
```

### 按固定窗口分块（简单场景）

```typescript
function chunkByWindow(text: string, size = 512, overlap = 64): string[] {
  const chunks: string[] = []
  for (let i = 0; i < text.length; i += size - overlap) {
    chunks.push(text.slice(i, i + size))
  }
  return chunks
}
```

**面试考点**：为什么需要 overlap？因为语义可能跨越切分边界，overlap 保证边界处的信息不丢失。

---

## Embedding 选型

| 模型 | 维度 | 特点 |
|------|------|------|
| `text-embedding-3-small` (OpenAI) | 1536 | 通用能力强，需代理 |
| `BGE-M3` (BAAI) | 1024 | 中文优秀，开源可部署 |
| `GTE-Qwen2` (阿里) | 768 | 代码理解能力强 |
| `Cohere embed-v3` | 1024 | 支持搜索/分类/聚类多任务 |

Coding Agent 场景推荐 **GTE-Qwen2** 或 **BGE-M3**——代码和中文都表现好，且可本地部署避免网络延迟。

---

## 向量数据库选择

| 工具 | 适用场景 | 特点 |
|------|---------|------|
| **ChromaDB** | 本地开发、原型验证 | Python 嵌入式，零配置 |
| **pgvector** | 已有 PostgreSQL | 无需新增服务，事务一致性 |
| **Milvus** | 大规模生产（亿级） | 分布式，高吞吐 |
| **Qdrant** | 中等规模生产 | Rust 实现，单机性能好 |

---

## 混合检索：稠密 + 稀疏

单纯的向量检索有盲区——对精确关键词匹配（函数名、变量名）效果差。生产系统通常用混合检索：

```typescript
// 伪代码：混合检索 + RRF 融合
async function hybridSearch(query: string, k: number): Promise<Chunk[]> {
  // 稠密检索：语义相似
  const denseResults = await vectorDB.search(embed(query), k * 2)

  // 稀疏检索：关键词匹配（BM25）
  const sparseResults = await bm25Index.search(query, k * 2)

  // Reciprocal Rank Fusion 融合排序
  return reciprocalRankFusion(denseResults, sparseResults, k)
}

function reciprocalRankFusion(lists: Result[][], k: number): Result[] {
  const scores = new Map<string, number>()
  const RRF_K = 60 // 常数，控制排名衰减速度

  for (const list of lists) {
    list.forEach((item, rank) => {
      const score = 1 / (RRF_K + rank + 1)
      scores.set(item.id, (scores.get(item.id) || 0) + score)
    })
  }

  return [...scores.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, k)
    .map(([id]) => getChunkById(id))
}
```

**GBrain**（OpenClaw 的生产记忆系统）就是用 Postgres + pgvector + BM25 + RRF 实现的混合检索，P@5 达到 49.1%，R@5 达到 97.9%。

---

## Reranker：精排提升精度

粗召回 Top-K 后，用 Cross-Encoder 做精排：

```typescript
async function rerankResults(query: string, chunks: Chunk[], topN: number): Promise<Chunk[]> {
  const scored = await Promise.all(
    chunks.map(async chunk => ({
      chunk,
      score: await crossEncoder.score(query, chunk.content)
    }))
  )
  return scored.sort((a, b) => b.score - a.score).slice(0, topN)
}
```

常用 Reranker：`bge-reranker-v2-m3`、`cohere-rerank-v3`。

精排可以将 Top-5 精度提升 10-20%，但增加约 200ms 延迟。

---

## 在 Agent 中的集成方式

Coding Agent 中 RAG 通常不是独立的"检索步骤"，而是作为**工具**被模型按需调用：

```typescript
const searchCodeTool = {
  name: 'search_codebase',
  description: '在代码库中搜索与查询语义相关的代码片段',
  parameters: {
    query: { type: 'string', description: '搜索查询' },
    k: { type: 'number', description: '返回结果数量', default: 5 }
  },
  execute: async ({ query, k }) => {
    const results = await hybridSearch(query, k)
    return results.map(r => `${r.metadata.path}:${r.metadata.startLine}\n${r.content}`).join('\n---\n')
  }
}
```

模型自己决定什么时候需要搜索代码库，而不是每次都强制检索。

---

## OpenClaw 的 RAG 特点

OpenClaw 没有在核心架构中内置 RAG——它把 RAG 当作**可选插件**。原因：

1. Coding Agent 的主要操作是读写文件（`read` 工具带 offset/limit），大多数情况下精确路径 + grep 就够了
2. 只有在处理大规模知识库（文档库、工单库）时才需要向量检索
3. RAG 质量高度依赖分块策略和 embedding 选型，不适合做通用默认方案

但 GBrain（OpenClaw 的外部记忆宿主）提供了完整的 RAG 能力：
- Postgres + pgvector 混合检索
- "Compiled Truth + Timeline" 模式——每个知识页有当前理解 + 追加式证据链
- 自动知识图谱：提取实体引用和类型化链接
- "Dream Cycle" 夜间合成：定期整理、聚合、丰富知识

---

## 面试高频题

**Q：RAG 和 Fine-tuning 什么时候选哪个？**

| 维度 | RAG | Fine-tuning |
|------|-----|-------------|
| 知识更新 | 实时（改文档即生效） | 需要重新训练 |
| 幻觉控制 | 有来源可追溯 | 无法保证 |
| 成本 | 推理时增加检索开销 | 训练成本高，推理不增加 |
| 适用场景 | 知识库问答、文档检索 | 风格/格式/推理模式固化 |

**Q：向量检索的 Top-K 设多少合适？**

> 取决于 Reranker 和上下文窗口。经验值：粗召回 K=20，精排后取 Top-5 注入 Prompt。K 太大会引入噪声，太小可能漏掉相关内容。

**Q：Embedding 模型和生成模型用同一个可以吗？**

> 不推荐。Embedding 模型是专门训练的双塔/对比学习模型，生成模型的隐状态不适合做相似度检索。用专用 Embedding 模型效果显著更好。

---

下一篇：[工具系统：MCP 协议与并行执行](../04-tools/index.html)
