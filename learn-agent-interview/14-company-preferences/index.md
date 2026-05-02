---
layout: default
title: 各公司面试偏好：按公司备战的高频题速查
description: 按公司分类的 Agent 面试高频考点分析与代表性问题速查，帮你针对目标公司定向备战
keywords: 腾讯Agent面试偏好,蚂蚁Agent面试重点,字节Agent面试特点,阿里Agent面试方向,快手Agent面试,淘宝闪购Agent面试,高德面试,百度Agent面试,bilibili面试,携程Agent面试,各公司面试对比,Agent面试公司分析
eyebrow: Agent 面试通关 / 14
---

# 各公司面试偏好：按公司备战的高频题速查

每家公司的 Agent 面试都有自己的“性格”——腾讯喜欢从 RAG 系统设计往下挖，蚂蚁全栈考察从 Prompt 到 AI Coding 测试，字节侧重记忆与上下文工程，淘宝闪购则专注 Human-in-the-Loop 和异常管控。

本文基于 245+ 道真实面试题的来源统计，帮你识别目标公司的考察重心，精准备战。

---

## 总览：各公司考察维度热力图

| 公司 | 题量 | 最高频维度 | 考察风格 |
|------|------|-----------|---------|
| **腾讯** | 51 | RAG(16) > 评估(8) > 工程(6) | 系统设计能力，从架构到细节逐层追问 |
| **蚂蚁集团** | 48 | 工具(7) > 容错(6) > RAG(6) | 全栈工程考察，AI Coding 实操 |
| **字节跳动** | 31 | 记忆(7) > 架构/Prompt/RAG(各4) | 项目深挖 + 工程踩坑经验 |
| **阿里-淘天** | 26 | 记忆(6) > RAG(4) > 架构(3) | 系统设计 + 理论深度，追问细节 |
| **快手** | 18 | 训练(6) > RAG(5) | 算法基础扎实，工程+模型并重 |
| **淘宝闪购** | 17 | 项目拷打(12) > 架构(2) | 几乎全程项目深挖，无八股 |
| **阿里国际** | 13 | 训练(7) > 评估(2) | RL/微调深度，模型层能力 |
| **高德** | 12 | RAG(4) > 记忆(3) | 实习题为主，MCP 协议+会话记忆 |
| **携程** | 5 | RAG(5) | RAG 基础，适合入门准备 |
| **bilibili** | 4 | 分散 | Agent 框架实战，项目驱动 |
| **百度** | 4 | 工程(3) | 前后端全栈，SSE/缓存等工程题 |

---

## 腾讯（51 题）

**面试风格**：腾讯 Agent 面试覆盖面最广，从终面到一面、从 AI 应用开发到通用 Agent 岗，都有大量真题。特点是**系统设计能力**考察突出——不只问“是什么”，更问“怎么设计”“为什么这么选”。RAG 方向出题量远超其他公司。

**高频考察维度**：

| 维度 | 题量 | 代表性问题 |
|------|------|-----------|
| [RAG 与检索](../09-rag-retrieval/index.html) | 16 | Embedding/ReRank 微调、双路召回 TopK 确定、GraphRAG 三元组抽取、PDF Layout 解析 |
| [评估与全局观](../05-eval-and-vision/index.html) | 8 | 量化评估除准确率外还看什么、线上最难监控的指标、Agent 端到端成功率量化 |
| [工程化踩坑](../07-engineering-pitfalls/index.html) | 6 | Demo 惊艳上线不稳定的原因、AI Coding 实践、Code Agent 优缺点 |
| [记忆与上下文](../04-memory-context/index.html) | 5 | 长上下文不丢信息、模糊需求处理、三类上下文优先级 |
| [架构选型](../01-architecture-design/index.html) | 4 | ReAct vs Plan-Execute（终面）、ToT 线上化成本、路径震荡防范 |
| [工具管理](../02-tool-management/index.html) | 4 | 参数校验、百级工具路由、多工具调度 |

**备考重点**：
- RAG 全链路是必考——从 chunk 设计到 Embedding 选型到 ReRank 微调，准备要深
- 评估体系设计是高频追问——不只说“准确率”，要能设计完整评测方案
- 终面偏架构选型，一二面偏工程实践

---

