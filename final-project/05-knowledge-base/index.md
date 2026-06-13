---
layout: default
title: 知识库构建
description: 从 learn-agent-interview 导入 385+ 道题，构建 FTS5 + embedding 双通道检索
eyebrow: Final Project / 05
---

# 知识库构建

面试诊断 Agent 的诊断质量上限取决于知识库。如果没有高质量参考答案做对比，诊断就会退化成 LLM 的自由发挥——结果不稳定、标准不统一。

我们的知识库来源是现成的：zero2Agent 项目的 `learn-agent-interview` 模块，15 个维度、385+ 道面试题，每题都有标准格式的新手答、高手答和差距分析。

本篇解决三个问题：

1. 怎么从 Markdown 文件中解析出结构化数据
2. 怎么存储和索引（FTS5 全文 + embedding 向量）
3. 怎么检索（双通道合并排序）

## 数据源概况

```text
learn-agent-interview/
├── 01-architecture-design/index.md    34 题
├── 02-tool-management/index.md        25 题
├── 03-fault-tolerance/index.md        23 题
├── 04-memory-context/index.md         46 题
├── 05-eval-and-vision/index.md        28 题
├── 06-multi-agent-collab/index.md     20 题
├── 07-engineering-pitfalls/index.md   47 题
├── 08-prompt-engineering/index.md     16 题
├── 09-rag-retrieval/index.md          54 题
├── 10-training-and-data/index.md      45 题
├── 11-ai-code-testing/index.md         7 题
├── 12-business-ai-engineering/index.md 7 题
├── 13-project-deep-dive/index.md      20 题
├── 14-company-preferences/index.md     — 
├── 15-agent-concepts/index.md         13 题
                                      ─────
                                      385+ 题
```

每题的 Markdown 格式是稳定的：

```markdown
### Q：{面试问题}

> 来源：{公司/岗位}

**新手答**："{浅层回答}"

**高手答**：

{深度回答，多段，带具体方案}

**差距在哪**：{分析}
```

这个统一格式就是我们的解析契约。

## 模块结构

```text
knowledge/
├── import.ts          # Markdown → 结构化 JSON 解析器
├── embed.ts           # 批量生成 embedding
├── store.ts           # SQLite 知识库读写
├── search.ts          # 双通道检索逻辑
├── types.ts           # 数据类型
└── data/
    └── knowledge.db   # 导入后的 SQLite 数据库
```

## 数据模型

```typescript
// knowledge/types.ts

export interface KnowledgeEntry {
  id: string;                    // dimension:index 如 "architecture-design:3"
  dimension: string;             // 维度标识
  dimensionLabel: string;        // 维度中文名
  question: string;              // 面试问题
  source?: string;               // 来源（公司/岗位）
  noviceAnswer: string;          // 新手答
  expertAnswer: string;          // 高手答
  gapAnalysis: string;           // 差距在哪
  keywords: string[];            // 从问题中提取的关键词
  embedding?: Float32Array;      // 向量（question + expertAnswer 拼接后编码）
}

export interface SearchOptions {
  dimension?: string;
  limit?: number;
  threshold?: number;            // embedding 相似度阈值
}

export interface SearchResult extends KnowledgeEntry {
  similarity: number;            // 0-1
  matchType: 'fts' | 'embedding' | 'both';
}
```

## SQLite Schema

