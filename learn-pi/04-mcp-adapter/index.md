---
layout: default
title: "pi-mcp-adapter：MCP 工具的 Token 经济学"
description: 把 MCP 工具 token 开销从万级降到百级的代理模式
eyebrow: Pi / 04
---

# pi-mcp-adapter：MCP 工具的 Token 经济学

## 为什么这个问题值得关注

MCP（Model Context Protocol）让 Agent 可以连接外部工具服务器。但有一个被低估的成本：每个 MCP 工具的定义（名称、描述、参数 schema）需要作为上下文发送给模型。根据 Anthropic 文档的数据，典型 5 个 MCP Server 的工具定义大约消耗 55,000 token。

这不是理论问题。如果你用 Claude 3.5 Sonnet，55k input token 的成本是每次请求约 $0.17。更重要的是，这 55k token 占据了宝贵的上下文窗口空间——留给实际任务描述和对话历史的空间就少了。

pi-mcp-adapter 针对这个问题提出了一个设计：用单个代理工具替代所有 MCP 工具的显式定义，把 token 开销从 10,000+/server 降到约 200 token。

仓库：[nicobailon/pi-mcp-adapter](https://github.com/nicobailon/pi-mcp-adapter)

安装方式：`pi install npm:pi-mcp-adapter`

## 问题的量化

每个 MCP 工具在发送给模型时包含：

- 工具名称：~10 token
- 描述文本：~50-200 token
- 参数 JSON Schema：~100-500 token

一个典型的 MCP Server 提供 5-20 个工具。以 filesystem server 为例，它提供 read_file、write_file、list_directory 等约 11 个工具，每个工具的定义加起来大约 2,000 token。

当你连接 5 个 MCP Server、总共 50 个工具时：

| 方案 | 工具定义 token | 占 200k 窗口比例 |
| --- | --- | --- |
| 原生方式（每个工具独立定义） | ~55,000 | 27.5% |
| pi-mcp-adapter（单代理工具） | ~200 | 0.1% |

27.5% 的上下文窗口被工具定义占据，这是一个严重的效率问题。

## 单代理工具模式的工作原理

pi-mcp-adapter 的核心思路：不把每个 MCP 工具作为独立工具注册给模型，而是注册一个"代理工具"。模型只看到这一个工具，需要调用 MCP 能力时通过它中转。

工作流程：

```
模型看到的工具列表：
  - mcp_proxy（description: "调用 MCP 工具"）

模型决定使用 MCP 能力：
  1. 模型调用 mcp_proxy，传入 server 名和工具名
  2. pi-mcp-adapter 查找对应的 MCP Server
  3. 转发调用到实际的 MCP Server
  4. 返回结果给模型
```

模型需要知道有哪些 MCP 工具可用，但这个信息不通过工具定义传递，而是通过系统 prompt 或按需查询。pi-mcp-adapter 可以在系统 prompt 中附加一份工具列表摘要（只有名称，不含完整 schema），或者让模型先调用一个"列出可用工具"的子命令。

## 命名规则与管理命令

通过 pi-mcp-adapter 调用的工具遵循命名规则：`mcp_{server}_{tool}`。比如连接了名为 `filesystem` 的 server，调用其 `read_file` 工具时，模型传入 `mcp_filesystem_read_file`。

pi-mcp-tools 扩展（通常和 adapter 一起安装）提供管理命令：

| 命令 | 作用 |
| --- | --- |
| `/mcp-status` | 查看所有已连接 MCP Server 的状态 |
| `/mcp-reconnect` | 重新连接断开的 Server |
| `/mcp-toggle` | 启用/禁用特定 Server |
| `/mcp-list` | 列出所有可用的 MCP 工具 |
| `/mcp-tools` | 查看特定 Server 提供的工具详情 |

## 代价：省了 token，丢了什么

单代理工具模式不是没有代价的。

### 模型推理负担增加

原生方式下，模型直接看到所有工具的完整定义（名称、描述、参数 schema），可以一步到位选择正确的工具并填入参数。代理模式下，模型需要：

1. 记住（或查询）有哪些 MCP 工具可用
2. 决定使用哪个工具
3. 正确拼出工具的全限定名（`mcp_{server}_{tool}`）
4. 在没有 schema 提示的情况下构造参数

第 4 步最容易出错。没有参数 schema 作为约束，模型更容易产生格式错误的参数。

### 调试更间接

原生方式下，工具调用的日志直接显示调了哪个工具、传了什么参数。代理模式下，所有调用都经过 mcp_proxy，需要展开一层才能看到实际调用。

### 工具选择准确率

Anthropic 的研究表明，模型在工具选择时高度依赖工具描述。当描述被压缩或省略时，选择准确率会下降。代理模式本质上是用推理成本换取 token 成本——模型需要更多思考来补偿信息缺失。

## 什么时候该用代理模式

适合代理模式的场景：

- MCP Server 数量多（5+），工具总数多（30+），token 开销已经影响了上下文空间
- 工具使用频率低——大部分对话不需要 MCP 工具，不值得每次都付 token 成本
- 模型能力强（Claude 3.5 Sonnet / GPT-4o 级别），能处理间接工具选择

不适合的场景：

- MCP Server 少（1-2 个），工具少（10 个以下），原生方式的 token 开销可接受
- 工具使用频率高——每次对话都大量调用 MCP 工具，代理模式的额外推理反而增加延迟
- 对工具调用准确率要求高——金融、医疗等不容错的场景

## 与 Claude Code 原生 MCP 支持的对比

Claude Code 目前采用原生方式：每个 MCP 工具作为独立工具注册。这意味着：

- 模型可以直接看到所有工具的完整定义
- 工具选择准确率高
- token 开销随 MCP Server 数量线性增长
- 没有内置的"代理模式"选项

Claude Code 管理 token 压力的方式不是压缩工具定义，而是限制同时激活的 MCP Server 数量，以及通过更大的上下文窗口（200k token）来容纳工具定义。

这是两种不同的哲学：

- Pi：压缩信息密度，让更少的 token 承载更多工具
- Claude Code：扩大容量，让窗口足够放下所有工具定义

两者各有适用边界。当模型窗口足够大且工具数量可控时，原生方式更可靠。当工具数量爆炸或窗口有限时，代理模式提供了实用的退路。

## 未来演进方向

随着模型上下文窗口持续增长（已经有 1M+ token 窗口的模型），工具定义的 token 压力会缓解。但两个因素让代理模式仍然有价值：

1. **成本**：即使窗口装得下，55k token 的 input 成本仍然存在，按量计费时这是真实开支
2. **注意力稀释**：模型在超长上下文中的注意力分配不均匀，工具太多可能导致选择质量下降

最终方案可能是混合模式：高频工具原生注册，低频工具走代理模式。pi-mcp-adapter 的价值不在于它是唯一正确的方案，而在于它量化了问题并提供了一种可测试的选择。

## 小结

pi-mcp-adapter 解决的是一个算术问题：MCP 工具定义消耗太多 token，而 token 既是成本也是稀缺资源。单代理工具模式把这个开销压缩了两个数量级。代价是模型需要额外推理来补偿信息缺失，调试变得更间接，工具选择准确率可能下降。

这是一个典型的工程 tradeoff：没有免费的抽象。省下的 token 会以其他形式的成本回来——可能是准确率，可能是延迟，可能是调试时间。理解这个 tradeoff 的量化边界，比选择"用还是不用"更重要。

---

下一篇：[安全模型深入：容器化隔离的实际边界](../05-security-model/index.html)
