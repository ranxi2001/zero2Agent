---
layout: default
title: 大模型 API 输入输出与 Tool Calling
description: 从消息协议到完整工具调用循环，理解 Agent 如何和大模型 API 交互
eyebrow: Agent Basic / 05
---

# 大模型 API 输入输出与 Tool Calling

很多人第一次感受到 Agent 和普通聊天应用的差别，往往就是从 Tool Calling 开始。

因为一旦系统能调工具，它就不再只能“基于参数里的知识说话”，而是开始具备外部行动能力。

不过，在写 Agent Loop 之前，必须先看懂模型 API 到底收到了什么、又返回了什么。否则代码虽然能跑，一遇到多轮对话、并行工具、流式中断或厂商切换，就很容易失控。

这一篇会回答几个基础问题：

- 模型为什么不会自动记住上一次请求
- 一次请求由哪些部分组成
- <code>system</code>、<code>developer</code>、<code>user</code>、<code>assistant</code>、<code>tool</code> 分别表示什么
- 响应除了文本，还包含哪些控制信息
- 客户端执行函数工具时，为什么通常要完成“请求工具—执行—回传”的多步闭环
- 并行调用、结构化输出和流式响应应该怎样处理

## 为什么模型需要工具

单靠模型本身，通常做不到下面这些事：

- 获取实时数据
- 查询私有数据库
- 读写文件
- 调用内部系统
- 执行代码
- 与外部 API 交互

模型擅长的是理解、推理、生成。

工具解决的是访问外部世界和执行动作。

所以 Tool Calling 的意义不是“让模型更聪明”，而是“让系统更有手”。

## 一个最简单的心智模型

你可以把工具调用理解成：

~~~mermaid
flowchart LR
    A([模型]) -->|决定做什么| B([程序])
    B -->|真的去做| C([结果])
    C -.->|返回| A
~~~

更完整一点就是：

~~~mermaid
flowchart TD
    A([用户目标]) --> B[模型判断是否需要工具]
    B --> C[模型选择工具并生成参数]
    C --> D[程序校验参数并执行工具]
    D --> E[程序把结果返回给模型]
    E --> F{信息是否足够}
    F -->|否| B
    F -->|是| G[模型生成最终答案]
~~~

这里最关键的是分工。

模型负责：

- 根据当前输入决定是否调用工具
- 选择工具并生成参数
- 根据工具结果继续决策或组织答案

程序负责：

- 校验模型生成的工具名和参数
- 真正执行工具
- 处理权限、超时、重试和异常
- 把结果按协议返回给模型

模型输出“我要调用某工具”不等于工具已经执行。只有宿主程序完成调用并得到结果，外部动作才真正发生。

## API 通常不会记住上一轮

从调用方视角看，大模型 API 通常是无状态的。一次 HTTP 请求结束后，下一次请求不会天然继承上一次请求里的用户问题、模型回复或工具结果。

例如，第一次只发送：

~~~json
[
  {"role": "user", "content": "我叫小林。"}
]
~~~

第二次只发送：

~~~json
[
  {"role": "user", "content": "我叫什么？"}
]
~~~

模型并不能仅凭第二个请求可靠地知道答案。应用需要在第二次请求中重新带上相关历史：

~~~json
[
  {"role": "user", "content": "我叫小林。"},
  {"role": "assistant", "content": "你好，小林。"},
  {"role": "user", "content": "我叫什么？"}
]
~~~

因此，“对话记忆”首先是 Agent Harness 的状态管理能力，而不是模型参数在每轮请求后发生了变化。

有些 API 支持会话 ID、服务端存储或引用上一条响应。此时客户端可能不用重复发送全部字节，但语义上仍然需要由服务端重建上下文。生产系统也不应把唯一状态只托管在厂商侧：任务进度、工具执行记录和可恢复检查点仍然要由应用管理。

## 一次请求由什么组成

不同厂商的字段名并不完全一样，但一次模型请求通常包含以下几类信息：

