---
name: classify-interview-questions
description: 将批量面经或零散面试题逐题去重并分发：Agent/LLM/AI工程题写入 zero2Agent 的 learn-agent-interview，传统后端八股写入相邻 zero2Leetcode 的夏季八股。大批量输入使用 gpt-5.6-luna API 逐篇并发抽题和语义召回，再审查、去重和写答案；不新建面经实录文章。
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
- 多篇面经或完整抓取目录：必须使用下面的 Luna 批处理流水线。不得把原始文章区间分给多个 Agent 逐篇阅读抽题；这种做法容易因上下文窗口、注意力分配和中途摘要造成静默遗漏。

## 批量 Luna 抽取与召回流水线

### 1. 建立输入清单

以本轮抓取的 `manifest.json` 为唯一输入清单，按 `articles[]` 顺序生成稳定序号。每篇必须使用 `localSourcePath` 指向的原文；不能只遍历当前输出目录，因为复用文章可能位于历史目录。

先读取两个仓库现有题目索引/标题。Agent 侧以本 Skill 的 `question-index.md` 为快速索引；后端侧读取 summer include 的编号标题。

### 2. 用 gpt-5.6-luna 批量并发抽题

批量任务统一运行维护脚本：

```bash
python .claude/skills/classify-interview-questions/scripts/batch_extract_and_recall.py \
  --manifest ".claude/skills/scrape-nowcoder/nowcoder-output-<range>/manifest.json" \
  --out ".codex-tmp/llm-interview-audit-<range>" \
  --model "gpt-5.6-luna" \
  --outer-workers 3 --workers 8 \
  --rerank-batch-size 1 --candidate-k 12 --top-k 5
```

固定约束：

- 默认模型是 `gpt-5.6-luna`。除非用户明确指定，不使用更慢的模型跑整批原文。
- 每篇文章独立调用 `extract_and_recall.py --llm`，不能把 `all-in-one.md` 当成一篇输入；否则会丢失文章归因和 canonical URL 边界。
- 外层并发负责文章级吞吐，单篇 `--workers` 负责问题级重排。默认 `3 x 8`；遇到限流时先降低外层并发，不降低抽取完整性。
- 每题先召回 12 个本地候选，再由 Luna 语义重排到 Top-5。`high/review/low` 只是召回带，不直接决定新增。
- Token 只在内存中使用。结果目录只保存逐篇 JSON 和 `batch-summary.json`，不保存配置密钥。
- 脚本默认断点续跑：复用成功 JSON 和已确认的 `gate_rejected`，自动重试 `failed`。需要重新检查门禁拒绝项时显式加 `--retry-gate-rejected`。
- 抽题前先做本地 source preflight：空稿、失效页、付费/标准答案模板、跨 URL 近重复正文，以及多数帖子已命中这些规则的内容账号，直接记为 `pre_gate_rejected`，不调用抽题 API。
- 通过本地门禁后，单篇脚本先调用 Luna 严格判断是否为作者亲历的技术面试；`gate_rejected` 同样不会进入抽题阶段。
- 每完成一篇，脚本立即重建五个题目队列：`duplicate-evidence.jsonl`、`enhancement.jsonl`、`novel.jsonl`、`review.jsonl`、`out-of-scope.jsonl`。中断时已完成文章的队列结果仍可恢复。

对于单篇诊断仍可直接运行：

```bash
python .claude/skills/classify-interview-questions/scripts/extract_and_recall.py \
  --input article.md --llm --llm-model gpt-5.6-luna --workers 8 \
  --rerank-batch-size 1 --candidate-k 12 --top-k 5 \
  --format json --out audit.json
```

### 3. 验收批处理账本

读取 `batch-summary.json` 并验证：

- `articleCount == completedCount == manifest.articles.length`。
- `failed == 0` 且所有成功结果的 `llmErrorCount == 0`。`no_questions` 表示 Luna 完成判断但没有抽出完整题干，是可审计的空结果；真正失败项必须重跑，不能用确定性抽取静默替代。
- `model` 和逐篇 `llm.model` 均为本轮指定的 Luna 模型。
- `gate_rejected` 保留在账本中，并与空正文、失效页、教程、推广、付费聚合和重复账号稿核对。
- 如果明确的一手面经被门禁误拒，先人工确认原文边界，再对该单篇使用 `extract_and_recall.py --allow-non-interview --llm` 重跑；禁止整批绕过门禁。
- 每个成功 JSON 都保留 `sourceClassification`、完整问题、Top-K、`llmRelation`、`llmConfidence` 和原因。不得只留最终题目清单。

