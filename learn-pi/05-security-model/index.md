---
layout: default
title: "安全模型：Project Trust、权限门禁与系统隔离"
description: 用分层威胁模型理解 Pi 无内置沙箱的真实边界
eyebrow: Pi / 05
---

# 安全模型：Project Trust、权限门禁与系统隔离

## 为什么这个问题值得关注

Pi 的 `read`、`write`、`edit`、`bash` 和 Extension 默认继承当前用户权限。模型说“我不会执行危险操作”，不能限制文件系统和网络；界面显示“项目已信任”，也不代表代码运行在沙箱里。

安全设计的第一步不是选 Docker 命令，而是分清每一层到底阻止什么。把 project trust、工具审批和系统隔离混成一个“安全模式”，会让边界看起来比实际更强。

> 本文以 Pi [Security](https://pi.dev/docs/latest/security) 与 [Containerization](https://pi.dev/docs/latest/containerization) 文档、官方源码 commit [`a470b121`](https://github.com/badlogic/pi-mono/tree/a470b121bf683b4c2b9fc0b3a7c807de7e0cfe9c) 为事实基线。

## 先建立威胁模型

在讨论控制措施前，至少列出四类来源：

| 来源 | 可能带来什么 | 典型入口 |
| --- | --- | --- |
| 模型错误 | 错删文件、错误命令、越界修改 | tool call、bash |
| Prompt injection | 诱导读取凭据、执行外部指令 | README、代码注释、网页、工具输出 |
| 恶意项目资源 | 启动时加载代码或改变设置 | `.pi/extensions`、`.pi/settings.json` |
| 恶意供应链 | 任意代码、依赖脚本、数据外传 | Pi Package、npm 依赖、MCP Server |

再列出需要保护的资产：源码、Git 历史、SSH 与云凭据、浏览器会话、生产 API、内网服务、宿主进程和远端数据。

若不知道攻击来源和资产，所谓“开启确认”或“放进容器”都无法证明覆盖了主要风险。

## 四层边界分别负责什么

### 第一层：Prompt 与项目说明

`AGENTS.md`、Skill 和系统 Prompt 能表达流程、禁止事项和验证要求。它们帮助模型做出更好的选择，但只是输入，不是执行权限。

适合：告诉 Agent 先读文件再编辑、不得自动发布、必须运行测试。

不适合：保证 `.env` 永远不能读取，或保证生产 API 永远不能调用。

### 第二层：Project Trust

Project trust 控制 Pi 是否加载项目级高影响资源：

- `.pi/settings.json`；
- `.pi/extensions`、`.pi/skills`、`.pi/prompts`、`.pi/themes`；
- `.pi/SYSTEM.md`、`.pi/APPEND_SYSTEM.md`；
- 项目或祖先目录中的 `.agents/skills`；
- 项目 settings 声明但本地缺失的 Package。

它解决的是“进入陌生目录时，是否让仓库立刻改变 Pi 的设置或运行代码”。它不限制已经加载的代码能访问什么，也不阻止模型调用内置工具。

一个容易忽略的事实是：`AGENTS.md`、`CLAUDE.md` 等 context 文件默认会在 trust 之前加载，除非关闭 context loading。Project trust 不是 Prompt injection 防火墙。

### 第三层：工具门禁与运行时策略

Extension 可以监听 `tool_call`，按工具名和参数阻止、确认或记录操作。例如：

- 禁止写入 `.env`、`.git/` 和凭据目录；
- `rm -rf`、`sudo` 或发布命令要求人工确认；
- headless 模式没有 UI 时默认拒绝；
- MCP 高风险工具只允许本 Session 一次。

这一层适合表达“允许读，写入要问”“测试可自动跑，发布必须人工批准”。但 Extension 和工具都运行在 Pi 进程权限域中，它不是强隔离。

### 第四层：操作系统和远端权限

容器、虚拟机、低权限账号、文件挂载、网络策略和服务端 IAM 决定最坏影响范围。这一层才真正限制：

- 能看到和写入哪些文件；
- 能启动哪些进程；
- 能连接哪些网络目标；
- 能获得哪些凭据；
- 远端账号能读取或修改哪些数据。

强边界应尽量靠近资产。例如即使本地 Extension 拦截了 `deploy`，生产账号仍应使用最小权限和独立审批。

## Project Trust 的具体行为

交互模式遇到未决项目时，默认 `defaultProjectTrust: "ask"` 会询问用户，决定记录在 `~/.pi/agent/trust.json`，并按 canonical path 匹配当前目录或父目录。

非交互模式不会弹窗：

| 模式 | 没有已保存决定且默认是 `ask` | 风险点 |
| --- | --- | --- |
| Interactive | 展示 trust 提示 | 用户可能未经审查直接同意 |
| `-p` | 跳过需要 trust 的项目资源 | 任务行为可能与交互模式不同 |
| `--mode json` | 跳过需要 trust 的项目资源 | CI 可能缺少项目 Extension 或 Skill |
| `--mode rpc` | 跳过需要 trust 的项目资源 | 外部宿主必须显式管理决定 |

`--approve` 与 `--no-approve` 可以覆盖单次运行，但自动化不应为了“让功能工作”就无条件 `--approve`。正确做法是先审查资源，再把 trust 决定当作部署配置。

## Pi 的实际权限范围

默认情况下，下列对象都可能触达当前用户能触达的资源：

- 内置文件与 bash 工具；
- 用户和项目 Extension；
- Package 中的 TypeScript 与依赖；
- Skill 引导模型运行的脚本；
- Language Server、测试、构建和其他子进程；
- MCP stdio Server 及其继承的环境变量。

“只让模型用 read”只能缩小模型直接可见的工具。如果某个已加载 Extension 自己使用 `node:fs` 或 `child_process`，仍然可以访问系统。因此工具 allowlist 与代码供应链审查是两个不同问题。

## 官方提供的三种隔离模式

| 模式 | 隔离对象 | 适合场景 | 主要限制 |
| --- | --- | --- | --- |
| Gondolin Extension | 内置工具与 `!` 命令进入 micro-VM | 本机交互，同时把认证留在宿主 | 其他自定义 Extension 仍可能在宿主运行 |
| Plain Docker | 整个 Pi 进程进入容器 | 简单、可复制的本地或 CI 环境 | bind mount 仍能修改宿主文件，API key 进入容器 |
| OpenShell | 整个 Pi 进入策略控制沙箱 | 需要文件、进程、网络和凭据策略 | 需要 gateway 与额外平台能力 |

这三种模式不是安全等级排名。选择取决于认证放哪里、项目文件如何进入、网络怎样限制，以及 Extension 在哪个执行世界运行。

## 一个更收敛的 Docker 起点

下面示例在官方 Plain Docker 模式上增加非 root 用户、只读根文件系统、能力删除和资源限制。它仍然把当前仓库以读写方式挂载，因此容器内写操作会直接改变宿主仓库。

`Dockerfile.pi`：

```dockerfile
FROM node:24-bookworm-slim

RUN apt-get update \
  && apt-get install -y --no-install-recommends bash ca-certificates git ripgrep \
  && rm -rf /var/lib/apt/lists/* \
  && npm install -g --ignore-scripts @earendil-works/pi-coding-agent \
  && useradd --create-home --uid 10001 agent \
  && install -d -o agent -g agent /home/agent/.pi/agent

WORKDIR /workspace
USER agent
ENTRYPOINT ["pi"]
```

构建和运行：

```bash
docker build -t pi-sandbox -f Dockerfile.pi .

docker run --rm -it \
  --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=256m \
  --cap-drop ALL \
  --security-opt no-new-privileges \
  --memory 2g \
  --pids-limit 256 \
  -e ANTHROPIC_API_KEY \
  -v "$PWD:/workspace:rw" \
  -v pi-agent-home:/home/agent/.pi/agent \
  pi-sandbox
```

不要机械复制这份命令到生产环境。需要继续回答：

- Provider endpoint 需要哪些出站网络，是否能只放行这些域名？
- API key 能否换成短期凭据或由网关注入？
- 项目是否必须 bind mount，还是可以复制进容器后再人工导出 diff？
- 测试是否需要数据库、Docker socket 或内网服务？
- Session volume 中是否允许长期保存工具结果和 Prompt？

### 为什么 bind mount 仍然危险

`-v "$PWD:/workspace:rw"` 允许容器直接修改宿主当前目录。容器可以保护主目录和其他路径，却不能保护这个挂载内的文件。

高风险或无人值守任务可以改成：

1. 把仓库复制到隔离环境；
2. 在隔离副本上运行；
3. 导出 patch、构建产物和验证报告；
4. 人工审查后再应用到可信仓库。

## 容器最常见的配置失误

- 以 root 运行整个 Agent；
- 挂载整个主目录或 `~/.pi/agent`；
- 透传 SSH agent、云凭据或浏览器 profile；
- 挂载宿主 Docker socket；
- 默认允许访问全部内网和公网；
- 用长期生产 Token 运行测试任务；
- 把 Secret、工具参数或原始结果写进 Session 和日志；
- 认为容器内的 Extension 不需要继续审计。

Docker 是边界工具，不是自动生成正确策略的按钮。

## Gondolin 的边界容易看错

官方 Gondolin 示例让宿主上的 Pi 保留 Provider 认证，同时把 `read`、`write`、`edit`、`bash`、`grep`、`find`、`ls` 和 `!` 命令路由到 micro-VM。

这能减少凭据进入 VM 的需求，但要注意：其他自定义 Extension 默认仍在宿主 Pi 进程中运行。若某个 Extension 直接调用 Node.js 文件或进程 API，它可能绕过被替换的内置工具。

因此，工具路由隔离的安全审计要检查所有执行出口，而不只是默认工具列表。

## 一次故障实验比一份安全声明更有价值

在临时目录创建一个带项目 Extension 的仓库，并设计三个测试：

1. **Trust 测试**：未批准项目时启动 `pi -p`，确认项目 Extension 未加载。
2. **门禁测试**：批准后触发对 `.env` 的写入，确认 Extension 在交互和 headless 模式都按预期处理。
3. **隔离测试**：在容器中尝试读取未挂载目录、写根文件系统和访问不应开放的网络目标。

每次测试都记录：请求、实际 tool call、拒绝或错误结果、文件系统状态和日志位置。不要以模型回答“已阻止”作为验证结果。

## 上线前的安全检查顺序

1. **资产**：哪些源码、凭据、网络服务和远端数据需要保护？
2. **身份**：Pi、Extension、MCP Server 和子进程分别以什么账号运行？
3. **可见面**：哪些目录、环境变量、socket 和 endpoint 可访问？
4. **写入面**：哪些操作自动允许，哪些要求批准，哪些永远拒绝？
5. **供应链**：Package、npm 依赖、Skill 脚本和更新由谁审查？
6. **证据**：tool call/result、审批、Git diff 和远端操作怎样关联？
7. **恢复**：误写、会话损坏、凭据泄露和错误发布怎样回滚？

## 小结

- Prompt 提供行为指导，project trust 控制项目资源加载，工具门禁表达运行时策略，系统隔离限制最坏影响。
- Project trust 不是沙箱，也不会默认阻止 `AGENTS.md` 等 context 文件进入模型。
- Extension 能拦截 tool call，但与 Pi 共享进程权限，不能作为唯一强边界。
- Plain Docker、Gondolin 和 OpenShell 隔离对象不同，必须结合执行出口和凭据位置选择。
- 安全结论应由故障实验、文件状态和审计证据证明，而不是由模型自述证明。

---

下一篇建议继续看：[生态使用：发现、审计与退出策略](../06-ecosystem/index.html)
