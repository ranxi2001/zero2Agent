---
layout: default
title: Context Engineering：系统化设计模型输入
description: 从 Prompt Engineering 到 Context Engineering——Skills 加载、状态栏、压缩策略的工程方法论
eyebrow: Agent Basic / 13
---

# Context Engineering：系统化设计模型输入

前面几篇已经分别讲了：

- 05：API 协议层面的消息结构
- 06：Context、State、Memory 的概念区分和压缩策略

这一篇把视角拉高一层：**当你面对一个完整的 Agent 系统时，怎样系统化地设计模型每一轮看到的 Context？**

这就是 Context Engineering——不只是"写好 Prompt"，而是设计整个信息供给策略。

## 为什么单独谈 Context Engineering

2025-2026 年，行业从 Prompt Engineering 过渡到 Context Engineering，背后有一个核心观察：

> Agent 的能力天花板不是模型参数量，而是模型每一步决策时能看到什么。

同一个模型，在以下两种情况下表现差距巨大：

- 情况 A：只给一句"帮我分析这个项目的风险"
- 情况 B：给出任务目标、已完成的步骤、待检查的工具列表、相关历史结论、当前约束

差别不在模型能力，而在 Context 质量。

Context Engineering 的范围比 Prompt Engineering 大得多：

| 层次 | 关注什么 | 典型产出 |
| --- | --- | --- |
| Prompt Engineering | 单次调用的指令质量 | 模板、结构化指令、Few-shot |
| **Context Engineering** | **整个信息供给链的设计** | **Skills 加载策略、状态栏、动态注入、压缩管道** |

Prompt Engineering 是 Context Engineering 的子集。

## Context 的五个组成部分

一次 Agent 调用中，模型可见的 Context 通常由五部分组成：

```text
┌─────────────────────────────────────────┐
│  1. System Prompt（系统指令）              │  ← 身份、规则、约束
│  2. Tool Definitions（工具定义）           │  ← 能力列表、参数 Schema
│  3. Conversation Trajectory（执行轨迹）    │  ← 历史消息、工具调用/结果
│  4. Dynamic Metadata（动态元数据）          │  ← 状态栏、时间、环境信息
│  5. Retrieved Content（检索内容）           │  ← RAG 结果、Skills 文档
└─────────────────────────────────────────┘
```

Context Engineering 的目标是：让这五部分在每一轮都恰好包含当前决策所需的信息——不多（浪费 token、引入噪声），不少（关键信息缺失导致错误决策）。

## Prompt Engineering 的五个维度

System Prompt 虽然只是 Context 的一部分，但它决定了模型的基础行为模式。一个好的 System Prompt 通常覆盖五个维度：

### 1. 语气与风格

定义模型应该怎样表达：

- 用大写或 **加粗** 标记硬约束（`NEVER`、`MUST`）
- 明确输出的详细程度和格式偏好
- 声明角色边界（"你是……，你不能……"）

### 2. 结构化组织

用 XML 标签或 Markdown 分区组织指令，而不是写一大段连续文字：

```text
<role>你是一个代码审查助手。</role>
<constraints>
- 不修改代码，只指出问题
- 每个问题必须引用具体行号
</constraints>
<output_format>
## 问题列表
- [文件:行号] 问题描述
</output_format>
```

结构化的好处：模型更容易定位和遵守不同类别的指令，调试时也更容易判断哪部分没生效。

### 3. 流程驱动而非规则堆砌

与其堆一大堆规则，不如给出清晰的执行流程（SOP）：

```text
收到用户请求后：
1. 先判断请求类型（查询 / 操作 / 闲聊）
2. 如果是查询，先检索知识库
3. 如果是操作，先验证权限
4. 最后生成回复
```

流程化指令比散列规则更容易被模型稳定遵守。

### 4. 业务规则精炼

从产品需求中提取出模型需要遵守的核心规则，删掉废话：

