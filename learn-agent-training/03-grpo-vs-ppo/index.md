---
layout: default
title: GRPO vs PPO：Agent 强化学习算法深度对比与选型
description: 从原理到实现到企业选型，全面对比 PPO 与 GRPO 在 Agent 训练中的差异
eyebrow: Agent 训练实战 / 03
---

# GRPO vs PPO：Agent 强化学习算法深度对比与选型

上一篇讲了 Agent RL 的整体框架和 Reward 设计。算法层面提到了 PPO 和 GRPO，但没有展开。这篇专门把这两个算法拆开讲清楚——不是推公式，而是回答一个工程问题：**你的 Agent 训练场景该选哪个，为什么？**

PPO 是 RLHF 时代的事实标准，InstructGPT、ChatGPT 都用它。GRPO 是 DeepSeek-R1 带火的新方案，去掉了 Critic 网络，用组内相对排序替代绝对打分。两者的设计哲学不同，适用场景也不同。

## 先搞清楚一个前置问题：为什么需要优势估计

不管是 PPO 还是 GRPO，核心目标都是一样的：**让好的动作出现概率增大，让差的动作出现概率减小。** 但怎么判断一个动作是“好”还是“差”？

直觉上用 Reward 就行了——Reward 高就是好动作。但 Reward 的绝对值没有意义，有意义的是**相对于基线好了多少**。这就是“优势（Advantage）”的概念：

```text
Advantage = 这个动作实际获得的回报 - 在当前状态下"平均"能获得的回报

A(s, a) = Q(s, a) - V(s)

> 0 → 这个动作比平均水平好 → 应该增加概率
< 0 → 这个动作比平均水平差 → 应该降低概率
= 0 → 和平均水平一样 → 不用调
```

PPO 和 GRPO 的核心分歧就在于：**怎么估计这个“平均水平”。**

## PPO：用 Critic 网络估计基线

### 核心机制

PPO 的做法是训练一个额外的 Value 网络（Critic），专门预测“在当前状态下，未来能拿到多少 Reward”。

<div class="mermaid">
graph TD
    A["当前状态 s<br/>(对话历史 + 工具返回)"] --> B["Policy 网络<br/>(Agent 模型)"]
    A --> C["Value 网络<br/>(Critic)"]
    B --> D["输出动作 a<br/>(tool_call 或文本)"]
    C --> E["输出 V(s)<br/>预估未来回报"]
    D --> F["环境返回 Reward r"]
    F --> G["Advantage = r + γV(s') - V(s)<br/>(用 GAE 更精确)"]
    G --> H["用 clipped objective<br/>更新 Policy"]
    G --> I["用 MSE loss<br/>更新 Critic"]

    style B fill:#022c22,stroke:#10b981,color:#34d399
    style C fill:#1e293b,stroke:#f59e0b,color:#fbbf24
    style G fill:#1a2535,stroke:#334155,color:#94a3b8
</div>

关键公式（伪代码形式）：

```python
# 1. 用 GAE 计算优势
for each step t in trajectory (reversed):
    delta_t = reward_t + gamma * V(s_{t+1}) - V(s_t)
    advantage_t = delta_t + gamma * lambda * advantage_{t+1}

# 2. 计算策略更新的目标函数
ratio = pi_new(a|s) / pi_old(a|s)       # 新旧策略的概率比
clipped_ratio = clip(ratio, 1-eps, 1+eps) # 限制更新幅度
policy_loss = -min(ratio * advantage, clipped_ratio * advantage)

# 3. 更新 Critic
value_loss = MSE(V(s), actual_return)

# 4. 总 loss
total_loss = policy_loss + c1 * value_loss + c2 * KL(pi_new || pi_sft)
```

### PPO 在 Agent 场景的具体问题

**问题 1：Critic 网络的显存开销**

Agent 模型本身可能就是 7B–70B 参数。PPO 需要一个同等规模的 Critic 网络（通常和 Policy 共享底层，加一个 Value Head）。在 Agent 场景中：

