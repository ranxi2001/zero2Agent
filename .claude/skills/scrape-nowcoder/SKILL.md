---
name: scrape-nowcoder
description: 基于 CDP 原生 WebSocket 抓取牛客网面经文章。当用户说"抓牛客"、"爬牛客面经"、"nowcoder 抓取"、"抓取面经列表"时触发。复用用户已有 Chrome profile（含登录状态），支持列表页 + 详情页全文抓取，输出 Markdown。
---

# scrape-nowcoder：牛客面经 CDP 抓取

基于 Chrome DevTools Protocol 原生 WebSocket，零依赖。复用用户现有 Chrome profile，无需额外登录。

## 工作方式

1. 关闭当前 Chrome（脚本会询问确认）
2. 用你原有的 Chrome profile 重新启动（headless），复用已有登录状态
3. 抓取完成后关闭 Chrome，你可以正常重新打开

## 前置条件

- Node.js ≥ 22（需要原生 WebSocket 和 fetch）
- Google Chrome（macOS）
- 已在 Chrome 中登录牛客网

## 用法

```bash
node .claude/skills/scrape-nowcoder/scrape.mjs [选项]
```

### 选项

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--pages <n>` | 1 | 抓取列表页数 |
| `--keyword <kw>` | (空) | 按关键词筛选标题（如 "AI"、"大模型"） |
| `--out <dir>` | `./nowcoder-output` | 输出目录 |
| `--port <port>` | 9222 | Chrome 调试端口 |
| `--no-headless` / `--visible` | headless | 显示浏览器窗口，观察抓取过程 |
| `--delay <ms>` | 2000 | 请求间隔，避免触发反爬 |

### 常用示例

```bash
# 默认抓 1 页面经
node .claude/skills/scrape-nowcoder/scrape.mjs

# 抓 3 页，只要 AI 相关
node .claude/skills/scrape-nowcoder/scrape.mjs --pages 3 --keyword "AI"

# 可视化调试
node .claude/skills/scrape-nowcoder/scrape.mjs --visible --pages 1
```

## 输出结构

```
nowcoder-output/
├── index.md          # 目录索引
├── all-in-one.md     # 全部文章合并
├── 01-标题.md        # 单篇文章
├── 02-标题.md
└── ...
```

## 执行流程

当用户触发此 skill 时：

### 1. 确认参数

询问用户：
- 抓几页？（默认 1）
- 关键词筛选？（如 "AI"、"大模型"、"后端"）
- 输出目录？

### 2. 提醒用户

告知用户：脚本需要临时关闭 Chrome，抓完后可以正常重新打开。

### 3. 执行抓取

```bash
node .claude/skills/scrape-nowcoder/scrape.mjs --pages <n> --keyword "<kw>" --out <dir>
```

注意：脚本会在终端中询问用户确认关闭 Chrome，这是交互式的。如果用户已经手动关闭了 Chrome，可以直接输入 y。

### 4. 检查输出

读取 `index.md` 汇报抓取结果。

### 5. 后续操作（可选）

抓取完成后询问用户是否需要：
- 使用 `classify-interview-questions` 将面试题分发到已有维度文章
- 筛选特定文章深入处理

## 注意事项

- 脚本复用 `~/Library/Application Support/Google/Chrome` profile
- 需要用户在 Chrome 中已登录牛客网
- 默认 2 秒间隔，不建议降低以免触发反爬
- headless 模式下浏览器不可见但功能完整
