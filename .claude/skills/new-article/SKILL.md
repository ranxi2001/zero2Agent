---
name: new-article
description: 在 zero2Agent 项目中创建新的学习文章。当用户说"写一篇新文章"、"创建文章"、"新建文章"、"在某模块下添加一篇关于X的文章"、"帮我起草一篇讲XX的内容"时触发。适用于在 learn-agent-basic、learn-langgraph、learn-claude-code、learn-frameworks、final-project 任意模块下新建内容。即使用户没有明确说"文章"，只要涉及给 zero2Agent 项目增加教学内容，也应当触发此技能。
---

# new-article：创建新文章

本技能用于在 zero2Agent 项目中创建符合项目风格的新学习文章。

## 项目约定

**目录结构**
```
{module-dir}/
└── {NN}-{slug}/
    └── index.md
```
- `{NN}` 是两位数编号，如 `01`、`09`、`10`
- `{slug}` 是英文小写、用连字符连接，如 `tool-calling-basics`
- 每篇文章独占一个子目录，主文件统一命名为 `index.md`

**已有模块目录**
| 模块 | 目录 | 已有文章数 |
|------|------|-----------|
| Agent Basic | `learn-agent-basic/` | 08 篇 (01–08) |
| LangGraph | `learn-langgraph/` | 0 篇 (占位符) |
| Claude Code | `learn-claude-code/` | 0 篇 (占位符) |
| Frameworks | `learn-frameworks/` | 0 篇 (占位符) |
| Final Project | `final-project/` | 0 篇 (占位符) |

**Frontmatter 格式**
```yaml
---
layout: default
title: {文章标题（中文）}
description: {一句话描述，10–25 字}
eyebrow: {Module Name} / {NN}
---
```
eyebrow 示例：`Agent Basic / 09`、`LangGraph / 01`

## 文章写作风格（必须遵守）

zero2Agent 的读者是懂代码、懂深度学习基础的开发者，但对 Agent 工程实践还不熟悉。写作时：

1. **问题优先**：先说"为什么要关心这个问题"，再讲概念和方案。不要一上来就定义。
2. **工程视角**：解释概念时，要说清楚它在系统里扮演什么角色，而不是给出教科书定义。
3. **避免框架崇拜**：不要把某个框架讲成"最佳答案"，要讲清楚它解决什么问题、有什么代价。
4. **暴露真实复杂度**：要主动提到"这里容易踩坑"、"Demo 能跑但生产不行"。
5. **精炼、不废话**：不加不必要的修饰语，每个段落有实际内容。
6. **使用代码块**：需要展示执行流程时优先用 ` ```text ` 代码块而不是大段描述。
7. **文末导航**：在最后用 `下一篇建议继续看：` + 链接收尾（或说明尚无后续）。

## 文章结构模板

```markdown
---
layout: default
title: {标题}
description: {一句话描述}
eyebrow: {Module} / {NN}
---

# {标题}

{开篇：1–3 句话，说明这个话题在实际工程中为什么重要 / 常见误解是什么}

## {核心概念或问题拆解}

{正文……}

## {深入一层：机制 / 设计原则 / 常见坑}

{正文……}

## {实践建议 或 典型误区}

{正文……}

## 小结

{用 3–5 个 bullet 提炼核心观点，不重复正文措辞}

下一篇建议继续看：

- [{下一篇标题}]({相对路径}/index.html)
```

## 执行步骤

1. **收集信息**：如果用户没有提供以下信息，先确认：
   - 目标模块（哪个目录）
   - 文章编号（`NN`）
   - 文章主题和标题
   - 是否需要参考已有文章风格（默认：是）

2. **创建目录和文件**：
   ```bash
   mkdir -p {module-dir}/{NN}-{slug}/
   ```
   然后写入 `index.md`。

3. **更新模块 index.md**：在对应模块的 `index.md` 中，把新文章加入"建议阅读顺序"和文章列表表格。

4. **输出确认**：告知用户创建了哪个文件，以及文章在模块中的位置。
