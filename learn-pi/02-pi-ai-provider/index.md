---
layout: default
title: "pi-ai：统一多 Provider 的适配层设计"
description: 用消息协议、事件流和失败实验理解 Provider 抽象
eyebrow: Pi / 02
---

# pi-ai：统一多 Provider 的适配层设计

## 为什么这个问题值得关注

Agent 若直接绑定一家模型 SDK，第一版通常很快，但消息格式、流式增量、tool call、stop reason、认证和错误处理会逐渐散落到控制流中。等到需要切换模型或做 A/B 测试时，真正难迁移的往往不是 HTTP 请求，而是这些已经渗入 Agent Loop 的语义。

`@earendil-works/pi-ai` 的目标不是让所有 Provider 表现一致，而是给上层提供一套稳定的内部协议，再把无法统一的差异留在明确边界里。这一点比“支持多少家 Provider”更值得学习。

> 事实基线：官方仓库 commit [`a470b121`](https://github.com/badlogic/pi-mono/tree/a470b121bf683b4c2b9fc0b3a7c807de7e0cfe9c)。Provider 与模型目录会自动更新，正文不固定维护数量和 SDK 版本。

## 先区分 Provider、Model 与 API

在当前 `pi-ai` 中，三个词承担不同职责：

| 概念 | 负责什么 | 例子 |
| --- | --- | --- |
| Provider | 模型目录、认证和请求路由 | Anthropic、OpenAI、OpenRouter |
| Model | 上下文窗口、价格、能力和具体模型 id | 某个 tool-capable model |
| API implementation | 真实 wire protocol 与流式转换 | `anthropic-messages`、`openai-responses` |

多个 Provider 可以共享一种 API implementation。例如若服务兼容 OpenAI 协议，适配层可以复用相同的消息与流转换，但仍由各自 Provider 管理模型目录、认证和 endpoint。

这个拆分避免把“厂商”“模型”和“协议”混成一个枚举。接入新厂商时，如果协议已经兼容，通常不需要再复制一套完整流式解析器。

## 统一消息是 Agent 的内部协议

`Context` 是传给模型的可序列化输入，核心由 system prompt、messages 和 tools 组成：

```typescript
import { Type, type Context, type Tool } from "@earendil-works/pi-ai";

const tools: Tool[] = [{
  name: "get_time",
  description: "Return the current time for a timezone",
  parameters: Type.Object({
    timezone: Type.String(),
  }),
}];

const context: Context = {
  systemPrompt: "Answer with tool evidence.",
  messages: [{
    role: "user",
    content: "What time is it in Asia/Shanghai?",
    timestamp: Date.now(),
  }],
  tools,
};
```

消息不是一段拼接字符串，而是可判别的结构：

- `user` 保存用户文本或图片；
- `assistant` 保存 text、thinking、tool call、usage 和 stop reason；
- `toolResult` 保存 `toolCallId`、工具名、内容、`isError` 与可选 details。

这套 Message IR 的价值在于可传递和可恢复。上层可以把同一段历史交给另一个模型，也可以保存到 Session，再从活动分支重建 Context。

## 从统一 Context 到 Provider 请求

一次模型调用经过的不是简单透传，而是两次方向相反的转换：

```text
统一 Context
  -> Provider/API adapter
  -> 厂商请求体与认证头
  -> SSE、WebSocket 或其他流式响应
  -> 统一 AssistantMessageEvent
  -> 完整 AssistantMessage
```

出站转换要处理 role、content block、tool schema、thinking 选项、缓存提示和 Provider 特有字段。入站转换更困难，因为 tool arguments 可能分多个 chunk 到达，usage 和 stop reason 也可能只在尾部事件中出现。

适配器必须在流结束时收束出一条完整 `AssistantMessage`。只消费屏幕上的 text delta 而不等待最终消息，会丢失 tool call、usage、错误和终态。

## 同一个流同时服务过程与终态

`pi-ai` 返回 `AssistantMessageEventStream`。消费者既可以 `for await` 接收过程事件，也可以等待 `result()` 得到完整消息：

```typescript
const stream = models.stream(model, context);

for await (const event of stream) {
  if (event.type === "text_delta") {
    process.stdout.write(event.delta);
  }
  if (event.type === "toolcall_end") {
    console.log(event.toolCall.name, event.toolCall.arguments);
  }
}

const assistant = await stream.result();
context.messages.push(assistant);
```

这对应《动手学 Pi》的 EventStream 练习：过程事件可能先到，消费者也可能先等待；无论时序怎样，最终 result 必须只结算一次，并包含已经累计的完整内容。

### 为什么不能只返回 AsyncIterator

纯 AsyncIterator 适合渲染增量，却不天然表达“所有增量收束后的最终对象”。如果每个消费者都自行拼接 delta，就会出现多个不一致版本：TUI 拼出一份、日志拼出一份、Agent Loop 又拼出一份。

让 stream 自己拥有最终 result，可以把以下不变量集中到一处：

- tool arguments 按 content index 正确合并；
- partial thinking 和 text 不丢失；
- usage 在尾部事件到达后结算；
- error 与 abort 仍返回结构化 AssistantMessage；
- 多个消费者不会修改同一份半成品。

## stop reason 是控制流，不是展示文字

当前统一终态包括：

| stop reason | 上层应如何理解 |
| --- | --- |
| `stop` | 正常结束，若没有 tool call 可结束当前 Loop |
| `toolUse` | assistant 请求工具，执行并追加结果后继续 |
| `length` | 输出达到限制，不应假装任务已经完成 |
| `error` | Provider 或协议失败，应保留诊断并决定是否重试 |
| `aborted` | 调用被取消，不应继续启动新工具或模型请求 |
| `deferred` | Provider 返回可延后获取的句柄，需由宿主管理生命周期 |

如果统一层只保留文本，不保留 stop reason，Agent Loop 就只能通过内容猜测下一步。可靠控制流必须依赖结构化终态，而不是“看起来像回答完了”。

## `streamSimple` 统一常用能力，不消灭差异

`streamSimple()` 提供 Provider-neutral 的常用选项，例如 tool choice 和 reasoning level。需要完整厂商能力时，可以进入具体 API implementation 的 typed options。

这形成两层使用方式：

1. **简单层**：业务只依赖共同语义，便于切换和测试。
2. **具体层**：显式选择某种 API，换取独有能力，同时接受绑定。

这比“所有 Provider 字段都塞进一个巨型 options”更诚实。真正无法等价表达的能力，应留在具体 API 边界，不应该用一个宽泛的 `Record<string, unknown>` 假装完全可移植。

## 抽象会从哪些地方泄漏

接口相同不代表行为相同。至少要测试：

- 并行 tool call 的生成质量和顺序；
- thinking block 是否可用、是否计入 output；
- prompt cache 的写入、读取与计费语义；
- image、grounding 或其他多模态能力；
- tool schema 严格模式与参数修复能力；
- retry-after、限流和网络错误的形态；
- usage、response id 和实际 response model 是否完整返回。

Provider 切换后，TypeScript 仍然编译通过，只能证明接口形状一致，不能证明任务成功率、成本和恢复行为一致。

## 错误为什么也要形成最终消息

当前 `StreamFunction` 的契约要求：调用开始后的请求、模型或运行时失败，应编码进返回流，而不是让消费者只收到一个裸异常。错误终态应产生 `stopReason: "error"` 或 `"aborted"`，并保留已经产生的 partial 内容和脱敏诊断。

这种设计解决两个问题：

1. UI、Agent Loop 和日志观察到同一种终态；
2. 中途已经产生的文本或 tool arguments 不会因为一次 throw 全部消失。

但“保留 partial”不代表可以把 partial 当作成功结果。上层仍要根据 stop reason 决定重试、停止或请求人工处理。

## 一个可复现的双模型实验

选择同一项只读任务，在两个 Provider 或模型上运行，不要同时改变 Prompt 和工具：

```text
任务：读取 package.json，报告 scripts 中是否存在 test，并引用原始字段。
工具：只开放 read。
失败注入：第一次请求一个不存在的文件，再观察是否恢复。
```

记录以下证据：

| 指标 | 模型 A | 模型 B |
| --- | --- | --- |
| 是否选择正确工具 |  |  |
| 参数是否一次通过 schema |  |  |
| 模型请求轮数 |  |  |
| 失败后是否恢复 |  |  |
| input / output / cache token |  |  |
| 延迟与最终验证结果 |  |  |

同一个任务至少重复数次。单次成功只能说明 Demo 能跑，无法说明 Provider 切换在你的任务分布上可靠。

## 何时使用统一层

适合使用 `pi-ai` 的情况：

- 需要多模型路由、回退或 A/B 测试；
- 希望统一记录 usage、cost、tool call 和错误；
- Agent Loop 不应直接依赖厂商 SDK 对象；
- 需要把 Session 历史交给不同模型继续处理。

不一定适合的情况：

- 只使用一家 Provider，且深度依赖其独有 API；
- 新能力上线后必须立即使用，无法等待中间层适配；
- 原始请求与响应本身就是业务审计对象；
- 统一层需要大量 passthrough 才能工作。

此时直接绑定原生 SDK 并不可耻。错误的是一边深度绑定，一边把系统描述成“随时可切换”。

## 源码阅读入口

- `packages/ai/src/types.ts`：Message、Model、Usage、StopReason 和 stream 契约。
- `packages/ai/src/models.ts`：Provider collection、模型查找和请求路由。
- `packages/ai/src/api/`：各 wire protocol 的出站与入站转换。
- `packages/ai/src/providers/`：模型目录、认证与 Provider factory。
- `packages/ai/test/`：跨 Provider 消息、工具、流和错误契约。

## 小结

- `pi-ai` 统一的是内部消息、事件和终态，不是模型行为。
- Provider 管理目录与认证，Model 描述能力，API implementation 处理 wire protocol。
- 流式事件服务实时观察，`result()` 负责收束完整 AssistantMessage。
- stop reason 是 Agent Loop 的控制信号，不能退化成一段文本。
- 切换 Provider 必须经过相同任务、失败注入和成本记录，不能只看类型是否兼容。

---

下一篇建议继续看：[扩展体系：Skill、Extension 与 Package](../03-extension-system/index.html)