```sql
-- knowledge/schema.sql

CREATE TABLE knowledge (
  id TEXT PRIMARY KEY,
  dimension TEXT NOT NULL,
  dimension_label TEXT NOT NULL,
  question TEXT NOT NULL,
  source TEXT,
  novice_answer TEXT NOT NULL,
  expert_answer TEXT NOT NULL,
  gap_analysis TEXT NOT NULL,
  keywords TEXT NOT NULL,           -- JSON array
  embedding BLOB,                   -- Float32Array serialized
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- FTS5 全文索引（对 question + expert_answer + keywords 建索引）
CREATE VIRTUAL TABLE knowledge_fts USING fts5(
  id,
  question,
  expert_answer,
  keywords,
  content=knowledge,
  content_rowid=rowid,
  tokenize='unicode61'
);

-- 触发器：knowledge 表变更时同步 FTS
CREATE TRIGGER knowledge_ai AFTER INSERT ON knowledge BEGIN
  INSERT INTO knowledge_fts(rowid, id, question, expert_answer, keywords)
  VALUES (new.rowid, new.id, new.question, new.expert_answer, new.keywords);
END;

CREATE TRIGGER knowledge_ad AFTER DELETE ON knowledge BEGIN
  INSERT INTO knowledge_fts(knowledge_fts, rowid, id, question, expert_answer, keywords)
  VALUES ('delete', old.rowid, old.id, old.question, old.expert_answer, old.keywords);
END;

-- 维度索引（按维度过滤用）
CREATE INDEX idx_knowledge_dimension ON knowledge(dimension);
```

## Markdown 解析器：从文件到结构化数据

解析逻辑的核心挑战是处理格式变体。虽然大部分题目遵循标准格式，但实际文件里存在：
- `## Q` 和 `### Q` 两种标题级别
- 有些题有“差距在哪”，有些用“考察点”
- 高手答可能包含代码块、列表、多层级标题

```typescript
// knowledge/import.ts

import { readFileSync, readdirSync } from 'fs';
import { join } from 'path';
import { KnowledgeEntry } from './types';

interface DimensionConfig {
  dir: string;
  id: string;
  label: string;
}

const DIMENSIONS: DimensionConfig[] = [
  { dir: '01-architecture-design', id: 'architecture-design', label: '架构选型' },
  { dir: '02-tool-management', id: 'tool-management', label: '工具管理' },
  { dir: '03-fault-tolerance', id: 'fault-tolerance', label: '容错与兜底' },
  { dir: '04-memory-context', id: 'memory-context', label: '记忆与上下文' },
  { dir: '05-eval-and-vision', id: 'eval-and-vision', label: '评估与愿景' },
  { dir: '06-multi-agent-collab', id: 'multi-agent-collab', label: '多Agent协作' },
  { dir: '07-engineering-pitfalls', id: 'engineering-pitfalls', label: '工程踩坑' },
  { dir: '08-prompt-engineering', id: 'prompt-engineering', label: 'Prompt工程' },
  { dir: '09-rag-retrieval', id: 'rag-retrieval', label: 'RAG检索' },
  { dir: '10-training-and-data', id: 'training-and-data', label: '训练与数据' },
  { dir: '11-ai-code-testing', id: 'ai-code-testing', label: 'AI代码测试' },
  { dir: '12-business-ai-engineering', id: 'business-ai-engineering', label: '业务AI工程' },
  { dir: '13-project-deep-dive', id: 'project-deep-dive', label: '项目深挖' },
  { dir: '15-agent-concepts', id: 'agent-concepts', label: 'Agent概念' },
];

export function importAll(interviewDir: string): KnowledgeEntry[] {
  const entries: KnowledgeEntry[] = [];

  for (const dim of DIMENSIONS) {
    const filePath = join(interviewDir, dim.dir, 'index.md');
    const content = readFileSync(filePath, 'utf-8');
    const questions = parseMarkdown(content, dim);
    entries.push(...questions);
  }

  console.log(`Imported ${entries.length} entries from ${DIMENSIONS.length} dimensions`);
  return entries;
}

function parseMarkdown(content: string, dim: DimensionConfig): KnowledgeEntry[] {
  const entries: KnowledgeEntry[] = [];

  // 按 Q 标题分割（支持 ## Q 和 ### Q）
  const sections = content.split(/(?=^#{2,3}\s*Q[：:])/m);
  let index = 0;

  for (const section of sections) {
    if (!section.match(/^#{2,3}\s*Q[：:]/m)) continue;
    index++;

    const entry = parseQuestion(section, dim, index);
    if (entry) entries.push(entry);
  }

  return entries;
}

function parseQuestion(
  section: string,
  dim: DimensionConfig,
  index: number
): KnowledgeEntry | null {
  // 提取问题
  const questionMatch = section.match(/^#{2,3}\s*Q[：:]\s*(.+)/m);
  if (!questionMatch) return null;
  const question = questionMatch[1].trim();

  // 提取来源
  const sourceMatch = section.match(/>\s*来源[：:]\s*(.+)/);
  const source = sourceMatch?.[1]?.trim();

  // 提取新手答
  const noviceMatch = section.match(/\*\*新手答\*\*[：:]\s*["""]?(.+?)["""]?\s*$/m);
  const noviceAnswer = noviceMatch?.[1]?.trim() ?? '';

  // 提取高手答（从"**高手答**："到下一个"**"标记）
  const expertMatch = section.match(
    /\*\*高手答\*\*[：:]\s*\n([\s\S]+?)(?=\n\*\*(?:差距|考察|关键))/
  );
  const expertAnswer = expertMatch?.[1]?.trim() ?? '';

  // 提取差距分析
  const gapMatch = section.match(
    /\*\*(?:差距在哪|考察点|关键差距)\*\*[：:]\s*([\s\S]+?)(?=\n---|\n#{2,3}\s|$)/
  );
  const gapAnalysis = gapMatch?.[1]?.trim() ?? '';

  if (!expertAnswer) return null;

  // 提取关键词
  const keywords = extractKeywords(question + ' ' + expertAnswer);

  return {
    id: `${dim.id}:${index}`,
    dimension: dim.id,
    dimensionLabel: dim.label,
    question,
    source,
    noviceAnswer,
    expertAnswer,
    gapAnalysis,
    keywords,
  };
}

function extractKeywords(text: string): string[] {
  // 提取技术术语（英文词 + 中文专有名词）
  const techTerms = text.match(
    /\b(?:ReAct|LangGraph|RAG|CoT|ToT|Agent|Tool|MCP|embedding|vector|prompt|token|LLM|fine-?tune|RLHF|hallucination|context|memory|planning|reflection)\b/gi
  ) ?? [];

  // 去重 + 小写化
  return [...new Set(techTerms.map(t => t.toLowerCase()))];
}
```

