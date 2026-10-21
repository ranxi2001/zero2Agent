---
layout: default
title: 各公司面试偏好：按公司备战的高频题速查
description: 按公司分类的 Agent 面试高频考点分析与代表性问题速查，帮你针对目标公司定向备战
keywords: 腾讯Agent面试偏好,蚂蚁Agent面试重点,字节Agent面试特点,阿里Agent面试方向,快手Agent面试,淘宝闪购Agent面试,高德面试,百度Agent面试,bilibili面试,携程Agent面试,各公司面试对比,Agent面试公司分析
eyebrow: Agent 面试通关 / 14
---

# 各公司面试偏好：按公司备战的高频题速查

准备目标公司面试时，可以先看该公司在当前题库里覆盖了哪些维度，再回到具体题目练习机制、失败模式和方案取舍。以下统计更新于 **2026-10-22**，从当前 **844 道题**的来源标注派生。

## 统计口径

每家公司对同一道核心题最多计一次；同一题被多家公司问到时，可以分别出现在各公司的覆盖数中，因此各行不能相加当作题库总数。统计只识别来源标签中的公司名称或下述别名，不根据答案内容、URL 或相似岗位推断公司；没有明确公司标签的来源不归类。

字节口径包含抖音、TikTok；蚂蚁包含 CodeFuse；腾讯包含明确的 WXG、TEG、CSIG 标签。阿里与淘天、阿里国际、淘宝闪购分别统计；来源过于笼统时保留其原标注，不强行分配业务线。

这些数字表示**当前题库的样本覆盖**，不代表某公司的全部题目、招聘偏好或实际出题概率。岗位、团队和轮次不同，考察重点也会变化；优先结合自己投递岗位的要求使用。

## 公司与维度覆盖

| 公司 | 覆盖题数 | 来源标注最多的三个维度 |
|------|---------|--------------------------|
| 字节跳动 | 333 | 训练、数据与模型优化（47）、RAG 与检索系统（44）、工程化踩坑（33） |
| 阿里与淘天（不含国际、闪购） | 186 | 训练、数据与模型优化（31）、RAG 与检索系统（28）、记忆与上下文（21） |
| 腾讯 | 120 | 训练、数据与模型优化（20）、RAG 与检索系统（18）、评估与全局观（14） |
| 小红书 | 116 | 训练、数据与模型优化（18）、工程化踩坑（16）、记忆与上下文（12） |
| 美团 | 103 | RAG 与检索系统（12）、架构选型（9）、记忆与上下文（9） |
| 百度 | 99 | 工程化踩坑（11）、训练、数据与模型优化（11）、工具管理（9） |
| 快手 | 95 | 工程化踩坑（13）、架构选型（8）、RAG 与检索系统（8） |
| 蚂蚁集团 | 63 | 架构选型（9）、评估与全局观（7）、概念考察（7） |
| 拼多多 | 56 | AI Infra（9）、记忆与上下文（7）、训练、数据与模型优化（7） |
| 携程 | 47 | 记忆与上下文（9）、RAG 与检索系统（9）、评估与全局观（6） |
| 淘宝闪购 | 26 | 简历项目拷打（14）、容错与鲁棒性（3）、架构选型（2） |
| 阿里国际 | 22 | 训练、数据与模型优化（5）、架构选型（3）、AI Infra（3） |
| 网易 | 19 | 业务 AI 工程分析（5）、AI 代码分析与测试（3）、记忆与上下文（2） |
| 高德 | 9 | 记忆与上下文（3）、RAG 与检索系统（3）、工具管理（2） |
| 京东 | 7 | RAG 与检索系统（2）、容错与鲁棒性（1）、记忆与上下文（1） |
| bilibili | 4 | 架构选型（1）、工程化踩坑（1）、RAG 与检索系统（1） |

## 按公司选择练习入口

### 字节跳动（333 题）

可先练：[训练、数据与模型优化](../10-training-and-data/index.html)、[RAG 与检索系统](../09-rag-retrieval/index.html)、[工程化踩坑](../07-engineering-pitfalls/index.html)。

代表性问题：

- [预训练数据清洗方法？](../10-training-and-data/index.html)
- [RAG 的检索如何实现？](../09-rag-retrieval/index.html)
- [如何评审 AI 生成的技术方案并进行重点提炼与技术取舍？](../07-engineering-pitfalls/index.html)

### 阿里与淘天（不含国际、闪购）（186 题）

