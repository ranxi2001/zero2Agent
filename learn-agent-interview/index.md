---
layout: default
title: learn-agent-interview
description: Agent 岗位高频面试题拆解，按考察维度分类，对比新手答 vs 高手答
eyebrow: Module 09
---

# learn-agent-interview

这个模块不是八股文合集。面试题按**考察维度**分类，每道题对比“新手答”和“高手答”的深度差距——让你看到同一道题，答到什么层次才算过关。

题目来自真实面试场景（腾讯、字节等），但分类不按公司，按能力维度。同一个维度下的题目放在一起，方便你系统性地补齐某个方向的短板。

适合准备 Agent 相关岗位面试的读者，也适合想检验自己工程理解深度的从业者。

## 五大考察维度

- **架构选型**：ReAct vs Plan-and-Execute、ToT 线上化——面试官考的是“你能不能在真实约束下选对方案”
- **工具管理**：参数校验、百级工具路由——考的是“你有没有做过防御性编程和检索工程”
- **容错与鲁棒性**：超时处理、误操作防范——考的是“你有没有做过高可用系统”
- **记忆与上下文**：长对话不丢信息、模糊需求处理——考的是“你理不理解 Agent Memory 的多层次需求”
- **评估与全局观**：量化评估体系、落地最大挑战——考的是“你有没有运营线上系统的经验和方法论”

## 建议阅读顺序

1. [架构选型：ReAct、Plan-and-Execute 与 ToT 怎么选](01-architecture-design/index.html)
2. [工具管理：参数校验、工具路由与百级工具库](02-tool-management/index.html)
3. [容错与鲁棒性：超时、报错、误操作的工程化处理](03-fault-tolerance/index.html)
4. [记忆与上下文：长对话不丢信息的实战方案](04-memory-context/index.html)
5. [评估与全局观：怎么量化 Agent 好坏、落地最大挑战](05-eval-and-vision/index.html)
