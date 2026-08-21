---
layout: default
title: LLM 接缝：把模型差异关在适配器里
description: 从统一词汇表理解模型适配、流式协议与失败策略
eyebrow: DeepSeek Harness / 04
---

# LLM 接缝：把模型差异关在适配器里

Agent Loop 如果直接理解每家模型的消息结构、工具调用格式、流式事件和错误码，Provider 每演进一次，控制循环就要做一次手术。更麻烦的是，模型历史、重试和会话回放会同时依赖这些差异。

DSH 把这类变化收进一个独立接缝：Loop 只使用统一词汇表，模型插件负责把统一请求翻译成 Provider 协议，再把响应翻译回来。

## 统一词汇表是架构边界

这个接缝不是“给 HTTP 请求包一层 SDK”，而是定义 Harness 内部如何谈论一次模型交互：

```text
Agent Loop
  -> provider-neutral Message / ContentBlock
  -> LLM registry selects adapter
  -> provider request and stream
  -> provider-neutral StreamChunk
  -> Session Log and Agent Loop
```

`Message` 由内容块组成，文本、推理、工具调用和工具结果使用带类型标签的结构表达。Adapter 只关心翻译，Loop 不需要出现 `if provider == ...` 的分支。

统一词汇表也有代价。它必须足够稳定，才能支撑多 Provider；又要允许扩展，才能接住图像、推理内容或新型块。抽象太窄会抹掉提供方能力，抽象太宽则会把每家协议的偶然细节泄漏进核心。

## 流式输出是一份协议，不是若干字符串

一次流式回复可能同时产生文本、推理内容、多个工具调用和用量信息。DSH 用块级增量表达这条流：块开始、若干 delta、块结束、用量和最终结束原因。

这套协议要维护几条关键不变量：

- 增量通过稳定的块索引归位，允许不同内容块交织出现。
- 块结束时给出完整结果，使消费者不必各自猜测怎样组装。
- 用量必须出现在终止事件之前，终止后不再产生新内容。
- 取消信号必须穿过适配器边界，用户停止任务时网络流也要停止。
- 工具参数在模型边界保留原始 JSON 字符串，校验属于工具执行阶段。

这些约束的价值在于把“不完整流”的处理集中在适配器。否则 UI、日志和 Loop 各自实现一套组装器，同一次断流可能得到三个不同结果。

## Replay State 解决无损回放

统一内容块未必能保存 Provider 为后续请求所需的全部状态。`finish.replayState` 为适配器保留一个不透明、可 JSON 序列化的最小投影，后续请求仍交给同类适配器解释。

这是一个克制的折中：Harness 可以保存和搬运状态，却不假装理解所有 Provider 私有语义。它换来更高的回放保真度，也带来版本兼容责任。适配器升级后若无法读取旧 replay state，会话恢复仍然可能失败。

## 失败事实和恢复策略要分开

Provider 错误先在适配器边界归一化为稳定的失败事实，例如认证失败、限流、没有适配器、HTTP 状态和服务端建议等待时间。至于是否重试、等待多久、是否切换路由，则交给 Agent 层或专门策略插件决定。

把二者分开有两个好处：Adapter 不会擅自重复有成本的请求，重试策略也不需要解析每家错误文案。失败是发生了什么，恢复是系统准备怎么做，它们不应被塞进同一个异常处理块。

## `llm/stream`：模型调用的横切接缝

注册表解决“由谁调用模型”，`llm/stream` waterfall 解决“每次调用还要经过哪些治理”。遥测、测试替身、限流、审计和故障注入都可以包裹真实适配器；策略插件也可以在明确条件下短路下游。

这里仍要遵守 Cordis 的纪律：只观察就必须委托；短路就要承担生成一条完整合法流的责任。Agent Loop 构造的请求还需要保持不可变，改变模型、工具或消息内容应发生在更合适的请求装配接缝，而不是在传输层偷偷修改。

## 这层抽象不能解决什么

- 统一协议不会自动抹平不同模型的能力和质量差异。
- Adapter 能归一化错误，却不能保证所有 Provider 都支持无损续接。
- 重试可以恢复瞬时故障，也可能放大费用或重复外部操作。
- Mock Adapter 能验证协议和 Loop，不能代表真实服务的限流、延迟和断流行为。
- 新 Provider 接入成功不等于生产可用，还需要兼容性样本、取消测试和流式故障测试。

事实基线见官方 [LLM Streaming 子系统文档](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.1.0-rc.8/docs/subsystems/llm-streaming.zh.md) 与 [`dsh-llm` 包说明](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.1.0-rc.8/packages/llm/llm/README.zh.md)。

## 小结

- LLM 接缝用统一词汇表隔离 Provider 协议变化，让 Loop 只理解 Harness 语义。
- StreamChunk 是有顺序、不变量和终止语义的协议，不是文本片段列表。
- Replay state 由适配器拥有，兼顾统一日志与 Provider 私有续接信息。
- 失败事实由适配器归一化，重试和路由属于独立策略。

下一篇建议继续看：

- [Agent Loop：控制平面如何推进任务](../05-agent-loop/index.html)