```text
显存占用估算（以 7B 模型为例）：
├── Policy 模型          ~14 GB (FP16)
├── Policy 优化器状态     ~28 GB (Adam, FP32)
├── Critic 模型          ~14 GB (FP16)
├── Critic 优化器状态     ~28 GB (Adam, FP32)
├── KV Cache + 激活值     变长，Agent 轨迹越长越大
└── 总计                 ~84 GB + 激活值
```

对比没有 Critic 的方案，PPO 的显存开销几乎翻倍。在 Agent 场景中轨迹本身就很长（几千到上万 tokens），KV Cache 已经占了不少显存，再加一个 Critic 压力很大。

**问题 2：Critic 网络难训**

Critic 要预测“从当前状态出发，未来能拿到多少 Reward”。这在 Agent 场景中特别难，因为：

- Agent 的状态空间是变长文本，不像游戏状态那样是固定维度的向量
- 一条轨迹里 Reward 可能只在最后一步才有（稀疏 Reward），中间步骤的 Value 全靠 Critic 自己估计
- Agent 执行路径的方差很大——同一个起点，不同的工具调用可能导致完全不同的结果

Critic 估计不准，Advantage 就不准，策略更新的方向就会偏。这是 PPO 在 Agent 场景中不稳定的主要来源。

**问题 3：Clip 机制的两面性**

PPO 的 clip 机制限制了每次更新的幅度（通常 ε = 0.1–0.2）。好处是稳定，坏处是在 Agent 场景中可能太保守——模型需要较大的策略调整才能从“错误的工具调用习惯”转变到“正确的调用方式”，clip 会拖慢这个过程。

## GRPO：用组内相对排序替代 Critic

### 核心机制

GRPO 的设计哲学完全不同：**不训练 Critic，不估计绝对 Value，而是让同一个 prompt 的多条轨迹互相比较。**

<div class="mermaid">
graph TD
    A["Prompt q"] --> B["Policy 模型<br/>生成 N 条轨迹"]
    B --> C1["轨迹 o₁ → Reward r₁"]
    B --> C2["轨迹 o₂ → Reward r₂"]
    B --> C3["轨迹 o₃ → Reward r₃"]
    B --> C4["... oₙ → Reward rₙ"]
    C1 --> D["组内归一化<br/>Â_i = (r_i - mean) / std"]
    C2 --> D
    C3 --> D
    C4 --> D
    D --> E["用归一化后的 Â<br/>更新 Policy"]

    style B fill:#022c22,stroke:#10b981,color:#34d399
    style D fill:#1e293b,stroke:#f59e0b,color:#fbbf24
</div>

关键公式（伪代码形式）：

```python
# 1. 对同一个 prompt，生成 N 条轨迹
for i in range(N):
    trajectory_i = policy.rollout(prompt)
    reward_i = compute_reward(trajectory_i)

# 2. 组内归一化，得到相对优势
mean_r = mean(rewards)
std_r = std(rewards)
for i in range(N):
    advantage_i = (reward_i - mean_r) / std_r

# 3. 用 clipped objective 更新策略（和 PPO 类似）
ratio = pi_new(o_i|q) / pi_old(o_i|q)
clipped_ratio = clip(ratio, 1-eps, 1+eps)
loss = -min(ratio * advantage_i, clipped_ratio * advantage_i)

# 4. 加 KL 约束
total_loss = loss + beta * KL(pi_new || pi_sft)
```

核心区别一目了然：**没有 Critic，没有 Value 估计，优势完全来自同组轨迹的相对比较。**

### GRPO 的关键设计决策

**决策 1：N 取多少？**

N 是每个 prompt 生成的轨迹数量，直接影响训练质量和成本：

| N | 优势估计质量 | Rollout 成本 | 适用场景 |
|---|---|---|---|
| 4 | 较粗，噪声大 | 低 | 快速迭代、Reward 区分度高 |
| 8 | 中等，实用 | 中 | 大多数场景的默认选择 |
| 16 | 较好 | 高 | Reward 区分度低、需要精细排序 |
| 32+ | 很好但边际递减 | 很高 | 不推荐，性价比低 |

