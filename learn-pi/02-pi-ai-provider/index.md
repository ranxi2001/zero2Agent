---
layout: default
title: "pi-ai：统一多 Provider 的适配层设计"
description: 一个接口适配五家 Provider 的工程选择与抽象泄漏
eyebrow: Pi / 02
---

# pi-ai：统一多 Provider 的适配层设计

## 为什么这个问题值得关注

当你的 Agent 需要调用 LLM 时，你面临一个选择：绑定一家 Provider 的 SDK，还是做一层统一抽象？前者简单但锁定，后者灵活但每一层抽象都会泄漏。Pi 选了后者，并且选了一种特别薄的方式来做。理解这个选择的 tradeoff，能帮你判断自己的项目是否需要类似的适配层，以及应该做到什么程度。

## pi-ai 的设计目标

pi-ai 是 Pi 框架的 Provider 适配层，npm 包名 `@earendil-works/pi-ai`（v0.84.2）。它的职责是：让消费者（pi-coding-agent）用一个统一接口调用任何支持的模型，不感知底层 SDK 差异。

支持的 Provider：

| Provider | 底层 SDK | 版本 |
| --- | --- | --- |
| OpenAI | openai | 6.40.0 |
| Anthropic | @anthropic-ai/sdk | 0.91.1 |
| Google | @google/genai | 1.52.0 |
| AWS Bedrock | @aws-sdk/client-bedrock-runtime | latest |
| Azure OpenAI | openai（Azure endpoint） | 6.40.0 |

这意味着 pi-ai 直接依赖五个 SDK。不是通过中间协议转发，而是包装每个 SDK 的原生调用。

## 设计选择：薄包装而非协议层

pi-ai 的核心设计决定是做**薄包装**：每个 Provider 有一个适配器，把 SDK 调用翻译成统一接口的输入输出格式，仅此而已。

这和 DeepSeek Harness 的 LLM Seam 形成对比：

| 维度 | pi-ai | DSH LLM Seam |
| --- | --- | --- |
| 抽象层级 | 直接包装 SDK | 定义完整协议（适配器注册表 + 统一词汇表） |
| Provider 切换 | 改配置即可 | 实现新适配器并注册 |
| 代码量 | 每个适配器几百行 | 协议定义 + 适配器 + 注册机制 |
| 特有功能暴露 | 通过 passthrough 参数 | 通过协议扩展字段 |
| 新 Provider 接入成本 | 低（包装 SDK） | 中（实现完整协议） |

DSH 更重但更正式，Provider 切换时行为一致性更强。pi-ai 更轻但一致性靠约定维护。

## 统一接口的核心抽象

pi-ai 把所有 Provider 的调用统一为以下概念：

- **Message**：统一消息格式（role + content blocks）
- **Tool Definition**：统一工具定义（name + description + parameters schema）
- **Completion Request**：统一请求（messages + tools + model config）
- **Completion Response**：统一响应（content + tool calls + usage）
- **Stream**：统一流式输出（逐 token 或逐 block 的异步迭代器）

消费者只和这些抽象交互。切换 Provider 只需要改模型标识符，不需要改调用代码。

## 流式输出的统一处理

流式响应是最难统一的部分。各 Provider 的 chunk 格式差异大：

- OpenAI 返回 delta 对象，content 和 tool_calls 分开
- Anthropic 用 event stream，有 content_block_start/delta/stop 三种事件
- Google 返回 candidates 数组里的 partial content
- Bedrock 通过 EventStream 返回二进制帧

pi-ai 的做法是：每个适配器把 Provider 特有的 chunk 格式转换成统一的 `StreamEvent`，消费者遍历同一种异步迭代器。转换逻辑是每个适配器最复杂的部分——占代码量的 60% 以上。

这里有一个隐含 tradeoff：统一流式格式意味着丢失 Provider 特有的流式信息。比如 Anthropic 的 input_tokens_so_far 实时计数，在统一格式里没有对应字段。

## 抽象泄漏：不可避免的现实

统一抽象听起来美好，但每个 Provider 都有独特能力：

- Anthropic 支持 extended thinking（返回推理过程 token）
- OpenAI 支持 function calling 的 parallel 模式
- Google 支持 grounding（搜索增强）
- Bedrock 支持 guardrails（内容过滤配置）

pi-ai 处理这些特有能力的方式是 passthrough 参数——允许消费者传入 Provider 特有的配置字段，适配器直接透传给底层 SDK。这意味着一旦你用了 passthrough，代码就隐式绑定了特定 Provider。

这不是 pi-ai 的设计缺陷，而是所有统一适配层的固有矛盾：**你越想暴露 Provider 特有能力，统一性就越弱；你越想保持统一，可用能力就越受限。**

## 什么时候统一适配层是收益

统一适配层值得做的场景：

- 你需要在多个 Provider 之间切换或做 A/B 测试
- 你的 Agent 逻辑不依赖 Provider 特有功能
- 你想让模型选择成为部署配置而非代码变更
- 你有多个消费者（多个 Agent）需要调用 LLM，不想每个都写一套

## 什么时候它是障碍

统一适配层会成为阻碍的场景：

- 你需要深度使用某个 Provider 的独有功能（比如 Anthropic 的 computer use、OpenAI 的 assistants API）
- 你只用一个 Provider，短期内不会换——适配层纯粹增加了一层间接性
- Provider SDK 更新频繁，你需要第一时间用新功能——适配层的更新总是滞后于原生 SDK
- 调试时需要看到原始请求/响应——统一格式让问题定位变得更绕

## 实际影响

对 Pi 用户而言，pi-ai 的存在意味着：

1. 切换模型只需改 `~/.pi/config.json` 里的 model 字段
2. 社区扩展不需要关心底层 Provider，一次开发到处运行
3. 模型能力差异不由框架抹平——同样的 Prompt 在不同模型上效果可能差异很大
4. Provider 更新新功能时，需要等 pi-ai 发版才能使用

第 4 点是最常见的抱怨：当 Anthropic 发布新的 API 特性时，Pi 用户需要等社区更新适配层。这是所有中间层的通病。

## 小结

pi-ai 选择了最薄的统一方式：直接包装 SDK，不定义中间协议。这让它轻便、易理解、接入新 Provider 成本低。代价是一致性靠人工维护，特有功能通过 passthrough 泄漏，流式处理是最大的复杂度来源。

判断你是否需要类似的适配层，看两个变量：你会用几个 Provider，以及你对 Provider 特有功能的依赖程度。如果只用一家且深度依赖其特性，直接用原生 SDK 更合理。

---

下一篇：[扩展体系：从 Extension 到 Package 的能力组合](../03-extension-system/index.html)
