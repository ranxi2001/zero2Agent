---
name: classify-interview-questions
description: 将批量面经或零散面试题逐题去重并分发：Agent/LLM/AI工程题写入 zero2Agent 的 learn-agent-interview，传统后端八股写入相邻 zero2Leetcode 的夏季八股。大批量输入使用并行子 Agent 逐篇审计、相似度召回、并行调研和并行写答案；不新建面经实录文章。
---

# classify-interview-questions：面试题分类分发

将新面试题按考察维度分类，拆分后加入已有题库。**不新建独立面经实录文章**。

## 两个目标仓库

- Agent、LLM、RAG、训练、多模态、AI Coding 与 AI 工程题：当前 `zero2Agent/learn-agent-interview/`。
- Java/Go/Python、JVM、并发、操作系统、网络、数据库、缓存、消息队列、分布式、前端与通用工程八股：相邻 `../zero2Leetcode/_includes/interview-seasons/2026/summer.md`。
- 算法/手撕题只进入 zero2leetcode 的算法题单，不计入传统八股总数；题干不完整时排除，不补造。
- 机器召回使用本 Skill 的 `question-index.json`；`question-index.md` 是人工维护源。每次修改 Markdown 后必须重建 JSON 并运行 stale check。
- `question-frequency.json` 是 Agent 题单频次事实源。`frequency` 等于 `evidence` 中可归因的独立面经出现次数；题库汇总、“高频题”等不可追溯标签不计数。正文只在现有最小主题组内按频次降序排列，同频按稳定的 `firstSeenOrder` 排列。
- 两个仓库分别检查 worktree、计数、提交和推送。不得把一个仓库的 commit 混入另一个。

## 来源与超链接契约

来源链接是题库可信度的一部分。以后新增题、增强已有题和调研答案都按以下标准维护，不只写不可核验的公司名或“高频题”。

### 面试题证据

- 有公开原文时，正文 `> 来源：` 使用可点击的 Markdown 链接，链接文字保留公司、岗位和轮次，例如：

  ```markdown
  > 来源：[阿里云 Agent Infra 一面](https://www.nowcoder.com/feed/main/detail/<id>)
  ```

- 链接必须直达原始面经文章或用户指定的一手页面，不使用搜索结果页、信息流首页、聚合转载、短链或无关主页。多个独立来源分别给链接，不能把多个 URL 藏在一个笼统标签里。
- 同一来源要贯穿三处：正文来源行、`question-index.md` 的题目来源、`question-frequency.json` 的 evidence。人工索引保留 Markdown 链接；频次 JSON 中每个独立原文 URL 单独占一个 evidence，同一核心题里的同一 canonical URL 只计一次。
- 增强已有题时保留原有链接，再追加新来源或追问链接；不要把已经可点击的来源降级成纯文本。
- URL 只是可追溯入口，不自动证明内容是一手面经。仍需按真实面试过程、公司/岗位/轮次和问题上下文判断是否可归因，转载、题库汇总和营销内容仍不计频次。
- 用户明确授权的本地题库或私有材料可以作为来源，但没有公开 URL 时必须写明“用户授权题库（无公开 URL）”，不得伪造链接，也不得把本机绝对路径、私有下载地址或凭证写进站点。若能定位到公开原文，先验证内容一致再补回原始链接。
- 无公开 URL、又没有用户明确授权或其他可归因证据的题目，不进入频次事实源。

### 答案事实依据

- 协议、框架、模型、Kubernetes、AIOps 等会变化或容易混淆的事实，优先查当前一手资料，并在支持该结论的正文附近直接链接官方文档、官方仓库、标准或论文，不只在文末列一个泛化“参考资料”。
- 链接应指向支持具体结论的页面；官方资料没有直接支持时，明确标注这是工程推断或经验判断，不借链接制造过度确定性。
- 答案实质依赖外部资料时同步更新 `THIRD_PARTY_NOTICES.md`。独立改写答案，不复制外部文章的长段落、图表或受版权保护内容。

### 链接验收

- 发布前验证新增链接可访问、页面标题与标注一致、没有误链到评论区或推荐页；登录受限页面至少确认 URL 是原始文章地址。
- 核对每个新增或增强题的正文来源、人工索引和频次 evidence，不允许其中一处有 URL、另两处丢失 URL。
- 汇报时增加来源覆盖：公开原文链接数、用户授权但无公开 URL 的来源数、无法归因而排除的来源数。

## 维度分类表

