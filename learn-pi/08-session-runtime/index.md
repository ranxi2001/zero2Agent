---
layout: default
title: Session Runtime：恢复、分支与压缩
description: 把会话当作可恢复的运行事实树
eyebrow: Pi / 08
---

# Session Runtime：恢复、分支与压缩

长任务真正困难的不是“保存聊天记录”，而是恢复到一个仍可继续工作的状态：目标、工具事实、关键决策和未完成事项都不能丢，UI 日志却不必全部塞回模型。

## Transcript 与事件不是一回事

教材序章中的抽象事件名 `model_start`、`tool_start` 适合说明实时进度；它们不是官方 JSON 事件 API 的固定名称。用户消息、完整 assistant message 和配对的 tool result 才是下一轮推理需要的 canonical transcript。

```text
运行事件：显示“正在调用 read”
持久事实：call_1 请求 read，call_1 返回 README 内容
```

恢复时若只保存最终文本，会失去工具证据；若把所有 UI 增量都保存，又会制造重复和噪声。

## Session 是树，不只是列表

Pi 原生支持持久化、恢复、树形导航、fork、clone 与 compaction。树形结构允许在同一历史节点尝试两种方案，而不用覆盖原路径。

- **resume**：继续原会话与当前路径；
- **fork**：从历史 user message 创建新的 session 文件；
- **clone**：复制为独立会话再继续；
- **tree**：在当前 session tree 中查看并切换节点路径；
- **compact**：用更短表示重建可用上下文。

具体命令以 [官方 Sessions 与 Compaction 文档](https://pi.dev/docs/latest/sessions) 为准，避免把当前快捷方式写成永久 API。

## Compaction 不是删除旧消息

好的压缩至少保留：

- 用户目标与硬约束；
- 已确认的环境事实；
- 已修改文件和验证结果；
- 关键决策及放弃原因；
- 尚未完成的步骤与风险。

需要舍弃的是重复讨论、过长工具噪声和已经被更可靠证据替代的猜测。压缩后应做恢复测试：让 Agent 说明当前目标、已完成项、下一步和禁止事项，再与压缩前记录对照。

## 四个运行面

同一个 Pi runtime 可以通过不同入口使用：

- **Interactive/TUI**：人持续在环，适合探索和审批；
- **Print/JSON event stream**：适合脚本和 CI 消费结构化输出；
- **RPC**：由 Python、Go 或编辑器进程控制 Pi，处理请求、事件和中止；
- **SDK**：直接在应用中创建会话、配置工具并订阅事件。

入口变化后，生命周期责任也变化。外部宿主必须处理超时、取消、并发、进程崩溃、凭据和会话关闭，不能只把 TUI 命令包一层 subprocess。

## 一次可验证实操

1. 在临时仓库开始一个跨文件任务；
2. 完成第一步后退出并恢复；
3. 从同一节点 fork 两种实现；
4. 为工具输出制造一段大日志并触发 compaction；
5. 比较压缩前后目标、约束、文件状态和待办是否一致；
6. 导出事件，确认 tool call 与 tool result 可配对；
7. 人工检查 Git diff 和测试，不以 Agent 自述代替验证。

## 结论

会话工程的目标不是永久保存所有 token，而是保留可恢复、可分支、可审计的事实。把运行事件、持久 transcript 和模型上下文分开，长任务才不会依赖“模型还记得”。

---

返回模块首页：[Pi Coding Agent](../index.html)