可先练：[训练、数据与模型优化](../10-training-and-data/index.html)、[RAG 与检索系统](../09-rag-retrieval/index.html)、[记忆与上下文](../04-memory-context/index.html)。

代表性问题：

- [预训练数据清洗方法？](../10-training-and-data/index.html)
- [RAG 的检索如何实现？](../09-rag-retrieval/index.html)
- [上下文窗口不够用，对话太长了怎么办？](../04-memory-context/index.html)

### 腾讯（120 题）

可先练：[训练、数据与模型优化](../10-training-and-data/index.html)、[RAG 与检索系统](../09-rag-retrieval/index.html)、[评估与全局观](../05-eval-and-vision/index.html)。

代表性问题：

- [构造数据集遇到过什么难点，怎么解决？](../10-training-and-data/index.html)
- [如果 RAG 召回了很多相互矛盾的文档，Agent 应该怎么处理，而不是直接让模型自己总结？](../09-rag-retrieval/index.html)
- [如何量化评估一个上线的 Agent 好坏？除了准确率。](../05-eval-and-vision/index.html)

### 小红书（116 题）

可先练：[训练、数据与模型优化](../10-training-and-data/index.html)、[工程化踩坑](../07-engineering-pitfalls/index.html)、[记忆与上下文](../04-memory-context/index.html)。

代表性问题：

- [自动标注系统的主要难点是什么？如何设计模型预标注、置信度分流和人工复核闭环？](../10-training-and-data/index.html)
- [Agent 的成本怎么控制？线上烧钱太快怎么办？](../07-engineering-pitfalls/index.html)
- [上下文窗口不够用，对话太长了怎么办？](../04-memory-context/index.html)

### 美团（103 题）

可先练：[RAG 与检索系统](../09-rag-retrieval/index.html)、[架构选型](../01-architecture-design/index.html)、[记忆与上下文](../04-memory-context/index.html)。

代表性问题：

- [多维度的查询改写是什么？改写遇到需要用户补充信息时怎么设计？](../09-rag-retrieval/index.html)
- [你用 ReAct 还是 Plan-and-Execute？为什么？](../01-architecture-design/index.html)
- [讲一下 Agent 中的“长短期记忆”](../04-memory-context/index.html)

### 百度（99 题）

可先练：[工程化踩坑](../07-engineering-pitfalls/index.html)、[训练、数据与模型优化](../10-training-and-data/index.html)、[工具管理](../02-tool-management/index.html)。

代表性问题：

- [Agent 的成本怎么控制？线上烧钱太快怎么办？](../07-engineering-pitfalls/index.html)
- [自动标注系统的主要难点是什么？如何设计模型预标注、置信度分流和人工复核闭环？](../10-training-and-data/index.html)
- [你们工具库有上百个工具，怎么让模型快速选对？](../02-tool-management/index.html)

### 快手（95 题）

可先练：[工程化踩坑](../07-engineering-pitfalls/index.html)、[架构选型](../01-architecture-design/index.html)、[RAG 与检索系统](../09-rag-retrieval/index.html)。

代表性问题：

- [Agent 的成本怎么控制？线上烧钱太快怎么办？](../07-engineering-pitfalls/index.html)
- [你用 ReAct 还是 Plan-and-Execute？为什么？](../01-architecture-design/index.html)
- [为什么在检索阶段引入BM25？它和向量检索怎样组合？](../09-rag-retrieval/index.html)

### 蚂蚁集团（63 题）

可先练：[架构选型](../01-architecture-design/index.html)、[评估与全局观](../05-eval-and-vision/index.html)、[概念考察](../15-agent-concepts/index.html)。

代表性问题：

- [你用 ReAct 还是 Plan-and-Execute？为什么？](../01-architecture-design/index.html)
- [你会怎么给 Agent 建立评测体系？只看最终成功率为什么不够？](../05-eval-and-vision/index.html)
- [讲一讲 Agent 的发展路线——从以前的架构到现在的 Harness Engineering](../15-agent-concepts/index.html)

### 拼多多（56 题）

可先练：[AI Infra](../17-ai-infra/index.html)、[记忆与上下文](../04-memory-context/index.html)、[训练、数据与模型优化](../10-training-and-data/index.html)。

代表性问题：

- [如何用 Roofline 和算术强度指导 CUDA 算子优化？从 GEMM 分块到寄存器压力如何逐层定位？](../17-ai-infra/index.html)
- [上下文窗口不够用，对话太长了怎么办？](../04-memory-context/index.html)
- [位置编码的作用是什么？](../10-training-and-data/index.html)

