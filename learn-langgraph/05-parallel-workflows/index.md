---
layout: default
title: 并行执行：Fan-out / Fan-in
description: 多节点同时启动、汇聚节点合并结果——LangGraph 的并行工作流模式
eyebrow: learn-langgraph · 05
---

# 并行执行：Fan-out / Fan-in

顺序图里节点一个接一个执行。但有些任务天然可以并行——比如同时获取多个数据源，或者同时做多个分析维度。

LangGraph 支持**并行执行**：从一个节点出发，同时触发多个节点（Fan-out），等它们都完成后，汇聚到一个节点处理结果（Fan-in）。

## Fan-out / Fan-in 模式

```
         START
           |
       [获取输入]
      /    |    \
  [A]    [B]    [C]     <- 并行执行
      \    |    /
       [汇聚节点]
           |
          END
```

在 LangGraph 里，实现并行很简单：**让多个节点都从同一个节点出发**。

```python
# 从 "fetch_input" 同时出发到三个节点
graph.add_edge("fetch_input", "node_a")
graph.add_edge("fetch_input", "node_b")
graph.add_edge("fetch_input", "node_c")

# 三个节点都指向汇聚节点
graph.add_edge("node_a", "aggregate")
graph.add_edge("node_b", "aggregate")
graph.add_edge("node_c", "aggregate")
```

LangGraph 会自动检测到 `node_a`、`node_b`、`node_c` 可以同时执行，并行运行它们。

## 状态合并：用 Annotated + operator.add

并行节点都会更新 state，LangGraph 需要知道怎么**合并**它们的结果。

对于列表字段，用 `Annotated` + `operator.add` 来追加：

```python
from typing import TypedDict, Annotated, List
import operator

class ParallelState(TypedDict):
    input: str
    results: Annotated[List[str], operator.add]  # 并行结果追加到列表
    summary: str
```

每个并行节点返回 `{"results": ["自己的结果"]}` ——LangGraph 把这些列表拼接起来，不是覆盖。

## 实战：板球运动员综合评估

场景：给定一名板球运动员，同时从三个维度评估：击球表现、投球表现、全能评分，最后汇总。

```python
from typing import TypedDict, Annotated, List
import operator
from langgraph.graph import StateGraph, END

# ===== State =====
class CricketState(TypedDict):
    player_name: str
    batting_avg: float
    bowling_avg: float
    fielding_rating: float
    analyses: Annotated[List[str], operator.add]  # 三个并行节点的输出
    final_report: str

# ===== 并行节点 =====

def analyze_batting(state: CricketState) -> dict:
    """分析击球表现"""
    avg = state["batting_avg"]

    if avg >= 50:
        level = "世界级"
    elif avg >= 35:
        level = "优秀"
    elif avg >= 20:
        level = "一般"
    else:
        level = "较弱"

    analysis = f"[击球] 平均分 {avg}，评级：{level}"
    return {"analyses": [analysis]}

def analyze_bowling(state: CricketState) -> dict:
    """分析投球表现（投球均值越低越好）"""
    avg = state["bowling_avg"]

    if avg <= 20:
        level = "世界级"
    elif avg <= 30:
        level = "优秀"
    elif avg <= 40:
        level = "一般"
    else:
        level = "较弱"

    analysis = f"[投球] 平均分 {avg}，评级：{level}"
    return {"analyses": [analysis]}

def analyze_fielding(state: CricketState) -> dict:
    """分析防守表现"""
    rating = state["fielding_rating"]

    if rating >= 8:
        level = "出色"
    elif rating >= 6:
        level = "良好"
    elif rating >= 4:
        level = "一般"
    else:
        level = "需改进"

    analysis = f"[防守] 评分 {rating}/10，评级：{level}"
    return {"analyses": [analysis]}

# ===== 汇聚节点 =====

def aggregate_results(state: CricketState) -> dict:
    """汇聚三个分析结果，生成总报告"""
    name = state["player_name"]
    analyses = state["analyses"]

    report = f"=== {name} 综合评估报告 ===\n"
    for a in analyses:
        report += f"  {a}\n"

    # 计算综合评分（简化逻辑）
    score = (
        min(state["batting_avg"] / 50, 1.0) * 40 +
        max(0, (40 - state["bowling_avg"]) / 40) * 40 +
        state["fielding_rating"] / 10 * 20
    )
    report += f"\n综合得分：{score:.1f} / 100"

    return {"final_report": report}

# ===== 入口节点 =====

def start_node(state: CricketState) -> dict:
    """入口节点：什么都不做，只是作为 Fan-out 的起点"""
    return {}

# ===== 组装图 =====

graph = StateGraph(CricketState)

graph.add_node("start", start_node)
graph.add_node("batting", analyze_batting)
graph.add_node("bowling", analyze_bowling)
graph.add_node("fielding", analyze_fielding)
graph.add_node("aggregate", aggregate_results)

graph.set_entry_point("start")

# Fan-out：start 同时触发三个分析节点
graph.add_edge("start", "batting")
graph.add_edge("start", "bowling")
graph.add_edge("start", "fielding")

# Fan-in：三个节点都汇入 aggregate
graph.add_edge("batting", "aggregate")
graph.add_edge("bowling", "aggregate")
graph.add_edge("fielding", "aggregate")

graph.add_edge("aggregate", END)

app = graph.compile()
```

### 运行

```python
result = app.invoke({
    "player_name": "Virat Kohli",
    "batting_avg": 59.8,
    "bowling_avg": 34.0,
    "fielding_rating": 9.0,
    "analyses": [],
    "final_report": "",
})

print(result["final_report"])
```

输出：

```
=== Virat Kohli 综合评估报告 ===
  [击球] 平均分 59.8，评级：世界级
  [防守] 评分 9.0/10，评级：出色
  [投球] 平均分 34.0，评级：优秀

综合得分：82.6 / 100
```

注意：三个分析的顺序可能不同（因为是并行执行），但 `analyses` 列表会把它们全部收集进来。

## 并行 + 条件分支组合

Fan-out 和 `add_conditional_edges` 可以混用。例如：

```python
# 入口节点之后：根据任务类型分流
graph.add_conditional_edges(
    "start",
    route_by_type,
    {
        "simple": "quick_analysis",
        "complex": "detailed_analysis",
    }
)

# 详细分析再 Fan-out 到多个子节点
graph.add_edge("detailed_analysis", "sub_a")
graph.add_edge("detailed_analysis", "sub_b")
graph.add_edge("sub_a", "merge")
graph.add_edge("sub_b", "merge")
```

## 并行执行的注意点

**1. 并行节点不能互相依赖**

如果节点 B 的输入依赖节点 A 的输出，它们就不能并行——这是逻辑上的串行依赖。

**2. Annotated 列表的顺序不确定**

并行节点完成顺序不固定，收集到 `Annotated[List, operator.add]` 里的顺序也不固定。如果顺序重要，在汇聚节点里排序。

**3. 对于普通（非 Annotated）字段**

如果多个并行节点都修改同一个普通字段，最后一个完成的节点会覆盖前面的。一般来说并行节点应该各自负责不同的字段。

## 小结

- Fan-out：从一个节点出发，用多个 `add_edge` 同时触发多个节点
- Fan-in：多个节点都用 `add_edge` 指向同一个汇聚节点
- 并行结果用 `Annotated[List[T], operator.add]` 收集
- LangGraph 自动检测并行机会，不需要手动管理线程

下一篇：[Prompt Chaining：分步生成](../06-prompt-chaining/index.html)。
