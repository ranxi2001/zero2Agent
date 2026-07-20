# Agent API Lab

这套实验用于观察“大模型请求、模型决策、工具执行、结果回传、下一轮请求”之间的协议关系。默认使用确定性的 `FakeProvider`，不联网、不需要 API Key，也不会因为模型版本变化而让测试随机失败。

这里的数据结构是跨厂商的教学模型，不是某一家 API 的完整 Schema。OpenAI Responses API、OpenAI-compatible Chat Completions、Anthropic Messages API 和 Gemini API 会使用不同字段名；共同不变量是：模型提出工具调用，Harness 执行工具，并把结果与对应调用建立因果关联。

## 快速运行

```powershell
python examples/agent-api-lab/run_lab.py
python examples/agent-api-lab/run_lab.py --scenario invalid_args
python examples/agent-api-lab/run_lab.py --scenario parallel --all-ablations
python examples/agent-api-lab/run_lab.py --transient-failures 1
python examples/agent-api-lab/run_lab.py --fault timeout --fault 5xx
```

需要查看逐轮协议时，可以输出经过尽力脱敏的 JSONL trace：

```powershell
python examples/agent-api-lab/run_lab.py `
  --scenario parallel `
  --trace examples/agent-api-lab/artifacts/parallel.jsonl
```

## 场景矩阵

| 场景 | 观察重点 |
| --- | --- |
| `text` | 普通文本响应不会误入工具循环 |
| `single` | 一次工具请求和结果回传 |
| `parallel` | 同一轮多个调用如何用 ID 分别关联 |
| `parallel_partial_failure` | 并行调用部分失败时保留成功结果 |
| `invalid_args` | 参数校验失败如何作为结果进入下一轮，并由模型修正 |
| `tool_failure` | 工具失败时不伪造结果 |
| `repeat` | 相同动作重复出现时由 Loop Guard 终止 |
| `refusal` | 内容拒绝不能被误报为正常完成 |
| `truncated` | 输出截断必须进入恢复或失败分支 |
| `duplicate_ids` | 同一批次的重复调用 ID 会在工具执行前被拒绝 |
| `truncated_tool_call` | 带工具请求的截断响应不会产生工具副作用 |

## 上下文消融

`--all-ablations` 对同一任务改变一个变量：

- `complete`：完整结构化轨迹，作为基线。
- `drop_assistant_call`：删除模型先前提出的工具请求。
- `mismatch_call_id`：让工具结果指向不存在的调用。
- `flatten_roles`：把所有角色和结构拍平成一段用户文本。
- `sliding_window`：机械保留最末消息，切断用户目标与工具结果的因果链。

实验输出包含状态、迭代次数、模型调用次数、工具调用次数和估算输入量。这里的 `input_units` 只是稳定的本地比较量，不冒充供应商账单 token。真实缓存命中、TTFT、token 和费用只能使用供应商实际返回的指标。

## 流式响应为什么需要状态机

`StreamAssembler` 演示两条规则：文本增量可以边到边显示，工具参数则必须等完整 JSON 和完成事件后才能执行。半截流、缺少完成事件或参数 JSON 不完整都会被判为协议错误。

不要把供应商内部推理或原始思维链当作稳定业务接口。生产系统应记录公开输出、工具调用、工具结果、停止原因和供应商允许保存的 reasoning summary，而不是依赖不可移植的私有推理文本。

## 测试

```powershell
python -m unittest discover -s examples/agent-api-lab/tests -v
```

测试覆盖普通文本、正常单工具、并行工具、参数修正、重复动作熔断、限流/超时/5xx 重试、拒绝与截断、无效模型响应、四种上下文破坏、流式参数组装和日志脱敏。

脱敏只能作为纵深防御，不能证明任意自由文本中都没有秘密。生产系统不应把 API Key、Cookie、Authorization Header 或用户敏感数据放进模型消息和工具自由文本；trace 还应配合字段白名单、访问控制和保留期限。

## 真实 API 适配

实验故意不绑定真实供应商。接入真实 API 时，应在适配器中把供应商的 response items、content blocks 或 candidates 转成这里的 `ModelTurn`，再把 `Message` 轨迹映射回供应商请求格式。这样协议测试仍然稳定，供应商差异集中在适配层。
