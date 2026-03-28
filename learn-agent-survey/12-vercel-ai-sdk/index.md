---
layout: default
title: "Vercel AI SDK：全栈 AI 应用框架"
description: Vercel 官方 AI SDK——流式 UI、useChat/useCompletion、Server Actions、工具调用，专为 Next.js 设计
eyebrow: 框架调研 · 12
---

# Vercel AI SDK：全栈 AI 应用框架

Vercel AI SDK（`ai` 包）是 Vercel 为 TypeScript 全栈开发者设计的 AI 框架，核心特点是**流式优先**和**框架无关**——虽然与 Next.js 集成最好，但也支持 Node.js、Svelte、Nuxt 等。

GitHub：[vercel/ai](https://github.com/vercel/ai)
文档：[sdk.vercel.ai](https://sdk.vercel.ai)

## 安装

```bash
npm install ai @ai-sdk/openai
# 或 Anthropic
npm install ai @ai-sdk/anthropic
# 或 Google
npm install ai @ai-sdk/google
```

## 核心分层

Vercel AI SDK 分三层：

| 层 | 说明 |
|----|------|
| **AI SDK Core** | 底层 API，`generateText`、`streamText`、`generateObject` |
| **AI SDK UI** | React/Vue hooks：`useChat`、`useCompletion`、`useObject` |
| **AI SDK RSC** | React Server Components 支持 |

## AI SDK Core：服务端

### 文本生成

```typescript
import { generateText } from "ai";
import { openai } from "@ai-sdk/openai";

const { text } = await generateText({
  model: openai("gpt-4o-mini"),
  prompt: "用中文介绍一下 Vercel AI SDK",
});
console.log(text);
```

### 流式生成

```typescript
import { streamText } from "ai";
import { anthropic } from "@ai-sdk/anthropic";

const { textStream } = await streamText({
  model: anthropic("claude-opus-4-5"),
  prompt: "写一首关于 AI 的短诗",
});

for await (const chunk of textStream) {
  process.stdout.write(chunk);
}
```

### 结构化输出

```typescript
import { generateObject } from "ai";
import { openai } from "@ai-sdk/openai";
import { z } from "zod";

const { object } = await generateObject({
  model: openai("gpt-4o-mini"),
  schema: z.object({
    city: z.string(),
    temperature: z.number(),
    condition: z.enum(["sunny", "cloudy", "rainy"]),
  }),
  prompt: "描述北京今天的天气",
});
console.log(object); // { city: "北京", temperature: 25, condition: "sunny" }
```

### 工具调用

```typescript
import { generateText, tool } from "ai";
import { openai } from "@ai-sdk/openai";
import { z } from "zod";

const { text, toolCalls, toolResults } = await generateText({
  model: openai("gpt-4o"),
  tools: {
    getWeather: tool({
      description: "获取城市天气",
      parameters: z.object({
        city: z.string().describe("城市名称"),
      }),
      execute: async ({ city }) => {
        const data: Record<string, string> = {
          北京: "晴天 25°C",
          上海: "多云 22°C",
        };
        return data[city] ?? "暂无数据";
      },
    }),
    calculate: tool({
      description: "计算数学表达式",
      parameters: z.object({
        expression: z.string(),
      }),
      execute: async ({ expression }) => {
        return String(eval(expression));
      },
    }),
  },
  maxSteps: 5, // 最多执行 5 步工具调用循环
  prompt: "北京今天天气怎样？另外 15 * 8 等于多少？",
});
console.log(text);
```

`maxSteps` 控制工具调用循环的最大步数，无需手写循环。

## Next.js App Router 集成

### API Route

```typescript
// app/api/chat/route.ts
import { streamText } from "ai";
import { openai } from "@ai-sdk/openai";

export async function POST(req: Request) {
  const { messages } = await req.json();

  const result = await streamText({
    model: openai("gpt-4o-mini"),
    system: "你是一个有帮助的助手，用中文回答。",
    messages,
  });

  return result.toDataStreamResponse();
}
```

### 前端 useChat

```typescript
// app/chat/page.tsx
"use client";
import { useChat } from "ai/react";

export default function ChatPage() {
  const { messages, input, handleInputChange, handleSubmit, isLoading } =
    useChat({ api: "/api/chat" });

  return (
    <div>
      <div>
        {messages.map((m) => (
          <div key={m.id}>
            <strong>{m.role === "user" ? "你" : "AI"}：</strong>
            {m.content}
          </div>
        ))}
      </div>
      <form onSubmit={handleSubmit}>
        <input
          value={input}
          onChange={handleInputChange}
          placeholder="输入消息..."
          disabled={isLoading}
        />
        <button type="submit" disabled={isLoading}>
          {isLoading ? "思考中..." : "发送"}
        </button>
      </form>
    </div>
  );
}
```

`useChat` 自动处理：消息历史、流式显示、加载状态、错误处理。

## Server Actions（RSC）

```typescript
// app/actions.ts
"use server";
import { streamUI } from "ai/rsc";
import { openai } from "@ai-sdk/openai";

export async function generateReport(topic: string) {
  const result = await streamUI({
    model: openai("gpt-4o"),
    prompt: `生成关于 ${topic} 的研究报告`,
    text: ({ content, done }) => (
      <div className={done ? "opacity-100" : "opacity-50"}>
        {content}
      </div>
    ),
  });
  return result.value;
}
```

## 多模型切换

AI SDK 的模型是可插拔的，切换只需换一行：

```typescript
import { openai } from "@ai-sdk/openai";
import { anthropic } from "@ai-sdk/anthropic";
import { google } from "@ai-sdk/google";

// 三行代码，三个不同模型，其余代码完全一样
const model = openai("gpt-4o-mini");
// const model = anthropic("claude-opus-4-5");
// const model = google("gemini-2.0-flash");

const { text } = await generateText({ model, prompt: "你好" });
```

## useCompletion：单次补全

```typescript
"use client";
import { useCompletion } from "ai/react";

export function CompletionDemo() {
  const { completion, input, handleInputChange, handleSubmit } = useCompletion({
    api: "/api/complete",
  });

  return (
    <div>
      <form onSubmit={handleSubmit}>
        <input value={input} onChange={handleInputChange} />
        <button type="submit">生成</button>
      </form>
      <p>{completion}</p>
    </div>
  );
}
```

## 中间件（Middleware）

AI SDK 支持在模型调用前后插入中间件：

```typescript
import { wrapLanguageModel, extractReasoningMiddleware } from "ai";
import { openai } from "@ai-sdk/openai";

// 提取思维链推理
const model = wrapLanguageModel({
  model: openai("o3-mini"),
  middleware: extractReasoningMiddleware({ tagName: "think" }),
});

// 自定义日志中间件
const loggingModel = wrapLanguageModel({
  model: openai("gpt-4o-mini"),
  middleware: {
    wrapGenerate: async ({ doGenerate, params }) => {
      console.log("调用模型:", params.prompt);
      const result = await doGenerate();
      console.log("输出 tokens:", result.usage?.completionTokens);
      return result;
    },
  },
});
```

## 优缺点

**优点：**
- TypeScript 原生，类型安全
- `useChat` 等 hooks 极大简化前端代码
- 多模型统一接口，切换零成本
- Next.js 生态最佳实践
- 流式优先，UX 体验好
- Zod schema 结构化输出

**缺点：**
- 主要面向 TypeScript/JavaScript 生态
- 复杂 Agent 逻辑不如 LangGraph 灵活
- Server Actions 只在 Next.js 里有用

## 适合什么场景

- Next.js 全栈 AI 应用（聊天、写作助手、代码补全）
- 需要快速上线的产品原型
- 多模型 A/B 测试场景
- 注重流式 UX 体验的前端项目