| 编号 | 维度 | 目录 | 典型考察内容 |
|------|------|------|------------|
| 01 | 架构选型 | `01-architecture-design/` | ReAct/Plan-Execute/ToT、Agent 组成、设计范式、规划器 |
| 02 | 工具管理 | `02-tool-management/` | 参数校验、工具路由、多工具调度、Mock 生成 |
| 03 | 容错与鲁棒性 | `03-fault-tolerance/` | 超时处理、误操作防范、幻觉治理、失败恢复 |
| 04 | 记忆与上下文 | `04-memory-context/` | 长对话、模糊需求、上下文污染、长短期记忆、to-do list |
| 05 | 评估与全局观 | `05-eval-and-vision/` | 量化评估、落地挑战、AI 工具价值/边界、行业认知 |
| 06 | 多智能体协作 | `06-multi-agent-collab/` | 角色分工、通信机制、冲突仲裁、记忆共享 |
| 07 | 工程化踩坑 | `07-engineering-pitfalls/` | 死循环、状态丢失、成本控制、AI Coding 实践、工具使用 |
| 08 | Prompt 工程 | `08-prompt-engineering/` | 模板构建、Skills 机制、好/差 Prompt 区别、框架创新 |
| 09 | RAG 与检索 | `09-rag-retrieval/` | chunk 设计、查询改写、召回精排、Embedding/ReRank 微调 |
| 10 | 训练与模型 | `10-training-and-data/` | 数据清洗、LoRA、PPO/DPO/GRPO、位置编码、归一化、量化部署、多模态 |
| 11 | AI 代码测试 | `11-ai-code-testing/` | 覆盖率插桩、前置分析、代码过滤 |
| 12 | 业务 AI 工程 | `12-business-ai-engineering/` | 业务需求拆解、方案选型、效果评估、智能客服与业务落地 |
| 13 | 简历项目拷打 | `13-project-deep-dive/` | 项目部署、框架选型、意图识别、工具设计、知识库构建、性能优化 |
| 14 | 公司偏好（派生页） | `14-company-preferences/` | 从各维度来源统计公司考察偏好，不直接写入新题 |
| 15 | Agent 概念 | `15-agent-concepts/` | Harness/Context Engineering、Vibe Coding、MCP、Skills 等概念辨析 |
| 16 | Agent Infra | `16-agent-infra/` | Runtime、Checkpoint、幂等、Sandbox、Kubernetes、调度与可观测 |
| 17 | AI Infra | `17-ai-infra/` | 分布式训练、LLM Serving、GPU 调度、模型发布与 AIOps |

## 模式选择

- 少量零散题：直接执行“分类 → 索引查重 → 写答案 → 校验”。
- 多篇面经或完整抓取目录：必须使用下面的并行流水线。题量大时无需先向用户展示确认表。

## 批量并行流水线

### 1. 建立输入清单

以本轮完整原始抓取目录为输入，不只读取优秀面经归档。按日期、索引或稳定文件名生成唯一序号，排除 `index.md`、合集和审计产物。

先读取两个仓库现有题目索引/标题。Agent 侧以本 Skill 的 `question-index.md` 为快速索引；后端侧读取 summer include 的编号标题。

只有一手面经进入问题提取：必须有真实面试过程或明确公司/轮次/面试官问题证据。招聘、内推、Offer 选择、求助、学习路线、教程、题库汇总和付费推广即使包含问句也整篇拒绝，并在 ledger 记录原因。

### 2. 并行逐篇提取

把连续且不重叠的文章区间分给多个子 Agent。每个子 Agent必须完整读取自己范围内的每篇正文，并逐篇返回：

```text
序号 | 标题 | 来源 URL
Agent 新增候选
后端新增候选
已有题/可增强追问
排除项与原因
```

约束：

- 子 Agent 只读，不直接编辑共享题库或同一个 ledger，避免并发写冲突。
- 评论、相关推荐、热榜和作者个人信息不算原帖问题。
- 重复账号稿、改公司名扩写稿、纯教程、推广和付费截断内容要标明可信边界。
- 付费/推广文章不能整篇静默跳过；仍逐题判断是否存在可归因的真实问题，但不采用营销答案和未验证数字。
- 题干不完整、术语不确定时保留原文并排除，不擅自修正成另一道题。

主 Agent 合并所有区间结果，确认原始文章数等于已扫描文章数，并维护逐篇审计 ledger。

ledger 中的来源 URL 使用原始 canonical URL；同一篇文章的跟踪参数、移动端地址或重复抓取地址要归一为一个证据。

### 3. 相似度召回

在逐篇语义提取之后，使用规范化文本、字符 n-gram、BM25 或 Embedding 与现有题标题计算相似度，给每个候选召回 Top-K 相近题。

对于单篇牛客面经或本地原文，优先运行完整流水线，一次完成正文解析、问题提取和召回：