### 携程（47 题）

可先练：[记忆与上下文](../04-memory-context/index.html)、[RAG 与检索系统](../09-rag-retrieval/index.html)、[评估与全局观](../05-eval-and-vision/index.html)。

代表性问题：

- [讲一下 Agent 中的“长短期记忆”](../04-memory-context/index.html)
- [RAG 的检索如何实现？](../09-rag-retrieval/index.html)
- [你会怎么给 Agent 建立评测体系？只看最终成功率为什么不够？](../05-eval-and-vision/index.html)

### 淘宝闪购（26 题）

可先练：[简历项目拷打](../13-project-deep-dive/index.html)、[容错与鲁棒性](../03-fault-tolerance/index.html)、[架构选型](../01-architecture-design/index.html)。

代表性问题：

- [你的 Agent 项目用了什么框架？为什么选它？](../13-project-deep-dive/index.html)
- [Agent 如何减少幻觉？在工业场景下怎么做？](../03-fault-tolerance/index.html)
- [了解过 Agent 的设计范式吗？](../01-architecture-design/index.html)

### 阿里国际（22 题）

可先练：[训练、数据与模型优化](../10-training-and-data/index.html)、[架构选型](../01-architecture-design/index.html)、[AI Infra](../17-ai-infra/index.html)。

代表性问题：

- [DPO、PPO、GRPO 的区别和优缺点？](../10-training-and-data/index.html)
- [如果模型特别擅长生成，但不擅长严格遵守流程，你会怎么把它放进一个强约束工作流里？](../01-architecture-design/index.html)
- [FlashAttention 为什么更快？Online Softmax、Tiling、重计算和不同版本分别解决什么瓶颈？](../17-ai-infra/index.html)

### 网易（19 题）

可先练：[业务 AI 工程分析](../12-business-ai-engineering/index.html)、[AI 代码分析与测试](../11-ai-code-testing/index.html)、[记忆与上下文](../04-memory-context/index.html)。

代表性问题：

- [时间紧张，“快速上线规则方案”和“训练一个更智能的 AI 方案”之间怎么选？](../12-business-ai-engineering/index.html)
- [AI 生成的代码线下测试没问题，上线后出了问题怎么办？](../11-ai-code-testing/index.html)
- [讲一下 Agent 中的“长短期记忆”](../04-memory-context/index.html)

### 高德（9 题）

可先练：[记忆与上下文](../04-memory-context/index.html)、[RAG 与检索系统](../09-rag-retrieval/index.html)、[工具管理](../02-tool-management/index.html)。

代表性问题：

- [会话记忆具体是怎么实现的？滑动窗口设几轮？摘要压缩怎么触发？](../04-memory-context/index.html)
- [分块策略怎么设计？不同策略的优缺点？](../09-rag-retrieval/index.html)
- [MCP 协议的完整调用过程是怎样的？](../02-tool-management/index.html)

### 京东（7 题）

可先练：[RAG 与检索系统](../09-rag-retrieval/index.html)、[容错与鲁棒性](../03-fault-tolerance/index.html)、[记忆与上下文](../04-memory-context/index.html)。

代表性问题：

- [讲一下项目里召回的流程](../09-rag-retrieval/index.html)
- [金融系统不能让 Agent 真实操作（钱放出去就是大问题），怎么设计？](../03-fault-tolerance/index.html)
- [你的向量记忆库是如何更新用户画像的？](../04-memory-context/index.html)

### bilibili（4 题）

可先练：[架构选型](../01-architecture-design/index.html)、[工程化踩坑](../07-engineering-pitfalls/index.html)、[RAG 与检索系统](../09-rag-retrieval/index.html)。

代表性问题：

- [如果设计一个科研辅助 Agent，整体流程应该怎么设计？](../01-architecture-design/index.html)
- [使用 LangGraph 开发 Agent，遇到最大的困难是什么？](../07-engineering-pitfalls/index.html)
- [Deep Research 在代码层面是怎么实现的？和普通 RAG 有什么区别？](../09-rag-retrieval/index.html)

## 怎么用这张表

先用岗位要求确定能力范围，再选择上表中对应公司的练习入口。对每道代表题，依次练习技术机制、业务约束、失败恢复、验证方法和成本权衡；遇到简历项目追问时，用真实经历解释自己的选择。

表中的前三维只是样本量较多的入口，不能据此跳过其他基础能力。题目的具体来源和追问请查看对应维度正文；同一主题组的阅读顺序按可归因面经频次维护。
