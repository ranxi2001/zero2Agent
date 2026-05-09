---
layout: default
title: 面试与实习准备
description: 基于 pi-mono/OpenClaw 源码级理解的面试策略
eyebrow: OpenClaw / 09
---

# 面试与实习准备

你读过了 pi-mono 源码，理解了 Agent Loop、Context Engine、MCP 协议、SubAgent 隔离。

这一节说怎么把这些变成面试竞争力——让面试官看出你不是调包侠。

---

## Agent 方向面试的三层考察

### 层 1：概念理解（筛选层）

考察你是否真正理解 Agent 本质，还是只会背定义。

| 问题 | 调包侠答法 | 源码级答法 |
|------|-----------|-----------|
| Agent 和 Chatbot 的区别 | "Agent 能调工具" | "Agent Loop 有内层循环——检测到 tool_calls 时继续执行工具并回调 LLM，而不是直接返回。本质是一个 while(hasToolCalls) 的循环" |
| 为什么 Agent 不稳定 | "因为 LLM 会幻觉" | "多轮工具调用是串行决策链，每步的输出影响下一步。上下文膨胀后早期信息被压缩/截断，导致后续决策失去依据" |
| Memory 怎么做 | "用向量数据库存对话" | "分三层：MEMORY.md 文件持久化关键信息（跨 Session），Context Engine 的 assemble() 在 token 预算内组装最优上下文，compact() 在接近上限时用 LLM 压缩早期对话" |

### 层 2：工程经验（核心层）

面试官会追问实现细节，判断你是读过源码还是只看了教程。

**Q：你的 Agent 用什么执行模型？**

> 源码级回答：EventStream 模式。Agent Loop 是一个 AsyncGenerator，流式发射结构化生命周期事件（agent_start → turn_start → message_update → tool_execution_start/end → turn_end → agent_end）。上层 UI 消费这个 EventStream 做渲染，实现了 Agent 逻辑和 UI 的完全解耦。

**Q：工具是串行还是并行执行的？**

> 源码级回答：默认并行。当 LLM 一次返回多个 tool_calls 时，用 Promise.all 并行执行所有工具。Coding Agent 的工具调用大多是 IO 密集（读文件、grep），互相无依赖，并行可以将延迟从 O(n) 降到 O(1)。只有配置了 sequentialTools 时才走串行路径。

**Q：上下文溢出怎么处理？**

> 源码级回答：Context Engine 有两个策略。第一是 compact()——对早期对话生成 LLM 摘要，用摘要替代原始消息，保留语义但大幅减少 token 占用。第二是 assemble() 的优先级裁剪——在固定 token budget 内，按优先级填充：系统指令 > 持久化记忆 > 压缩摘要 > 近期对话。预算不够时从低优先级裁剪。

**Q：MCP 协议解决什么问题？**

> 源码级回答：MCP 解决工具和 Agent 的耦合问题。工具可以是独立进程（Node.js、Python、Go），通过 JSON-RPC over stdio/HTTP 和 Agent 通信。好处：1) 语言无关；2) 进程隔离（工具崩溃不影响 Agent）；3) 社区可以独立开发和共享工具。代价是序列化开销和进程管理复杂度。

### 层 3：系统设计（高级层）

**Q：设计一个支持 10,000 文件代码库的 Coding Agent**

关键点：
- 不能把所有文件塞进上下文——用 Read 工具的 offset/limit 按需读取
- 文件发现用 grep/find 而不是全量遍历
- 大规模重构用 Worktree 隔离 + SubAgent 并行
- 项目结构理解用 AST 级别的代码索引（按需建立，不全量）

**Q：如何让 Agent 在多用户间安全隔离**

关键点：
- Session 级别隔离（每个用户独立 Context Engine 实例）
- 文件系统级别隔离（Docker 沙箱或 chroot）
- 工具权限隔离（不同用户可用不同工具子集）
- 秘钥隔离（用户的 API Key 只存在该用户的 Session 中）

---

## 项目经历怎么讲

### STAR 格式

```
Situation: 我需要一个能辅助日常编程的 Agent，主流框架太重且不可控
Task:      基于 pi-mono 架构改造一个个人 Coding Agent
Action:    Fork pi-mono，接入 DeepSeek/Claude，添加 MEMORY.md 持久化和
           Slack 接入，构建 15-case Eval 测试集
Result:    日常使用中任务完成率 82%，上下文压缩策略使单次会话可处理
           的工具调用轮次从 ~20 提升到 ~50
```

### 讲述重点

面试官想听的不是"我用了什么技术"，而是"我做了什么判断"：

1. **为什么不用 LangChain？** — 因为它的 AgentExecutor 内部做了太多隐式处理（输出解析、重试、回退），出了问题无法精确定位
2. **为什么选 EventStream 模式？** — 因为需要实时反馈（用户能看到 Agent 正在做什么），也需要可观测性（每个事件都是结构化日志）
3. **为什么用文件（MEMORY.md）存记忆而不是数据库？** — 因为人类可读可编辑、Git 可追踪、零依赖。只有记忆量超过几百条时才需要升级到 pgvector

---

## Eval：量化能力的加分项

面试中能说出 pass rate 数字的候选人非常少。这是显著的差异化点。

