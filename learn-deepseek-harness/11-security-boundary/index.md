---
layout: default
title: 安全边界：把信任放到模型之外
description: 用审批、沙箱和凭据策略约束 Agent 的真实副作用
eyebrow: DeepSeek Harness / 11
---

# 安全边界：把信任放到模型之外

模型会犯错，Prompt 会漂移，插件也可能有缺陷。只要系统能写文件、执行 Shell 或访问网络，就不能把“模型理解了安全规则”当成安全机制。真正的边界必须由运行时强制，而且要能在模型不合作时仍然成立。

## 设计理念：策略平面独立于决策平面

模型可以提出动作，策略平面决定动作是否可执行。Approval、Sandbox、凭据和审计属于策略平面，它们不应由模型自己关闭，也不应隐藏在某个工具实现的分支里。

| 机制 | 保护什么 | 失败时的原则 |
| --- | --- | --- |
| Approval | 高风险动作的人或系统确认 | 服务不可用也不能默认放行 |
| Sandbox | 进程、文件和网络的执行边界 | 策略解析失败就拒绝执行 |
| Credentials | 模型和插件可见的秘密范围 | 不进入上下文、日志或代码绑定 |
| Audit | 谁在何时请求和决定了什么 | 拒绝、取消和错误也必须记录 |

## 为什么要 fail closed

安全策略最危险的失败不是报错，而是静默退回更宽的权限。`danger-full-access` 之类的旁路应该是显式选择，并被记录为运行模式；受限执行失败时不能悄悄改用宿主进程。

Approval 也不是一个弹窗。请求必须绑定工具、参数摘要、操作者、有效期和决定来源；重试同一动作时，不能默认复用上一次的允许。这样审批才是可审计协议，而不是 UI 装饰。

## 实测攻击面：间接提示注入

腾讯 AI-Infra-Guard 团队在 2026 年 8 月发布的系统性安全研究（[arxiv 2608.16393](https://arxiv.org/abs/2608.16393)）提供了量化证据：

| 指标 | 数据 |
| --- | --- |
| 受控执行次数 | 14,560 |
| 间接内容通道 | 16 种（文件内容、剪贴板、搜索结果等） |
| 攻击方法 | 12 种 |
| 最高攻击成功率（文件模式，隐藏 Unicode） | **25.5%** |
| 最高攻击成功率（文本模式，fake-completion） | **17.0%** |

这组数据说明：即使 DSH 在设计上把策略与决策分开，模型仍可能在间接内容中被诱导执行恶意指令。fail-closed 不是保守，而是在攻击成功率可达四分之一时的基本底线。

值得注意的是，该研究基于 rc 版本，正式发布后攻击面可能变化。但它验证了一条规则：安全策略的有效性不能只看设计文档，必须有对抗性测试。

## 设计取舍

外部策略会增加等待和配置成本，也可能让 Agent 看起来”不够聪明”。但它把信任从概率性输出转移到可以测试、撤销和审计的组件上，这是生产系统必须付出的成本。

参考 [Approval](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.1.0-rc.8/docs/subsystems/approval.zh.md)、[Sandbox](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.1.0-rc.8/docs/subsystems/sandbox.zh.md) 与 [Indirect Prompt Injection Security Study](https://arxiv.org/abs/2608.16393)。

下一篇建议继续看：[Subagent 编排：扩展能力而不是复制 Loop](../12-subagent-orchestration/index.html)
