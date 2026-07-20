---
layout: default
title: Loop Engineering：让 Agent 自主迭代直到正确
description: Agent 执行循环中的自我纠错、退出判断与防护设计
eyebrow: Agent Basic / 10
---

# Loop Engineering：让 Agent 自主迭代直到正确

2026 年 6 月起，"Loop Engineering"成为 Agent 面试的高频词。它不是一个全新概念——Agent 本身就是循环，但过去大家把注意力放在单次迭代的质量上（Prompt 写得好不好、工具调得对不对）。Loop Engineering 关注的是**循环本身的工程设计**：什么时候该再来一轮、什么时候该停、怎么防止跑飞、怎么让每一轮比上一轮更接近正确答案。

一句话定义：**Loop Engineering 是对 Agent 执行循环的退出条件、纠错策略和资源约束进行系统化工程设计的实践。**

## 和 Prompt / Context / Harness Engineering 的层次关系

这些术语经常在面试中被放在一起问。它们不是互斥的选择，也不是严格的行业标准分层，而是观察同一套 Agent 系统的不同视角：

| 层次 | 关注点 | 典型产出 |
|------|--------|---------|
| Prompt Engineering | 单次 LLM 调用的输入质量 | 模板、Few-shot、结构化指令 |
| Context Engineering | 送进模型的上下文组合 | 记忆检索、RAG 注入、上下文压缩 |
| Harness Engineering | 模型外的上下文、工具、约束、验证与纠正体系 | 工具注册、状态管理、权限、验证器 |
| Agent Loop | 驱动模型决策、工具执行和状态更新的执行内核 | 协议循环、工具派发、状态转移 |
| **Loop Engineering** | **循环本身的迭代策略和退出判断** | **纠错模式、收敛检测、防护机制** |

Harness 的范围大于 Loop：它还包含循环之外的上下文装配、权限、验证和人工审批。Agent Loop 解决"如何跑一轮"；Loop Engineering 解决"要跑多少轮、跑偏后怎么拉回来、凭什么宣布完成"。

第 09 篇中的 Agent Infra 则是承载这些逻辑的运行时、持久化、可观测和治理底座。把四者拆开后，故障归因会清楚很多：消息缺失是 Context/协议问题，工具越权是 Harness 问题，反复重试是 Loop 问题，进程恢复失败是 Infra 问题。

## 为什么需要单独谈 Loop Engineering

大多数 Agent 的 bug 不出在单次调用——模型一般能理解指令、工具一般能正确执行。问题出在**循环层面**：

- 模型认为任务没完成，反复重试同一个已经成功的操作
- 检索到了错误文档，下一轮基于错误上下文继续推理，错误滚雪球
- 生成了代码但没验证，发现错误后重写，新版本引入另一个 bug，无限震荡
- Token 预算在第 3 轮就耗尽了，但 Agent 毫无知觉地继续调用直到报错

这些问题的共同特征是：单步逻辑没错，但循环策略失控。

## 从 API 协议落到可验证 Agent Loop

一个真实的工具调用循环，不是把模型输出的文本交给 `eval()`，而是维护一条结构化轨迹：

```text
1. Harness 组装 system/developer 指令、用户目标、历史轨迹和工具定义
2. 模型返回公开文本，或一个/多个结构化工具调用请求
3. 先把完整 assistant 决策写入轨迹
4. 校验工具名、参数和协议关联信息，再执行客户端工具
5. 按当前协议把每个工具结果与对应调用写回轨迹
6. 下一轮重新提交所需上下文，直到验证通过或触发退出条件
```

这里有四条不能破坏的协议不变量：

1. **工具请求不等于客户端工具已经执行。** 客户端 function tool 只有通过 Harness 的权限检查后才执行；供应商托管工具则可能由服务端执行，必须在请求配置和审计中单独治理。
2. **assistant 决策必须先入轨迹。** 如果只留下工具结果，下一轮无法知道结果对应哪次决策。
3. **工具结果必须与调用一一关联。** 并行调用时尤其不能靠数组位置或工具名称猜测。
4. **流式参数必须组装完成后再校验执行。** 收到半段 JSON 不代表工具调用已经完成。

下面是比“30 行 Demo”更接近生产语义的伪代码：

```text
while not should_stop(state):
    request = context_builder.build(state)
    response = model.complete(request)
    terminal = normalize_terminal_state(response)
    validate_typed_response(response, terminal)
    state.history.append(response.assistant_message)

    if terminal in {"refused", "incomplete", "failed", "cancelled"}:
        return handle_non_success_terminal(terminal, response)

    if terminal == "tool_calls":
        for call in response.tool_calls:
            args = schema.validate(call.arguments)
            result = tool_registry.execute(call.name, args)
            state.history.append(link_tool_result(call, result))
        checkpoint(state)
        continue

    if terminal != "completed":
        return protocol_error(terminal, response)

    verification = verifier.check(response.public_output)
    if verification.passed:
        return success(response.public_output)
    state.history.append(verification.feedback)
```

