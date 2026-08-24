---
layout: default
title: "Pi 为什么不内置 MCP：Adapter 与 Token 取舍"
description: 从互操作需求、工具发现和上下文成本判断是否接入 MCP
eyebrow: Pi / 04
---

# Pi 为什么不内置 MCP：Adapter 与 Token 取舍

## 为什么这个问题值得关注

MCP 解决工具、资源和 Prompt 在不同宿主之间的标准化连接，但它不是所有扩展需求的默认答案。一个团队流程没有写清楚时，接入 MCP 只会把知识问题变成连接、认证、schema、超时和权限问题。

Pi 官方刻意不内置 MCP，建议优先考虑带 README 的 CLI、Skill 或自定义 Extension；确实需要 MCP 生态时，再安装第三方 Adapter。这项选择不是反对协议，而是要求先证明互操作收益高于新增复杂度。

> 本文的 Pi 行为以 [官方说明](https://pi.dev) 为准；Adapter 行为以 [pi-mcp-adapter 源码](https://github.com/nicobailon/pi-mcp-adapter) commit `6c08147f` 和 [Pi Package 页面](https://pi.dev/packages/pi-mcp-adapter) 为基线。Adapter 是第三方 Package，不是 Pi 内置安全能力。

## 先判断缺的到底是什么

| 现状 | 应先选择 | 例子 |
| --- | --- | --- |
| 已有工具，只缺团队流程 | Skill | 发布前检查版本、测试、diff 和回滚条件 |
| 缺少一个 Pi 专用运行时能力 | Extension Tool | 受控读取内部索引、注册一个状态命令 |
| 已有稳定 CLI，单宿主使用 | CLI + Skill | 用 `gh`、`kubectl`、内部命令行完成任务 |
| 已有 MCP Server，要在多个宿主复用 | MCP Adapter | Jira、数据库、浏览器服务同时供多个 Agent 使用 |
| 需要 MCP resources、prompts、OAuth 或远程生命周期 | MCP Adapter | 不是简单命令包装能够覆盖的服务 |

“重复流程优先 Skill”并不表示 Skill 能替代外部系统连接。Skill 负责教模型如何做，MCP 负责提供它原本没有的连接能力。两者也可以组合：MCP 连接数据库，Skill 说明数据模型和查询约束。

## 为什么工具 schema 会消耗上下文

模型若要直接调用工具，通常需要看到：

- 工具名称和用途；
- 参数 JSON Schema；
- 必填项、枚举和字段描述；
- 可能的使用约束。

工具很少时，直接暴露最简单。工具数量增大后，问题不只是 token 数：相似名称和长 schema 还会增加选择错误，工具列表频繁变化也可能破坏 prompt cache 的稳定前缀。

不能脱离具体 tokenizer、模型、schema 和序列化格式引用一个统一数字。真正有意义的指标是：在你的工具集和任务分布上，直接暴露与按需发现分别消耗多少输入、增加几次调用、最终成功率怎样。

## pi-mcp-adapter 的两种工具表面

当前 `pi-mcp-adapter` 默认提供单个 `mcp` proxy tool。模型先搜索或描述工具，再通过代理执行。对少量高频工具，也可以配置 `directTools`，让它们像 `read`、`edit` 一样直接进入模型工具列表。

### Proxy 模式

```text
模型只看到 mcp proxy
  -> mcp(search="screenshot")
  -> 返回候选工具与参数说明
  -> mcp(tool="chrome_devtools_take_screenshot", args={...})
  -> Adapter 连接 Server 并转发调用
  -> 结果回到 Agent Loop
```

收益：常驻 schema 少，Server 可以懒连接，大型工具目录不必全部进入每轮请求。

代价：通常多一次发现调用；模型需要先搜索再构造参数；调试链路多一层；代理的搜索和命名规则也会影响成功率。

### Direct Tools 模式

```text
模型直接看到选定 MCP 工具
  -> 直接生成工具名和参数
  -> Adapter 转发调用
  -> 结果回到 Agent Loop
```

收益：调用路径短，模型直接获得完整 schema，适合少量稳定且高频的工具。

代价：每个工具都增加上下文，目录变化可能改变工具表面，Server 很大时会重新出现工具拥挤问题。

Adapter README 给出的经验估计是：单个 proxy tool 约两百 token，每个 direct tool 约 150 到 300 token。这些只能当设计提示，不能当你的成本结论。不同模型和 schema 必须实测。

## 安装前先看清 Package

在 2026-08-24 的核验基线中，Pi 市场展示的 `pi-mcp-adapter` 同时包含 Extension 和 Skill。它会以 Pi 进程权限运行，并管理 MCP 子进程、网络连接、配置和凭据路径。

先在 [Package 页面](https://pi.dev/packages/pi-mcp-adapter) 查看版本、manifest、依赖、仓库和许可证，再检查源码。确认后安装：

```bash
pi install npm:pi-mcp-adapter
```

对团队或生产环境，应安装审查过的具体版本，并记录升级验证。市场下载量不是安全证明。

## 一个最小的项目配置

Adapter 推荐使用项目级 `.mcp.json`。下面用固定版本的 stdio Server 展示结构，包名和版本仅是示例，实际接入前仍需独立审计：

```json
{
  "mcpServers": {
    "browser": {
      "command": "npx",
      "args": ["-y", "some-reviewed-mcp-server@1.2.3"],
      "lifecycle": "lazy",
      "directTools": ["take_screenshot"],
      "includeTools": ["take_screenshot", "get_page_text"]
    }
  }
}
```

这里的工程含义是：

- `lifecycle: "lazy"` 避免 Session 启动时立即拉起 Server；
- `directTools` 只直接暴露高频工具；
- `includeTools` 缩小可见面，不把整个 Server 目录交给模型；
- `npx -y` 会执行第三方包，固定版本仍不能替代源码与依赖审计。

Adapter 还支持用户级共享配置和 Pi 专属 override。多个配置层存在时，必须能回答最终 Server 定义来自哪个文件，避免同名配置覆盖后连接到意外 endpoint。

## 工具发现不是免费的

Proxy 模式把 schema token 换成了运行时工作：

1. 搜索索引必须能根据用户意图找到候选工具；
2. describe 结果必须足以让模型生成合法参数；
3. 元数据缓存需要处理首次缺失和 Server list change；
4. 断线重连后，工具表面与 Session 上下文要保持一致；
5. 失败结果要区分未找到、未连接、需认证、超时和执行错误。

如果搜索召回率低，模型可能反复查询或放弃正确工具。节省首轮 token 不一定降低总成本，必须连同调用轮数、延迟和成功率一起看。

## 生命周期是引入 MCP 后新增的责任

一个 MCP Server 不只是工具 schema 文件。宿主还要管理：

- stdio 子进程、HTTP 或其他 transport；
- 懒连接、保活、重连和 shutdown；
- `tools/list` 更新与 Session 内工具同步；
- OAuth、静态 Token 和 credential store；
- 每次请求的超时、取消与大输出；
- Server 日志是否泄露参数、结果或凭据。

Demo 能连接只证明 happy path。生产可用至少还要模拟 Server 启动失败、运行中退出、schema 变化、认证过期和返回超大结果。

## 安全边界不能交给工具描述

MCP tool 的 description 可以写“只读”，但真正权限由 Server 和外部系统决定。Adapter 的审批功能也需要正确配置：

- 高风险工具应使用 allowlist 或显式 approval；
- headless 模式没有人确认时应 fail closed；
- Token 不应写入 `.mcp.json`、Session 或仓库；
- Server 子进程继承哪些环境变量必须可审计；
- 远程 endpoint、OAuth redirect 和证书验证不能模糊处理；
- 大结果应裁剪或落到受控临时文件，避免把原始数据全部塞回模型。

Adapter 能提供门禁和输出保护，但它仍运行在 Pi 进程中。若 MCP Server 能删除生产数据，最强边界应在服务端账号权限、网络策略和审批系统中，而不是只靠本地 Prompt 或扩展。

## Direct 与 Proxy 的对照实验

不要比较两个不同 Server。固定同一个模型、任务、Server 和工具集，只改变工具暴露方式。

### 实验任务

选择 10 到 20 个候选工具，其中只有两个与任务相关：

```text
查找指定页面的标题并保存截图。不得调用写入外部系统的工具。
```

### 记录指标

| 指标 | Proxy | Direct subset | Direct all |
| --- | --- | --- | --- |
| 首轮 input token |  |  |  |
| 发现调用次数 |  |  |  |
| 参数校验失败次数 |  |  |  |
| 总模型请求轮数 |  |  |  |
| 首次有效结果延迟 |  |  |  |
| 最终任务成功率 |  |  |  |
| prompt cache 命中情况 |  |  |  |

每种配置重复多次，并保留失败轨迹。若 Proxy 节省输入却显著降低成功率，选定少量 direct tools 可能更合适；若工具目录巨大且低频，Proxy 更有优势。

## 最小验收清单

- [ ] 能说明为什么这里需要 MCP，而不是 Skill、CLI 或 Extension。
- [ ] Package、Server 和依赖都固定到已审查版本。
- [ ] 配置来源、覆盖顺序和实际 endpoint 可追踪。
- [ ] 高风险工具默认不静默执行。
- [ ] OAuth、Token、环境变量和日志不进入仓库或 Session。
- [ ] Server 崩溃、超时、取消和 schema 变化有测试。
- [ ] 大输出有边界，并保留获取原始结果的受控路径。
- [ ] 移除 Adapter 后，业务流程说明仍然存在。

## 什么时候值得接 MCP

优先接入的场景：

- 组织已经维护 MCP Server，需要被多个 Harness 使用；
- 需要 MCP 的 resources、prompts、OAuth 或远程 transport；
- 工具生命周期和协议兼容比一个简单 CLI 更重要；
- 团队愿意承担连接、认证、监控和升级成本。

继续使用 Skill、CLI 或 Extension 的场景：

- 问题只是模型不知道步骤；
- 能力只服务 Pi，接口很窄且本地可控；
- 已有稳定、可脚本化、帮助文本清楚的 CLI；
- MCP Server 只是给一个命令套了高复杂度外壳。

## 小结

- Pi 不内置 MCP 是明确的产品选择，不代表无法连接 MCP 生态。
- Skill 解决流程知识，Extension 解决宿主能力，MCP 解决跨宿主协议互操作。
- Proxy 模式节省常驻 schema，却增加发现和调试步骤；direct tools 路径短，却增加上下文成本。
- 任何 token 数都必须在固定模型、工具集和任务下测量。
- 引入 MCP 后，生命周期、认证、输出边界和服务端权限都成为系统责任。

---

下一篇建议继续看：[安全模型：Project Trust、权限门禁与系统隔离](../05-security-model/index.html)
