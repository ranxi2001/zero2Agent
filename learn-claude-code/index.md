---
layout: default
title: learn-claude-code
description: 理解 Claude Code 这类 Code Agent 的系统机制
eyebrow: Module 03
---

# learn-claude-code

这一部分不打算停留在“怎么使用 Claude Code”，而是要理解它为什么能工作，以及它为什么经常在工程细节上表现得像一个系统，而不是一个聊天窗口。

## 重点内容

- 代码 Agent 的输入不是一句问题，而是一个仓库
- 上下文窗口只是约束之一，不是全部
- 文件系统、命令执行、补丁写入和反馈闭环共同构成执行系统
- 代码任务需要分解、验证和回退策略

## 建议写作结构

1. 先解释 Code Agent 与普通聊天 Agent 的区别。
2. 再拆解工具系统和执行循环。
3. 最后分析真实编码任务的失败模式。

## 后续可补充的文章

- [ ] Claude Code 的工作方式
- [ ] Code Agent 的上下文管理
- [ ] 工具系统与安全边界
- [ ] 命令执行和补丁生成
- [ ] 代码 Agent 的评估方式
