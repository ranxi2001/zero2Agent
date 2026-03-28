---
layout: default
title: 顺序图：第一个可运行的 Workflow
description: 用 add_edge 连接多个节点，构建顺序执行的 LangGraph Workflow——以 BMI 计算器为例
eyebrow: learn-langgraph · 03
---

# 顺序图：第一个可运行的 Workflow

顺序图是 LangGraph 里最简单的模式：节点 A 执行完，接着执行节点 B，再接着节点 C，没有分支，没有循环。

这一篇用一个 BMI 计算器来演示，因为它的逻辑足够清晰：输入 → 计算 → 分类 → 输出。

## 为什么从顺序图开始

顺序图没有额外的复杂度，可以让你专注于 LangGraph 的基本操作：

1. 怎么设计 State
2. 怎么写节点
3. 怎么用 `add_edge` 连接节点
4. 怎么运行和查看结果

学完这篇，条件分支（下一篇）只是在顺序图基础上加了一个路由函数。

## BMI 计算器：需求

输入：身高（cm）、体重（kg）、姓名

步骤：
1. 验证输入
2. 计算 BMI 值
3. 根据 BMI 分类（偏瘦/正常/超重/肥胖）
4. 生成健康建议
5. 格式化输出报告

## 代码实现

```python
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END

# ===== State 定义 =====
class BMIState(TypedDict):
    name: str
    height_cm: float
    weight_kg: float
    bmi: float
    category: str
    advice: str
    report: str
    error: Optional[str]

# ===== 节点定义 =====

def validate_input(state: BMIState) -> dict:
    """验证输入数据"""
    height = state["height_cm"]
    weight = state["weight_kg"]

    if height <= 0 or height > 300:
        return {"error": f"身高数据异常: {height}cm"}
    if weight <= 0 or weight > 500:
        return {"error": f"体重数据异常: {weight}kg"}

    return {"error": None}

def calculate_bmi(state: BMIState) -> dict:
    """计算 BMI"""
    if state.get("error"):
        return {}

    height_m = state["height_cm"] / 100
    bmi = state["weight_kg"] / (height_m ** 2)
    bmi = round(bmi, 2)

    return {"bmi": bmi}

def classify_bmi(state: BMIState) -> dict:
    """BMI 分类"""
    if state.get("error"):
        return {}

    bmi = state["bmi"]

    if bmi < 18.5:
        category = "偏瘦"
    elif bmi < 24.9:
        category = "正常"
    elif bmi < 29.9:
        category = "超重"
    else:
        category = "肥胖"

    return {"category": category}

def generate_advice(state: BMIState) -> dict:
    """生成健康建议"""
    if state.get("error"):
        return {}

    category = state["category"]
    advice_map = {
        "偏瘦": "建议适量增加营养摄入，加强力量训练，必要时咨询营养师。",
        "正常": "保持当前的饮食和运动习惯，定期体检。",
        "超重": "建议控制饮食，每周至少进行 150 分钟中等强度有氧运动。",
        "肥胖": "建议在医生指导下制定减重计划，注意饮食结构和规律运动。",
    }

    return {"advice": advice_map[category]}

def format_report(state: BMIState) -> dict:
    """生成最终报告"""
    if state.get("error"):
        report = f"错误：{state['error']}"
    else:
        report = f"""
=== BMI 健康报告 ===
姓名：{state['name']}
身高：{state['height_cm']} cm
体重：{state['weight_kg']} kg
BMI：{state['bmi']}
分类：{state['category']}
建议：{state['advice']}
""".strip()

    return {"report": report}

# ===== 组装图 =====

graph = StateGraph(BMIState)

# 添加节点
graph.add_node("validate", validate_input)
graph.add_node("calculate", calculate_bmi)
graph.add_node("classify", classify_bmi)
graph.add_node("advise", generate_advice)
graph.add_node("format", format_report)

# 设置顺序边
graph.set_entry_point("validate")
graph.add_edge("validate", "calculate")
graph.add_edge("calculate", "classify")
graph.add_edge("classify", "advise")
graph.add_edge("advise", "format")
graph.add_edge("format", END)

app = graph.compile()
```

## 运行

```python
# 正常输入
result = app.invoke({
    "name": "张三",
    "height_cm": 175.0,
    "weight_kg": 70.0,
    "bmi": 0.0,
    "category": "",
    "advice": "",
    "report": "",
    "error": None,
})
print(result["report"])
```

输出：

```
=== BMI 健康报告 ===
姓名：张三
身高：175.0 cm
体重：70.0 kg
BMI：22.86
分类：正常
建议：保持当前的饮食和运动习惯，定期体检。
```

```python
# 异常输入
result = app.invoke({
    "name": "李四",
    "height_cm": -10.0,
    "weight_kg": 60.0,
    "bmi": 0.0,
    "category": "",
    "advice": "",
    "report": "",
    "error": None,
})
print(result["report"])
# 输出：错误：身高数据异常: -10.0cm
```

## 用 stream 观察每个节点的输出

```python
for step in app.stream({
    "name": "王五",
    "height_cm": 160.0,
    "weight_kg": 80.0,
    "bmi": 0.0,
    "category": "",
    "advice": "",
    "report": "",
    "error": None,
}):
    node_name, state_update = list(step.items())[0]
    print(f"[{node_name}] {state_update}")
```

输出：

```
[validate] {'error': None}
[calculate] {'bmi': 31.25}
[classify] {'category': '肥胖'}
[advise] {'advice': '建议在医生指导下制定减重计划，注意饮食结构和规律运动。'}
[format] {'report': '=== BMI 健康报告 ===\n...'}
```

每个节点输出的是它修改的字段，不是完整 state。这就是 stream 模式的用法：可以实时看到每一步的结果。

## 顺序图的图结构

```
START
  |
validate
  |
calculate
  |
classify
  |
advise
  |
format
  |
END
```

五个节点，五条边，没有分叉。`add_edge(A, B)` 的意思是：节点 A 完成后，**无条件**执行节点 B。

## 初始 State 怎么设置

注意调用 `invoke` 时我们传入了完整的初始 state，包括 `bmi: 0.0`、`category: ""`、`report: ""` 这些"空值"。

这是因为 `TypedDict` 要求字段完整。实际项目里通常有两种处理方式：

**方式一：用 Optional 加默认值**

```python
class BMIState(TypedDict):
    name: str
    height_cm: float
    weight_kg: float
    bmi: Optional[float]      # 允许为 None
    category: Optional[str]
    advice: Optional[str]
    report: Optional[str]
    error: Optional[str]
```

这样初始 state 里未知字段传 `None` 就行。

**方式二：用 `total=False`**

```python
class BMIState(TypedDict, total=False):
    name: str
    height_cm: float
    # ...其他字段不是必填的
```

`total=False` 让所有字段都变成可选的。

## 小结

顺序图的要点：

- `add_edge(A, B)` = A 完成后执行 B，无条件
- `set_entry_point("node_name")` = 从哪个节点开始
- `add_edge("last_node", END)` = 告诉 LangGraph 到这里结束
- `invoke` 运行图，传入初始 state，返回最终 state
- `stream` 流式运行，每个节点完成后 yield 一次

下一篇加入条件判断：[条件分支：add_conditional_edges](../04-conditional-edges/index.html)。
