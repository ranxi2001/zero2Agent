<div align="center">

# zero2Agent

**面向程序员的 Agent 工程教程 · 从概念到生产**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/ranxi2001/zero2Agent?style=social)](https://github.com/ranxi2001/zero2Agent)
[![Site](https://img.shields.io/badge/Site-onefly.top%2FzeroAgent-brightgreen)](https://onefly.top/zero2Agent)

[在线阅读](https://onefly.top/zero2Agent) · [Agent Basic](https://onefly.top/zero2Agent/learn-agent-basic/) · [OpenClaw](https://onefly.top/zero2Agent/learn-openclaw/) · [Claude Code](https://onefly.top/zero2Agent/learn-claude-code/)

</div>

---

## 这是什么

**zero2Agent** 是一个面向程序员的 Agent 工程教程仓库，目标是帮助已经会写代码、会用 AI 工具，但还没系统做过 Agent 工程的开发者，真正从零搭出自己的 Agent 系统。

内容不停留在 Demo、Prompt、套壳工作流，而是从核心机制出发，覆盖 Agent 的工程设计原理、框架拆解、代码实现，最终落到一个完整的实战项目。

**在线阅读（GitHub Pages）**：[https://onefly.top/zero2Agent](https://onefly.top/zero2Agent)

---

## 模块概览

| 模块 | 状态 | 内容 |
|------|------|------|
| [Agent Basic](https://onefly.top/zero2Agent/learn-agent-basic/) | ✅ 进行中 | Agent 核心概念、Tool Calling、Memory、Planning、RAG、多 Agent 模式 |
| [OpenClaw Agent](https://onefly.top/zero2Agent/learn-openclaw/) | ✅ 完成 | 60 行核心框架，从 Node 推导到 Agent，pi-mono 架构解析，部署实战 |
| [Claude Code](https://onefly.top/zero2Agent/learn-claude-code/) | ✅ 完成 | 12 节课手写 Coding Agent：Loop → Tools → Subagent → Teams → Worktree 隔离 |
| LangGraph | 🔲 待开始 | Graph 状态机、条件分支、持久化、Human-in-the-loop |
| Frameworks | 🔲 待开始 | LangChain、OpenAI Agents SDK、MCP、CrewAI 横向对比 |
| Final Project | 🔲 待开始 | 加密货币市场风控 Agent 完整实战 |

---

## 模块详情

### Agent Basic

建立正确的 Agent 工程认知，覆盖：

- 什么是 Agent，与 Workflow 的本质区别
- Tool Calling 的完整机制
- Memory 设计模式（短期 / 长期 / 外部存储）
- Planning、Reflection、RAG 的作用边界
- 单 Agent vs 多 Agent 的常见架构模式
- 为什么 Demo 能跑、落地就不稳定

### OpenClaw Agent

从 60 行核心代码出发，一步步推导出完整的 Agent 框架：

```python
workflow = node + node        # 有向路径，无循环
chatbot  = workflow + loop    # 外层循环，多轮对话
agent    = chatbot + tools    # 图内回路，模型驱动工具
```

覆盖 RAG、Tool/MCP/Skill 三种工具形式、Memory 压缩、多 Agent 并行团队、pi-mono 架构解析，以及完整的部署和面试准备。

参考仓库：[lasywolf/Learn-OpenClaw](https://github.com/lasywolf/Learn-OpenClaw) · [pi-mcp/pi-mono](https://github.com/pi-mcp/pi-mono)

### Claude Code

12 节课，从 30 行 Agent 循环逐步构建完整 Coding Agent 系统：

| 章节 | 机制 |
|------|------|
| s01–s06 | Agent Loop · Tool Dispatch · TodoWrite · Subagent · Skill Loading · Context Compact |
| s07–s12 | Task DAG · Background Tasks · Agent Teams · Protocols · Autonomous Agents · Worktree Isolation |

参考仓库：[shareAI-lab/learn-claude-code](https://github.com/shareAI-lab/learn-claude-code)

---

## 适合谁

- 学过深度学习，但没做过 LLM 应用开发
- 会 Python，想补齐 Agent 工程能力
- 用过 Claude Code / Cursor 等工具，想理解背后的实现
- 准备 Agent 方向技术面试或实习
- 想把 Agent 真正部署上线，而不只是跑 Demo

## 不适合谁

- 大模型预训练、对齐、推理优化等底层算法研究
- 纯学术导向的 Agent 论文综述
- 只想快速复制"几分钟搭建 Agent"的短教程

---

## 仓库结构

```
zero2Agent/
├── _layouts/           # Jekyll 页面模板
├── _data/
│   └── nav.yml         # 导航配置
├── assets/
│   ├── css/docs.css    # 三栏布局样式
│   └── js/app.js       # 侧边栏 + TOC + Mermaid
├── learn-agent-basic/  # Agent 基础概念（8 篇）
├── learn-openclaw/     # OpenClaw 框架教程（9 篇）
├── learn-claude-code/  # Claude Code 课程（12 篇）
├── learn-langgraph/    # LangGraph（待开始）
├── learn-frameworks/   # 框架横向对比（待开始）
└── final-project/      # 加密货币风控 Agent 实战（待开始）
```

---

## 本地运行

```bash
git clone https://github.com/ranxi2001/zero2Agent
cd zero2Agent

# 安装 Jekyll（需要 Ruby）
gem install bundler jekyll
bundle install

# 本地预览
bundle exec jekyll serve
# 访问 http://localhost:4000/zero2Agent
```

---

## 引用与致谢

本仓库的内容参考并引用了以下开源项目：

- **[shareAI-lab/learn-claude-code](https://github.com/shareAI-lab/learn-claude-code)** — Claude Code 模块的课程结构和核心内容来源，12 节渐进式 Agent 构建课程
- **[lasywolf/Learn-OpenClaw](https://github.com/lasywolf/Learn-OpenClaw)** — OpenClaw 模块的核心思路和代码框架来源
- **[pi-mcp/pi-mono](https://github.com/pi-mcp/pi-mono)** — 生产级 Coding Agent 的参考实现

---

## Contributing

欢迎 PR 和 Issue。内容补充、错误修正、新模块建议均可。

提 Issue 前请先检查是否已有相关讨论。PR 建议一个 PR 只做一件事。

---

## License

[MIT](LICENSE)
