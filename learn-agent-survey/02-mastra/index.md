---
layout: default
title: "Mastra：TypeScript 原生 Agent 框架"
description: 面向 TypeScript 开发者的 Agent 框架——工作流、工具、记忆、RAG 一体化，与 Next.js 深度集成
eyebrow: 框架调研 · 02
---

# Mastra：TypeScript 原生 Agent 框架

Mastra 是 2024 年底出现的 TypeScript 原生 Agent 框架，定位是"给 TypeScript 开发者的 LangChain"。如果你的技术栈是 Next.js / Node.js，Mastra 是目前最自然的选择之一。

GitHub：[mastra-ai/mastra](https://github.com/mastra-ai/mastra)

## 安装

```bash
npm install @mastra/core
# 或
pnpm add @mastra/core
```

集成 OpenAI：

```bash
npm install @ai-sdk/openai
```

## 核心概念

| 概念 | 说明 |
|------|------|
| `Agent` | 带工具、记忆、指令的 Agent 实例 |
| `Tool` | 用 `createTool` 定义，Zod schema 验证参数 |
| `Workflow` | 有向图工作流，节点是步骤，边是转移 |
| `Mastra` | 顶层实例，注册所有 Agent、工具、工作流 |

## 最小示例

```typescript
import { Mastra } from "@mastra/core";
import { Agent } from "@mastra/core/agent";
import { openai } from "@ai-sdk/openai";

// 创建 Agent
const assistant = new Agent({
  name: "Assistant",
  instructions: "你是一个有帮助的助手，用中文回答。",
  model: openai("gpt-4o-mini"),
});

// 注册到 Mastra 实例
const mastra = new Mastra({
  agents: { assistant },
});

// 运行
const result = await mastra.getAgent("assistant").generate(
  "介绍一下 Mastra 框架"
);
console.log(result.text);
```

## 定义工具

Mastra 用 [Zod](https://github.com/colinhacks/zod) 做工具参数校验：

```typescript
import { createTool } from "@mastra/core/tools";
import { z } from "zod";

const getWeatherTool = createTool({
  id: "get-weather",
  description: "获取指定城市的当前天气",
  inputSchema: z.object({
    city: z.string().describe("城市名称，例如：北京、上海"),
  }),
  outputSchema: z.object({
    temperature: z.number(),
    condition: z.string(),
  }),
  execute: async ({ context }) => {
    const { city } = context;
    // 实际调用天气 API
    const data: Record<string, { temperature: number; condition: string }> = {
      北京: { temperature: 25, condition: "晴天" },
      上海: { temperature: 22, condition: "多云" },
    };
    return data[city] ?? { temperature: 0, condition: "暂无数据" };
  },
});

// 挂载到 Agent
const weatherAgent = new Agent({
  name: "WeatherAgent",
  instructions: "你可以查询天气，根据天气给出出行建议。",
  model: openai("gpt-4o-mini"),
  tools: { getWeatherTool },
});
```

## 工作流（Workflow）

Mastra 的 Workflow 是有向图，支持顺序、条件、并行：

```typescript
import { Workflow, Step } from "@mastra/core/workflows";
import { z } from "zod";

// 定义步骤
const fetchDataStep = new Step({
  id: "fetch-data",
  outputSchema: z.object({ data: z.string() }),
  execute: async ({ context }) => {
    // context.triggerData 是工作流入参
    const topic = context.triggerData.topic as string;
    return { data: `关于 ${topic} 的原始数据...` };
  },
});

const analyzeStep = new Step({
  id: "analyze",
  outputSchema: z.object({ summary: z.string() }),
  execute: async ({ context }) => {
    // 读取上一步的输出
    const prevData = context.getStepResult<{ data: string }>("fetch-data");
    const summary = `分析结果：${prevData?.data ?? ""}`;
    return { summary };
  },
});

// 组装工作流
const researchWorkflow = new Workflow({
  name: "research-workflow",
  triggerSchema: z.object({ topic: z.string() }),
})
  .step(fetchDataStep)
  .then(analyzeStep)
  .commit();

// 运行
const { runId, start } = researchWorkflow.createRun();
const result = await start({ triggerData: { topic: "LangGraph" } });
console.log(result.results["analyze"].output.summary);
```

## 记忆（Memory）

Mastra 内置记忆系统，让 Agent 记住历史对话：

```typescript
import { Agent } from "@mastra/core/agent";
import { Memory } from "@mastra/memory";
import { openai } from "@ai-sdk/openai";

const memory = new Memory();

const agent = new Agent({
  name: "MemoryAgent",
  instructions: "你是一个有记忆的助手。",
  model: openai("gpt-4o-mini"),
  memory,
});

// 传入 threadId 关联同一个会话
const thread = { threadId: "user-123", resourceId: "resource-1" };

await agent.generate("我叫张三", { ...thread });
const r = await agent.generate("我叫什么名字？", { ...thread });
console.log(r.text); // 应该记得张三
```

## RAG 集成

```typescript
import { MastraVector } from "@mastra/vector-pg"; // 或其他向量数据库
import { openai } from "@ai-sdk/openai";

// 创建向量存储
const vectorStore = new MastraVector({ connectionString: process.env.DB_URL! });

// 索引文档
await vectorStore.upsert({
  indexName: "docs",
  vectors: await embedDocuments(documents), // 你的 embedding 函数
});

// 在 Agent 里接入 RAG 工具
const ragTool = createTool({
  id: "search-docs",
  description: "搜索文档库",
  inputSchema: z.object({ query: z.string() }),
  execute: async ({ context }) => {
    const results = await vectorStore.query({
      indexName: "docs",
      queryVector: await embed(context.query),
      topK: 3,
    });
    return { results };
  },
});
```

## 与 Next.js 集成

Mastra 可以直接在 Next.js App Router 里用：

```typescript
// app/api/chat/route.ts
import { mastra } from "@/mastra";
import { NextRequest } from "next/server";

export async function POST(req: NextRequest) {
  const { message } = await req.json();
  const agent = mastra.getAgent("assistant");

  const stream = await agent.stream(message);
  return stream.toDataStreamResponse();
}
```

```typescript
// src/mastra/index.ts
import { Mastra } from "@mastra/core";
import { assistant } from "./agents/assistant";

export const mastra = new Mastra({
  agents: { assistant },
});
```

## 优缺点

**优点：**
- TypeScript 原生，类型安全，IDE 自动补全
- Zod schema 验证工具参数，减少运行时错误
- 工作流 + Agent + 记忆 + RAG 一体化设计
- 与 Next.js / Vercel 生态无缝集成
- 活跃开发中，2024-2025 年增长快

**缺点：**
- Python 生态不支持（TypeScript only）
- 相比 LangChain 社区还小，插件少
- 仍在快速迭代，API 可能变动

## 适合什么场景

- 技术栈是 TypeScript / Next.js 的团队
- 需要在 Web 应用里内嵌 Agent 功能
- 需要工作流 + 记忆 + RAG 一体的解决方案
- 想要类型安全的 Agent 开发体验