## Embedding 生成：批量向量化

```typescript
// knowledge/embed.ts

import OpenAI from 'openai';
import { KnowledgeEntry } from './types';

const EMBEDDING_MODEL = 'text-embedding-3-small';
const BATCH_SIZE = 100;   // OpenAI embedding API 单次最多 2048，100 比较安全
const EMBEDDING_DIM = 1536;

export async function generateEmbeddings(
  entries: KnowledgeEntry[],
  apiKey: string,
): Promise<KnowledgeEntry[]> {
  const client = new OpenAI({ apiKey });
  const results: KnowledgeEntry[] = [];

  for (let i = 0; i < entries.length; i += BATCH_SIZE) {
    const batch = entries.slice(i, i + BATCH_SIZE);
    const texts = batch.map(e => buildEmbeddingText(e));

    const response = await client.embeddings.create({
      model: EMBEDDING_MODEL,
      input: texts,
    });

    for (let j = 0; j < batch.length; j++) {
      results.push({
        ...batch[j],
        embedding: new Float32Array(response.data[j].embedding),
      });
    }

    console.log(`Embedded ${Math.min(i + BATCH_SIZE, entries.length)}/${entries.length}`);

    // 限流：避免打满 API
    if (i + BATCH_SIZE < entries.length) {
      await sleep(200);
    }
  }

  return results;
}

function buildEmbeddingText(entry: KnowledgeEntry): string {
  // 拼接 question + expertAnswer 的前 500 字作为 embedding 输入
  // 原因：question 太短语义不够，expertAnswer 太长浪费 token
  const expert = entry.expertAnswer.slice(0, 500);
  return `问题：${entry.question}\n答案：${expert}`;
}

function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}
```

**成本估算：**

