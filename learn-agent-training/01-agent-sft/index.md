---
layout: default
title: Agent SFT 关键细节：从轨迹数据到 Loss Mask
description: Agent SFT 与对话 SFT 的本质区别、轨迹数据构造、Loss Mask 策略与数据配比经验
eyebrow: Agent 训练实战 / 01
---

# Agent SFT 关键细节：从轨迹数据到 Loss Mask

你可能已经会用 Agent 框架搭 Demo 了，但有没有想过一个问题：这些模型是怎么学会“做 Agent”的？

不是靠 prompt 硬塞规则，而是在训练阶段就让模型见过大量的 Agent 执行轨迹——调工具、读返回、思考、再调工具、最终回复。这就是 Agent SFT。它和普通对话 SFT 看起来都是“微调”，但数据形态、训练策略、loss 计算方式完全不同。

本篇整理自彭思达的 Agent SFT 学习笔记，覆盖四个关键问题：什么是 Agent SFT、怎么造数据、怎么训练、怎么和 RL 配合。

## Agent SFT vs 对话 SFT：区别在哪

对话 SFT 训练的是“一问一答”——用户说一句，模型回一句，一个回合就结束了。

Agent SFT 训练的是“执行一整条轨迹”——模型要完成多个回合的推理和工具调用，最终给出结果。一条训练样本的执行流程：

<div class="mermaid">
graph TD
    A["🔧 System Prompt<br/>你是一个天气助手，可以调用 get_weather 工具"] --> B["👤 User<br/>帮我查一下北京明天的天气<br/>如果下雨就提醒我带伞"]
    B --> C["💭 Think<br/>需要先调天气 API<br/>查询北京明天的天气..."]
    C --> D["⚡ Tool Call<br/>get_weather&#40;city=北京, date=tomorrow&#41;"]
    D --> E["📦 Tool Return<br/>&#123;weather: 小雨, temp: 12-18°C&#125;"]
    E --> F["💭 Think<br/>结果显示明天有小雨<br/>需要提醒用户带伞..."]
    F --> G["✅ Response<br/>北京明天小雨，12-18°C<br/>建议带伞出门"]

    style A fill:#1a2535,stroke:#334155,color:#94a3b8
    style B fill:#1a2535,stroke:#334155,color:#94a3b8
    style C fill:#1e293b,stroke:#f59e0b,color:#fbbf24
    style D fill:#022c22,stroke:#10b981,color:#34d399
    style E fill:#1a2535,stroke:#334155,color:#94a3b8
    style F fill:#1e293b,stroke:#f59e0b,color:#fbbf24
    style G fill:#022c22,stroke:#10b981,color:#34d399
</div>

> 绿色部分（Tool Call、Response）是 Loss Mask 中**需要计算 loss** 的核心目标，黄色部分（Think）视质量决定是否计算，灰色部分（System Prompt、User、Tool Return）**不计算 loss**。

核心区别：

| | 对话 SFT | Agent SFT |
|---|---|---|
| 训练目标 | 生成一个好回复 | 执行一整条正确的轨迹 |
| 数据粒度 | 单轮问答 | 多轮推理 + 工具调用 + 最终回复 |
| 涉及的 token 类型 | 用户输入 + 模型回复 | System Prompt / User / Think / Tool Call / Tool Return / Response |
| loss 计算 | 对模型回复算 loss | 需要精细控制哪些 token 算 loss（后面展开讲） |

## 怎么造 Agent 轨迹数据

Agent SFT 的数据不是简单的问答对，而是完整的执行轨迹。造这种数据有两条路：

**方式一：人工标注**

人类专家手动执行任务，记录每一步的思考、工具调用和结果。质量高但成本极高，适合构建种子数据集。

**方式二：强模型生成 + 人工筛选**

用 GPT-4、Claude 等强模型跑任务，自动生成轨迹数据，再由人工筛选和修正。这是目前更主流的做法——成本可控，规模上得去。

不管哪种方式，轨迹数据有两个容易忽略的注意点：

**注意点 1：必须包含“失败”动作的轨迹**

不能只给模型看“一路顺风”的轨迹。真实场景中工具会报错、返回空结果、参数填错——模型需要见过这些情况，才知道怎么处理。只用成功轨迹训练出来的 Agent，遇到失败就会陷入死循环或胡说。

**注意点 2：轨迹长度要适中**

轨迹太短，模型学不到复杂任务的处理流程。轨迹太长，训练效率低且容易引入噪声。一条好的轨迹应该是“刚好完成任务”，不多不少。如果一个任务天然需要很多步，考虑拆分成子任务分别训练。

## 关键训练技巧

### 基本训练流程

Agent SFT 的训练流程和标准语言模型微调一致，只是数据更长、结构更复杂：

```text
1. 把一整条轨迹拼接成 token 序列
2. 使用 Causal Mask（因果掩码）：模型预测第 N 个 token 时，只能看到前 N-1 个 token
3. 用 ground truth token 和模型预测的 token 计算 cross-entropy loss
4. 反向传播，更新模型参数
```