注意这里记录的是公开输出、工具调用、工具结果和验证反馈，不要求读取或保存模型的私有思维链。不同供应商可能返回 reasoning summary、签名块或不透明状态，这些都应由适配层处理，不能成为业务逻辑的隐式依赖。

### 用确定性实验验证协议

[Agent API Lab](../../examples/agent-api-lab/index.html) 用 Fake Provider 跑同一套循环，因此不需要 API Key，也不会受模型随机性影响。它覆盖：

- 单工具和同轮并行工具调用
- 非法参数作为结构化失败回传，下一轮再修正
- 瞬时 429 限流的有限重试
- 相同动作重复时的 Loop Guard
- 删除 assistant 工具请求、错配 call ID、拍平角色和机械滑窗四种消融
- 流式工具参数的增量组装与半截流拒绝

可以直接运行：

```powershell
python examples/agent-api-lab/run_lab.py --scenario parallel
python examples/agent-api-lab/run_lab.py --scenario parallel --all-ablations
python -m unittest discover -s examples/agent-api-lab/tests -v
```

先用 Fake Provider 验证状态机，再接真实模型，可以先隔离一部分变量：确定性测试失败通常说明 Harness 或内部协议有 bug；只在真实接入中失败时，还要依次排查 provider adapter、SDK/Schema、流事件、鉴权与配额，确认集成层正常后，再评估模型能力、提示词和任务分布。

## 四种核心 Loop 模式

### 1. ReAct Loop（思考-行动循环）

最基础的 Agent 循环。每轮根据当前轨迹做 Decision（决定下一步），再 Action（调用工具），最后 Observation（接收结果），然后决定是否继续。经典论文常把第一步写作 Thought，但工程实现不应假设供应商一定暴露原始思维链。

```text
while not done:
    decision = llm("根据当前状态，下一步该做什么？")
    action = parse_tool_call(decision)
    observation = execute(action)
    context.append(decision.public_message, action, observation)
    done = llm("任务是否完成？")
```

**Loop Engineering 在这里的关键设计**：
- `done` 的判断不能只靠模型自己说"完成了"——需要外部验证
- 连续 N 轮 Action 相同且 Observation 不变 → 强制终止（防止死循环）

### 2. Reflection Loop（反思循环）

在 ReAct 基础上增加一个"回头看"的步骤：Agent 执行完一轮后，显式评估自己的产出质量，决定是接受还是修改。

```text
while attempts < max_attempts:
    output = generate(task, context)
    critique = reflect(output, criteria)
    if critique.passed:
        return output
    context.append(critique.feedback)
    attempts += 1
```

**适用场景**：代码生成、文案撰写、方案设计——产出质量可被结构化评估的任务。

**核心设计决策**：Reflection 用同一个模型还是不同模型？用同一个模型容易"自我欺骗"（对自己的错误视而不见）；用更强的模型做裁判则成本翻倍。工程上的平衡点是：用同一个模型做 Reflection，但给它不同的 system prompt（扮演审核者角色），加上结构化检查清单。

### 3. Verification Loop（验证循环）

产出不是靠模型自我评价，而是靠**外部验证器**确认。验证器可以是：单元测试、类型检查、正则匹配、人工审批、沙箱执行。

```text
while attempts < max_attempts:
    output = generate(task, context)
    result = verify(output)  # 外部验证器
    if result.success:
        return output
    context.append(f"验证失败：{result.error}")
    attempts += 1
```

**这是生产级 Agent 最常用的模式。** 因为验证结果是确定性的（测试要么过要么不过），不存在模型"自我欺骗"的问题。

Claude Code 的代码生成就是典型的 Verification Loop：生成代码 → 跑测试 → 如果失败，把错误信息塞回上下文 → 重新生成 → 再跑测试。

### 4. Self-Correction Loop（自我修正循环）

比 Reflection 更进一步：不仅识别问题，还要在不重新生成全部内容的前提下**局部修复**。

```text
while attempts < max_attempts:
    if attempts == 0:
        output = generate(task, context)
    else:
        output = patch(output, error_info)  # 局部修复而非全量重写
    result = verify(output)
    if result.success:
        return output
    error_info = diagnose(output, result.error)
    attempts += 1
```

**优势**：节省 token（不用每次重新生成完整输出）、修复更精准。

**风险**：连续 patch 可能导致产出质量逐轮下降（补丁摞补丁）。工程上需要设一个"patch 次数上限"，超过后回退到全量重新生成。

## 退出条件设计

Loop Engineering 最关键的工程决策是：**什么时候停下来？**