```bash
# 牛客 discuss 页面
python .claude/skills/classify-interview-questions/scripts/extract_and_recall.py \
  --url "https://www.nowcoder.com/discuss/<id>" --top-k 5 --format markdown

# 本地 Markdown 或纯文本
python .claude/skills/classify-interview-questions/scripts/extract_and_recall.py \
  --input article.md --top-k 5 --format json --out audit.json

# 复用 Codex 配置中的 base URL、token、model 和 wire API，并行抽题与语义重排
python .claude/skills/classify-interview-questions/scripts/extract_and_recall.py \
  --url "https://www.nowcoder.com/discuss/<id>" --llm --workers 8 \
  --rerank-batch-size 1 --candidate-k 12 --top-k 5 --format json --out audit.json
```

流水线只解析原帖 SSR `contentData`，不读取评论和推荐区；默认同时加载 zero2Agent 索引、相邻 zero2Leetcode 夏季八股和算法题单，输出每道题的 BM25、字符 n-gram、综合分、维度和 Top-K 标题。`high/review/low` 只是召回置信带，不是新增判定。

`--llm` 默认从 Codex 配置读取连接信息：优先显式 `--codex-config` 或 `~/.codex/config.json` / `codex.json`，否则读取官方 `~/.codex/config.toml` 当前 `model_provider` 和 `auth.json`。兼容 `baseURL/base_url`、`token/apiKey`，按 `wire_api` 调用 Responses 或 Chat Completions。Token 只在内存中使用，输出仅包含配置来源、API host、模型名和 wire API。默认每题一个请求并用 `--workers` 并行；限流严格或网络开销高时可增大 `--rerank-batch-size`，但必须用真实面经基准测试，批量更大不保证更快。`--llm-extract`、`--llm-rerank` 可单独启用。某个批次失败时保留本地召回并在 `llmErrors` 中报告，不静默丢题。

优先运行随 Skill 提供的确定性召回工具：

```bash
python .claude/skills/classify-interview-questions/scripts/recall_similar_questions.py \
  --input candidates.txt --top-k 5

# 也可从 stdin 输入，一行一道题
python .claude/skills/classify-interview-questions/scripts/recall_similar_questions.py \
  --input - --top-k 5 --json
```

工具从 `question-index.md` 同时识别所有维度和连续编号题目，输出字符 n-gram、BM25 与混合分数。批量处理时保存原始输出或在审计 ledger 中记录每题 Top-K，不能只写“已查重”而没有召回证据。

相似度只是加速工具：

- 高相似候选由子 Agent/主 Agent 判断是同题、追问增强还是约束不同的新题。
- 低相似不自动等于新题；答案句、项目描述和无来源问题仍需排除。
- 自动匹配必须同时识别 `## Q：` 与 `### Q：` 等现有标题格式，运行后校验加载到的题数与索引总计一致。
- 禁止用相似度结果替代逐篇读取和逐题语义判断。

### 4. 并行语义去重与调研

按维度或互不重叠的候选集合分给子 Agent。每个子 Agent读取相近题正文并输出：

- `新增`：核心考点或工程约束确实不同。
- `增强`：同一核心题，只追加来源、追问、反例或现有答案缺失部分。
- `排除`：非目标域、个人化且无法通用、题干不完整、重复/推广/无可靠来源。

对需要当前事实、协议、框架或模型细节的新增题，子 Agent 使用当前一手资料调研，返回支持具体结论的官方直达链接，并明确事实与推断。不要让调研 Agent 直接编辑题库。

### 5. 并行写答案

把最终确认的新题按**互不重叠的目标文件**分配给写作子 Agent。一个文件同一时间只允许一个写作者；会写同一文件的题合并成一个任务。

写作子 Agent必须读取目标全文及相邻问题，把新题插入最匹配的现有主题组。它只修改被分配的文件，不改 `question-index.md`、`question-frequency.json`、导航或其他仓库；主 Agent 合并后统一按频次重排。

传统后端题由独立子 Agent 按连续编号写入 zero2leetcode summer include；它同时返回新增题数，但不自行更新入口总数。

### 6. 主 Agent 合并

主 Agent负责：

1. 审查所有子 Agent diff，解决语义重复和文件冲突。
2. 更新 Agent `question-index.md` 的连续编号、维度数、总数、来源追问和日期。
3. 更新 `question-frequency.json`：同题新增面经时追加唯一 evidence，新题新增完整记录，然后执行组内频次排序。
4. 更新 zero2leetcode summer 总数及 `05_interview/index.md` 的入口计数。
5. 核对正文标题数、人工索引、频次 JSON 和机器索引总数完全一致。
6. 核对新增/增强题的正文来源、人工索引和频次 evidence 链接一致，并抽查链接落到原始页面。
7. 汇报原始文章数、扫描数、新增数、增强数、公开原文链接数、授权但无公开 URL 的来源数，以及重复、教程/推广、算法、个人化、空正文、题干不完整等排除数。

## 少量题执行步骤

### 1. 分类

收到面试题后，逐题判断属于哪个维度：
- 如果题目明显属于某个维度 → 直接分配
- 如果题目跨维度 → 选最核心的那个维度
- 如果题目太个人化（如“你简历上的XX项目”）→ 剥离简历细节，转为通用问题再分配
- 如果题目和已有题目高度重复 → 增强已有答案，不新增

