---
layout: default
title: Pi Coding Agent
description: 从 Agent Loop 到可扩展 Harness 的工程学习路线
eyebrow: Pi
---

# Pi Coding Agent：从一次真实任务开始

Pi 把自己定义为一个 minimal agent harness。这里的“minimal”不是功能简陋，而是尽量把稳定内核与工作流偏好分开：模型调用、Agent Loop、工具和 Session 由运行时负责；Skill、Extension 与 Package 负责按需定制。

学习 Pi 最容易走偏的方式，是先收集插件和配置，再试图从功能列表反推架构。本模块采用相反顺序：先跑通一条可观察的工具闭环，再沿 Provider、扩展、MCP、安全、生态和 Session 逐层拆解。

> 事实基线：2026-08-24，官方仓库 [`badlogic/pi-mono`](https://github.com/badlogic/pi-mono) commit [`a470b121`](https://github.com/badlogic/pi-mono/tree/a470b121bf683b4c2b9fc0b3a7c807de7e0cfe9c)。Pi 迭代很快，安装命令和 API 以 [官方 latest 文档](https://pi.dev/docs/latest/) 为准。

## 先完成一次最小实操

安装 Pi：

```bash
npm install -g --ignore-scripts @earendil-works/pi-coding-agent
```

建立一个不会影响真实项目的临时仓库：

```bash
pi_lab_dir=$(mktemp -d)
cd "$pi_lab_dir"
git init
printf '# pi-lab\n' > README.md
git add README.md
git -c user.name=pi-lab -c user.email=pi-lab@example.invalid \
  commit -m "baseline"
pi
```

第一次启动时使用 `/login` 选择 Provider，然后给 Pi 一个边界清楚的任务：

```text
读取 README.md，增加一句项目说明。修改后检查 git diff，
不要提交，不要访问仓库外的文件，也不要执行任何发布操作。
```

退出后不要只看 Pi 的最终回答，要检查环境事实：

```bash
git diff --check
git diff
git status --short
```

这次练习至少应让你看到四件事：模型提出工具调用，运行时执行工具，工具结果回到下一轮模型请求，最终文件状态由 Git 而不是模型自述证明。

## 模块主线

本模块保留旧版“轻内核的收益与代价”主线，并加入《动手学 Pi》的实践方法。每篇文章都回答四个问题：

1. 这个部件在完整运行链中负责什么？
2. 输入、输出和失败终态是什么？
3. 当前官方实现把职责放在哪个包或源码目录？
4. 读者怎样用一个小实验验证，而不是只相信文字？

## 阅读顺序

1. [Pi 是什么：定位、架构与 Agent Loop](./01-what-is-pi/index.html)
2. [pi-ai：统一多 Provider 的适配层设计](./02-pi-ai-provider/index.html)
3. [扩展体系：Skill、Extension 与 Package](./03-extension-system/index.html)
4. [Pi 为什么不内置 MCP：Adapter 与 Token 取舍](./04-mcp-adapter/index.html)
5. [安全模型：Project Trust、权限门禁与系统隔离](./05-security-model/index.html)
6. [生态使用：发现、审计与退出策略](./06-ecosystem/index.html)
7. [Pi vs Claude Code vs DSH：按约束选择 Harness](./07-comparison/index.html)
8. [Session Runtime：树形历史、恢复与 Compaction](./08-session-runtime/index.html)

## 每篇文章的学习产物

| 文章 | 核心问题 | 建议产物 |
| --- | --- | --- |
| 01 定位与架构 | 一次工具往返怎样穿过 Pi 的职责层 | 一份 JSON 事件轨迹 |
| 02 Provider 适配 | 统一消息和流事件后，哪些差异仍会泄漏 | 一张双模型对照表 |
| 03 扩展体系 | 流程知识、运行时代码和分发分别放哪里 | 一个 Skill + 一个 Extension |
| 04 MCP | 何时需要协议互操作，何时 CLI 或 Skill 更简单 | 一次 direct/proxy 对照实验 |
| 05 安全 | trust、审批、沙箱分别防什么 | 一份威胁模型和隔离配置 |
| 06 生态 | “市场可安装”为什么不等于“可以信任” | 一份安装前审计记录 |
| 07 选型 | 如何用同一任务比较三个 Harness | 一张带证据的决策矩阵 |
| 08 Session | 历史、活动分支和模型上下文如何分离 | 一次 resume/tree/compact 记录 |

## 只保留这些入口

### 官方事实源

- [Pi 官网](https://pi.dev)：安装、更新、核心定位和文档入口。
- [Skills](https://pi.dev/docs/latest/skills)：`SKILL.md`、发现目录、渐进披露和显式调用。
- [Extensions](https://pi.dev/docs/latest/extensions)：工具、命令、事件拦截、UI 和运行时状态。
- [Pi Packages](https://pi.dev/docs/latest/packages)：`pi install`、包结构、作用域和更新。
- [Package 市场](https://pi.dev/packages)：发现候选包，不能替代源码审计。
- [官方源码](https://github.com/badlogic/pi-mono)：类型、示例、安全边界和行为的最终依据。

### 学习与辅助入口

- [《动手学 Pi》](https://chasen-liao.github.io/pi-textbook-page/learn/prologue/)：沿 15 个 checkpoint 手写 Pi-style Agent，适合补 Agent Loop、Session 和 Eval 的实践理解。
- [Pi 中文文档](https://pi-doc.com)：用于快速阅读；与官方 latest 冲突时以后者为准。
- [awesome-pi-agent](https://github.com/qualisero/awesome-pi-agent)：历史社区目录。该仓库已于 2026-06-03 归档，只用于发现旧项目，不用于判断当前兼容性。

## 四条选择规则

- 团队流程、检查清单和领域知识：先写 **Skill**。
- 新增工具、命令、事件拦截或 UI：写 **Extension**。
- 分发 Extension、Skill、Prompt Template 或 Theme：做 **Package**。
- 已有 MCP Server 需要跨宿主复用：再引入 **MCP Adapter**。

收藏本身不会提升 Agent 工程能力。完成一次 diff、一次失败实验、一次 Session 恢复和一次安全拦截，才算把资料变成可复用经验。
