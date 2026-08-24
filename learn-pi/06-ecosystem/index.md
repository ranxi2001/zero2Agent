---
layout: default
title: "生态使用：发现、审计与退出策略"
description: 从官方示例到社区 Package 建立可维护的采用流程
eyebrow: Pi / 06
---

# 生态使用：发现、审计与退出策略

## 为什么这个问题值得关注

Pi 把许多产品能力留给 Extension 和 Package，因此生态不是附属功能，而是实际使用方式的一部分。但“能在市场搜到”“下载量很高”“群里有人推荐”都不能证明一个包安全、兼容或值得长期依赖。

评价生态的关键不是收藏多少链接，而是能否把发现、验证、安装、升级和退出连成一个闭环。

> 本文的官方事实入口是 [Pi 官网](https://pi.dev)、[Package 市场](https://pi.dev/packages) 和 [官方源码](https://github.com/badlogic/pi-mono)。社区目录只用于发现候选项目，不作为兼容性或安全背书。

## 把资料入口分成四层

| 层级 | 主要用途 | 可信到什么程度 |
| --- | --- | --- |
| 官方文档 | 安装、配置、Skills、Extensions、Packages、Session、安全 | 当前公开行为说明，仍需与版本对应 |
| 官方源码与测试 | 类型、边界、示例、失败语义 | 最接近实现事实 |
| Package 市场 | 搜索候选包、查看 manifest、版本、依赖和仓库 | 发现入口，不等于审核市场 |
| 中文文档与社区列表 | 快速理解、寻找关键词和历史项目 | 辅助导航，冲突时回到官方事实源 |

这四层不需要扩展成几十个收藏夹。遇到问题时遵循固定顺序：官网定位机制，latest 文档确认用法，源码与测试确认边界，市场和社区目录寻找实现。

## awesome 列表已经不能当当前目录

[`qualisero/awesome-pi-agent`](https://github.com/qualisero/awesome-pi-agent) 已于 2026-06-03 归档。仓库 README 明确表示内容过时，并被更专门的项目替代。

它仍有两个用途：

- 查找早期生态项目和关键词；
- 观察某类需求曾经有哪些实现方向。

它不适合用来判断：

- 包是否兼容当前 `@earendil-works/*` 命名和 API；
- 项目是否仍维护；
- 安装命令是否安全；
- 当前市场里哪个实现更成熟。

旧列表发现的任何项目，都应重新回到仓库、npm 和当前 Pi Package 页面核验。

## 先从官方示例理解能力边界

在安装社区包前，先阅读 `packages/coding-agent/examples/extensions/`。官方示例覆盖：

- `permission-gate.ts`：危险 bash 命令确认；
- `protected-paths.ts`：阻止写入敏感路径；
- `dirty-repo-guard.ts`：工作区脏时阻止 Session 切换；
- `subagent/`：通过独立 Pi 进程实现隔离上下文；
- `gondolin/`：把内置工具路由到 micro-VM；
- 自定义工具、命令、UI、Provider、compaction 与 Session 状态。

这些示例不是开箱即用的企业安全方案，但能回答两个问题：Pi 当前 Extension API 能做什么，以及某个社区包是否只是把官方示例包装了一层。

如果需求只需几十行窄逻辑，自行维护一个小 Extension 可能比引入大型 Package 更容易审计和升级。

## Package 市场能提供哪些证据

Pi Package 页面通常可以展示：

- 当前版本、发布时间和许可证；
- Package 类型，例如 extension、skill、prompt、theme；
- `pi` manifest 声明的资源；
- npm、源码和问题报告入口；
- 包体积、依赖和下载信息。

这些信息适合第一轮筛选。它们不能证明：

- 源码与 npm tarball 完全一致；
- 依赖没有高风险行为；
- Extension 不访问主目录、网络或环境变量；
- 包升级后仍保持原权限范围；
- 下载量来自真实 Pi 用户。

市场是目录，不是自动信任链。

## 安装前的十分钟审计

### 第一步：确认身份与维护状态

检查仓库是否匹配 npm 元数据，最近提交和 release 是否一致，issue 中是否存在兼容性或安全问题。不要只看 star。

```bash
npm view pi-mcp-adapter \
  name version license repository dist.tarball dependencies --json
```

### 第二步：检查实际发布内容

在临时目录下载 tarball，不运行包：

```bash
pi_audit_dir=$(mktemp -d)
cd "$pi_audit_dir"
npm pack pi-mcp-adapter --ignore-scripts
tar -tf ./*.tgz | sed -n '1,160p'
```

重点确认 manifest、入口源码、依赖和 README 是否都包含在发布包内。仓库中存在测试，不代表 npm tarball 发布的是同一份代码。

### 第三步：搜索高影响行为

解包后检查：

```bash
tar -xf ./*.tgz
rg -n 'child_process|exec\(|spawn\(|node:fs|node:net|fetch\(|https?://' package
rg -n 'process\.env|\.ssh|\.aws|\.config|\.pi/agent|keychain|keyring' package
rg -n 'preinstall|install|postinstall|prepare' package/package.json
```

命中这些字符串不自动表示恶意。它们告诉你权限面在哪里，需要继续读调用路径和默认配置。

### 第四步：确认失败和退出路径

至少回答：

- 包加载失败时，Pi 是继续运行还是进入半启用状态？
- headless 模式没有 UI 时，审批会放行还是拒绝？
- 禁用或移除后，设置、缓存、凭据和后台进程如何清理？
- 能否固定版本，升级是否有 changelog 和迁移说明？
- 旧版 API 不兼容时，团队是否能快速回退？

## 分清 Package 内的资源类型

同一个 Package 可以混合多种资源。审计时不要把它当成一个黑盒：

| 资源 | 主要风险 | 核验重点 |
| --- | --- | --- |
| Skill | 诱导模型运行脚本、读取外部资料 | 指令、脚本、相对路径、触发描述 |
| Extension | 同进程任意代码执行 | import、事件 hook、文件、进程、网络、凭据 |
| Prompt Template | 用户触发后进入上下文 | Prompt injection、参数和输出要求 |
| Theme | TUI 渲染变化 | 资源路径和意外代码依赖 |
| MCP config | 拉起子进程或连接远端服务 | 命令、endpoint、认证、工具权限 |

只想使用包内 Skill 时，可以通过 Package filtering 禁用 Extension。最小化启用面比“全部安装后再提醒模型小心”更可靠。

## 用户级与项目级安装的取舍

```bash
# 用户级：影响所有项目
pi install npm:@scope/package@1.2.3

# 项目级：写入 .pi/settings.json，随仓库共享
pi install npm:@scope/package@1.2.3 -l

# 临时试用：仅当前运行
pi -e npm:@scope/package@1.2.3
```

用户级方便，但会扩大影响范围，并让不同项目共享同一 Extension 组合。项目级更容易版本化和复现，却可能在项目被信任后触发缺失包安装。

稳妥流程通常是：先在隔离环境用 `-e` 试用，确认资源和权限面，再选择项目级固定版本；真正适用于所有仓库的窄工具，才考虑用户级安装。

## Skill 的跨 Harness 复用

Pi 可以从共享 `.agents/skills/` 发现 Skill，也可以在 settings 中加入其他 Harness 的 Skill 目录：

```json
{
  "skills": [
    "~/.claude/skills",
    "~/.codex/skills"
  ]
}
```

可移植的是 `SKILL.md` 的结构、相对资源和工作流知识，不是完整运行环境。跨宿主时要重新验证：

- 工具名称和参数是否存在；
- project trust 和目录发现顺序是否相同；
- Skill 激活后在 Context 中保留多久；
- `allowed-tools` 等字段如何解释；
- 附带脚本依赖的运行时是否可用；
- 同名 Skill 冲突时哪个版本获胜。

“能被两个 Harness 发现”只是一项兼容证据，不能推出任务行为一致。

## 什么时候该 Fork

Package、复制小段代码和 Fork 是三种不同维护承诺：

| 方式 | 适合情况 | 你承担什么 |
| --- | --- | --- |
| 直接依赖 Package | 上游维护活跃、权限面可接受 | 版本固定、升级测试、退出预案 |
| 复制窄 Extension | 逻辑很小、团队只需其中一部分 | 本地代码审查和 API 迁移 |
| Fork 上游 | 长期依赖且必须修改权限、行为或发布节奏 | 合并安全更新、发布、文档和完整回归 |

Fork 不是“一劳永逸地拥有代码”。它把上游维护责任转移给团队。如果没有负责人、升级窗口和差异清单，Fork 往往比固定旧版本更难治理。

## 建立升级回归而不是追最新

对长期依赖的 Package，维护一组最小行为测试：

1. Package 能加载，资源数量和名称符合预期；
2. 高风险工具在交互与 headless 模式下都遵守策略；
3. Session 恢复后扩展状态正确；
4. `/reload` 不会重复注册 handler；
5. 失败的依赖或 Server 不会阻断无关功能；
6. 卸载后没有残留进程、配置或凭据引用。

先在临时 Pi agent dir 和测试仓库升级。只有这些证据通过，才更新团队使用的版本。

## 一份采用记录应该写什么

```text
Package: npm:@scope/package@1.2.3
Source commit: <reviewed commit>
Purpose: 解决哪个具体问题
Enabled resources: 哪些 Extension / Skill / Prompt
Permissions: 文件、进程、网络、凭据范围
Validation: 运行了哪些成功与失败测试
Owner: 谁负责升级和安全问题
Rollback: 如何固定旧版、禁用和清理状态
Review date: 下次复核时间
```

这份记录比“推荐插件列表”更有长期价值，因为它把团队的信任判断和退出条件留下来了。

## 小结

- 官网、latest 文档和官方源码足以覆盖大多数 Pi 机制问题，不需要堆积大量教程入口。
- Package 市场用于发现和初筛，不代表第三方包已经通过官方安全审核。
- `awesome-pi-agent` 已归档，只能当历史目录使用。
- 采用 Package 前要检查发布内容、权限面、失败行为、版本固定和退出路径。
- Skill 格式可以跨 Harness 复用，但工具、权限、加载顺序和生命周期仍需逐宿主验证。

---

下一篇建议继续看：[Pi vs Claude Code vs DSH：按约束选择 Harness](../07-comparison/index.html)
