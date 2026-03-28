---
layout: default
title: learn-frameworks
description: OpenAI Agents SDK、Google Gemini SDK、Claude Anthropic SDK——三大原厂 SDK 的核心用法与选型指南
eyebrow: Module 05
---

# learn-frameworks

这个模块不是 API 文档的复读，而是帮你建立**选型判断力**。

三大模型厂商（OpenAI、Google、Anthropic）各自提供了官方 SDK。它们的 API 设计哲学不同，适合的场景也不同。这个模块逐一讲清楚各 SDK 的核心模式，最后做横向对比。

## 这个模块覆盖什么

| # | 文章 | 核心内容 |
|---|------|---------|
| 01 | OpenAI Agents SDK | Agent 对象、Runner 执行、工具注册、Handoff 多 Agent |
| 02 | Google Gemini SDK | Function Calling、多模态、流式生成、安全设置 |
| 03 | Claude Anthropic SDK | Messages API、Tool Use、流式、视觉能力 |
| 04 | 三大 SDK 横向对比 | API 设计差异、Tool Calling 实现、选型建议 |

## 为什么要关注原厂 SDK

用 LangChain 这类封装框架，出问题时要翻三层抽象。原厂 SDK 的优势：

- **稳定**：跟着模型版本同步更新，不会因为 LangChain 版本不兼容踩坑
- **完整**：能用到最新功能（比如 OpenAI 的 Realtime API、Google 的 grounding）
- **轻量**：不引入额外依赖，适合生产环境
- **可读**：代码意图直接，出问题好排查

学会原厂 SDK，再用封装框架时也能理解底层在做什么。

## 前置知识

- 了解什么是 Tool Calling（参考 [Agent Basic - Tool Calling 入门](../learn-agent-basic/05-tool-calling-basics/index.html)）
- 会写基本 Python，了解 async/await 更佳