## 蚂蚁集团（48 题）

**面试风格**：蚂蚁的 Agent 面试**覆盖维度最全面**（横跨 11 个维度），且是唯一大量考察 AI Coding 测试（代码插桩、覆盖率）的公司。Prompt 工程和 Skills 机制也是蚂蚁特色题。面试分多个团队（智能体平台、AI Coding、AI 应用开发），侧重点略有不同。

**高频考察维度**：

| 维度 | 题量 | 代表性问题 |
|------|------|-----------|
| [工具管理](../02-tool-management/index.html) | 7 | MCP Server 构建、Skill vs MCP 区别、参数幻觉修正、工具 token 优化 |
| [容错与鲁棒性](../03-fault-tolerance/index.html) | 6 | 幻觉治理手段、安全权限管理、Human-in-the-Loop、Self-Reflection |
| [RAG 与检索](../09-rag-retrieval/index.html) | 6 | 文档召回率提升、向量 vs 关键词检索、GraphRAG 应用 |
| [架构选型](../01-architecture-design/index.html) | 5 | Skill/MCP/Rule 区别、微服务接入 Agent、ReAct 原理 |
| [Prompt 工程](../08-prompt-engineering/index.html) | 4 | Skills 原理、Claude Code 创新设计、好/差 Prompt 区别 |
| [AI 代码测试](../11-ai-code-testing/index.html) | 4 | 分支覆盖率插桩、前置分析、代码过滤策略 |
| [记忆与上下文](../04-memory-context/index.html) | 4 | 上下文工程、Prompt Caching、长期记忆设计 |

**备考重点**：
- **蚂蚁特色题**：Skills 机制、SDD（Skill Driven Development）、AI Coding 测试——其他公司几乎不考
- 工具管理和容错是蚂蚁高频区，准备 MCP 协议细节和安全权限设计
- 如果面的是 AI Coding 方向，11-ai-code-testing 维度必看

---

## 字节跳动（31 题）

**面试风格**：字节（含抖音基础架构）的 Agent 面试**最重视记忆与上下文工程**，出题量是所有公司中最高的。同时 Prompt 工程方向出题多——Skills 系统设计、MCP vs Skills 区别是字节高频题。面试风格偏向项目深挖+工程踩坑。

**高频考察维度**：

| 维度 | 题量 | 代表性问题 |
|------|------|-----------|
| [记忆与上下文](../04-memory-context/index.html) | 7 | 对话太长怎么办、上下文污染防治、长短期记忆、Claude Code 记忆架构 |
| [架构选型](../01-architecture-design/index.html) | 4 | Agent 学术组成、设计范式、模型 vs Agent 区别 |
| [Prompt 工程](../08-prompt-engineering/index.html) | 4 | 提示词模板构建、Skill 系统设计、LobeChat 插件 vs Skills |
| [RAG 与检索](../09-rag-retrieval/index.html) | 4 | 查询改写、并行意图识别、Claude Code 为什么不用 RAG |
| [工程化踩坑](../07-engineering-pitfalls/index.html) | 4 | 成本控制、API 延迟、开发流程、AI Coding 检查效率 |

**备考重点**：
- 上下文工程是字节核心考点——准备好滑动窗口、摘要压缩、上下文污染防治的完整方案
- Prompt 工程和 Skills 机制是字节特色——需要理解 Skills 的三层本质（模板→知识封装→能力树）
- 字节喜欢问“为什么”和“踩过什么坑”，准备具体案例比背八股更有效

---

## 阿里-淘天（26 题）

**面试风格**：淘天的 Agent 面试**理论深度要求高**，喜欢追问底层原理（Attention 稀释、平方复杂度工程影响），同时系统设计题偏大——“设计一个智能导购助手”这类综合题是淘天特色。追问细节很深。

**高频考察维度**：

| 维度 | 题量 | 代表性问题 |
|------|------|-----------|
| [记忆与上下文](../04-memory-context/index.html) | 6 | 极度模糊表达处理、主动澄清 vs 历史推断、摘要丢细节怎么办 |
| [RAG 与检索](../09-rag-retrieval/index.html) | 4 | 查询改写提升精准度原理、BM25+RRF 调优、召回不准排查 |
| [架构选型](../01-architecture-design/index.html) | 3 | 逻辑塌缩纠正、分布式智能导购架构、CoT vs ReAct |
| [工具管理](../02-tool-management/index.html) | 3 | 100+工具召回偏差、外部数据格式自动映射、跨协议工具注册 |
| [容错与鲁棒性](../03-fault-tolerance/index.html) | 3 | 思维死循环检测、RAG 不能彻底解决幻觉、全链路降幻觉 |