到这一步，和普通 SFT 没区别。关键差异在下一步——**Loss Mask**。

### Loss Mask：哪些 token 该算 loss

一条 Agent 轨迹里包含很多不同角色的内容。如果对所有 token 都算 loss，模型会花大量精力去“学习”如何生成 system prompt 和用户消息——这显然不是我们要的。

Loss Mask 的核心思想：**只对模型应该生成的部分计算 loss，屏蔽掉不需要学习的部分。**

具体来说，在 token level 做 mask：

| 轨迹部分 | 计算 Loss? | 原因 |
|---|---|---|
| System Prompt | 不算 | 模型不需要学生成这个 |
| User 消息 | 不算 | 同上 |
| `<think>` 部分 | 看情况 | 质量高就留，质量差就 mask |
| `<tool_call>` 部分 | **算** | 这是核心学习目标——学会正确调用工具 |
| Tool 返回结果 | 不算 | 这是环境返回的，不是模型生成的 |
| 最终回复 | **算** | 学习怎么根据工具结果总结输出 |

几个要点：

- **`<tool_call>` 是最核心的学习目标**。Agent 的本质能力就是“在正确的时机调用正确的工具、传正确的参数”。
- **`<think>` 部分要看质量**。如果你的轨迹数据里 think 部分写得很好（逻辑清晰、推理正确），保留它让模型学习思维链。如果质量参差不齐，建议 mask 掉，避免模型学到低质量的推理模式。
- **Tool 返回绝对不算 loss**。这部分是外部环境给的，模型不需要也不应该学习“生成工具返回值”。

### 训练数据配比：防止通用能力崩塌

这是 Agent SFT 中最容易踩的坑之一：**只用 Agent 轨迹数据训练，模型的通用能力会严重退化。**

原因很直觉——如果模型只见 Agent 轨迹，它会把所有问题都当成需要调工具的任务，连“你好”都想调个 API。

实践中的经验配比：

```text
Agent 轨迹数据          40-50%    ← 核心，但不能占太多
Tool Calling 单轮数据    15-20%    ← function calling 的基本功
通用指令跟随（Alpaca 类） 15-20%    ← 保持正常对话能力
长文本理解               5-10%    ← Agent 天然上下文很长，需要保持长文本能力
安全 / 拒绝              5-10%    ← Agent 能真的执行操作，安全比纯对话重要得多
```

为什么安全数据比例要比对话模型更高？因为 Agent 能真的执行操作——删文件、发请求、改数据库。一个对话模型说错话顶多尴尬，一个 Agent 执行错误操作是真会造成损失的。

## SFT 与 RL 的配合

Agent 训练通常分两个阶段：先 SFT，再 RL。两者的目标不同，配合方式也有讲究。

### 各自的目标

**Agent SFT 的目标：让模型先能跑起来。**

- 知道怎么调工具（格式对、参数对）
- 大致的推理流程走得通
- 输出格式没问题

SFT 不需要模型做出最优决策，只需要它“能完成任务”——就像教一个新员工先走通标准流程。

**Agent RL 的目标：提升决策质量。**

- 基于环境 Reward（任务是否完成、步骤是否高效）优化策略
- 让模型学会在多个可行路径中选最优的那条
- 提升鲁棒性，减少无效操作

### 配合的关键技巧

**技巧 1：SFT 阶段不要把完成率刷太高**

这是反直觉的——SFT 阶段如果把训练数据上的任务完成率刷到 95%+，RL 阶段就没什么探索空间了。模型已经“过拟合”到 SFT 的轨迹模式上，RL 很难再教它学到更好的策略。

经验做法：SFT 阶段让模型达到“能跑通大部分任务”就行（比如 70-80% 完成率），把提升空间留给 RL。

**技巧 2：SFT checkpoint 作为 RL 的 reference model**

RL 训练时，用 SFT 阶段的 checkpoint 做 KL 散度约束（reference model）。这样做的好处：

- 防止 RL 阶段策略偏太远，导致格式退化（比如不再输出合法的 tool call 格式）
- 保持 SFT 阶段学到的基本能力，在此基础上优化决策

```text
SFT 训练
  ↓
SFT Checkpoint ──→ 作为 RL 的 reference model（KL 约束）
  ↓
RL 训练（基于环境 Reward）
  ↓
最终 Agent 模型
```

## 小结

- Agent SFT 训练的是多轮执行轨迹，不是单轮问答——数据形态和 loss 计算方式都不同
- 轨迹数据要包含失败案例、长度适中；主流做法是强模型生成 + 人工筛选
- Loss Mask 是 Agent SFT 的核心技巧：只对 tool_call 和最终回复算 loss，屏蔽 system prompt、user 消息和 tool 返回
- 训练数据不能只放 Agent 轨迹，需要混入通用指令、安全数据等，防止能力崩塌
- SFT 和 RL 是两个阶段：SFT 让模型“能跑”，RL 让模型“跑得好”；SFT 不要刷太高完成率，给 RL 留探索空间

下一篇建议继续看：

- 本模块正在撰写中，后续将补充 Agent RL、训练数据配比实战、Agent 评测等内容