| 部分 | 常见内容 | 是否直接成为模型上下文 |
| --- | --- | --- |
| 连接与鉴权 | API 地址、密钥、HTTP Header、超时 | 通常不会 |
| 模型与推理配置 | 模型名、最大输出、采样参数 | 会影响生成，但不一定作为文本输入 |
| 指令与输入 | system/developer 指令、用户消息、历史消息、图片或文件 | 通常会 |
| 工具定义 | 工具名、用途、参数 Schema、工具选择策略 | 通常会 |
| 输出约束 | JSON Schema、文本格式、模态类型 | 视接口而定 |
| 追踪元数据 | 自定义 metadata、请求标签、租户信息 | 通常不会 |

下面使用一种 OpenAI-compatible Chat Completions 风格展示结构：

~~~jsonc
{
  "model": "example-model",
  "messages": [
    {"role": "system", "content": "实时信息必须通过工具查询。"},
    {"role": "user", "content": "上海现在天气如何？"}
  ],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "get_weather",
        "description": "查询指定城市的当前天气",
        "parameters": {
          "type": "object",
          "properties": {
            "city": {"type": "string"},
            "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
          },
          "required": ["city", "unit"],
          "additionalProperties": false
        }
      }
    }
  ],
  "tool_choice": "auto",
  "stream": false
}
~~~

这里借用 Chat Completions 风格，是因为它便于观察消息数组和工具调用配对。它不是所有厂商的统一格式，也不代表 OpenAI 当前所有场景下唯一或最新的通用接口。OpenAI Responses、Anthropic Messages 和 Gemini 的精确字段应以对应 SDK 与官方文档为准。

## 用 provider-neutral 的 item 来理解消息

不要先背某个 SDK 的类名。更稳定的理解方式，是把一次交互拆成几类有来源、有类型的 item：

| 语义类型 | 谁产生 | 作用 |
| --- | --- | --- |
| 开发者指令 | 应用开发者 | 定义身份、规则、边界和输出要求 |
| 用户输入 | 终端用户 | 提出目标、数据和补充约束 |
| 助手文本 | 模型 | 给用户的普通文本或最终答案 |
| 工具请求 | 模型 | 声明要调用的工具、参数和协议要求的关联信息 |
| 工具结果 | Agent 程序 | 返回某次工具执行的结果或错误 |

有的协议把这些 item 都表现成带 <code>role</code> 的 message；有的协议在一条 message 内使用多个 content block；还有的协议直接返回一组不同类型的 output item。字段形式不同，语义流转却基本相同。

### 角色不是跨厂商通用枚举

常见角色可以这样理解：

- <code>system</code>：系统级规则。部分接口把它放在消息数组中，部分接口使用顶层字段。
- <code>developer</code>：开发者指令。某些 OpenAI 接口或模型用它区分应用规则与普通用户输入；并非所有兼容接口都支持。
- <code>user</code>：用户提供的目标和内容。
- <code>assistant</code>：模型产生的文本、工具请求或其他输出。
- <code>tool</code>：在部分 Chat Completions 风格协议中表示工具执行结果，不是模型自己生成的事实。

下表只用于建立语义映射，不用于代替官方字段文档：

| 语义 | Chat Completions 风格 | OpenAI Responses 风格 | Anthropic 风格 | Gemini 风格 |
| --- | --- | --- | --- | --- |
| 开发者规则 | <code>system</code> / 部分模型支持 <code>developer</code> | <code>instructions</code> 或输入 item | 顶层 <code>system</code> | <code>systemInstruction</code> |
| 用户输入 | <code>user</code> message | input message/item | <code>user</code> message | <code>user</code> content |
| 模型输出 | <code>assistant</code> message | output item | <code>assistant</code> content block | <code>model</code> content |
| 工具请求 | <code>assistant.tool_calls</code> | function call item | <code>tool_use</code> block | <code>functionCall</code> part |
| 工具结果 | <code>tool</code> + <code>tool_call_id</code> | function call output + <code>call_id</code> | <code>tool_result</code> block | <code>functionResponse</code> part |

这里真正跨厂商的不变量，是**工具结果必须与产生它的工具请求保持可验证的因果关联**。显式 call ID 是常见实现，但不是所有协议都强制提供：例如 Gemini 的函数调用可以没有显式 ID，此时应按该协议规定的消息结构、名称和顺序关联，不能自行套用其他厂商的字段约束。