**备考重点**：
- 准备好“设计一个XX Agent”的系统设计题——淘天喜欢出综合架构题
- 理论深度要求高——Attention 机制、Token 稀释等底层原理要能讲清楚
- 记忆与上下文是淘天高频——模糊需求处理、摘要压缩是必考点

---

## 快手（18 题）

**面试风格**：快手面试**模型层和工程基础并重**。训练与模型方向出题量高（RLHF、GRPO、SFT 选型），同时 RAG 全链路也是重点。工程基础题（布隆过滤器、索引失效、分布式限流）比其他公司多。

**高频考察维度**：

| 维度 | 题量 | 代表性问题 |
|------|------|-----------|
| [训练与模型](../10-training-and-data/index.html) | 6 | RLHF 奖励模型训练、SFT vs 蒸馏 vs GRPO 选型、GRPO Loss 函数 |
| [RAG 与检索](../09-rag-retrieval/index.html) | 5 | 父子索引、BM25+向量组合、Rerank TopK 截断、端到端性能优化 |
| [容错与鲁棒性](../03-fault-tolerance/index.html) | 2 | Prompt 注入防御、工具调用安全控制 |
| [工程化踩坑](../07-engineering-pitfalls/index.html) | 2 | 布隆过滤器、数据库索引失效 |

**备考重点**：
- **快手特色**：RLHF/GRPO 训练细节是必考——奖励函数设计、全0/全1 reward 处理、SFT 不够时什么时候上 RL
- RAG 全链路要熟——从父子索引到 BM25 到 Rerank 截断，每一步都可能追问
- 准备传统工程基础题——布隆过滤器、分布式限流、数据库索引，快手比其他公司更重视这些

---

## 淘宝闪购（17 题）

**面试风格**：淘宝闪购是**项目拷打最极致**的公司——全程围绕 Agent 工程经验展开，几乎无纯八股。面试官拿着简历从框架选型到线上效果一层一层挖。特别关注**安全管控**（Human-in-the-Loop、权限控制、异常管控）。

**高频考察维度**：

| 维度 | 题量 | 代表性问题 |
|------|------|-----------|
| [简历项目拷打](../13-project-deep-dive/index.html) | 12 | 框架选型 trade-off、意图识别实现、知识库构建、分块策略、工具调用正确率 |
| [架构选型](../01-architecture-design/index.html) | 2 | Agent 设计范式、LangChain vs LangGraph |
| [容错与鲁棒性](../03-fault-tolerance/index.html) | 2 | Human-in-the-Loop 流程、高风险异常管控 |

**备考重点**：
- **核心策略**：准备好你的 Agent 项目，能从头讲到尾，每个技术选型说得出 trade-off
- Human-in-the-Loop 和异常管控是淘宝闪购必考——操作分级、熔断机制、审计日志都要准备
- 面试官会追问“为什么这么做”——每个决策准备好 trade-off 表述比准备“最优答案”更重要
- 坦诚讲系统不足比吹牛更加分——“你的 Agent 还有哪些没优化的”几乎必问

---

## 阿里国际（13 题）

**面试风格**：阿里国际面试**最侧重模型训练与优化**——微调方法、RL 训练、推理加速是核心。评估体系也是重点。整体偏算法研发，对模型层理解要求高。

**高频考察维度**：

| 维度 | 题量 | 代表性问题 |
|------|------|-----------|
| [训练与模型](../10-training-and-data/index.html) | 7 | LoRA vs 全参微调、PPO vs GRPO、推理加速、SFT+蒸馏+GRPO 选型 |
| [评估与全局观](../05-eval-and-vision/index.html) | 2 | 评测体系构建、调优 case + 评测集构建 |
| [RAG 与检索](../09-rag-retrieval/index.html) | 2 | 向量数据库选型、Embedding 升级一致性 |

