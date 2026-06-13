---
layout: default
title: final-project
description: 面试诊断 Agent 实战——从 PRD 到工程系统
eyebrow: Module 05
---

# Final Project：面试诊断 Agent

最终实战围绕一个高集成度的真实问题展开：

**面试诊断 Agent —— 上传面试录音或文字稿，自动诊断回答质量，输出结构化改进建议。**

## 为什么选这个方向

这个场景同时覆盖 Harness 工程的全部 10 层能力：

- **Tools**：STT 转写、知识库检索、内容分析、语音分析
- **Skills**：文字稿诊断、录音诊断、模拟面试、单题对标
- **Query Engine**：多模型路由、流式输出、缓存、重试
- **Context**：长面试稿的分段压缩、按需加载参考答案
- **Memory**：用户画像、弱点追踪、进步趋势
- **Permission**：面试内容隐私保护、敏感操作确认
- **Sessions**：长诊断任务的中断恢复、状态回滚
- **Command**：确定性操作入口（/diagnose, /mock, /report）
- **Hook**：权限检查、审计日志、上下文压缩、指标收集
- **Sub-agent**：内容/表达/语音多维度并行诊断

同时，知识库直接复用本项目 learn-agent-interview 模块的 384 道面试题——吃自己的狗粮。

## 文档目录

| 编号 | 文档 | 内容 |
|------|------|------|
| 01 | [PRD：产品需求文档](01-prd/index.html) | 产品定位、用户场景、10 层架构映射、技术选型、开发路线图 |
| 02 | [系统架构设计](02-architecture/index.html) | 模块划分、数据流、接口定义、手写 Harness 全貌 |
| 03 | [Query Engine 实现](03-query-engine/index.html) | 模型调用层：三 Provider + stream + retry + cache + 路由 |
| 04 | [Tools & Skills 实现](04-tools-skills/index.html) | 原子工具 + 任务级 Skill 编排 |
| 05 | [知识库构建](05-knowledge-base/index.html) | 385 题导入 + FTS5/embedding 双通道检索 |
| 06 | [Context & Memory](06-context-memory/index.html) | 5 层上下文管理 + 克制的跨会话记忆 |
| 07 | [Permission & Session](07-permission-session/index.html) | 权限分级 + 检查点恢复 + 审计日志 |
| 08 | [Hook & Command](08-hook-command/index.html) | 可插拔治理管线 + 14 个确定性命令 |
| 09 | [Sub-agent 编排](09-sub-agent/index.html) | Agent-as-Tool + 并发池 + 上下文隔离 |
| 10 | [STT 集成与语音分析](10-stt-speech/index.html) | Whisper/FunASR + 说话人分离 + 语音诊断 |
| 11 | [部署与演示](11-deploy-demo/index.html) | CLI 入口 + Demo 演示 + 三种部署方案 |
| 12 | [Web UI 交互设计](12-web-ui/index.html) | Next.js + SSE 流式 + 三大核心交互流程 |

## 开发顺序

按 Harness 工程的推荐迭代顺序：

1. Query Engine → 2. Tools → 3. Permission → 4. Context → 5. Sessions → 6. Skills → 7. Memory → 8. Hooks → 9. Command → 10. Sub-agent

先把单 Agent 做稳，再让它长出团队。