迁移厂商时，不要只做字段名替换。还要检查：

- 指令究竟放在顶层还是消息列表
- 工具请求和结果是否必须相邻
- 是否要求回传模型原始输出 item
- 并行调用时工具结果怎样配对
- 多模态内容和流式事件怎样编码

## 响应不只是一个字符串

只读取 <code>content</code> 是许多 Agent Bug 的起点。一次成功响应至少可能包含：

- 普通文本
- 一个或多个工具调用请求
- 结构化输出或多模态 output item
- 停止原因，例如正常结束、请求工具、长度截断或安全拦截
- token 用量，例如输入、输出和缓存 token
- 响应 ID，以及 HTTP Header 或 SDK 元数据里的 provider request ID
- 警告、拒答、安全状态或错误信息

一个简化的 Chat Completions 风格响应可能是：

~~~jsonc
{
  "id": "chatcmpl_example",
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": null,
        "tool_calls": [
          {
            "id": "call_weather_01",
            "type": "function",
            "function": {
              "name": "get_weather",
              "arguments": "{\"city\":\"上海\",\"unit\":\"celsius\"}"
            }
          }
        ]
      },
      "finish_reason": "tool_calls"
    }
  ],
  "usage": {
    "prompt_tokens": 312,
    "completion_tokens": 28,
    "total_tokens": 340
  }
}
~~~

这里有三个容易忽略的细节：

1. <code>content</code> 为空不代表响应失败，模型可能正在请求工具。
2. 在这种协议中，<code>arguments</code> 是一段 JSON 字符串，程序仍需解析并按 Schema 校验。
3. <code>finish_reason</code> 和 <code>usage</code> 的字段名、取值会因厂商而异，不能在跨厂商代码里直接写死。

生产环境还应记录 provider request ID。它通常位于响应 Header 或 SDK 暴露的元数据中，是向服务商排查延迟、限流和异常的重要线索；不要把它与业务会话 ID、响应 ID 或工具调用 ID 混为一谈。

## 客户端工具闭环：通常至少两次模型请求

下面完整走一遍“上海现在几点，天气如何？”的调用序列。示例是由客户端执行函数工具、再把结果交还模型组织答案的闭环，因此通常至少需要两次模型请求。若只提取工具参数而不需要自然语言收尾，或使用由供应商代为执行的托管工具，调用次数和数据流可能不同。示例仍采用 OpenAI-compatible Chat Completions 风格，时间和天气都是固定实验数据，不代表真实查询结果。

### 第一次请求：把问题和工具交给模型

~~~jsonc
{
  "model": "example-model",
  "messages": [
    {
      "role": "system",
      "content": "回答实时问题前必须调用合适的工具，不得猜测。"
    },
    {
      "role": "user",
      "content": "上海现在几点，天气如何？"
    }
  ],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "get_local_time",
        "description": "查询 IANA 时区的当前本地时间",
        "parameters": {
          "type": "object",
          "properties": {
            "timezone": {
              "type": "string",
              "description": "IANA 时区，例如 Asia/Shanghai"
            }
          },
          "required": ["timezone"],
          "additionalProperties": false
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "get_weather",
        "description": "查询城市当前天气",
        "parameters": {
          "type": "object",
          "properties": {
            "city": {"type": "string"},
            "unit": {
              "type": "string",
              "enum": ["celsius", "fahrenheit"]
            }
          },
          "required": ["city", "unit"],
          "additionalProperties": false
        }
      }
    }
  ],
  "tool_choice": "auto"
}
~~~

### 第一次响应：模型请求两个工具

~~~jsonc
{
  "id": "chatcmpl_step_1",
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": null,
        "tool_calls": [
          {
            "id": "call_time_01",
            "type": "function",
            "function": {
              "name": "get_local_time",
              "arguments": "{\"timezone\":\"Asia/Shanghai\"}"
            }
          },
          {
            "id": "call_weather_01",
            "type": "function",
            "function": {
              "name": "get_weather",
              "arguments": "{\"city\":\"上海\",\"unit\":\"celsius\"}"
            }
          }
        ]
      },
      "finish_reason": "tool_calls"
    }
  ],
  "usage": {
    "prompt_tokens": 428,
    "completion_tokens": 67,
    "total_tokens": 495
  }
}
~~~