| 退出策略 | 原理 | 适用场景 |
|----------|------|---------|
| Max Iterations | 硬上限，超过即终止 | 所有场景的兜底 |
| Convergence Check | 连续 N 轮输出不再变化 → 收敛 | 优化类任务 |
| Confidence Threshold | 模型自评置信度 > 阈值 | 信息检索、QA |
| External Verification | 外部验证器通过 | 代码、数据、格式类任务 |
| Token Budget | 累计消耗 token 达上限 | 成本敏感场景 |
| Wall-clock Timeout | 总耗时超限 | 用户面向型产品 |
| Repetition Detection | 检测到重复行为模式 | 防死循环 |

**生产系统通常组合使用 3-4 种退出策略**，形成多重保险：

```text
def should_stop(state):
    if state.iterations >= MAX_ITER:           return "max_iter"
    if state.tokens_used >= TOKEN_BUDGET:      return "budget"
    if state.wall_clock() >= TIMEOUT:          return "timeout"
    if state.last_n_same(3):                   return "stuck"
    if state.verifier_passed:                  return "success"
    return None  # 继续
```

## 工程落地的关键实践

### 循环防护（Loop Guard）

防止 Agent 在循环中失控的机制：

1. **行为指纹去重**：记录每轮的 (action_type, params_hash)，连续 2 次相同指纹 → 强制切换策略或终止
2. **渐进式降级**：第 1-3 轮正常执行 → 第 4-5 轮切换到更简单的策略 → 第 6 轮强制输出当前最优结果
3. **上下文污染检测**：如果错误信息在上下文中累积过多（超过总 token 的 30%），触发上下文重置

### Token Budget 管理

一次完整的 Loop 可能消耗 10 万+ token。必须有预算意识：

```text
budget = TokenBudget(total=100_000)

while not should_stop(state):
    remaining = budget.remaining()
    if remaining < MINIMUM_USEFUL:  # 剩余不够一轮有意义的调用
        return best_so_far
    
    # 根据剩余预算调整策略
    if remaining < budget.total * 0.2:
        strategy = "精简模式"  # 缩短 prompt、跳过 reflection
    else:
        strategy = "完整模式"
```

### 状态快照（Checkpoint）

长循环中任何一轮都可能因为网络超时、服务重启而中断。必须能从中间状态恢复：

- 每轮结束后持久化当前状态（iteration count、最新输出、上下文摘要）
- 恢复时从最近的 checkpoint 继续，而不是从头开始
- LangGraph 的 `StateSnapshot` 和 `MemorySaver` 就是为这个场景设计的

### 可观测性

Loop 内部发生了什么，必须对外可见：

| 监控项 | 为什么重要 |
|--------|-----------|
| 每轮迭代的 action + result | 排查"为什么跑了 10 轮" |
| token 消耗曲线 | 发现成本异常 |
| 退出原因分布 | 判断系统健康度（success 占比 vs timeout 占比） |
| 平均迭代次数 | 衡量系统效率 |
| 重复行为比例 | 发现潜在死循环 |

## 典型面试问题

这些问题在 6-7 月的面试中高频出现：

1. **Prompt / Context / Harness / Loop Engineering 四者有什么区别？**（成都某中厂 Agent 产品开发实习）
2. **Agent 循环中怎么防止死循环？退出条件怎么设计？**（快手、淘天）
3. **Verification Loop 和 Reflection Loop 分别适用什么场景？**
4. **如果 Agent 连续 3 轮犯同一个错误，该怎么处理？**
5. **Token 预算快耗尽时，Agent 应该怎么降级？**
6. **上下文压缩在循环过程中导致之前的流程丢失，怎么解决？**（不鸣科技 AI Native 开发）

## 小结

- Loop Engineering 不是新发明，而是对 Agent 循环控制层面的工程关注度提升
- Prompt、Context、Harness、Agent Loop、Loop Engineering 是不同观察层次，不要把 Harness 简化成一个 `while` 循环
- 核心模式四种：ReAct / Reflection / Verification / Self-Correction，生产中最常用 Verification Loop
- 退出条件必须多重组合，单一策略在生产中不可靠
- 循环防护、token budget、checkpoint、可观测性——四件事缺一不可

## 参考与延伸

- 李博杰《深入理解 AI Agent》第二章“上下文工程”，固定参考版本：[bojieli/ai-agent-book@e3883f8c](https://github.com/bojieli/ai-agent-book/blob/e3883f8cec222c31e59c646be96641120863027e/book/chapter2.md)。本文使用独立结构、示例和实验代码重新组织。

下一篇建议继续看：

- [Agent Infra：从 Harness 到生产环境](../09-agent-infra/index.html)——Loop 设计好之后，需要 Infra 支撑它在生产中稳定运行
