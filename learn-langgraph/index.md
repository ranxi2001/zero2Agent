---
layout: default
title: learn-langgraph
description: 用 LangGraph 构建可维护的 Agent 系统
eyebrow: Module 02
---

# learn-langgraph

这一部分专注于如何把 Agent 系统真正搭起来。

和简单链式调用不同，LangGraph 更适合描述状态、节点、条件分支、循环和可恢复执行，这也是很多真实 Agent 系统需要的能力。

## 这部分的主线

- 用图结构描述 Agent 执行流
- 设计状态对象，而不是只传字符串
- 处理循环、错误恢复和中断重试
- 支持持久化和 human-in-the-loop

## 建议写作结构

1. 先给出最小 LangGraph 示例。
2. 再讲 `State`、`Node`、`Edge` 怎么设计。
3. 最后进入多节点协作和持久化。

## 后续可补充的文章

- [ ] LangGraph 最小示例
- [ ] 状态驱动开发
- [ ] 条件路由与循环
- [ ] Memory 与持久化
- [ ] 多 Agent 协作