- 原始需求："在用户询问退款相关问题时，系统应该首先查询订单状态，如果订单已完成且在7天内，可以自动处理退款……"
- 精炼版：`退款条件：订单状态=已完成 AND 下单≤7天 → 自动退款；否则转人工`

规则越精炼，模型遵守率越高。

### 5. Few-shot 示例

给 2-3 个精选示例比给 10 个冗余示例效果更好。

好的 Few-shot 应覆盖：

- 一个标准场景
- 一个边界场景
- 一个应该拒绝的场景

示例的格式应和真实交互格式一致，不要用虚构的格式。

## Agent Skills：按需加载能力

当 Agent 具备几十甚至上百种能力时，不可能把所有指令都塞进 System Prompt。这时需要 **Skills 架构**——一种按需加载的能力管理系统。

### 三层加载架构

```text
┌────────────────────────────────────────────┐
│  第一层：Metadata（始终在 Context 中）        │
│  · 每个 Skill 的名称和一句话描述              │
│  · 总共几百 token                            │
│  · 让模型知道"有哪些能力可以用"               │
├────────────────────────────────────────────┤
│  第二层：Core Workflow（按需加载）             │
│  · 当模型决定使用某个 Skill 时加载            │
│  · 包含完整的执行指令和约束                    │
│  · 通常几千 token                            │
├────────────────────────────────────────────┤
│  第三层：Detailed Docs（深度按需）            │
│  · Core Workflow 中引用的详细文档              │
│  · 只在模型需要时通过工具读取                  │
│  · 可能是完整的 API 文档或参考资料             │
└────────────────────────────────────────────┘
```

### 为什么不把所有 Skills 直接注入

| 方案 | 优势 | 问题 |
| --- | --- | --- |
| 全部注入 System Prompt | 模型看到完整信息 | token 爆炸、指令冲突、注意力分散 |
| 全部通过工具读取 | 极省 token | 模型不知道有什么能力，无法主动选择 |
| **三层架构** | 平衡 token 和能力发现 | 需要设计加载逻辑 |

### Skills 的 cache-friendly 设计

第一层 Metadata 放在 Context 的稳定前缀中，这样跨请求时更容易命中 Provider 的前缀缓存。第二层和第三层是动态内容，放在 Context 的后部。

```text
稳定区域：System Prompt + Tool Definitions + Skills Metadata
动态区域：执行轨迹 + 当前加载的 Skill Workflow + 检索内容
```

### 实际例子

以 Claude Code 为例，它的 Skills 就是这种架构：

- Metadata：每个 skill 有 name 和一句话触发描述，始终可见
- Core Workflow：用户触发特定 skill 后加载完整指令
- Detailed Docs：skill 内部需要时再读取参考文件

这让系统能管理几十种能力而不爆 Context。

## Agent Status Bar：结构化的执行元数据

传统的 Agent 只在消息历史中保留执行轨迹。Status Bar 是一种补充机制——用结构化字段把当前执行状态显性地注入 Context。

### Status Bar 包含什么

```text
<status_bar>
  <task_plan>
    - [x] 查询用户订单状态
    - [x] 验证退款条件
    - [ ] 执行退款操作
    - [ ] 发送确认通知
  </task_plan>
  <environment>
    <current_time>2026-07-22T14:30:00+08:00</current_time>
    <session_duration>4m 32s</session_duration>
    <tool_calls_remaining>5</tool_calls_remaining>
    <token_budget_remaining>45000</token_budget_remaining>
  </environment>
  <warnings>
    - 上一次 payment_api 调用延迟 >3s，可能不稳定
  </warnings>
</status_bar>
```

### 为什么 Status Bar 有效

模型在上下文学习中的行为更接近"检索"而非"推理"——它擅长从已有内容中提取和遵守信息，但不擅长从散乱的历史消息中自行统计和推断状态。

Status Bar 把分散在历史中的状态信息 **显性化**，减少模型需要自己推断的工作量。

具体好处：