```text
385 道题 × 平均 200 tokens/题 = ~77,000 tokens
text-embedding-3-small 价格: $0.02 / 1M tokens
总成本: ~$0.002（忽略不计）
```

## 知识库存储

```typescript
// knowledge/store.ts

import Database from 'better-sqlite3';
import { KnowledgeEntry, SearchOptions, SearchResult } from './types';

export class KnowledgeStore {
  private db: Database.Database;

  constructor(dbPath: string) {
    this.db = new Database(dbPath);
    this.db.pragma('journal_mode = WAL');
    this.initSchema();
  }

  private initSchema(): void {
    this.db.exec(SCHEMA_SQL); // 上面的 schema.sql
  }

  insertBatch(entries: KnowledgeEntry[]): void {
    const stmt = this.db.prepare(`
      INSERT OR REPLACE INTO knowledge
        (id, dimension, dimension_label, question, source, novice_answer, expert_answer, gap_analysis, keywords, embedding)
      VALUES
        (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);

    const tx = this.db.transaction((items: KnowledgeEntry[]) => {
      for (const e of items) {
        stmt.run(
          e.id,
          e.dimension,
          e.dimensionLabel,
          e.question,
          e.source ?? null,
          e.noviceAnswer,
          e.expertAnswer,
          e.gapAnalysis,
          JSON.stringify(e.keywords),
          e.embedding ? Buffer.from(e.embedding.buffer) : null,
        );
      }
    });

    tx(entries);
    console.log(`Stored ${entries.length} entries`);
  }

  getEntry(id: string): KnowledgeEntry | null {
    const row = this.db.prepare('SELECT * FROM knowledge WHERE id = ?').get(id);
    return row ? this.rowToEntry(row) : null;
  }

  getDimensions(): Array<{ id: string; label: string; count: number }> {
    return this.db.prepare(`
      SELECT dimension as id, dimension_label as label, COUNT(*) as count
      FROM knowledge GROUP BY dimension ORDER BY dimension
    `).all() as any;
  }

  getStats(): { totalEntries: number; dimensions: number; withEmbedding: number } {
    const total = this.db.prepare('SELECT COUNT(*) as c FROM knowledge').get() as any;
    const dims = this.db.prepare('SELECT COUNT(DISTINCT dimension) as c FROM knowledge').get() as any;
    const embedded = this.db.prepare('SELECT COUNT(*) as c FROM knowledge WHERE embedding IS NOT NULL').get() as any;
    return {
      totalEntries: total.c,
      dimensions: dims.c,
      withEmbedding: embedded.c,
    };
  }

  sampleQuestions(opts: { dimension?: string; count: number }): KnowledgeEntry[] {
    let sql = 'SELECT * FROM knowledge';
    const params: any[] = [];

    if (opts.dimension) {
      sql += ' WHERE dimension = ?';
      params.push(opts.dimension);
    }

    sql += ' ORDER BY RANDOM() LIMIT ?';
    params.push(opts.count);

    const rows = this.db.prepare(sql).all(...params);
    return rows.map(r => this.rowToEntry(r));
  }

  private rowToEntry(row: any): KnowledgeEntry {
    return {
      id: row.id,
      dimension: row.dimension,
      dimensionLabel: row.dimension_label,
      question: row.question,
      source: row.source,
      noviceAnswer: row.novice_answer,
      expertAnswer: row.expert_answer,
      gapAnalysis: row.gap_analysis,
      keywords: JSON.parse(row.keywords),
      embedding: row.embedding ? new Float32Array(row.embedding.buffer) : undefined,
    };
  }
}
```

## 双通道检索

检索是知识库最关键的能力。单用 FTS 会漏掉语义相似但措辞不同的题，单用 embedding 会漏掉精确匹配。双通道合并才能兼顾准确率和召回率。

```typescript
// knowledge/search.ts

import { KnowledgeStore } from './store';
import { SearchOptions, SearchResult, KnowledgeEntry } from './types';
import OpenAI from 'openai';