经验值：**N=8 是大多数 Agent 场景的 sweet spot。** 更大的 N 带来的优势估计改善不足以 justify 翻倍的 rollout 成本。

**决策 2：Reward 归一化的粒度**

GRPO 原始论文是在每个 prompt 的 N 条轨迹内做归一化。但也有变体：

```text
选项 A：Per-prompt 归一化（原版）
  优势_i = (r_i - mean(同 prompt 的 N 条)) / std(同 prompt 的 N 条)
  ✓ 消除了不同 prompt 难度差异的影响
  ✗ N 太小时 std 估计不稳定

选项 B：Per-batch 归一化
  优势_i = (r_i - mean(整个 batch 所有轨迹)) / std(整个 batch)
  ✓ 统计量更稳定
  ✗ 简单 prompt 和难 prompt 的 Reward 混在一起，信号被稀释

选项 C：Per-prompt 归一化 + batch 级别 std 兜底
  mean 用 per-prompt，std 用 max(per-prompt std, batch std * 0.1)
  ✓ 兼顾两者优点
```

实践中选项 A 最常用，但如果发现训练不稳定（loss 震荡大），可以切换到选项 C。

**决策 3：如果一个 prompt 的 N 条轨迹全成功或全失败怎么办？**

这是 GRPO 一个容易被忽略的 edge case：

```text
情况 1：N 条轨迹全拿到 Reward=1
  → std=0，归一化除以 0
  → 所有 advantage 变成 0，这个 prompt 对训练没贡献

情况 2：N 条轨迹全拿到 Reward=0
  → 同上，对训练没贡献
```

这在 Agent 场景中很常见——简单任务全做对，极难任务全做错。

解决方法：
- 给 std 加一个小的下界（如 1e-4），防止除零
- 在任务采样时做难度均衡，确保每个 batch 里有一定比例的“中等难度”任务（模型做对 30%–70% 的那种）
- 监控“有效 prompt 比例”——如果超过 50% 的 prompt 的 N 条轨迹结果完全一致，说明任务难度分布需要调整

### GRPO 的优势：为什么 DeepSeek 选它

**省显存，省得不是一点点。**

```text
GRPO 显存占用（7B 模型）：
├── Policy 模型          ~14 GB
├── Policy 优化器状态     ~28 GB
├── Reference 模型       ~14 GB (SFT checkpoint, 推理模式, 不需要优化器)
├── KV Cache + 激活值     变长
└── 总计                 ~56 GB + 激活值

对比 PPO：~84 GB + 激活值

省了 ~28 GB（Critic 的优化器状态）+ Critic 的激活值
```

对于 Agent 场景，这个差距更大——Agent 轨迹长，KV Cache 本身就吃显存，省掉 Critic 的显存可以换成更长的轨迹长度或更大的 batch size。

**不存在 Critic 估计不准的问题。**

GRPO 的优势完全来自实际 Reward 的比较，不依赖任何网络的估计。只要 Reward 函数本身是可靠的，优势估计就是可靠的。在 Agent 场景中，Reward 通常比 Value 好估计得多——“这条轨迹任务完成了吗”比“从当前状态出发未来大概能得多少分”简单太多。

**更适合结果导向的 Reward。**

Agent 场景中最常见的 Reward 形式是“任务最终完成了给 +1，否则 0”——整条轨迹只有一个 Reward。PPO 在这种场景下需要 Critic 把这个终末 Reward 传播到每一步（通过 GAE），传播过程中误差会累积。GRPO 直接在轨迹级别比较，天然适合这种粗粒度 Reward。

### GRPO 的劣势：什么场景不该选它

**Rollout 成本翻了 N 倍。**

PPO 每个 prompt 只需要 1 条轨迹，GRPO 需要 N 条。在 Agent 场景中，一条轨迹可能涉及多次工具调用，每次调用都有延迟。N=8 意味着 rollout 时间（和工具调用成本）翻 8 倍。

