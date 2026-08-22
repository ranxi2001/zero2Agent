---
layout: default
title: learn-agent-practice
description: 用 AI Coding Agent 完成第一个作品上线，到面试交付，再到稳定的工程工作流
eyebrow: Module 09
---

# learn-agent-practice

**从第一次打开 VS Code，到稳定使用 Agent 完成工程交付。**

Vibe Coding 降低了写代码的门槛，但真正的第一步不是背语法，而是理解项目文件夹、终端、运行环境和版本控制之间的关系。你需要知道 Agent 在哪个目录工作、修改了哪些文件，以及怎样把成果发布出去。

这个模块从零基础起步：先用 AI Coding Agent（Codex、Claude Code、Cursor 均可）完成一个 GitHub Pages 个人主页；再进入面试交付、日常开发中的 Context、Harness、Loop Engineering，以及 Harness 自适应演进。

主线不是“记住更多提示词”，而是逐步建立完整闭环：**打开正确的项目 → 在正确目录启动 Agent → 验证修改 → 用 Git 记录 → 发布和交付。**

这个模块面向的读者：

- 从未创建过项目，不清楚文件夹、终端、Git 和 GitHub 区别 → 从 01 开始
- 想用 AI Agent 完成第一个可公开访问作品的 Vibe Coding 用户 → 从 01 开始
- 面试中被要求做 AI Coding Demo，不知道怎么拿高分 → 直接看 02
- 已经在用 AI Coding 工具，但产出质量不稳定、时好时坏 → 重点看 03
- 想建立一套可复用的 Agent 使用方法论，而不是每次碰运气 → 重点看 03
- 想让 Prompt、工具与工作流从失败轨迹中持续改进，同时守住评估和安全边界 → 重点看 04
- 想用可测量的评估信号驱动 Agent 工作流改进，而不是凭感觉调 Prompt → 重点看 05

## 这部分的主线

**01 — 建立完整闭环：**

- VS Code、项目文件夹、文件树和集成终端是什么关系
- Python、Node.js、Git、GitHub 和 GitHub Pages 分别解决什么问题
- 如何在项目目录启动 Agent，并理解默认权限与安全边界
- 如何让 Agent 创建、预览并发布一个个人主页

**02 — 面试场景交付：**

- 面试场景下的 AI Coding 怎么拿高分
- 限时压力下的需求拆解、方案决策和验收策略

**03 — 日常稳定提效：**

- 日常开发中如何让 Agent 真正提效而不是添乱
- 不同工具的适用场景和切换策略
- Context / Harness / Loop Engineering 的落地实践

**04 — Auto Harness 迭代：**

- 区分运行时适配、Harness Engineering 与真正的 Auto Harness
- 从重复失败中生成可证伪的最小 Harness Diff
- 比较新旧版本，并逐步开放 Prompt、Skill、工具和控制流的迭代

**05 — Eval 驱动迭代：**

- 用可测量的评估信号替代"感觉更好了"
- Promptfoo / Braintrust / LangSmith 各自解决什么问题和代价
- Prompt 回归测试接入 CI/CD 的最小路径
- 何时不该依赖 Eval 自动化

## 建议阅读顺序

1. [从 0 开始 Vibe Coding：用 AI Agent 发布个人主页](./01-vibe-coding-homepage/index.html)
2. [AI Coding 面试：解题流程与交付策略](./02-ai-coding-interview/index.html)
3. [日常开发中的 Agent 工作流：从 Context 到 Loop 的实战方法论](./03-daily-dev-workflow/index.html)
4. [Auto Harness 实战：从失败轨迹迭代 Agent 运行骨架](./04-auto-harness/index.html)
5. [Eval-Driven Agent Practice：用评估驱动 Agent 工作流迭代](./05-eval-driven-practice/index.html)
