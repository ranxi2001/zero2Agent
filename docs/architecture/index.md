---
layout: default
title: site-architecture
description: zero2Agent 静态站与内容组织方式
eyebrow: Notes
---

# Site Architecture

当前站点采用和 `zero2Leetcode` 同一路线的静态方案，但为了适配知识库项目做了简化和重组。

## 当前结构

| 层级 | 作用 |
| --- | --- |
| `index.html` | 首页展示和学习路线导航 |
| `_layouts/default.html` | Markdown 页面统一布局 |
| `assets/css/style.css` | 首页视觉与模块卡片样式 |
| `assets/css/docs.css` | Markdown 文档样式与代码高亮适配 |
| `learn-*` / `final-project` | 教程章节入口目录 |

## 设计原则

- 内容优先，样式服务内容
- 首页和文档页分离，避免互相污染
- Markdown 排版优先考虑长文阅读和代码块展示
- 后续新增章节时只需要补目录和 `index.md`
