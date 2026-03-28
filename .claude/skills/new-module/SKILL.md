---
name: new-module
description: 在 zero2Agent 项目中创建新的学习模块。当用户说"新建模块"、"添加模块"、"创建一个新的学习章节"、"我想增加一个关于X的模块"时触发。负责创建模块目录结构、index.md，并同步更新主页 index.html 和 _layouts/default.html 的导航。即使用户只是说"我想增加一个讲XX的章节"，也应当触发此技能。
---

# new-module：创建新学习模块

本技能用于在 zero2Agent 项目中新建一个学习模块，并同步更新所有相关导航。

## 现有模块结构（参考）

```
zero2Agent/
├── learn-agent-basic/     # Module 01 — 已完成 8 篇文章
├── learn-langgraph/       # Module 02 — 占位符
├── learn-claude-code/     # Module 03 — 占位符
├── learn-frameworks/      # Module 04 — 占位符
└── final-project/         # Module 05 — 占位符
```

每个模块是根目录下的一个子目录，包含 `index.md` 作为模块入口。

## 模块 index.md 结构

```markdown
---
layout: default
title: {module-dir-name}
description: {模块一句话描述，15–30 字}
eyebrow: Module {NN}
---

# {module-dir-name}

{2–3 句话：这个模块解决什么问题，适合什么阶段的读者}

## 这部分的主线

{3–5 个 bullet，说明核心学习路径}

## 建议阅读顺序

{初始为空，随文章增加而补充}

## 后续可补充的文章

- [ ] {建议文章1}
- [ ] {建议文章2}
- [ ] {建议文章3}
```

## 需要同步更新的位置

创建新模块时，必须更新以下 3 处：

### 1. `_layouts/default.html` — 顶部导航
在 `<nav class="doc-nav">` 中添加链接：
```html
<a href="{module-dir}/index.html">{显示名称}</a>
```

### 2. `_layouts/default.html` — 侧边栏
在 `<aside class="doc-sidebar">` 中添加链接（按编号顺序）：
```html
<a href="{module-dir}/index.html">{NN}. {module-dir-name}</a>
```

### 3. `index.html` 主页 — 模块卡片
在主页的模块列表区域添加新卡片。参考现有卡片的 HTML 结构，保持格式一致。

## 执行步骤

1. **收集信息**：如果用户没有提供，先确认：
   - 模块编号（`NN`，当前最大为 05）
   - 模块目录名（如 `learn-mcp`）
   - 模块显示名（如 `MCP`）
   - 模块描述（一句话）
   - 模块主线（预期涵盖哪些主题）

2. **创建目录和文件**：
   ```bash
   mkdir -p {module-dir}/
   ```
   写入 `{module-dir}/index.md`。

3. **更新 `_layouts/default.html`**：
   - 在 `<nav class="doc-nav">` 中添加导航链接
   - 在 `<aside class="doc-sidebar">` 中添加侧边栏链接

4. **更新 `index.html`**：在主页模块卡片区域追加新模块的卡片 HTML。

5. **输出确认**：列出创建/修改的所有文件，说明模块编号和导航位置。
