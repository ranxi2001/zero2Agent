---
layout: default
title: Skill、Extension 与 Package 怎么选
description: 分清知识层、运行时代码层与分发层
eyebrow: Pi / 03
---

# Skill、Extension 与 Package 怎么选

很多 Pi 教程把三者都叫“插件”，结果是：本来一份 `SKILL.md` 能解决的问题，被写成拥有系统权限的 TypeScript；本来需要代码拦截的风险，又被寄希望于 Prompt。

## Skill：按需加载的操作知识

Pi 实现 [Agent Skills 标准](https://pi.dev/docs/latest/skills)。启动时只把 Skill 的名称和描述放进上下文；任务匹配后，模型再通过 `read` 加载完整 `SKILL.md`。这就是渐进披露。

```text
my-review-skill/
├── SKILL.md
├── scripts/
│   └── check.py
└── references/
    └── policy.md
```

```markdown
---
name: review-release
description: 发布前检查版本、测试、变更和回滚条件
---

# Release Review
1. 确认工作树范围。
2. 运行测试与构建。
3. 检查变更和敏感信息。
4. 输出验证证据；失败则停止发布。
```

全局目录包括 `~/.pi/agent/skills/` 与 `~/.agents/skills/`；项目目录包括 `.pi/skills/` 与 `.agents/skills/`，项目级资源只有在项目被信任后才加载。

Skill 不是 JSON 纯函数协议，也不是安全边界。它可以附带脚本并指示模型执行命令，因此仍要审查。

## Extension：改变运行时行为

当需求涉及新增工具、命令、事件监听、危险操作拦截或状态栏时，才进入 [Extension](https://pi.dev/docs/latest/extensions)。当前 API 使用接收 `ExtensionAPI` 的工厂函数：

```typescript
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

export default function auditExtension(pi: ExtensionAPI) {
  pi.on("tool_call", async (event) => {
    // 记录或检查工具调用；事件名与字段以当前官方类型为准
  });

  pi.registerCommand("audit-status", {
    description: "显示审计扩展状态",
    handler: async (_args, ctx) => {
      ctx.ui.notify("audit extension enabled", "info");
    },
  });
}
```

Extension 是宿主加载的可执行代码。不要从旧文章复制 API；写之前查看 latest 文档和当前类型定义。

## Package：交付与复用

[Pi Package](https://pi.dev/docs/latest/packages) 是分发容器，可组合 Extension、Skill、Prompt Template 和 Theme。它不是第三种运行机制。

```bash
pi install npm:@foo/bar@1.0.0
pi install git:github.com/user/repo@v1
pi install ./local-package
```

用户级 npm 包位于 `~/.pi/agent/npm/`，项目级位于 `.pi/npm/`。项目被信任后，项目设置声明但本地缺失的包可能在启动时自动安装。Package 中的 Extension 可执行任意代码，Skill 也可能诱导 Agent 运行脚本；安装前必须审查源码、依赖、安装脚本、网络和凭据访问。

## 选择树

```text
只是重复流程、检查清单、领域说明？
└─ Skill

必须新增工具、命令、事件钩子或 UI？
└─ Extension

要把上述资源交付给别人？
└─ Package
```

先用最小机制。Skill 能表达的流程，不要为了“更强”先写 Extension；Extension 能通过窄工具解决的问题，也不要直接开放任意 shell。

---

下一篇建议继续看：[先写 Skill：什么时候才需要 MCP](../04-mcp-adapter/index.html)