```text
Rollout 成本对比（假设每条轨迹 5 次工具调用，每次 2 秒）：

PPO:  1 条轨迹 × 10 秒 = 10 秒/prompt
GRPO: 8 条轨迹 × 10 秒 = 80 秒/prompt（可并行到 ~10 秒，但 GPU 成本 ×8）
```

如果工具调用涉及付费 API（比如外部搜索引擎、数据库查询），这个成本会更直接。

**对 Reward 区分度的要求高。**

GRPO 靠同组轨迹之间的 Reward 差异来学习。如果 Reward 区分度低（大部分轨迹得分差不多），GRPO 的学习信号就很弱。

```text
好的 Reward 分布（GRPO 友好）：
轨迹 1: 0.9  轨迹 2: 0.3  轨迹 3: 0.7  轨迹 4: 0.1
→ 有明显的排序，GRPO 能学到东西

差的 Reward 分布（GRPO 不友好）：
轨迹 1: 0.82  轨迹 2: 0.79  轨迹 3: 0.81  轨迹 4: 0.78
→ 差异太小，归一化后的优势接近噪声
```

PPO 不存在这个问题，因为它的优势估计来自 Critic，不依赖同组比较。

**不擅长 step-level 的信用分配。**

GRPO 原版对整条轨迹给一个统一的优势分数。但 Agent 轨迹中，可能前 4 步都是对的，第 5 步选错了工具导致失败——GRPO 会给整条轨迹一个负优势，前 4 步被错误惩罚了。

PPO 通过 GAE 可以做 step-level 的信用分配——每一步有各自的优势估计，更精细。

缓解方法：GRPO 的变体可以引入 step-level 的 Reward（比如每一步工具调用成功 +0.1），但这就回到了“需要设计过程 Reward”的老问题。

## 全面对比

| 维度 | PPO | GRPO |
|---|---|---|
| Critic 网络 | 需要，额外显存和训练成本 | 不需要 |
| 显存占用 | 高（Policy + Critic + 两套优化器） | 中（Policy + Reference） |
| 每 prompt rollout 数 | 1 条 | N 条（通常 8） |
| 优势估计方式 | Value 网络 + GAE | 组内 Reward 归一化 |
| 信用分配粒度 | step-level（通过 GAE） | trajectory-level（整条轨迹） |
| 对 Reward 稀疏性的容忍 | 较差（Critic 难学稀疏信号） | 较好（直接比较最终结果） |
| 对 Reward 区分度的要求 | 低 | 高（同组轨迹需要有差异） |
| 训练稳定性 | Critic 估计不准会导致不稳定 | N 太小或 Reward 区分度低时不稳定 |
| 实现复杂度 | 高（GAE、Critic 训练、双网络同步） | 中（主要是 rollout 管理） |
| 代表性工作 | InstructGPT, ChatGPT | DeepSeek-R1, Kimi-K1.5 |

## 企业场景选型指南

不存在“哪个绝对更好”的结论，选型取决于你的具体约束。

### 选 GRPO 的场景

```text
✓ Reward 可以自动计算且区分度高
  → 代码 Agent（测试通过/失败）、SQL Agent（结果正确/错误）
  → 二值 Reward 天然有区分度

✓ GPU 显存紧张
  → 模型大（13B+）、轨迹长（8K+ tokens）
  → 省掉 Critic 的显存可以换更大 batch 或更长轨迹

✓ 团队 RL 基础设施不成熟
  → GRPO 实现比 PPO 简单，不需要调 Critic 的超参
  → 出了问题更容易 debug（没有 Critic 这个变量）

✓ 训练任务的难度可控
  → 可以调整任务采样策略，保证 N 条轨迹有足够差异
```

### 选 PPO 的场景

```text
✓ 需要 step-level 的精细优化
  → 长轨迹（15+ 步）场景，需要知道每一步的好坏
  → 有明确的过程 Reward 可以利用

✓ Rollout 成本极高
  → 工具调用涉及付费 API、长时间计算
  → 每个 prompt 多跑 8 条轨迹不可接受

✓ Reward 区分度低
  → 轨迹之间的 Reward 差异小（比如都在 0.7-0.9 之间）
  → GRPO 的组内比较信号太弱

✓ 已有成熟的 PPO 基础设施
  → 团队有 PPO 调参经验、Critic 训练经验
  → 不需要从零搭建
```

