---
layout: default
title: Pi Coding Agent
description: 从真实运行闭环到扩展与会话工程
eyebrow: Pi
---

# Pi Coding Agent：少收藏，先跑通

Pi 更新很快。真正有效的学习方法不是收集几十个链接，而是先让一次任务完整跑通，再沿着 Agent Loop、会话、Skill 和 Extension 逐层拆解。

本模块以 **2026-08-24** 核验的官方仓库 commit `a470b121` 为事实基线；[《动手学 Pi》序章](https://chasen-liao.github.io/pi-textbook-page/learn/prologue/)用于组织教学路径，不替代官方文档和源码。

## 先做一个最小实操

在临时 Git 仓库中让 Pi 完成一项小任务：读取 `README.md`、修改一处文字、运行检查，然后查看 `git diff`。观察这条轨迹：

```text
用户目标 → 模型请求工具 → 工具返回事实 → 模型继续推理 → 验证结果
```

工具调用只是“模型想做什么”，工具结果才是“环境实际发生了什么”。先理解这个闭环，再谈插件数量。

## 阅读顺序

1. [Pi 是什么：从一次工具往返理解运行时](./01-what-is-pi/index.html)
2. [pi-ai：统一 Provider 的边界](./02-pi-ai-provider/index.html)
3. [Skill、Extension 与 Package 怎么选](./03-extension-system/index.html)
4. [先写 Skill：什么时候才需要 MCP](./04-mcp-adapter/index.html)
5. [安全边界：信任、权限与隔离](./05-security-model/index.html)
6. [生态使用：发现不等于信任](./06-ecosystem/index.html)
7. [Pi、Claude Code 与 DSH：按约束选 Harness](./07-comparison/index.html)
8. [Session Runtime：恢复、分支与压缩](./08-session-runtime/index.html)

## 只保留这些入口

### 主要入口

- [Pi 官网](https://pi.dev)：安装、更新、配置和文档总入口。
- [Skills](https://pi.dev/docs/latest/skills)：重复流程如何写成 `SKILL.md`。
- [Extensions](https://pi.dev/docs/latest/extensions)：新增命令、工具、事件拦截或状态栏行为。
- [Pi Packages](https://pi.dev/docs/latest/packages)：`pi install`、包结构、作用域和更新。
- [Package 市场](https://pi.dev/packages)：先在官方目录发现包，再审查源码。
- [官方源码](https://github.com/badlogic/pi-mono)：API、示例和安全边界的最终依据。

### 辅助入口

- [Pi 中文文档](https://pi-doc.com)：用于快速入门；与官方 latest 冲突时以后者为准。
- [awesome-pi-agent](https://github.com/qualisero/awesome-pi-agent)：只当社区目录，不当安全背书。

## 一个实用判断

- 想让 Agent 重复执行一套流程：先写 **Skill**。
- 想改变 Pi 运行时、注册工具或拦截危险操作：写 **Extension**。
- 想分发 Skill、Extension、模板或主题：做 **Package**。
- 想连接已有 MCP Server，或让工具跨多个宿主复用：再接 **MCP**。

收藏不能替代反馈闭环。每学一项能力，都应留下可验证产物：一份 diff、一次测试、一个会话恢复记录，或一条被正确拦截的危险操作。
