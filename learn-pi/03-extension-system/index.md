---
layout: default
title: "扩展体系：从 Extension 到 Package 的能力组合"
description: Pi 三层扩展抽象的边界、组合方式与生态问题
eyebrow: Pi / 03
---

# 扩展体系：从 Extension 到 Package 的能力组合

## 为什么这个问题值得关注

Pi 的内核刻意做得小——Agent Loop + 工具调度 + 扩展注册。这意味着 Pi 的真实能力几乎完全由扩展决定。理解扩展体系的设计，就是理解 Pi 如何在保持内核简洁的同时支撑复杂的工作流。更重要的是，理解它在什么地方妥协了。

一个框架的扩展体系回答的核心问题是：**什么东西应该被共享，以什么粒度共享，谁来保证质量。**

## 三层扩展抽象

Pi 把可扩展的能力分成三个层级，从细粒度到粗粒度递进：

### TypeScript Extensions

最基础的扩展单元。一个 Extension 可以向 Pi 注册以下任意能力：

- **工具（Tools）**：模型可以调用的函数，比如文件读写、Shell 执行、代码搜索
- **命令（Commands）**：用户在终端输入的斜杠命令，如 `/search`、`/commit`
- **事件监听（Event Listeners）**：对 Agent 生命周期事件的响应，如消息发送前、工具调用后
- **自定义 UI 组件**：终端中渲染的自定义展示（进度条、diff 视图等）

Extension 的注册是声明式的——在入口文件中 export 一个符合接口的对象，Pi 在启动时加载并注册。

```typescript
// 一个最简 Extension 的结构
export default {
  name: "my-extension",
  tools: [/* 工具定义 */],
  commands: [/* 命令定义 */],
  onEvent: {/* 事件监听 */},
}
```

Extension 之间没有显式的依赖关系管理。如果 Extension A 依赖 Extension B 提供的工具，这种依赖是隐式的——Pi 不保证加载顺序，也不检查依赖是否满足。

### Agent Skills

Skill 是比 Extension 更高一层的抽象。一个 Skill 代表一个"可复用的按需能力"——不是始终激活的工具，而是 Agent 在特定任务上下文中被告知可以使用的能力。

Skill 和 Extension 的关键区别：

| 维度 | Extension | Skill |
| --- | --- | --- |
| 激活方式 | 启动时加载，始终可用 | 按需加载，任务触发 |
| 粒度 | 单个工具或命令 | 一组协作的工具 + prompt |
| 上下文 | 全局 | 任务作用域 |
| 跨框架 | Pi 专属 | 可跨框架兼容 |

最后一行是 Pi Skills 最有野心的设计：pi-skills 协议定义了一种跨框架的 Skill 格式，同一个 Skill 可以在 Claude Code、Codex CLI、Amp、Droid 中运行。这通过标准化 Skill 的输入输出格式实现——Skill 接收结构化输入，返回结构化输出，中间的执行逻辑和宿主框架无关。

### Pi Packages

Package 是分发单元。一个 Package 可以包含：

- 多个 Extensions
- 多个 Skills
- Prompt 模板
- 主题配置（终端配色、UI 样式）
- 配置文件

Package 通过 `pi install` 安装。来源可以是 npm registry、GitHub 仓库或本地路径：

```bash
pi install npm:pi-mcp-adapter
pi install github:user/my-package
pi install ./local-package
```

Package 解决的是组合和分发问题：一组相关的 Extensions 和 Skills 打包成一个可分享的单元，带上必要的 prompt 和配置。

## 与其他框架的对比

### 与 Claude Code Skills/MCP 的对比

Claude Code 的扩展模型更简单：

- **Skills**（Slash Commands）：`/` 触发的用户定义命令，基于 Markdown prompt
- **MCP Servers**：标准化的外部工具提供者
- **Hooks**：生命周期事件的 shell 脚本监听