**备考重点**：
- 训练三件套必背：LoRA 原理与适用场景、PPO vs DPO vs GRPO 对比、SFT 什么时候不够
- 推理加速技术要熟——算子融合、KV Cache、量化部署
- 如果面的是应用开发方向，RAG 和评估也要准备

---

## 高德（12 题）

**面试风格**：高德面试以**实习岗**为主，题目侧重工程实现细节——MCP 协议完整调用过程、会话记忆具体实现、滑动窗口设几轮。适合实习生备战。

**高频考察维度**：

| 维度 | 题量 | 代表性问题 |
|------|------|-----------|
| [RAG 与检索](../09-rag-retrieval/index.html) | 4 | BM25+向量多路检索、Embedding 模型选型、知识库整体设计、分块策略 |
| [记忆与上下文](../04-memory-context/index.html) | 3 | 会话记忆实现（滑动窗口+摘要压缩）、话题切换记忆设计 |
| [工具管理](../02-tool-management/index.html) | 2 | MCP 协议完整调用过程、意图到工具参数的映射 |
| [Prompt 工程](../08-prompt-engineering/index.html) | 2 | Skills 本质理解、Claude Code 源码设计哲学 |

**备考重点**：
- MCP 协议从 Host→Client→Server 的完整链路是高德特色题
- 会话记忆的**具体实现**要准备——不只说“用滑动窗口”，要说清楚窗口设几轮、摘要怎么触发
- Prompt 工程追问较深——Skills 的三层理解（模板→知识封装→能力树）要能讲清

---

## 携程（5 题）

**面试风格**：携程实习面试**聚焦 RAG 基础**，题目相对入门。适合刚开始准备 Agent 面试的同学练手。

**代表性问题**：
- 如何向非技术人员解释 RAG？
- RAG 检索到文档很多但回答质量差，怎么排查？
- 什么是余弦相似度？在 RAG 中做什么？
- 什么是嵌入（Embedding）？为什么需要向量化？

**备考重点**：RAG 基础概念要能“用人话讲清楚”——面试官可能考察你解释技术概念的能力。

---

## bilibili（4 题）

**面试风格**：B 站 AI 研发实习面试**项目驱动**，围绕科研辅助 Agent 设计展开，也会考 subagent 拆分和 LangGraph 实战。

**代表性问题**：
- 如果设计一个科研辅助 Agent，整体流程怎么设计？
- 什么时候该用 subagent？主 Agent 和子 Agent 共用上下文吗？
- LangGraph 开发中遇到最大的困难？
- Deep Research 和普通 RAG 的区别？

**备考重点**：准备一个“设计XX Agent”的完整方案——感知、规划、记忆、执行四模块。

---

## 百度（4 题）

**面试风格**：百度实习面试偏**工程化**——多 Agent 编排、前端 SSE 处理、资源缓存等实际开发问题。

**代表性问题**：
- 多 Agent 怎么编排？用的什么编排模式？
- AI 应用的前端资源缓存怎么配的？
- AI 应用中 SSE 流式数据怎么处理？数据格式是什么？

**备考重点**：前后端全栈能力，SSE 流式处理和缓存策略要能讲实现细节。

---

## 备战策略总结

**通用高频维度**（所有公司都考）：
1. **RAG 与检索**——几乎每家都问，从 chunk 到 Embedding 到 Rerank
2. **架构选型**——ReAct vs Plan-Execute、Agent 设计范式
3. **记忆与上下文**——长对话、摘要压缩、模糊需求

**公司特色维度**（针对性准备）：
- 面蚂蚁 → 额外准备 [Prompt 工程](../08-prompt-engineering/index.html) + [AI 代码测试](../11-ai-code-testing/index.html)
- 面快手/阿里国际 → 额外准备 [训练与模型](../10-training-and-data/index.html)（RLHF/GRPO）
- 面淘宝闪购 → 额外准备 [项目拷打](../13-project-deep-dive/index.html) + [容错](../03-fault-tolerance/index.html)（HiL、异常管控）
- 面腾讯 → 额外准备 [RAG 与检索](../09-rag-retrieval/index.html)（深度，不止基础）
- 面字节 → 额外准备 [Prompt 工程](../08-prompt-engineering/index.html)（Skills 系统设计）