### 4. 从结构化结果生成候选 ledger

候选判断只消费逐篇 JSON、四类队列和必要的现有目标题块，不再重新把整篇原文交给 Agent 阅读。默认自动归并规则：

- `same` 置信度不低于 0.85：从新题候选中丢弃，进入 `duplicate-evidence`，用于补来源和 frequency。
- 没有高置信 `same`，但 `overlap` 不低于 0.80：进入 `enhancement`，补追问、反例或答案缺口。
- Top-K 没有 `same/overlap`，且 `different` 不低于 0.85：进入 `novel` 新题候选队列。
- 关系混合但低于阈值、缺少 LLM judgment 或出现降级：进入 `review`，禁止自动新增。
- 职业规划、Offer/转正、职级地点等非技术问题进入 `out_of_scope`；缺少指代对象或题干截断的问题进入 `review`。它们不能因为与技术题库不同而进入 novel。

可随时用结果账本重新生成队列：

```bash
python .claude/skills/classify-interview-questions/scripts/build_recall_queues.py \
  --summary ".codex-tmp/llm-interview-audit-<range>/batch-summary.json" \
  --out ".codex-tmp/llm-interview-audit-<range>/queues"
```

最终逐题输出：

- `新增`：核心考点或工程约束确实不同。
- `增强`：同一核心题，只追加来源、追问、反例或现有答案缺失部分。
- `排除`：非目标域、个人化且无法通用、题干不完整、重复/推广/无可靠来源。

LLM 的 `same/overlap/different` 和置信度是证据，不是最终裁决。高相似仍可能是约束不同的新题；低相似也可能是已有题的换词。每项 ledger 必须记录原始文章序号、canonical URL、LLM 问题文本、Top-K 和最终理由。

对需要当前事实、协议、框架或模型细节的新增题，查当前一手资料，返回支持具体结论的官方直达链接，并明确事实与推断。调研阶段不直接编辑题库。

### 5. 按互不重叠文件写答案

把最终确认的新题和增强映射按目标文件分组。一个文件同一时间只允许一个写作者；写作者只读取目标全文、相邻问题和结构化候选，不重新扫描原始面经。共享的 `question-index.md`、`question-frequency.json`、入口计数和排序由主流程最后单点维护。

传统后端题按连续编号写入 zero2leetcode summer include；算法题只更新算法题单，不占传统八股编号。

### 6. 合并、校验和汇报

主流程负责：

1. 审查所有正文 diff，解决语义重复和文件冲突。
2. 更新 Agent `question-index.md` 的连续编号、维度数、总数、来源追问和日期。
3. 更新 `question-frequency.json`：同题新增面经时追加唯一 evidence，新题新增完整记录，然后执行组内频次排序。
4. 更新 zero2leetcode summer 总数及 `05_interview/index.md` 的入口计数。
5. 核对正文标题数、人工索引、频次 JSON 和机器索引总数完全一致。
6. 核对新增/增强题的正文来源、人工索引和频次 evidence 链接一致，并抽查链接落到原始页面。
7. 汇报 manifest 文章数、Luna 成功抽取数、门禁拒绝数、失败/`llmErrors`、抽取题数、新增数、增强数、公开原文链接数、授权但无公开 URL 的来源数，以及各类排除数。

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

- 原始文章的分类、抽题和 Top-K 重排只由 Luna 批处理脚本执行；不创建原文分片阅读任务。
- 后续审查只消费逐篇 JSON、候选 Top-K 和必要的现有题块，避免重新加载整批原文。
- 写入只按互不重叠文件并行；`question-index.md`、`question-frequency.json`、总数入口、频次排序和最终统计始终由主 Agent 单点维护。
- 全部结果合并并验证前不提交、不推送；两个仓库保持独立 commit。
- 如果用户要求 push，先同步远端、检查精确 diff，再推送并观察两个 Pages 工作流。

## 注意事项

- **绝不新建面经实录文章**。Agent 题分发到现有 01-13、15-17 维度；14 是公司偏好派生页，不直接收题
- 个人化问题（“你用过XX吗”“你简历上的XX”）必须转为通用问题
- 与已有题目重复时，增强已有答案而非新增
- 来源标注保留原始公司/岗位/轮次和原文超链接；无公开 URL 时明确标注可信边界
- Luna 的关系分类和相似度不能单独决定新增；结构化候选的语义裁决才是最终题库事实源