export class KnowledgeSearch {
  private store: KnowledgeStore;
  private openai: OpenAI;

  constructor(store: KnowledgeStore, openaiApiKey: string) {
    this.store = store;
    this.openai = new OpenAI({ apiKey: openaiApiKey });
  }

  async search(query: string, opts: SearchOptions = {}): Promise<SearchResult[]> {
    const { dimension, limit = 3, threshold = 0.5 } = opts;

    // 通道 1: FTS5 全文检索
    const ftsResults = this.searchFTS(query, { dimension, limit: limit * 3 });

    // 通道 2: Embedding 语义检索
    const embeddingResults = await this.searchEmbedding(query, { dimension, limit: limit * 3, threshold });

    // 合并 + 重排序
    return this.mergeResults(ftsResults, embeddingResults, limit);
  }

  searchFTS(query: string, opts: { dimension?: string; limit: number }): SearchResult[] {
    // 构造 FTS5 查询（分词 + OR 连接）
    const tokens = this.tokenize(query);
    const ftsQuery = tokens.map(t => `"${t}"`).join(' OR ');

    let sql = `
      SELECT k.*, rank
      FROM knowledge_fts fts
      JOIN knowledge k ON k.id = fts.id
      WHERE knowledge_fts MATCH ?
    `;
    const params: any[] = [ftsQuery];

    if (opts.dimension) {
      sql += ' AND k.dimension = ?';
      params.push(opts.dimension);
    }

    sql += ' ORDER BY rank LIMIT ?';
    params.push(opts.limit);

    const rows = this.store.db.prepare(sql).all(...params);
    return rows.map((row: any) => ({
      ...this.store.rowToEntry(row),
      similarity: this.normalizeRank(row.rank),
      matchType: 'fts' as const,
    }));
  }

  async searchEmbedding(
    query: string,
    opts: { dimension?: string; limit: number; threshold: number }
  ): Promise<SearchResult[]> {
    // 生成 query embedding
    const response = await this.openai.embeddings.create({
      model: 'text-embedding-3-small',
      input: query,
    });
    const queryVec = new Float32Array(response.data[0].embedding);

    // 从 DB 取出所有候选（有 embedding 的行）
    let sql = 'SELECT * FROM knowledge WHERE embedding IS NOT NULL';
    const params: any[] = [];

    if (opts.dimension) {
      sql += ' AND dimension = ?';
      params.push(opts.dimension);
    }

    const rows = this.store.db.prepare(sql).all(...params);

    // 计算余弦相似度 + 排序
    const scored: Array<{ entry: KnowledgeEntry; similarity: number }> = [];

    for (const row of rows) {
      const entry = this.store.rowToEntry(row);
      if (!entry.embedding) continue;
      const sim = cosineSimilarity(queryVec, entry.embedding);
      if (sim >= opts.threshold) {
        scored.push({ entry, similarity: sim });
      }
    }

    scored.sort((a, b) => b.similarity - a.similarity);

    return scored.slice(0, opts.limit).map(s => ({
      ...s.entry,
      similarity: s.similarity,
      matchType: 'embedding' as const,
    }));
  }

  private mergeResults(
    fts: SearchResult[],
    embedding: SearchResult[],
    limit: number,
  ): SearchResult[] {
    const merged = new Map<string, SearchResult>();

    // embedding 结果优先（语义匹配通常更准）
    for (const r of embedding) {
      merged.set(r.id, r);
    }

    // FTS 结果补充（可能捕获精确匹配）
    for (const r of fts) {
      if (merged.has(r.id)) {
        // 两个通道都命中——提升分数
        const existing = merged.get(r.id)!;
        existing.similarity = Math.min(1.0, existing.similarity * 1.2);
        existing.matchType = 'both';
      } else {
        merged.set(r.id, r);
      }
    }

    // 按 similarity 排序
    return Array.from(merged.values())
      .sort((a, b) => b.similarity - a.similarity)
      .slice(0, limit);
  }

