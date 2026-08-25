---
name: scrape-nowcoder
description: 基于 CDP 原生 WebSocket 抓取牛客网面经文章。当用户说"抓牛客"、"爬牛客面经"、"nowcoder 抓取"、"抓取面经列表"时触发。通过 Chrome 调试端口直接连接已登录的浏览器会话，支持首页、话题、搜索分页和详情全文抓取，输出 Markdown。
---

# scrape-nowcoder：牛客面经 CDP 抓取

基于 Chrome DevTools Protocol 原生 WebSocket，零依赖。直接连接已运行的 Chrome 调试端口，复用浏览器登录态。

## 工作方式

1. 连接 Chrome 调试端口（默认 9222）
2. 如果端口不可达，自动启动独立 Chrome 实例（`~/.chrome-nowcoder`）
3. 支持首页推荐流、标准话题 API、`creation/subject` 无限滚动话题和面经分类搜索结果
4. 在已登录的浏览器中操作，抓取完成后 Chrome 保持运行

## 前置条件

- Node.js >= 22（需要原生 WebSocket 和 fetch）
- Google Chrome（Windows 或 macOS）以调试端口运行
- 已在该 Chrome 中登录牛客网

### 首次使用

启动带调试端口的 Chrome（会自动创建 `~/.chrome-nowcoder` profile）：

```bash
node .claude/skills/scrape-nowcoder/scrape.mjs --login
```

在弹出的 Chrome 中登录牛客，profile 会持久化 cookie。cookie 过期或页面跳转登录页时重新执行 `--login`。

## 用法

```bash
node .claude/skills/scrape-nowcoder/scrape.mjs [选项]
```

### 选项

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--login` | — | 首次使用：启动 Chrome 并打开登录页 |
| `--home` | — | 抓取首页推荐流，通过连续下拉加载后续内容 |
| `--topic <url\|id>` | `818_1` | 抓取话题流；支持 `creation/subject/<uuid>` URL、其他完整牛客 URL 或 `type` 值 |
| `--pages <n>` | 1 | 最大页数；首页模式下为连续滚动批次 |
| `--limit <n>` | 0 | 列表去重和关键词筛选后最多抓取前 n 篇详情；0 表示不限 |
| `--since <date>` | (空) | 标准话题接口或搜索模式仅保留该日及之后内容；话题接口连续两页全部更早时停止 |
| `--until <date>` | (空) | 标准话题接口或搜索模式仅保留该日及之前内容；与 `--since` 组合限定月份/区间 |
| `--keyword <kw>` | (空) | 按关键词筛选标题和列表摘要（如“AI”、“大模型”） |
| `--search <query>` | (空) | 面经分类搜索模式；固定使用 `type=all&searchType=顶部导航栏&subType=818` 并翻页 |
| `--out <dir>` | `.claude/skills/scrape-nowcoder/nowcoder-output` | 输出目录 |
| `--port <port>` | 9222 | Chrome 调试端口 |
| `--delay <ms>` | 2000 | 请求间隔，避免触发反爬 |

### 常用示例

```bash
# 默认抓牛客面经话题 type=818_1 的第 1 页
node .claude/skills/scrape-nowcoder/scrape.mjs

# 从面经话题抓 10 页，连续两页全部早于指定日期时自动停止
node .claude/skills/scrape-nowcoder/scrape.mjs --topic "https://www.nowcoder.com/?type=818_1" --pages 10 --since "2026-08-12"

# 抓 creation/subject 无限滚动话题：初始可见页 + 9 次加载
node .claude/skills/scrape-nowcoder/scrape.mjs --topic "https://www.nowcoder.com/creation/subject/14710425d5b74593b2ef7103d293606f" --pages 10

# 只取 subject 首屏前 3 篇做流水线冒烟测试
node .claude/skills/scrape-nowcoder/scrape.mjs --topic "https://www.nowcoder.com/creation/subject/14710425d5b74593b2ef7103d293606f" --pages 1 --limit 3

# 首页推荐流连续滚动 3 个批次，只保留 AI 相关内容
node .claude/skills/scrape-nowcoder/scrape.mjs --home --pages 3 --keyword "AI"

# 面经分类搜索：搜"字节跳动 后端 面经"，抓 5 页
node .claude/skills/scrape-nowcoder/scrape.mjs --search "字节跳动 后端 面经" --pages 5