输出分类结果表格供用户确认（如果题量大可直接执行）。

### 2. 检查已有内容

**先读取 `question-index.md`**（位于本 skill 目录下），快速判断新题是否与已有题目重复或高度相似；再读取 `question-frequency.json`，确认已有题的历史面经证据。仅在需要定位主题组和插入位置时读取目标 md 文件。

对每篇目标文章：
- 检查是否已有相同或相似问题
- 找到最匹配的现有主题组；先完成内容写入，最终位置由频次排序脚本确定

### 3. 写答案并插入

每道题用标准格式：

```markdown
## Q：{面试题（通用化后的表述）}

> 来源：[{公司 / 岗位 / 轮次}]({原始面经 URL})

**新手答**："{浅层回答}"

**高手答**：

{深度回答，分层递进，带具体方案}

**差距在哪**：{分析差距，点出面试官考什么}
```

如果来源是用户授权但没有公开 URL 的本地材料，使用：

```markdown
> 来源：用户授权的「{题库名称}」（无公开 URL）
```

答案中的外部事实链接放在对应结论附近。面试来源链接证明“这道题被问过”，官方资料链接证明“答案里的事实依据”，两者不能互相替代。

**善用 Mermaid 流程图**：当答案涉及多阶段流程、对比关系或架构拆分时，优先用 ```` ```mermaid ```` 流程图替代纯文本 ASCII 图。项目前端已支持 Mermaid 渲染，流程图比文字列表更直观。适合使用的场景：
- 多阶段管线（如 RAG 检索 → 精排 → 生成）
- 对比（如有/无某方案的效果对比）
- 架构分层（如 Agent 四层架构）
- 决策分支（如“什么场景用什么方案”）

不需要每道题都加图，只在图比文字更清晰时使用。

### 4. 修复引号

插入完成后，对所有修改过的文件运行：
```bash
python3 .claude/skills/chinese-quotes-fix/fix_quotes.py "learn-agent-interview/{目标目录}/index.md"
```

### 5. 更新索引与题单频次

分发完成后，更新 `question-index.md`：
- 在对应维度记录新增题目，增强题补充来源追问
- 保留正文中的来源 Markdown 链接，人工索引不要退化为纯文本来源
- 更新统计表中的题数和总计
- 更新“最后更新”日期

同步维护 `question-frequency.json`：
- 一篇面经对同一核心题只贡献一次 evidence；重复转载、题库汇总和无法归因的“高频题”标签不计数
- 有公开原文时 evidence 保留可点击的来源标签与 canonical URL；多个独立 URL 拆成多个 evidence
- 同题增强时追加新的唯一 evidence，并令 `frequency == evidence.length`
- `firstSeenOrder` 记录题目在当前维度的初次入库顺序，只在新题首次建档时分配，后续重排不得修改
- 新题可以先运行同步脚本生成记录，再人工核对 evidence；题目改名时同步修改 JSON，不能丢失原证据

最后执行稳定排序并校验三个索引：

```bash
python .claude/skills/classify-interview-questions/scripts/sync_question_frequency.py
python .claude/skills/classify-interview-questions/scripts/sort_questions_by_frequency.py
python .claude/skills/classify-interview-questions/scripts/sync_question_frequency.py --check
python .claude/skills/classify-interview-questions/scripts/sort_questions_by_frequency.py --check
python .claude/skills/classify-interview-questions/scripts/build_question_index_json.py
python .claude/skills/classify-interview-questions/scripts/build_question_index_json.py --check
```

### 6. 汇报

输出分发结果表格：

| 题目 | 分发到 |
|------|--------|
| Q1: ... | 05-eval-and-vision (新增) |
| Q2: ... | 10-training-and-data (增强已有) |

## 并发与写入安全

- 优先并行只读提取、相似度分析和资料调研。
- 写入只按互不重叠文件并行；`question-index.md`、`question-frequency.json`、总数入口、频次排序和最终统计始终由主 Agent 单点维护。
- 子 Agent 不提交、不推送。主 Agent 在全部结果合并、验证后再按仓库分别提交。
- 如果用户要求 push，先同步远端、检查精确 diff，再推送并观察两个 Pages 工作流。

## 注意事项

- **绝不新建面经实录文章**。Agent 题分发到现有 01-13、15-17 维度；14 是公司偏好派生页，不直接收题
- 个人化问题（“你用过XX吗”“你简历上的XX”）必须转为通用问题
- 与已有题目重复时，增强已有答案而非新增
- 来源标注保留原始公司/岗位/轮次和原文超链接；无公开 URL 时明确标注可信边界
- 自动相似度不能决定新增；逐篇人工语义判断才是最终事实源