  private tokenize(text: string): string[] {
    // 简单分词：按空格 + 中文字符边界切
    const tokens = text
      .replace(/[，。？！、；：""''（）《》【】]/g, ' ')
      .split(/\s+/)
      .filter(t => t.length >= 2);
    return [...new Set(tokens)];
  }

  private normalizeRank(rank: number): number {
    // FTS5 rank 是负数（越小越好），转成 0-1
    return Math.min(1.0, Math.max(0, 1 + rank / 10));
  }
}

function cosineSimilarity(a: Float32Array, b: Float32Array): number {
  let dot = 0, normA = 0, normB = 0;
  for (let i = 0; i < a.length; i++) {
    dot += a[i] * b[i];
    normA += a[i] * a[i];
    normB += b[i] * b[i];
  }
  return dot / (Math.sqrt(normA) * Math.sqrt(normB));
}
```

## 导入脚本：一键构建知识库

```typescript
// knowledge/cli.ts — 通过 Commander 暴露为 CLI 命令

import { importAll } from './import';
import { generateEmbeddings } from './embed';
import { KnowledgeStore } from './store';

export async function buildKnowledgeBase(opts: {
  interviewDir: string;
  dbPath: string;
  openaiApiKey: string;
}): Promise<void> {
  console.log('Step 1/3: Parsing Markdown files...');
  const entries = importAll(opts.interviewDir);
  console.log(`  → Parsed ${entries.length} questions`);

  console.log('Step 2/3: Generating embeddings...');
  const withEmbeddings = await generateEmbeddings(entries, opts.openaiApiKey);
  console.log(`  → Generated ${withEmbeddings.length} embeddings`);

  console.log('Step 3/3: Storing to SQLite...');
  const store = new KnowledgeStore(opts.dbPath);
  store.insertBatch(withEmbeddings);

  const stats = store.getStats();
  console.log(`\nDone! Knowledge base ready:`);
  console.log(`  Total entries: ${stats.totalEntries}`);
  console.log(`  Dimensions: ${stats.dimensions}`);
  console.log(`  With embedding: ${stats.withEmbedding}`);
  console.log(`  Database: ${opts.dbPath}`);
}
```

**使用：**

```bash
pnpm tsx knowledge/cli.ts build \
  --interview-dir ../learn-agent-interview \
  --db-path ./data/knowledge.db
```

输出：

```text
Step 1/3: Parsing Markdown files...
  → Parsed 385 questions
Step 2/3: Generating embeddings...
  Embedded 100/385
  Embedded 200/385
  Embedded 300/385
  Embedded 385/385
  → Generated 385 embeddings
Step 3/3: Storing to SQLite...
  Stored 385 entries

Done! Knowledge base ready:
  Total entries: 385
  Dimensions: 14
  With embedding: 385
  Database: ./data/knowledge.db
```

## 检索效果验证

知识库建好了，必须验证检索质量。核心指标：**用户问的面试题能否命中相关参考答案。**

```typescript
// knowledge/eval.ts

export async function evaluateSearch(
  search: KnowledgeSearch,
  testCases: Array<{ query: string; expectedDimension: string; expectedKeywords: string[] }>,
): Promise<void> {
  let hits = 0;

  for (const tc of testCases) {
    const results = await search.search(tc.query, { limit: 3 });

    const topResult = results[0];
    const dimensionMatch = topResult?.dimension === tc.expectedDimension;
    const keywordMatch = tc.expectedKeywords.some(kw =>
      topResult?.expertAnswer.includes(kw)
    );

    if (dimensionMatch || keywordMatch) hits++;

    console.log(`[${dimensionMatch ? '✓' : '✗'}] "${tc.query.slice(0, 40)}..." → ${topResult?.dimension ?? 'NO RESULT'} (sim: ${topResult?.similarity.toFixed(3) ?? 'N/A'})`);
  }

  console.log(`\nAccuracy: ${hits}/${testCases.length} (${(hits / testCases.length * 100).toFixed(1)}%)`);
}