# 搜索"面"并逐篇按详情发布日期筛选已召回的 2026 年 7 月候选
node .claude/skills/scrape-nowcoder/scrape.mjs --search "面" --pages 50 --since "2026-07-01" --until "2026-07-31" --out ".claude/skills/scrape-nowcoder/nowcoder-output-2026-07-search"

# 面经分类搜索：搜 Redis 八股
node .claude/skills/scrape-nowcoder/scrape.mjs --search "Redis 面经 八股" --pages 3

# 指定端口
node .claude/skills/scrape-nowcoder/scrape.mjs --port 9333
```

### 三种模式对比

| | 首页模式（`--home`） | 标准话题（`?type=`） | Subject 话题（`creation/subject`） | 搜索模式（`--search`） |
|---|---|---|---|---|
| 数据源 | 牛客首页推荐流 | 牛客标准话题 API | 牛客专题无限滚动页 | 牛客搜索页 `/search/all?type=all&searchType=顶部导航栏&subType=818` |
| 筛选方式 | `--keyword` 按标题和摘要过滤 | 可叠加 `--keyword` 和日期区间 | 可叠加 `--keyword`；日期区间不适用 | `query` 在面经分类内检索；可用日期区间 |
| 翻页方式 | 每批多次连续下拉 | `home/tab/content?pageNo=N` | 初始可见页后每页触发一次加载，等待 URL/高度增长 | 客户端点击分页并确认页码与结果 URL |
| 适用场景 | 发现个性化推荐内容 | 按时间遍历面经 | 完整扫描指定专题 | 精准搜索公司、岗位或主题 |

三种模式都会按文章 URL 跨页去重；页码不存在、切换失败或某一页没有新增结果时会提前停止，避免重复抓取旧页。
搜索模式先收集每页 URL，再逐篇打开详情解析可验证的发布日期；“今天”“昨天”等相对时间仅在实时详情读取时按 Asia/Shanghai 转换为绝对日期，历史文件中的相对时间不会按重跑日期重新解释。日期区间外或无法验证发布日期的文章不会进入本轮索引、manifest 或合集。索引在详情过滤完成后生成，因此不会留下列表阶段的越界条目。
写盘前还会扫描整个 Skill 数据区内 `nowcoder-output*` 和 `nowcoder-agent-excellent-full` 的单篇 Markdown `**来源**` URL；URL 会先移除查询参数、锚点和末尾斜杠再比较。重跑命中同一来源时直接复用已有正文，也不在新目录生成单篇副本。标题相同但来源 URL 不同的帖子仍分别保留。
`creation/subject/<uuid>` 会进入专用滚动分页：`--pages 1` 只取初始可见结果，后续每页触发一次加载并等待 URL 数或页面高度增长；连续一页没有新增 URL 时停止。其他非标准话题 URL 仍回退为连续滚动。滚动模式无法可靠获得列表发布时间，传入的 `--since/--until` 会明确标记为未应用。

### 搜索覆盖边界

`subType=818` 搜索按相关性返回结果，不是按发布日期排列的全量时间流。`--since/--until` 只过滤已经翻页召回的候选，不能单独证明目标月份已全量覆盖。月份扫描以 `type=818_1` 话题流为主，`--search "面"` 及公司、岗位、技术主题 query 用于补漏；搜索应翻到没有下一页，并记录 query、实际扫描页数、候选数、区间外数、日期未知数和详情失败数。

同一轮抓取使用独立输出目录。不要把不同 query 或日期区间反复写到同一目录，因为新运行会覆盖 `index.md`、`manifest.json` 和 `all-in-one.md`，但不会删除旧单篇文件。多轮结果通过各自 manifest 的规范 URL 合并去重。

## 输出结构

```
.claude/skills/scrape-nowcoder/nowcoder-output/
├── index.md                # 目录索引
├── manifest.json           # 本轮逐篇来源、日期、复用状态和本地原文路径
├── all-in-one.md           # 全部文章合并
├── 2026-05-20-标题.md      # 单篇文章（按发布日期命名）
├── 2026-05-18-标题.md
└── ...
```

## 长期 Agent 面经档案

完整抓取结果默认仍写入 Git 忽略目录。只有用户明确要求长期保留时，才从原始结果中筛选高质量 Agent 一手面经，归档到：

```text
.claude/skills/scrape-nowcoder/nowcoder-agent-excellent-full/
```

归档时遵循以下规则：

1. 只收录真实的一手面试记录，优先保留完整面试流程、连续追问和项目深挖链路。
2. 排除重复账号稿、逐题复用稿、教程、推广、付费墙、重构题库和纯笔试。
3. 一旦收录，保留整轮面试链路：自我介绍这一流程项、Agent 与传统技术题、项目追问、原作者记录的回答和面试官反馈、算法题及反问；不能只摘 Agent 题。
4. 保持原帖顺序与表述，不补答案，不把不确定术语擅自改成另一个技术名词。
5. 每篇保留发布日期和牛客来源 URL；移除用户名、学校、作者所在地、具体个人结果、互动区和相关推荐。
6. 新增单篇文件后同步更新档案目录的 `index.md`，记录日期、面试标题、本地文件和原始链接。

### 归档筛选与题目抽取必须解耦

长期原文档案的收录资格只决定是否保存整篇原文，不能作为后续题目抽取的前置过滤器。用户要求整理 Agent 题或传统八股时：

1. 以本轮 `manifest.json` 为输入，按 `articles[].localSourcePath` 逐篇扫描全部文章；不得只遍历当前目录的单篇文件或 `nowcoder-agent-excellent-full/`。复用文章不会在新目录重复生成单篇副本，但 manifest 会指向原始文件。
2. 即使文章因推广、教程、重构稿或付费内容未进入长期档案，仍要逐题判断其中是否包含可归因的真实面试问题。
3. 去重在题目级执行：高度重复时增强已有答案并补充来源，缺失时新增；不得用文章级排除代替逐题去重。
4. 只提取通用化后的问题和必要的公司、岗位、轮次来源，不复制推广文案、个人信息或无法验证的答案。
5. 汇报覆盖情况：原始文章数、已扫描文章数、新增题数、增强题数，以及按原因排除的候选题数，避免静默漏项。

单篇文件整理完成后，用维护脚本校验来源 URL 唯一性并重建索引与合集：

```bash
node .claude/skills/scrape-nowcoder/rebuild-archive.mjs
```

## 执行流程

当用户触发此 skill 时：

### 1. 确认参数

确认用户已提供或可从上下文确定：
- 从首页、话题还是面经分类搜索抓取（默认面经话题 `type=818_1`）
- 最大抓几页（默认 1）
- 是否需要起止日期或关键词筛选

用户给出搜索词、页数或日期区间时直接执行，不重复询问。按月份抓取搜索结果时必须同时提供 `--since` 和 `--until`。

### 2. 执行抓取

```bash
node .claude/skills/scrape-nowcoder/scrape.mjs --topic "818_1" --pages <n> --since "<YYYY-MM-DD>"
```

面经分类搜索由脚本固定 `type=all&searchType=顶部导航栏&subType=818`，用户只提供 query：

```bash
node .claude/skills/scrape-nowcoder/scrape.mjs --search "面" --pages <n> --since "<YYYY-MM-DD>" --until "<YYYY-MM-DD>"
```

脚本自动连接 Chrome 调试端口，无需用户额外操作。

### 3. 检查输出

读取 `manifest.json` 和 `index.md`，汇报候选数、保留数、复用数、区间外数、日期未知数、详情失败数和规范 URL 重复数。

### 4. 后续操作（可选）

抓取完成后询问用户是否需要：
- 使用 `classify-interview-questions` 将面试题分发到已有维度文章
- 筛选特定文章深入处理

## 注意事项

- Chrome 必须以 `--remote-debugging-port` 启动
- 首次需用 `--login` 在独立 Chrome 中登录牛客
- 登录 profile 位于 `~/.chrome-nowcoder`；cookie 过期、搜索异常为空或跳转登录页时重新执行 `--login`
- Chrome 实例保持运行，不会被脚本关闭
- 默认 2 秒间隔，不建议降低以免触发反爬
- `type=818_1` 是牛客“面经”话题流，默认全量收集，不需要先按标题关键词过滤
- 月份抓取同时传 `--since YYYY-MM-01 --until YYYY-MM-<末日>`，避免把后续月份写进目标目录
- 增量重跑使用新的独立输出目录；整个 Skill 数据区同一来源 URL 只保存一份单篇正文。抓取后仍应核对 manifest URL 唯一性和单篇文件中的来源 URL 唯一性
- 抓取原文属于临时输入，应写入 Git 忽略目录，不提交浏览器配置、Cookie 或原始抓取结果