### 混合方案：先 GRPO 后 PPO

一种在企业实践中越来越常见的做法是两阶段训练：

```text
阶段 1：GRPO（快速拉升基线）
├── 用自动 Reward（任务完成率）
├── 不需要 Critic，快速迭代
├── 目标：把 Agent 从"能跑"提升到"大部分场景跑得通"
│
阶段 2：PPO（精细优化）
├── 引入过程 Reward 和更细粒度的评估
├── 用 GRPO 阶段的 checkpoint 初始化 Critic
├── 目标：优化边界场景、减少冗余步骤、提升鲁棒性
```

这个方案的逻辑是：GRPO 在粗粒度优化上效率高（不需要 Critic），PPO 在精细优化上能力强（step-level 信用分配）。先粗调再精调。

## 实战踩坑经验

### 坑 1：GRPO 的 N 条轨迹要真正独立采样

如果你用了 temperature=0 或者 top_p 太小，N 条轨迹可能几乎一模一样——归一化之后 advantage 全是噪声。

```text
错误配置：temperature=0.1, top_p=0.9
→ 8 条轨迹中有 6 条几乎相同

正确配置：temperature=0.7-1.0, top_p=0.95
→ 8 条轨迹有足够的多样性
```

但 temperature 也不能太高——太高轨迹质量太差，高 Reward 的轨迹比例太低，学不到什么。需要根据模型当前的能力调整。

### 坑 2：PPO 的 Critic 不能用太旧的 checkpoint

如果 Policy 更新了很多步但 Critic 还是用的旧参数，Value 估计会严重偏离真实值，导致 Advantage 估计错误。

```text
好的做法：Policy 和 Critic 同步更新，每一步都更新 Critic
坏的做法：Policy 更新 10 步才更新一次 Critic（为了省计算）
```

### 坑 3：KL 约束在两种算法里都不能省

不管是 PPO 还是 GRPO，都需要 KL 散度约束策略不要偏离 SFT checkpoint 太远。在 Agent 场景中，没有 KL 约束最常见的崩溃模式是：

```text
格式退化：模型不再输出合法的 JSON tool call，开始胡乱生成
重复循环：模型学到"多调几次工具"能偶尔碰上正确答案，陷入重复调用
能力崩塌：Agent 能力上去了，但通用对话能力崩了
```

### 坑 4：监控 Reward 分布，而不只是均值

训练过程中只看平均 Reward 是不够的。要同时监控：

```text
必须监控的指标：
├── Reward 均值和方差        趋势是否正常
├── Reward 分布直方图        是否出现双峰（部分 hack，部分正常）
├── 高 Reward 轨迹的人工抽检  模型真的做对了还是在 hack
├── KL 散度                  策略偏离是否在可控范围
├── 有效 prompt 比例 (GRPO)  多少 prompt 的 N 条轨迹有足够差异
└── Critic loss (PPO)        Value 估计是否在收敛
```

## 小结

- PPO 和 GRPO 的核心分歧在优势估计：PPO 用 Critic 网络做绝对估计，GRPO 用组内相对比较
- GRPO 省显存、实现简单、天然适合结果导向的稀疏 Reward，但 rollout 成本翻 N 倍且需要 Reward 有区分度
- PPO 能做 step-level 信用分配、对 Reward 区分度要求低，但 Critic 难训且显存开销大
- 企业选型看三个约束：显存预算、rollout 成本、Reward 粒度。代码/SQL 类 Agent 优先试 GRPO，长轨迹精细优化场景考虑 PPO
- 混合方案（先 GRPO 粗调 + 后 PPO 精调）是越来越常见的工程实践
- 不管选哪个，KL 约束不能省、Reward 分布要监控、高 Reward 轨迹要人工抽检

下一篇建议继续看：

- [训练数据配比实战：Agent 不只吃轨迹数据](../04-data-mix/index.html)