Claude Code 没有 Package 概念——没有打包分发机制，Skills 通过文件系统共享，MCP 配置手动管理。好处是简单，坏处是没有生态分发渠道。

### 与 DSH Cordis 插件的对比

DeepSeek Harness 基于 Cordis 插件树，走的是更重的依赖管理路线：

- 插件之间有显式依赖声明
- 生命周期由框架严格管理（初始化顺序、销毁顺序）
- 服务注入机制（一个插件可以消费另一个插件提供的服务）
- 热重载支持

Pi 的 Extension 没有这些。这让 Pi 扩展开发门槛更低（不需要理解依赖注入），但组合复杂扩展时更容易出问题。

## pi-skills 的跨框架兼容设计

pi-skills 协议试图解决一个行业问题：为什么一个"搜索代码"的能力需要为每个 Agent 框架分别实现？

协议的核心思路：

1. Skill 用标准 JSON 描述输入输出 schema
2. Skill 的执行逻辑是纯函数（输入 -> 输出）
3. 宿主框架负责把 Skill 的 schema 翻译成自己的工具格式
4. 执行时宿主框架把参数传给 Skill，拿回结果

目前声称兼容的框架：Claude Code、Codex CLI、Amp、Droid。但"兼容"的程度差异大——简单的工具类 Skill 跨框架没问题，涉及 UI 交互或框架特有 API 的 Skill 实际上做不到真正的跨框架。

## 扩展生态的质量控制问题

Pi 没有扩展审核机制。任何人可以发布 Package 到 npm，任何人可以安装。这意味着：

**安全风险**：一个恶意 Package 可以注册一个工具，在模型调用时执行任意代码。由于 Pi 不内置权限系统，这个工具获得的权限和 Pi 本身一样大。

**质量不一致**：Package 之间可能注册同名工具导致冲突，或者修改全局状态影响其他扩展。Pi 没有命名空间隔离或冲突检测。

**维护断裂**：社区扩展依赖 Pi 的内部 API，而 Pi 迭代快、breaking changes 频繁。一次大版本升级可能导致大量扩展失效。

对比来看：

- VS Code 有审核市场，扩展需要通过审查才能发布
- Chrome 扩展有权限声明和用户授权机制
- Pi 什么都没有

这不一定是错误的选择——早期生态需要低门槛来吸引贡献者。但当扩展数量增长后，质量控制的缺失会成为真实问题。

## pi install 的工作方式

`pi install` 做以下事情：

1. 解析来源（npm/GitHub/本地路径）
2. 下载 Package 到 `~/.pi/packages/` 目录
3. 解析 Package 的 manifest 文件（声明了包含哪些 Extensions 和 Skills）
4. 在 Pi 配置中注册这个 Package
5. 下次启动时加载注册的 Extensions

没有沙箱隔离、没有权限确认、没有签名验证。`pi install` 本质上等同于 `npm install` 加上注册到 Pi 配置。

## 实际使用模式

常见的 Package 组合模式：

- **工具包**：一组相关工具（文件操作、Git 操作、数据库查询）
- **工作流包**：工具 + prompt + 配置，封装一个完整工作流（如"代码审查"）
- **Provider 包**：新模型 Provider 的适配器（通过 pi-ai 扩展点）
- **UI 包**：自定义终端渲染组件

## 小结

Pi 的三层扩展抽象解决了不同粒度的复用问题：Extension 解决单一能力注册，Skill 解决跨框架按需能力，Package 解决组合分发。设计选择偏向低门槛——没有依赖管理、没有命名空间隔离、没有审核机制。

这个选择在生态早期是合理的：降低贡献门槛比保证质量更重要。但 Pi 已经是 95k stars 的项目，扩展数量在增长。质量控制问题从"将来可能有"变成了"现在就是"。

---

下一篇：[pi-mcp-adapter：MCP 工具的 Token 经济学](../04-mcp-adapter/index.html)