此时模型没有查时间，也没有查天气。它只生成了两个待执行请求。Agent 程序接下来需要：

1. 确认工具名在允许列表中
2. 解析 <code>arguments</code>
3. 按 JSON Schema 和业务规则校验参数
4. 检查权限、预算和审批要求
5. 执行工具并取得结果

假设两个工具返回：

~~~json
{"timezone":"Asia/Shanghai","datetime":"2026-07-20T15:42:00+08:00"}
~~~

~~~json
{"city":"上海","temperature":33.1,"unit":"celsius","conditions":"多云","observed_at":"2026-07-20T15:40:00+08:00"}
~~~

### 第二次请求：把原调用和工具结果一起送回

~~~jsonc
{
  "model": "example-model",
  "messages": [
    {
      "role": "system",
      "content": "回答实时问题前必须调用合适的工具，不得猜测。"
    },
    {
      "role": "user",
      "content": "上海现在几点，天气如何？"
    },
    {
      "role": "assistant",
      "content": null,
      "tool_calls": [
        {
          "id": "call_time_01",
          "type": "function",
          "function": {
            "name": "get_local_time",
            "arguments": "{\"timezone\":\"Asia/Shanghai\"}"
          }
        },
        {
          "id": "call_weather_01",
          "type": "function",
          "function": {
            "name": "get_weather",
            "arguments": "{\"city\":\"上海\",\"unit\":\"celsius\"}"
          }
        }
      ]
    },
    {
      "role": "tool",
      "tool_call_id": "call_time_01",
      "content": "{\"timezone\":\"Asia/Shanghai\",\"datetime\":\"2026-07-20T15:42:00+08:00\"}"
    },
    {
      "role": "tool",
      "tool_call_id": "call_weather_01",
      "content": "{\"city\":\"上海\",\"temperature\":33.1,\"unit\":\"celsius\",\"conditions\":\"多云\",\"observed_at\":\"2026-07-20T15:40:00+08:00\"}"
    }
  ],
  "tools": [
    // 与第一次请求相同的工具定义
  ]
}
~~~

第二次请求必须让模型看见完整因果链：

~~~text
用户提出问题
  -> 模型发出 call_time_01 和 call_weather_01
  -> 程序分别返回两个调用结果
  -> 模型根据结果生成答案
~~~

不能只发送工具结果，也不要省略第一次响应里的 assistant 工具请求。许多协议会校验这个配对关系。

### 第二次响应：模型生成最终答案

~~~jsonc
{
  "id": "chatcmpl_step_2",
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "上海当前时间是 2026 年 7 月 20 日 15:42（UTC+8）。天气为多云，气温 33.1°C；天气观测时间为 15:40。"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 612,
    "completion_tokens": 48,
    "total_tokens": 660
  }
}
~~~

只有到这里，这轮面向用户的回答才完成。如果第二次响应又包含工具请求，程序就继续执行下一轮，直到获得最终输出或触发结束条件。

## 因果关联是工具轨迹的外键

对于带显式 call ID 的协议，一个工具调用至少有三项关键数据：

- 工具名：要执行哪个能力
- 参数：这次具体要做什么
- 调用 ID：结果应该归属于哪次请求

处理这类协议的调用 ID 时应遵守以下规则：

- 原样保存模型返回的 ID，不自行改写
- 每个工具结果都精确引用对应 ID
- 不按数组顺序猜测结果归属
- 同一轮多个调用即使工具名相同，也要分别配对
- 工具失败也要返回结构化错误，并绑定原调用 ID

例如：

~~~json
{
  "ok": false,
  "error": {
    "code": "UPSTREAM_TIMEOUT",
    "message": "天气服务超时",
    "retryable": true
  }
}
~~~

这段错误应作为 <code>call_weather_01</code> 的工具结果返回，而不是伪装成普通用户消息。

调用 ID 解决的是协议内配对，不等于业务幂等键。流式重试或整轮重新生成时，厂商可能返回新的调用 ID。支付、发信、下单等副作用工具还需要独立的业务幂等键和执行台账，防止重试造成重复操作。