// 测试用例示例
const TEST_CASES = [
  { query: 'Agent 的记忆系统怎么设计', expectedDimension: 'memory-context', expectedKeywords: ['长短期', 'memory'] },
  { query: 'ReAct 和 Plan-and-Execute 怎么选', expectedDimension: 'architecture-design', expectedKeywords: ['ReAct', 'Plan'] },
  { query: 'RAG 检索质量怎么提升', expectedDimension: 'rag-retrieval', expectedKeywords: ['chunk', 'embedding', 'rerank'] },
  { query: '多 Agent 之间怎么通信', expectedDimension: 'multi-agent-collab', expectedKeywords: ['消息', '协议'] },
  { query: 'Tool 调用失败了怎么兜底', expectedDimension: 'fault-tolerance', expectedKeywords: ['重试', 'fallback'] },
];
```

## 增量更新：新题入库

当 learn-agent-interview 新增面试题时，知识库需要增量更新而不是全量重建。

```typescript
// knowledge/incremental.ts

export async function incrementalUpdate(
  store: KnowledgeStore,
  interviewDir: string,
  openaiApiKey: string,
): Promise<{ added: number; updated: number }> {
  const entries = importAll(interviewDir);
  let added = 0, updated = 0;

  for (const entry of entries) {
    const existing = store.getEntry(entry.id);

    if (!existing) {
      // 新题：生成 embedding + 入库
      const [withEmbed] = await generateEmbeddings([entry], openaiApiKey);
      store.insertBatch([withEmbed]);
      added++;
    } else if (existing.expertAnswer !== entry.expertAnswer) {
      // 答案更新：重新生成 embedding
      const [withEmbed] = await generateEmbeddings([entry], openaiApiKey);
      store.insertBatch([withEmbed]);
      updated++;
    }
    // 无变化则跳过
  }

  return { added, updated };
}
```

## 性能考量

**当前规模（385 题）下的性能特征：**

```text
FTS5 检索: < 1ms（SQLite 内存级）
Embedding 检索:
  - 生成 query embedding: ~200ms（网络往返）
  - 余弦相似度计算 385 × 1536 维: < 5ms（CPU）
  - 总计: ~205ms

双通道合并: < 1ms
```

385 题全部加载到内存做余弦相似度完全可行。如果未来题库增长到 10000+，需要引入 ANN（近似最近邻）索引，比如：
- sqlite-vss（SQLite 向量搜索扩展）
- 或导出到 Faiss / Hnswlib

当前阶段不需要——过早优化是万恶之源。

## 与 Tool 层的集成

知识库通过 `query_knowledge_base` Tool 暴露给 Agent：

```typescript
// 在 Tool 的 execute 中使用
const kbResult = await knowledgeSearch.search(input.question, {
  dimension: input.dimension,
  limit: input.limit ?? 3,
});

return {
  success: true,
  data: {
    results: kbResult.map(r => ({
      question: r.question,
      noviceAnswer: r.noviceAnswer,
      expertAnswer: r.expertAnswer,
      gap: r.gapAnalysis,
      dimension: r.dimensionLabel,
      similarity: r.similarity,
    })),
    totalMatched: kbResult.length,
  },
};
```

## 小结

- 数据源是现成的：learn-agent-interview 15 个维度 385+ 道题，格式统一
- Markdown 解析器处理 `## Q` / `### Q` 两种标题、新手答/高手答/差距分析三段结构
- SQLite FTS5 做全文检索（精确匹配），embedding 做语义检索（模糊匹配），双通道合并
- 导入成本极低：embedding 不到 $0.01，全流程 < 1 分钟
- 检索延迟 ~200ms（主要是 embedding API 往返），FTS 本地 < 1ms
- 支持增量更新，不需要每次全量重建
- 385 题规模下纯暴力余弦相似度足够，不需要 ANN 索引

下一篇建议继续看：

- [06-context-memory：上下文工程与记忆系统](../06-context-memory/index.html)
