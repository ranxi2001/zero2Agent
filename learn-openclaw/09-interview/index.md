---
layout: default
title: 面试与实习准备
description: Agent 方向的面试考什么，怎么用项目经历证明你真的懂
eyebrow: OpenClaw / 09
---

# 面试与实习准备

你跑通了 Node → Workflow → Agent，改了 pi-mono，部署起了自己的 [你的名字]Claw。

这一节说怎么把这些变成面试竞争力。

---

## Agent 方向面试考什么

2025 年 Agent 相关岗位（AI Engineer、LLM Application Engineer、Agent Developer）的面试通常分三层：

### 层 1：概念理解（筛选层）

考察你有没有真正用过、理解过 Agent，还是只是听说过。

常见问题：

- **Workflow 和 Agent 的区别是什么？**
  > 正确答案的方向：Workflow 是有向路径，执行路径在开发时确定；Agent 在图内部有循环，执行路径由模型在运行时决定。

- **为什么 Agent 比 Chatbot 更难稳定？**
  > 正确答案的方向：Chatbot 每轮结果相对独立；Agent 有多轮工具调用，每一步的输出影响下一步，错误会累积。

- **Tool Calling 的机制是什么？**
  > 正确答案的方向：模型输出结构化的 `tool_calls` JSON，应用层解析并执行对应函数，把结果追加进对话历史，模型再继续。

- **RAG 是什么，什么时候用？**
  > 正确答案的方向：从向量数据库检索相关片段注入上下文，解决 LLM 上下文窗口不够放知识库的问题。

### 层 2：工程经验（核心层）

考察你有没有真正动手解决过问题。

常见问题：

- **你用过哪些工具框架，遇到过什么问题？**
  > 这里你应该能说出：LangChain 的过度抽象导致排查困难，以及你选择轻量级自定义方案的原因。

- **Agent 的上下文管理怎么做？**
  > 短期上下文 + 长期压缩摘要。超出阈值时用 LLM 生成早期对话的摘要，保留近期的完整历史。

- **多 Agent 架构你怎么设计？**
  > 上下文隔离而非主从调度。每个子任务独立进程，避免上下文污染。可并行时用 ThreadPoolExecutor 并发执行。

- **如何评估 Agent 的质量？**
  > 这引出下面的 Eval 话题。

### 层 3：系统设计（高级层）

通常只有高级岗位或 Senior Intern 才会到这层。

- 设计一个能处理 10,000 文件代码库的 Coding Agent
- 如何让 Agent 在多个用户之间安全隔离
- Agent 的观测性（Observability）怎么做

---

## 项目怎么讲

面试官最害怕的是候选人的“项目”只是跑了个 Demo，改了改 Prompt。

你需要能讲清楚**你做了什么判断，遇到了什么问题，怎么解决的**。

### STAR 格式

```
Situation:  我在用 LangChain 搭一个代码审查 Agent
Task:       需要处理大型代码库，上下文经常溢出
Action:     我把 LangChain 换成自定义的 Node/Flow 框架（60 行），
            实现了 offset/limit 的文件读取和对话历史压缩
Result:     上下文使用量降低了约 60%，任务完成率从 73% 提升到 89%
```

数字是关键。哪怕是粗略的估计，也比“提升了很多”有说服力。

---

## Eval（评估）：面试中的加分项

能说清楚如何评估 Agent 的候选人非常少，这是显著的差异化点。

### 什么是 Eval

Eval 是一组有预期输出的测试用例，用来量化 Agent 的任务完成率。

```json
{
  "eval_id": 1,
  "prompt": "在 src/auth.py 第 42 行有一个 SQL 注入漏洞，请修复它",
  "expected_behavior": [
    "读取 src/auth.py",
    "定位第 42 行附近的 SQL 拼接",
    "改为参数化查询",
    "运行测试确认修复"
  ],
  "assertions": [
    "修改后文件不包含字符串拼接 SQL",
    "测试通过"
  ]
}
```

### 简单的 Eval 框架

```python
# eval/runner.py
import subprocess, json

def run_eval(eval_case: dict) -> dict:
    """运行一个 eval case，返回是否通过"""
    result = subprocess.run(
        ["uv", "run", "python", "-m", "agent.main",
         "--task", eval_case["prompt"]],
        capture_output=True, text=True, timeout=300
    )

    passed = []
    for assertion in eval_case["assertions"]:
        # 用 LLM 判断断言是否满足（或者写规则匹配）
        check = call_llm_simple(
            f"判断以下断言是否被满足（只回答 yes/no）：\n"
            f"断言：{assertion}\n"
            f"Agent 执行结果：{result.stdout}"
        )
        passed.append("yes" in check.lower())

    return {
        "eval_id": eval_case["eval_id"],
        "pass_rate": sum(passed) / len(passed),
        "details": passed
    }
```

在面试中能说出“我的 Eval 集有 20 个 case，改了压缩策略之后 pass rate 从 70% 提升到 85%”，比大多数候选人的表述都更有说服力。

---

## 简历怎么写

### 推荐工具：rxresu.me

[rxresu.me](https://rxresu.me) 是一个开源的在线简历生成器，支持中英文、PDF 导出、各种模板。

对程序员友好：可以把简历数据导出为 JSON，用 git 管理版本。

### Agent 项目的描述模板

```
[你的名字]Claw — 个人 Coding Agent
- 从零实现 Node/Flow 核心框架（~60 行），不依赖 LangChain
- 基于 pi-mono 架构，接入 [Kimi/DeepSeek/GLM]，部署于本地，通过飞书对话
- 实现对话历史压缩（超 20 轮时 LLM 生成摘要），上下文使用量降低约 60%
- 构建 20-case Eval 集，任务完成率 [X]%
- 工具集精简至 8 个，排除 bash 安全模式，支持代码审查和文件操作
```

把 X 填上真实数字，其余根据你的实际情况调整。

---

## 实习岗位方向

Agent 方向的实习通常在这几类公司里：

| 类型 | 代表公司 | 岗位名称 |
|------|---------|---------|
| AI 原生 | Kimi、智谱、百川、MiniMax | LLM Application Engineer |
| 大厂 AI 部门 | 阿里通义、腾讯混元、字节豆包 | AI Engineer Intern |
| Coding Agent 方向 | Cursor 类产品、IDE 插件团队 | Agent Developer Intern |
| 工具链 | 各类 DevTool 创业公司 | Full-Stack + AI |

**准备材料清单：**

```
□ GitHub 上有 OpenClaw / pi-mono fork 的改造版本（能跑）
□ README 写清楚：做了什么改动，解决了什么问题
□ 简历项目描述有数字（pass rate / 上下文降低比例）
□ 能流畅讲 Node → Workflow → Agent 的推导过程（5 分钟内）
□ 能回答"为什么不用 LangChain"（有自己的判断，不是背的）
```

---

## 一个最重要的建议

**把 Agent 跑起来，跟它对话。**

面试中被问到的任何细节——上下文溢出怎么办、工具调用出错怎么处理、怎么评估质量——如果你真的跑过，就会有真实的感受和判断。

如果你只是读了文档，这些问题很难回答得自然。

这套课程的最终目标：你有一个真正跑起来的、属于你自己的 Agent，用来辅助你的日常编程。其他的都是副产品。

---

[← 返回 OpenClaw 模块首页](../index.html)