```typescript
// eval 示例
const results = {
  'read-and-explain': { pass: true, time: '3.2s' },
  'fix-simple-bug': { pass: true, time: '8.1s' },
  'refactor-function': { pass: true, time: '15.4s' },
  'multi-file-edit': { pass: false, time: 'timeout' },
  'write-test': { pass: true, time: '12.7s' },
}
// Pass rate: 4/5 = 80%
```

面试话术：

> "我建了一个 15-case 的 Eval 集，覆盖读取分析、单文件修改、多文件重构、测试编写四个维度。初始版本 pass rate 60%，优化了上下文压缩策略和工具结果截断后提升到 82%。主要失败 case 集中在多文件重构——上下文不够同时持有多个文件的完整内容，后续改用 SubAgent 并行处理解决了部分问题。"

---

## 简历描述模板

```
[YourName]Claw — 基于 pi-mono 架构的个人 Coding Agent
- 基于 pi-mono（TypeScript）架构实现 EventStream 驱动的 Agent Loop
- 接入 Anthropic / DeepSeek 双 Provider，支持配置切换
- 实现 MEMORY.md 跨 Session 持久化 + Context Engine 动态上下文组装
- 工具并行执行（Promise.all），支持 Read/Write/Edit/Bash/Grep 5 类核心工具
- 集成 Slack Bot，PM2 后台部署
- 构建 15-case Eval 集，任务完成率 82%
```

---

## 岗位方向

| 类型 | 代表公司 | 岗位 |
|------|---------|------|
| AI 原生 | Kimi、智谱、百川、MiniMax | LLM Application Engineer |
| 大厂 AI | 阿里通义、腾讯混元、字节豆包 | AI Engineer Intern |
| Coding Agent | Cursor 类产品、IDE 插件 | Agent Developer |
| 工具链 | DevTool 创业公司 | Full-Stack + AI |

---

## 进阶面试题（来自源码分析社区）

这些题目来自 OpenClaw-Internals、claude-code-vs-openclaw 等深度分析项目，是面试官可能追问的高级问题：

**Q：OpenClaw 的 Compaction 和 Claude Code 的 Compaction 有什么区别？**

> OpenClaw 做标识符保留（strict 模式下，文件路径、函数名、行号必须原样保留在摘要中）+ 质量检查点（压缩后验证关键信息是否丢失，不通过则重试）。Claude Code 用 LLM 直接摘要，没有验证步骤。这意味着 OpenClaw 压缩后 Agent 能继续精确操作，而 Claude Code 可能丢失具体位置信息。

**Q：OpenClaw 的 Dreaming 系统解决什么问题？**

> 解决记忆质量随时间退化的问题。三阶段（Light/Deep/REM）定时合成——扫描候选记忆、合并相似主题、跨主题关联。通过加权评分（relevance 0.30 + frequency 0.24 + ...）决定哪些记忆提升为长期存储，哪些退休。只有 grounded snippets（有证据支撑的）才能被提升——防止幻觉记忆。

**Q：为什么 OpenClaw 用文件锁做 per-session 串行化，而不是消息队列？**

> 文件锁是零依赖方案——不需要 Redis/RabbitMQ。OpenClaw 设计为个人助手（单用户），不是多租户平台，并发度低。文件锁在这个规模下延迟可忽略，但带来了简单性和可靠性。如果是多租户场景，才需要升级到消息队列。

**Q：SKILL.md 格式为什么能跨 Agent 通用？**

> 因为它本质是 Markdown + YAML frontmatter——人类可读、Agent 可解析、不依赖特定运行时。任何支持 system prompt 注入的 Agent 都能加载 SKILL.md。这是"写一次，多处运行"的设计——你为 pi-mono 写的 Skill，在 Claude Code 中也能直接用。

**Q：GBrain 为什么用"确定性操作优先于 LLM 判断"的原则？**

> LLM 调用有三个问题：1) 成本高（每次调用花钱）；2) 不确定性（同样输入可能不同输出）；3) 延迟高。GBrain 的实体抽取用正则，关系链接用模式匹配，知识图谱连边用共现分析——都是确定性的、免费的、毫秒级的。只在必须推理时（如 Compiled Truth 更新、冲突消解）才调用 LLM。生产系统追求的是可预测性，不是"全用 AI"。

---

## 准备清单

```
□ GitHub 有你的 pi-mono fork（能跑，有你的改动）
□ README 写清楚改动说明和架构图
□ 能流畅讲 Agent Loop 的 EventStream 模式（1 分钟内）
□ 能回答 "Context Engine 的 assemble/compact 怎么工作"
□ 能解释 "为什么不用 LangChain"（有判断依据，不是背的）
□ 有 Eval 数字（pass rate + 改进前后对比）
□ 能画出 pi-mono 的包结构和数据流图
```

---

## 最重要的一件事

**把 Agent 跑起来，用它做事。**

面试中被追问的任何细节——上下文溢出怎么办、工具出错怎么处理、多文件任务怎么拆——如果你真的日常使用过自己的 Agent，你会有真实的体感和判断。

这些体感是背不出来的。面试官一听就知道你是真用过还是只读了教程。

---

[← 返回 OpenClaw 模块首页](../index.html)
