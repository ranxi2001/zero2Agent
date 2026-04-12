---
layout: default
title: Agent 面试通关
description: Agent 岗位高频面试题拆解，按考察维度分类，对比新手答 vs 高手答
eyebrow: Module 09
---

# Agent 面试通关

这个模块不是八股文合集。面试题按**考察维度**分类，每道题对比“新手答”和“高手答”的深度差距——让你看到同一道题，答到什么层次才算过关。

题目来自真实面试场景（腾讯、阿里、抖音、字节等），按能力维度分类，方便你系统性地补齐某个方向的短板。

适合准备 Agent 相关岗位面试的读者，也适合想检验自己工程理解深度的从业者。

## 十一大考察维度

- **架构选型**：ReAct vs Plan-and-Execute、ToT 线上化、Agent 学术组成、四种设计范式
- **工具管理**：参数校验、百级工具路由、多工具调度、Mock 自动化生成
- **容错与鲁棒性**：超时处理、误操作防范、幻觉治理多层防线
- **记忆与上下文**：长对话不丢信息、模糊需求处理、上下文污染防治、长短期记忆分层、to-do list 机制
- **评估与全局观**：量化评估体系、落地最大挑战
- **多智能体协作**：角色分工、通信机制、冲突仲裁、子 Agent 拆分设计
- **工程化踩坑**：死循环、状态丢失、成本控制
- **Prompt 工程与框架原理**：提示词模板分层构建、Skills 可复用能力单元
- **RAG 与检索系统**：chunk 设计、查询改写、并行意图识别、多路召回精排
- **训练、数据与模型优化**：数据清洗、工具调用训练、LoRA vs 全参微调、DPO/PPO/GRPO、kernel 优化
- **AI 代码分析与测试**：覆盖率插桩原理、前置分析与有效性判断、代码过滤策略

## 建议阅读顺序

1. [架构选型：ReAct、Plan-and-Execute 与 ToT 怎么选](01-architecture-design/index.html)
2. [工具管理：参数校验、工具路由与百级工具库](02-tool-management/index.html)
3. [容错与鲁棒性：超时、报错、误操作的工程化处理](03-fault-tolerance/index.html)
4. [记忆与上下文：长对话不丢信息的实战方案](04-memory-context/index.html)
5. [评估与全局观：怎么量化 Agent 好坏、落地最大挑战](05-eval-and-vision/index.html)
6. [多智能体协作：角色分工、通信机制与冲突仲裁](06-multi-agent-collab/index.html)
7. [工程化踩坑：死循环、状态丢失与成本控制](07-engineering-pitfalls/index.html)
8. [Prompt 工程与框架原理：模板构建、Skills 机制](08-prompt-engineering/index.html)
9. [RAG 与检索系统：从 chunk 设计到多路召回](09-rag-retrieval/index.html)
10. [训练、数据与模型优化：从数据清洗到 LoRA](10-training-and-data/index.html)
11. [AI 代码分析与测试：覆盖率、插桩、代码过滤](11-ai-code-testing/index.html)
