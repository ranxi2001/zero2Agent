---
name: scrape-nowcoder
description: 基于 CDP 原生 WebSocket 抓取牛客网面经文章。当用户说"抓牛客"、"爬牛客面经"、"nowcoder 抓取"、"抓取面经列表"时触发。通过 Chrome 调试端口直接连接已登录的浏览器会话，支持列表页 + 详情页全文抓取，输出 Markdown。
---

# scrape-nowcoder：牛客面经 CDP 抓取

基于 Chrome DevTools Protocol 原生 WebSocket，零依赖。直接连接已运行的 Chrome 调试端口，复用浏览器登录态。

## 工作方式

1. 连接 Chrome 调试端口（默认 9222）
2. 如果端口不可达，自动启动独立 Chrome 实例（`~/.chrome-nowcoder`）
3. 在已登录的浏览器中操作，抓取完成后 Chrome 保持运行

## 前置条件

- Node.js >= 22（需要原生 WebSocket 和 fetch）
- Google Chrome（macOS）以调试端口运行
- 已在该 Chrome 中登录牛客网

### 首次使用

启动带调试端口的 Chrome（会自动创建 `~/.chrome-nowcoder` profile）：

```bash
node .claude/skills/scrape-nowcoder/scrape.mjs --login
```

在弹出的 Chrome 中登录牛客，之后 cookie 永久保存。后续直接抓取即可。

## 用法

```bash
node .claude/skills/scrape-nowcoder/scrape.mjs [选项]
```

### 选项

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--login` | — | 首次使用：启动 Chrome 并打开登录页 |
| `--pages <n>` | 1 | 抓取列表页数（每页约 20 篇） |
| `--keyword <kw>` | (空) | 按关键词筛选标题（如 "AI"、"大模型"） |
| `--search <query>` | (空) | 搜索模式，在搜索页按关键词抓取面经 |
| `--out <dir>` | `.claude/skills/scrape-nowcoder/nowcoder-output` | 输出目录 |
| `--port <port>` | 9222 | Chrome 调试端口 |
| `--delay <ms>` | 2000 | 请求间隔，避免触发反爬 |

### 常用示例

```bash
# 抓 1 页面经（约 20 篇）
node .claude/skills/scrape-nowcoder/scrape.mjs

# 抓 3 页，只要 AI 相关
node .claude/skills/scrape-nowcoder/scrape.mjs --pages 3 --keyword "AI"

# 指定端口
node .claude/skills/scrape-nowcoder/scrape.mjs --port 9333
```

## 输出结构

```
.claude/skills/scrape-nowcoder/nowcoder-output/
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
- 关键词筛选？（如 "AI"、"大模型"、"Agent"）

### 2. 执行抓取

```bash
node .claude/skills/scrape-nowcoder/scrape.mjs --pages <n> --keyword "<kw>"
```

脚本自动连接 Chrome 调试端口，无需用户额外操作。

### 3. 检查输出

读取 `index.md` 汇报抓取结果。

### 4. 后续操作（可选）

抓取完成后询问用户是否需要：
- 使用 `classify-interview-questions` 将面试题分发到已有维度文章
- 筛选特定文章深入处理

## 注意事项

- Chrome 必须以 `--remote-debugging-port` 启动
- 首次需用 `--login` 在独立 Chrome 中登录牛客
- 登录后 cookie 永久保存在 `~/.chrome-nowcoder`，后续无需重复登录
- Chrome 实例保持运行，不会被脚本关闭
- 默认 2 秒间隔，不建议降低以免触发反爬
