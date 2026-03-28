---
layout: default
title: Claude Code
description: 从 30 行代码出发，手写一个能真正干活的 Coding Agent
---

# Claude Code

> *"One loop & Bash is all you need"*

这个模块做一件事：**从零手写一个 Agent，一层一层叠加机制，最终变成一个能处理真实任务的 Coding Agent。**

不调包，不用框架。每一章都是对上一章的一次有限扩展，代码始终可运行。

---

## 课程结构

12 节课，分两段：

**基础 Harness（s01–s06）**：搭出 Agent 的核心骨架

| 章节 | 机制 | 核心思路 |
|------|------|---------|
| s01 | Agent Loop | `while True` + stop_reason = 整个 Agent |
| s02 | Tool Use | dispatch map，加工具不改循环 |
| s03 | TodoWrite | 规划层，防止模型在长任务中迷路 |
| s04 | Subagent | 上下文隔离，子任务不污染主对话 |
| s05 | Skill Loading | 按需加载领域知识，节省 token |
| s06 | Context Compact | 三层压缩，换来无限会话长度 |

**高级系统（s07–s12）**：让 Agent 能处理真实工程任务

| 章节 | 机制 | 核心思路 |
|------|------|---------|
| s07 | Task System | 磁盘持久化 DAG，任务依赖和阻塞 |
| s08 | Background Tasks | 非阻塞工具执行，Agent 循环不卡住 |
| s09 | Agent Teams | 文件消息总线，多 Agent 协作 |
| s10 | Team Protocols | 请求-响应握手，结构化通信 |
| s11 | Autonomous Agents | 自组织团队，成员自己认领任务 |
| s12 | Worktree Isolation | 每个任务独立 Git worktree，并行不踩踏 |

---

## 设计哲学

**Agent 的复杂度应该随需求增长，而不是从一开始就引入。**

s01 是 30 行。每一节只加必要的机制，解决前一节暴露出来的具体问题。读完之后你会发现，所有的"框架"都是这些机制的不同组合。

参考仓库：[shareAI-lab/learn-claude-code](https://github.com/shareAI-lab/learn-claude-code)

---

## 章节列表

- [Agent Loop：一个循环就是一个 Agent](./01-agent-loop/index.html)