| 没有 Status Bar | 有 Status Bar |
| --- | --- |
| 模型需要从长历史中推断已完成哪些步骤 | 直接读取 task_plan 的 checkbox |
| 模型不知道还能调几次工具 | 直接看 tool_calls_remaining |
| 模型不知道当前时间 | 直接读 current_time |
| 模型可能重复已做过的事 | 已完成步骤有明确标记 |

### Status Bar 的风险

Status Bar 中的信息会被模型无条件信任。如果 Status Bar 写入了错误状态，模型会基于错误信息继续决策。

因此：

- Status Bar 只能从可靠的程序状态派生，不能从未验证的模型输出生成
- 更新 Status Bar 的逻辑必须有明确的触发条件和验证
- 不要把未确认的猜测写进 Status Bar

## 上下文的三个设计原则

### 原则 1：稳定内容在前，动态内容在后

```text
较稳定：System Prompt → Tool Schema → Skills Metadata → 固定约束
较动态：历史轨迹 → Status Bar → 检索结果 → 当前用户输入
```

好处：

- Provider 前缀缓存更容易命中（token 不白算）
- 模型注意力的位置偏差倾向于更关注开头和结尾的内容

### 原则 2：不在 Context 中重复信息

如果一条约束已经在 System Prompt 中声明过，不需要在每轮历史中重复。

如果一个工具的返回结果已经被提取到 State 中，历史中的原始结果可以压缩或删除。

重复信息不仅浪费 token，还可能在版本不一致时造成冲突。

### 原则 3：正确性优先于缓存

不能为了保持前缀稳定而保留过时信息。如果约束变了、权限变了、环境变了，必须更新 Context，即使这意味着缓存失效。

缓存是优化，不是约束。

## Context Engineering 的核心思维模式

回顾一下，Context Engineering 解决的核心问题是：

> 在有限的 token 预算内，让模型每一步都能看到当前决策所需的**最相关**信息。

这意味着需要同时管理：

- **信息供给**：什么时候注入什么（Skills 加载、RAG 检索、Status Bar 更新）
- **信息压缩**：什么时候删掉什么（窗口裁剪、摘要、归档）
- **信息质量**：注入的信息是否准确、相关、不矛盾

如果把 Agent 比作一个人在做决策，Context Engineering 就是"决定这个人每一步能看到哪些资料"。资料太少会做错决策，资料太多会找不到重点，资料有误会被误导。

## 和其他工程层次的关系

| 层次 | 关注点 | Context Engineering 的角色 |
| --- | --- | --- |
| Prompt Engineering | 单次调用的指令 | Context Engineering 的子集 |
| Harness Engineering | 工具、权限、验证 | Context Engineering 决定 Harness 送什么给模型 |
| Loop Engineering | 循环策略和退出 | Loop 的每一轮都需要 Context Engineering 组装输入 |
| Agent Infra | 运行时和持久化 | Infra 负责存储和恢复 Context 需要的数据 |

它们不是互斥的，而是同一个系统的不同观察角度。Context Engineering 贯穿所有层次——因为不管系统怎么设计，最终都要回到"这一轮模型看到什么"。

## 小结

Context Engineering 是 Agent 工程中从"写好 Prompt"到"设计信息系统"的跃升。

核心要点：

1. Context 由五部分组成：指令、工具定义、执行轨迹、动态元数据、检索内容
2. Prompt Engineering 是五个维度的系统化方法，不是"写一段话"
3. Agent Skills 三层架构解决"能力太多怎么加载"的问题
4. Status Bar 把执行状态显性化，减少模型需要推断的负担
5. 三个设计原则：稳定在前、不重复、正确性优先于缓存

如果你的 Agent 表现不稳定，很多时候不是模型不行，而是 Context 组织得不好——关键信息没送进去，或者垃圾信息太多。

## 参考资料

- 李博杰《深入理解 AI Agent：设计原理与工程实践》，[第二章：上下文工程](https://github.com/bojieli/ai-agent-book/blob/e3883f8cec222c31e59c646be96641120863027e/book/chapter2.md)，固定提交 `e3883f8c`。本文按本仓库基础教程定位重新组织结构和表述，聚焦方法论层面。
