---
layout: default
title: "扩展体系：Skill、Extension 与 Package"
description: 分清按需知识、运行时代码和分发容器的工程边界
eyebrow: Pi / 03
---

# 扩展体系：Skill、Extension 与 Package

## 为什么这个问题值得关注

很多扩展系统最后都会出现同一种混乱：一份 Markdown 能解决的流程被写成高权限代码，必须确定执行的安全规则却只写进 Prompt，一组资源需要分发时又靠聊天窗口复制目录。

Pi 把这些需求分成 Skill、Extension 与 Package。三者不是能力从弱到强的升级路线，而是作用层不同：**Skill 改变模型知道什么，Extension 改变运行时能做什么，Package 改变资源怎样交付。**

> 本文基于 [Skills](https://pi.dev/docs/latest/skills)、[Extensions](https://pi.dev/docs/latest/extensions)、[Pi Packages](https://pi.dev/docs/latest/packages) 和官方源码 commit [`a470b121`](https://github.com/badlogic/pi-mono/tree/a470b121bf683b4c2b9fc0b3a7c807de7e0cfe9c)。

## 先用一张表做选择

| 需求 | 首选机制 | 原因 |
| --- | --- | --- |
| 团队规范、检查清单、调试手册 | Skill | 让模型按需读取知识，不新增常驻工具 |
| 用户明确触发的一段可复用 Prompt | Prompt Template | 展开文本即可，不需要自动匹配 |
| 新工具、命令、事件监听、状态栏 | Extension | 必须执行代码或改变运行时行为 |
| 无条件阻止某类 tool call | Extension + 外部隔离 | Prompt 不能保证执行，Extension 仍不是强沙箱 |
| 分享 Skill、Extension、Prompt、Theme | Package | 统一版本、安装和更新入口 |
| 连接已有跨宿主工具服务 | MCP Adapter | 需求是协议互操作，不只是流程知识 |

一个实用顺序是：先问缺的是知识还是能力，再问是否需要分发。不要从“哪个更强”开始。

## Skill：按需进入上下文的操作知识

Skill 是自包含的能力目录，至少包含一份 `SKILL.md`，还可以附带脚本、参考资料和资产：

```text
release-review/
├── SKILL.md
├── scripts/
│   └── check-release.sh
├── references/
│   └── rollback-policy.md
└── assets/
    └── report-template.md
```

`SKILL.md` 的最小 frontmatter 是 `name` 和 `description`：

```markdown
---
name: release-review
description: 发布前检查版本、测试、变更范围和回滚条件。用于准备发布或审查发布计划。
---

# Release Review

1. 读取仓库规则并确认本次变更范围。
2. 运行与变更相关的测试和构建。
3. 检查 diff、敏感信息和版本号。
4. 输出验证证据；任何必需检查失败时停止发布。
```

描述不是装饰字段。Pi 启动时把 Skill 的名称和描述放进系统上下文，模型匹配到任务后才用 `read` 加载完整正文。描述过于宽泛，会导致误触发或永远不触发。

### 渐进披露怎样节省上下文

```text
启动：扫描 Skill -> 只加载 name + description
匹配：模型判断任务需要 release-review
激活：read SKILL.md
深入：按相对路径读取 references 或运行 scripts
```

这与把整套手册永久塞进 `AGENTS.md` 不同。常驻上下文只承担路由，具体知识在需要时进入会话。

模型不一定总会主动加载正确 Skill。需要确定使用时，可以显式调用：

```text
/skill:release-review
```

### Skill 的发现位置

| 作用域 | 目录 |
| --- | --- |
| 用户全局 | `~/.pi/agent/skills/`、`~/.agents/skills/` |
| 项目 | `.pi/skills/`、项目或祖先目录中的 `.agents/skills/` |
| Package | 包内 `skills/` 或 `package.json` 的 `pi.skills` |
| 显式路径 | settings 的 `skills` 或 `--skill <path>` |

项目级 Skill 只有在项目被信任后才加载。全局 Skill 则影响所有项目，权限范围反而更大，不能因为放在用户目录就跳过审查。

### Skill 不是安全边界

Skill 虽然以 Markdown 为主，但可以附带脚本并指示模型执行。它能写“发布前必须确认”，却不能保证运行时一定阻止发布。必须确定执行的规则，应放进 Extension hook、CI、操作系统权限或远端审批系统。

## Extension：改变运行时行为的同进程代码

Extension 是 TypeScript 模块。它可以：

- 使用 `pi.registerTool()` 注册模型工具；
- 使用 `pi.registerCommand()` 注册斜杠命令；
- 监听 Agent、Session、Model 和 Tool 事件；
- 在 tool call 前阻止或修改行为；
- 注入上下文、自定义 compaction 或保存 Session entry；
- 修改状态栏、编辑器、渲染和其他 TUI 组件；
- 注册自定义 Provider。

当前 Extension 入口是一个接收 `ExtensionAPI` 的工厂函数，不是旧稿中的声明对象：

```typescript
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

export default function auditExtension(pi: ExtensionAPI) {
  pi.on("tool_call", async (event, ctx) => {
    if (event.toolName !== "bash") return;

    const command = String(event.input.command ?? "");
    const dangerous = /\b(rm\s+-rf|sudo)\b/i.test(command);
    if (!dangerous) return;

    if (!ctx.hasUI) {
      return { block: true, reason: "Dangerous command blocked in headless mode" };
    }

    const allowed = await ctx.ui.confirm("危险命令", command);
    if (!allowed) {
      return { block: true, reason: "Rejected by user" };
    }
  });

  pi.registerCommand("audit-status", {
    description: "显示审计扩展状态",
    handler: async (_args, ctx) => {
      ctx.ui.notify("audit extension enabled", "info");
    },
  });
}
```

项目内快速测试：

```bash
pi -e ./.pi/extensions/audit.ts
```

稳定使用时放到 `~/.pi/agent/extensions/` 或 `.pi/extensions/`，然后用 `/reload` 重载。项目级 Extension 必须经过 project trust。

### 为什么 headless 模式要 fail closed

交互模式可以弹出确认框，`-p`、JSON 或 RPC 模式通常没有 UI。如果扩展在 `ctx.hasUI === false` 时默认放行，自动化恰好会绕过最需要的保护。

上面的代码选择直接阻止危险命令。但这仍然只是 Pi 进程内的一段代码：扩展本身可以被错误修改，其他工具也可能绕过这条正则。真正的损害上限仍由容器、账号、挂载和网络策略决定。

## Context、Skill 与 Extension 的加载顺序

项目 trust 很容易被误解成“拒绝后 Pi 什么都不读”。当前行为更细：

```text
进入项目
  -> 加载 AGENTS.md / CLAUDE.md 等 context 文件
  -> 判断项目是否包含需要 trust 的资源
  -> 允许：加载项目 settings、Skill、Extension、Package 等
  -> 拒绝：跳过这些可执行或高影响资源
```

`AGENTS.md` 等 context 文件默认不受 project trust 阻止，因为它们属于项目上下文。它们仍可能包含 prompt injection，所以“未信任项目”不等于“模型未读取任何不可信文本”。

《动手学 Pi》的资源章节把这一点概括为“知识按需进入上下文，代码先过信任门”。用于教学很准确，但生产系统还要再加一层：Prompt 内容也不可信，只是它与可执行 Extension 的直接权限不同。

## Extension 注册要么完整，要么失败

复杂 Extension 可能同时注册工具、hook 和命令。若加载到一半失败，却留下前半部分注册，运行时会进入无法解释的半启用状态。

可靠的 Extension loader 应保证：

1. 先解析和验证模块；
2. 通过 trust 判断；
3. 在临时注册上下文中完成所有注册；
4. 全部成功后再对 Session 可见；
5. reload 或 dispose 时撤销旧资源和事件监听。

使用者不必自己实现 loader，但调试扩展冲突时要寻找这些证据：资源来源、加载错误、重复名称、reload 后旧 handler 是否仍存在。

## Package：把资源组合成可安装单元

Package 可以组合 Extension、Skill、Prompt Template 和 Theme。它不是另一种运行机制，而是分发容器。

一个显式 manifest 可以写成：

```json
{
  "name": "@acme/pi-release-review",
  "version": "1.0.0",
  "type": "module",
  "pi": {
    "extensions": ["./extensions/audit.ts"],
    "skills": ["./skills/release-review"],
    "prompts": ["./prompts/release.md"]
  }
}
```

也可以使用约定目录，让 Pi 自动发现 `extensions/`、`skills/`、`prompts/` 和 `themes/`。

### 安装、试用和作用域

```bash
# 用户全局安装
pi install npm:@acme/pi-release-review@1.0.0

# 项目级安装，写入 .pi/settings.json
pi install git:github.com/acme/pi-release-review@v1.0.0 -l

# 当前运行临时试用，不写入长期设置
pi -e npm:@acme/pi-release-review@1.0.0

# 查看与移除
pi list
pi remove npm:@acme/pi-release-review
```

项目 settings 中缺失的 Package，可能在项目被信任后自动安装。对团队仓库来说，这意味着 `.pi/settings.json` 的变更也属于供应链变更，必须像 lockfile 一样审查。

### Package 的最高风险组件决定信任级别

只含 Theme 的包与包含 Extension 的包，风险不相同。但安装决策应按最高风险部分评估：

- Extension 能以 Pi 进程权限执行任意 TypeScript 和 Node.js API；
- Skill 能诱导模型执行脚本或外部写操作；
- npm 依赖可能带来额外代码和安装面；
- 更新可能改变资源内容、权限范围和加载顺序。

市场页面、下载量和作者简介只能帮助发现，不能替代源码、依赖、版本和退出路径检查。

## 一个完整的小实验

用同一需求分别验证 Skill 与 Extension：

1. 在临时仓库创建 `.pi/skills/release-review/SKILL.md`，只写发布检查流程。
2. 启动 Pi，确认 project trust 后用 `/skill:release-review` 加载。
3. 让 Skill 检查 Git diff，观察它是否只提供流程知识。
4. 创建 `.pi/extensions/audit.ts`，拦截包含 `sudo` 的 bash 调用。
5. 用 `pi -e` 加载，分别在交互模式和 `-p` 模式触发。
6. 确认交互模式要求批准，headless 模式直接拒绝。
7. 删除 Extension 后重复实验，证明安全行为来自代码层而不是 Skill 文本。

验收产物应包括：Skill 触发记录、被拦截的 tool call、headless 拒绝结果和最终 `git diff`。

## 常见误区

### “Skill 是一组工具”

不准确。Skill 的核心是按需加载的说明、脚本和参考资料；它不会自动把每个脚本注册为模型工具。

### “Extension 拦截了命令，所以有沙箱”

不成立。Extension 与被保护对象处于同一进程权限域，适合策略和交互，不是操作系统强边界。

### “Package 市场里的包经过官方安全审核”

不能这样推断。市场是发现入口，Package 文档明确要求安装前审查第三方源码。

### “跨 Harness Skill 行为完全一致”

不同宿主的工具、目录发现、权限和 Skill 生命周期不同。文件格式可移植，不代表执行行为等价。

## 源码阅读入口

- `packages/coding-agent/src/core/resource-loader.ts`：资源发现和加载组合。
- `packages/coding-agent/src/core/extensions/`：Extension loader、runner 与类型。
- `packages/coding-agent/src/core/project-trust.ts`：项目 trust 决策。
- `packages/coding-agent/examples/extensions/`：工具、命令、门禁、UI、subagent 和 sandbox 示例。
- `packages/coding-agent/docs/skills.md`、`extensions.md`、`packages.md`：当前行为说明。

## 小结

- Skill 解决按需知识和流程，Extension 解决运行时行为，Package 解决版本化分发。
- 先判断缺的是知识还是能力，不要默认从 Extension 或 MCP 开始。
- project trust 会保护项目级可执行资源，但不会把所有项目文本隔绝在模型之外。
- Extension 可以做门禁，却与 Pi 共享进程权限，不能替代系统隔离。
- 安装 Package 等于信任其中风险最高的代码和后续更新路径。

---

下一篇建议继续看：[Pi 为什么不内置 MCP：Adapter 与 Token 取舍](../04-mcp-adapter/index.html)