如果当前协议没有显式调用 ID，就应使用官方规定的结构和顺序维持关联，并在自己的适配层生成稳定的内部事件 ID 用于追踪；内部 ID 不能伪装成厂商字段回传。

## 并行工具调用怎样处理

上例中的时间查询和天气查询互不依赖，可以并行执行。模型可能在一次响应中返回多个工具请求，Agent Harness 应该：

1. 先解析并校验整组调用
2. 判断调用之间是否存在数据依赖或写冲突
3. 对独立、只读调用设置并发上限后并行执行
4. 为每个调用单独记录成功、错误、耗时和结果
5. 按当前协议的关联机制组装结果，再发起下一次模型请求

不要为了追求速度盲目并行写操作。例如“创建订单”和“扣减库存”可能有顺序、事务或补偿要求，应由业务工作流控制，而不是根据模型返回数组直接同时执行。

某个并行调用失败时，也不要丢掉其他调用的结果。应为每个调用生成一条明确的成功或失败结果，让模型决定是否重试、降级或向用户说明信息不完整。

## 最小 Agent Loop

把上面的协议压缩成伪代码，核心循环并不复杂：

~~~python
history = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "user", "content": user_input},
]

for step in range(MAX_STEPS):
    response = call_model(
        messages=history,
        tools=tool_definitions,
    )
    record_usage_and_request_id(response)

    assistant_item = parse_assistant_item(response)
    stop = classify_stop_reason(response)
    validate_model_turn(assistant_item, stop)
    history.append(assistant_item)

    if stop in {"refusal", "truncated", "incomplete"}:
        return handle_non_success_stop(stop, assistant_item)

    if stop == "completed" and not assistant_item.tool_calls:
        return assistant_item.text

    if stop != "tool_calls" or not assistant_item.tool_calls:
        raise ProtocolError("stop reason and typed output disagree")

    calls = validate_tool_calls(assistant_item.tool_calls)
    results = execute_with_policy(calls)

    for call, result in match_by_call_id(calls, results):
        history.append({
            "role": "tool",
            "tool_call_id": call.id,
            "content": serialize(result),
        })

raise StepBudgetExceeded(MAX_STEPS)
~~~

真正困难的部分不在循环，而在周围的工程约束：

- 输入和输出校验
- 权限与人工审批
- 超时、重试和幂等
- 上下文长度与成本
- 结束条件和调用预算
- 日志、追踪与故障恢复

## Structured Output 和 Tool Calling 的边界

两者都可能使用 JSON Schema，但解决的问题不同。

| 能力 | Structured Output | Tool Calling |
| --- | --- | --- |
| 核心目的 | 约束模型输出的数据结构 | 让模型请求宿主程序执行能力 |
| 是否访问外部世界 | 通常不会 | 可能会，由客户端工具或供应商托管工具执行 |
| 典型用途 | 信息抽取、分类、生成固定字段 | 查询数据库、搜索、发邮件、写文件 |
| 结果由谁产生 | 模型 | 客户端工具、供应商托管工具或外部系统 |
| 是否需要客户端回传结果再调用模型 | 通常不需要 | 客户端执行的函数工具通常需要；托管工具未必需要 |

如果任务只是“把这段合同抽取成固定 JSON”，优先考虑 Structured Output。

如果任务是“查询合同系统，再把结果写入审批流”，就需要 Tool Calling。

二者也可以组合：先调用工具取得外部数据，再让模型按 Schema 生成最终结构化结果。需要注意，工具参数符合 Schema 只说明参数格式合法，不代表该工具有权限执行，也不代表业务语义正确；程序仍然要做业务校验。

本章后续所说的“执行工具并回传结果”，默认指客户端执行的 function tool loop。搜索、代码执行等供应商托管工具可能在一次 API 交互内部完成调用与结果注入，客户端看到的是另一种事件序列。

## 流式响应不是一串可以随时解析的完整 JSON

打开 stream 后，服务端通常会把一次响应拆成一系列事件。概念上可能经历：

~~~text
response_started
text_delta 或 tool_call_started
tool_arguments_delta
tool_arguments_delta
tool_call_completed
response_completed
~~~

