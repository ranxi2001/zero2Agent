---
layout: default
title: Profile、Bundle 与 Patch：运行时如何组装
description: 解释 DeepSeek Harness 的配置来源、覆盖顺序和可复现实验方法
eyebrow: DeepSeek Harness / 03
---

# Profile、Bundle 与 Patch：运行时如何组装

当你看到一个 DSH 实例时，先不要假设它是固定产品。它是多个 Bundle 加上多个 Patch 组合出的 Profile。理解组合顺序，才能解释为什么同一条命令在不同机器上行为不同。

## 当前组装顺序

官方架构文档给出的概念顺序是：

```text
Bundles -> Profile cordis.patch.yml -> Harness Home patch -> CLI --patch overlay
```

Bundle 声明 `dsh.bundle`，Profile 声明 `dsh.profile`。Profile 负责选择和排序 Bundle，Patch 负责覆盖配置。后者不是自动深合并的魔法：数组、对象和标量的合并规则必须以实现和 schema 为准。

## 先 dump，再猜

调试配置时使用官方提供的可观测入口：

```bash
dsh --profile web --dump-config
```

把输出保存为构建产物的一部分，能够回答“当前到底启用了哪些插件、工具和策略”。部署环境还应记录 Profile 名称、版本、Patch 摘要和运行时 commit，而不是只记录一个产品名。

## 一个常见误区

不要把教学项目里的 `config.ts` 直接映射成 DSH 的 Profile。教学代码通常把默认值、依赖注入和启动顺序写在同一个文件；生产 Harness 需要把能力拆成 Bundle，并为每个覆盖点建立 schema、测试和回滚策略。

参考：[Architecture](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.1.0-rc.8/docs/architecture.zh.md)、[Configuration](https://github.com/deepseek-ai/deepseek-harness/tree/dsh-v0.1.0-rc.8/docs)。若文档与本地 `dsh --dump-config` 冲突，以当前构建输出和对应 commit 为准。
