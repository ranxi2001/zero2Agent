---
layout: default
title: learn-agent-training
description: Agent 场景下 SFT、RLHF 等训练技术的实战细节与经验总结
eyebrow: Module 08
---

# learn-agent-training

Agent 不只是 prompt + tool calling——当你需要让模型真正学会"做 Agent"，就得进入训练层面。这个模块聚焦 Agent 场景下的 SFT、RL 等训练技术，从数据构造到 Loss Mask 策略到上线配比，覆盖工程落地中最容易踩坑的细节。

适合已经理解 Agent 基本架构、想深入了解"如何训练一个 Agent 模型"的读者。

## 这部分的主线

- Agent SFT 和普通对话 SFT 的核心区别：轨迹数据 vs 单轮问答
- 轨迹数据构造：人工标注 vs 强模型生成 + 人工筛选
- 关键训练技巧：Causal Mask、Loss Mask 策略（哪些 token 该算 loss）
- SFT 与 RL 的配合：SFT 让模型"能跑起来"，RL 提升决策质量
- 训练数据配比经验：Agent 轨迹、Tool Calling、通用指令、长文本、安全数据的比例

## 建议阅读顺序

1. [Agent SFT 关键细节：从轨迹数据到 Loss Mask](01-agent-sft/index.html)
2. [Agent RL 实战：用强化学习提升推理与决策质量](02-agent-rl/index.html)
3. [GRPO vs PPO：Agent 强化学习算法深度对比与选型](03-grpo-vs-ppo/index.html)
4. [训练数据配比实战：Agent 不只吃轨迹数据](04-data-mix/index.html)
5. [Agent 评测：怎么衡量你训练出来的 Agent 到底行不行](05-agent-eval/index.html)
6. [从 SFT 到部署：Agent 模型上线全流程](06-train-to-deploy/index.html)

## 文章完成状态

- [x] Agent SFT 关键细节：从轨迹数据到 Loss Mask
- [x] Agent RL：基于环境 Reward 提升决策质量
- [x] GRPO vs PPO：Agent 强化学习算法深度对比与选型
- [x] 训练数据配比实战经验
- [x] Agent 评测：怎么衡量训练效果
- [x] 从 SFT 到部署：Agent 模型上线全流程