实际事件名因厂商而异。关键是把流式处理写成状态机，而不是“每收到一段就当成完整响应”。

例如工具参数可能分成三段到达：

~~~text
{"city":"上
海","unit":"cel
sius"}
~~~

任何一个中间片段都不是可独立解析的 JSON。正确做法是：

1. 按 output item、调用索引或调用 ID 累积增量
2. 等待该工具调用的完成事件
3. 拼接完整参数
4. 解析 JSON 并执行 Schema 校验
5. 等待该工具调用的协议完成边界；如果供应商只提供整轮完成事件，就等待整轮结束

如果供应商提供可靠的 item-level 完成事件，某个调用的参数完整并通过校验后，可以在同一响应的其他内容仍在生成时提前执行；本仓库的入门实验采用更保守的整轮完成策略。无论哪种策略，连接在参数传输一半时中断，都应丢弃未完成调用，不能猜测剩余字段，更不能执行半截参数。恢复或重试还要考虑重复副作用：模型重新生成的调用可能语义相同但调用 ID 不同，因此业务幂等不能只依赖调用 ID。

流式文本也可能因长度限制、安全拦截、网络断开而提前结束。只有收到协议定义的完成状态，并检查停止原因后，才能把输出标记为完整成功。

## 不要把原始思维链当成系统接口

Agent 系统需要可观测性，但可观测性不等于保存模型的原始 Chain of Thought。

不同模型对 reasoning 的处理差异很大：

- 有的只返回最终答案
- 有的返回可展示的 reasoning summary
- 有的返回不透明或加密的 reasoning item
- 有的要求在后续请求中原样回传某些协议块

因此，不要让业务逻辑依赖“读取模型内心独白”，也不要主动索取、持久化或分析原始隐藏思维链。它不是稳定的跨模型 API 合同，还可能带来隐私、安全和存储风险。

调试 Agent 时应记录可验证的执行轨迹：

- 输入与指令版本，敏感内容应脱敏
- 模型输出的文本或 typed item
- 工具名、校验后的参数和协议关联信息（若有显式调用 ID 则一并记录）
- 工具结果摘要、错误码和耗时
- 停止原因、token 用量和 provider request ID
- 预算、审批与最终退出状态

如果厂商返回 reasoning summary，可以把它当作可选的解释性输出，不能把它当作真实执行证据。如果协议要求回传不透明 reasoning 数据，应把它作为受控的临时协议状态原样传递，不解析，也不写入普通业务日志。

## 工具调用不等于随便开放能力

很多新手一做 Tool Calling，就喜欢把很多能力一次性暴露给模型：

- 搜索
- 文件系统
- shell
- 数据库
- 浏览器
- 写入接口

这在 Demo 阶段看起来很酷，但问题也很快会出现：

- 模型选错工具
- 参数乱填
- 调用次数失控
- 权限过大
- 调试困难

所以工具系统设计的第一原则不是“越多越强”，而是“越清晰越稳”。

## 一个好工具至少要满足什么

至少要满足这几件事：

### 1. 职责清晰

工具到底做什么，边界必须明确。

不要让一个工具同时负责搜索、总结、打分、写入。

### 2. 输入清晰

参数结构应该明确、稳定、可校验。

最好是结构化字段，而不是一大段模糊字符串。

字段描述要说明格式、单位和限制。例如时间使用哪个时区，金额使用元还是分，枚举有哪些合法值。Schema 校验通过后，还应继续做路径范围、资源归属和业务权限校验。

### 3. 输出清晰

返回值尽量稳定，方便模型和程序继续处理。

建议至少区分成功数据与错误对象，并保留来源、时间戳或版本等必要证据。不要把几百 KB 的原始日志直接塞回上下文，可以保存原文，只返回摘要和可追溯引用。

### 4. 权限清晰

能不能写、能不能删、能不能执行命令，必须有边界。

只读与写入工具最好分开。高风险副作用操作应增加白名单、人工确认、沙箱或审批节点，而不是只靠 Prompt 约束。

### 5. 错误可处理

工具失败时要能区分：

- 参数错误
- 权限错误
- 网络错误
- 数据为空
- 超时或限流
- 部分成功

否则系统一失败就不知道问题在哪，也无法决定应该重试、换工具、降级还是停止。

## Tool Calling 最容易踩的坑

### 模型假装调用过工具

这是最常见的问题之一。

模型可能直接编一个结果，而不是发起真正的工具请求。

所以系统需要按响应类型显式区分：

- 模型输出普通文本
- 模型输出工具调用请求
- 程序实际执行工具并取得结果

对实时数据或副作用操作，最终文本不能代替可验证的工具执行记录。

### 工具接口设计过于宽泛

例如一个搜索工具同时支持十几种模式，但没有明确字段。

这会让模型很难稳定地产生正确参数。

### 工具返回结果太脏

如果工具返回的是超长原始文本、混乱 JSON 或不稳定结构，模型后续也会处理得很差。

外部网页、邮件和文档还可能包含提示注入内容。工具结果是“不可信数据”，不能因为它进入了 tool item 就自动获得指令权限。

### 没有调用预算

一旦任务进入循环，系统可能不断尝试：

- 再搜一次
- 再换个参数
- 再调用一次

如果没有轮数、时间、token 和费用预算，成本很容易失控。

### 把传输成功当成任务成功

HTTP 200 只表示接口成功返回，不代表：

- 模型输出没有被截断
- 工具参数已经通过校验
- 所有并行工具都成功
- 最终答案满足业务要求

程序必须继续检查 typed output、停止原因、工具状态和业务验收条件。

## 工具设计的一个务实建议

比起一开始就设计一个万能工具系统，更好的方法是：

1. 先围绕具体任务列出真正需要的能力
2. 每个能力做成边界清晰的小工具
3. 优先保证输入输出稳定
4. 再逐步补权限控制、异常处理和预算控制
5. 用失败样例测试错参、超时、中断、重复调用和越权

也就是说，先做“可控工具”，再做“强大工具”。

## 动手实验

配套实验位于 [examples/agent-api-lab](../../examples/agent-api-lab/index.html)，建议按下面顺序运行：

1. 打印一次普通文本请求的脱敏输入、typed output、停止原因和 usage
2. 跑通上面的两次请求，观察消息轨迹怎样增长
3. 删除第一次 assistant 工具请求，观察协议或模型行为怎样变化
4. 故意错配 call ID，验证 Harness 能否在发请求前拦截
5. 模拟并行调用中一个成功、一个工具失败，并分别模拟模型 API 超时与 5xx
6. 把工具参数拆成多个流式片段，并在中途断流

实验重点不是记住某家 SDK 的字段，而是验证三件事：谁产生了这个 item、它与哪个调用关联、下一轮模型能看到哪些上下文。

## 小结

Tool Calling 是 Agent 非常关键的一步，因为它让系统从“只会说”变成“能行动”。

但模型 API 返回的不是一段孤立文本，而是一组带类型、来源和控制状态的输出。一个可靠的 Agent Harness 必须：

- 显式维护每轮上下文
- 区分文本、工具请求和工具结果
- 按厂商协议保存完整的调用—结果因果关系
- 检查停止原因、usage 和 request ID
- 在流式、并行和重试场景下保证完整性与幂等
- 只记录可验证轨迹，不依赖原始思维链

工具系统也不是插件市场，不是接得越多越好。真正重要的是分工清晰、接口稳定、权限明确、错误可控。

## 参考与边界

本文参考了李博杰《深入理解 AI Agent：设计原理与工程实践》[固定提交 e3883f8c 的第二章“上下文工程”](https://github.com/bojieli/ai-agent-book/blob/e3883f8cec222c31e59c646be96641120863027e/book/chapter2.md)中关于 API 上下文结构和实验教学的思路，并按本仓库的基础教程定位使用独立结构、文字、示例与实验重新实现。链接固定到提交版本，避免上游后续修改导致引用内容漂移。

本文只建立跨厂商心智模型。OpenAI Responses、Anthropic Messages、Gemini 以及具体 SDK 的精确语法与版本差异，继续参考：

- [SDK 与框架选型](../../learn-sdk-frameworks/index.html)

下一篇建议继续看：

- [Memory 设计模式](../06-memory-patterns/index.html)
