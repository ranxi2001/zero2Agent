---
layout: default
title: Cordis 插件内核：服务、事件与生命周期
description: 从 apply、inject 和 ctx.effect 理解 DeepSeek Harness 的插件化运行时
eyebrow: DeepSeek Harness / 02
---

# Cordis 插件内核：服务、事件与生命周期

DeepSeek Harness 不是把所有能力写进一个巨型类，而是建立在 Cordis 的插件运行时上。插件通过 `apply(ctx)` 安装服务、监听事件或修改配置；主程序只依赖服务契约，不依赖具体实现。

## 三个基本动作

```ts
export function apply(ctx: Context) {
  ctx.inject(['sessions', 'events'])
  ctx.on('session/created', (session) => {
    ctx.logger.info('session created', session.id)
  })
  ctx.effect(() => {
    return () => ctx.logger.info('plugin disposed')
  })
}
```

- `apply` 是插件的安装入口，应该保持轻量、可重复初始化。
- `inject` 声明插件需要哪些服务；依赖缺失时应尽早失败，而不是运行到深处才出现空指针。
- `ctx.effect` 管理启动和销毁副作用，适合订阅、定时器、文件句柄等资源。

## 服务与事件不是一回事

服务是可调用的能力，例如 `ctx.sessions`、`ctx.tools`；事件是观察和编排边界，例如 `agent/request` 或 `tools/pre-execute`。事件监听器不应偷偷改变日志事实，改变执行结果要通过明确的 waterfall 或服务 API 完成。

Cordis 的 [插件教程](https://cordis.js.org/guide/plugin) 和官方 Harness 的 [能力接缝说明](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.1.0-rc.8/docs/capability-seams.zh.md) 是两份互补资料：前者讲内核生命周期，后者列出 DSH 的服务地图。

## 为什么这对调试重要

插件化把复杂度从主循环转移到组合层，但也引入了依赖顺序、生命周期和事件语义。排查问题时先回答三个问题：服务是谁注册的，事件在哪个阶段触发，销毁时是否释放了资源。不要只看最终的模型回复。
