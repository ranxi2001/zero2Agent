---
layout: default
title: Tool / MCP / Skill 全解析
description: 三种工具形式的本质区别，以及为什么少即是多
eyebrow: OpenClaw / 04
---

# Tool / MCP / Skill 全解析

"工具"这个词在 Agent 领域被滥用了。不同的框架、不同的文档，对"工具"的定义并不一样。

这一节把工具拆成三种形式，搞清楚它们的边界和使用场景。

---

## 三种工具形式

| 类型 | 调用方式 | 本质 | 例子 |
|------|---------|------|------|
| **Tool** | 本地函数调用 | Python 函数 | `read_file()`, `bash()` |
| **MCP** | 远程进程调用 | 独立进程，标准协议 | MCP Server |
| **Skill** | 本地进程调用 | 结构化能力包 | `tools/skills/pdf/` |

三者最核心的区别是**调用边界**：

- Tool 在当前进程内直接执行
- MCP 通过 IPC/stdio 跨进程通信
- Skill 是介于两者之间的结构化包装

---

## Tool：最基本的形式

Tool 就是一个 Python 函数加上给 LLM 看的描述。

```python
# tools/builtins/file_ops.py
from tools.base import Tool

class ReadFile(Tool):
    name = "read"
    description = "读取文件内容，支持 offset 和 limit 参数"
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "文件路径"},
            "offset": {"type": "integer", "description": "起始行（可选）"},
            "limit": {"type": "integer", "description": "读取行数（可选）"}
        },
        "required": ["path"]
    }

    def run(self, path: str, offset: int = 0, limit: int = None) -> str:
        with open(path) as f:
            lines = f.readlines()
        if limit:
            lines = lines[offset:offset + limit]
        else:
            lines = lines[offset:]
        return "".join(lines)
```

`Tool` 基类提供 `to_llm_format()` 方法，把 `name`/`description`/`parameters` 转成 OpenAI function calling 格式。

### OpenClaw 的 8 个内置工具

```python
# tools/builtins/__init__.py
from .file_ops import ReadFile, WriteFile, EditFile, ListDir
from .shell import Bash
from .search_ops import Grep, Find
from .web import SearchWeb

ALL_TOOLS = [ReadFile(), WriteFile(), EditFile(), ListDir(),
             Bash(), Grep(), Find(), SearchWeb()]
```

为什么是这 8 个？Vercel 的工程团队做过一个实验：把内置工具从 20+ 削减到 8 个，Agent 任务完成率反而提升了约 15%。

**原因**：工具越多，模型在"选哪个"上消耗的决策空间越大，越容易选错或组合错。职责清晰、数量少的工具更容易被正确使用。

**实用原则：能用 `bash` 解决的，不要单独做工具。**

---

## MCP：Anthropic 提出的跨进程标准

MCP（Model Context Protocol）是 Anthropic 在 2024 年底提出的标准协议，用于 LLM 和外部工具服务之间的通信。

<div class="mermaid">
flowchart LR
    A[Claude / Agent] -->|stdio 或 HTTP| B[MCP Server]
    B --> C[文件系统]
    B --> D[数据库]
    B --> E[第三方 API]
</div>

MCP Server 是独立的进程（可以是 Node.js、Python、Go……），通过标准化的 JSON-RPC 格式对外暴露工具列表和调用接口。

### 什么时候用 MCP

- 工具需要**跨语言**（Agent 是 Python，工具是 Node.js）
- 工具需要**多个 Agent 共享**（一个 MCP Server，多个客户端）
- 需要**复用社区已有的 MCP Server**（如 GitHub MCP、Slack MCP）

### 什么时候不用 MCP

- 工具只有一个 Agent 使用
- 工具逻辑简单，不到 50 行

过度使用 MCP 会增加进程管理和序列化开销。对于简单工具，直接写 Tool 类更清晰。

---

## Skill：结构化能力包

Skill 是 OpenClaw 特有的概念，介于 Tool 和完整 Agent 之间。

它不是一个单一函数，而是一个**有内部流程的能力单元**——可以包含多步骤、子流程、甚至自己的 LLM 调用。

```
tools/skills/
  pdf/
    skill.py        ← 入口：接收参数，返回结果
    extract.py      ← 内部步骤：PDF 文本提取
    summarize.py    ← 内部步骤：LLM 摘要
    schema.json     ← 给 LLM 看的描述
```

```python
# tools/skills/pdf/skill.py
class PDFSkill(Tool):
    name = "process_pdf"
    description = "提取 PDF 内容并生成结构化摘要"

    def run(self, path: str) -> str:
        text = extract_pdf(path)
        summary = summarize(text)
        return summary
```

从 LLM 的角度看，Skill 和 Tool 没有区别——都是一次函数调用。区别在于内部实现的复杂度。

---

## Tool Executor：统一调用层

所有工具（Tool 和 Skill）通过同一个执行器统一调用：

```python
# tools/executor.py
import json

class ToolExecutor:
    def __init__(self, tools: list):
        self.tool_map = {t.name: t for t in tools}

    def execute(self, tool_calls: list) -> list:
        results = []
        for call in tool_calls:
            name = call["function"]["name"]
            args = json.loads(call["function"]["arguments"])
            tool = self.tool_map.get(name)
            if tool:
                output = tool.run(**args)
                results.append(ToolResult(
                    tool_call_id=call["id"],
                    name=name,
                    output=str(output)
                ))
            else:
                results.append(ToolResult(
                    tool_call_id=call["id"],
                    name=name,
                    output=f"Tool '{name}' not found"
                ))
        return results
```

`ToolResult.to_message()` 把结果转成 OpenAI 格式的 `tool` 角色消息，追加进对话历史。

---

## 工具系统的整体结构

```
tools/
  base.py              ← Tool 基类，to_llm_format()
  executor.py          ← ToolExecutor，统一调用
  builtins/
    __init__.py        ← ALL_TOOLS 列表
    file_ops.py        ← read, write, edit, ls
    shell.py           ← bash
    search_ops.py      ← grep, find
    web.py             ← search（DuckDuckGo）
  skills/
    pdf/               ← PDF 处理能力包
    ...
```

---

## 工具安全性

Bash 工具是双刃剑：功能强大，但执行任意 shell 命令有安全风险。

在生产环境，可以加沙箱限制：

```python
class Bash(Tool):
    BLOCKED_PATTERNS = [
        r"rm\s+-rf",
        r"sudo",
        r"curl.*\|.*sh",   # 禁止管道执行远程脚本
    ]

    def run(self, command: str) -> str:
        for pattern in self.BLOCKED_PATTERNS:
            if re.search(pattern, command):
                return f"Command blocked: matches security pattern '{pattern}'"
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        return result.stdout + result.stderr
```

在 Coding Agent 场景（只操作本地项目），轻量级的模式匹配就够了。

---

下一篇：[Context 与 Memory](../05-memory/index.html)
