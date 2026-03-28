---
layout: default
title: Tool Use：扩展模型能触达的边界
description: dispatch map 设计——加一个工具，只加一个 handler，循环永远不变
eyebrow: Claude Code / s02
---

# Tool Use：扩展模型能触达的边界

> *"加一个工具，只加一个 handler"*

s01 只有一个 `bash` 工具。这一节加 3 个专用工具，同时引入一个关键设计：**dispatch map**。

加工具不需要改循环。循环永远不变。

---

## 问题

只有 `bash` 时，所有操作都走 shell：

- `cat` 输出可能被截断，不可预测
- `sed` 遇到特殊字符就崩
- 每次 bash 调用都是不受约束的安全面，没有路径沙箱

专用工具（`read_file`、`write_file`、`edit_file`）可以在工具层做路径验证，防止模型意外访问工作区外的文件。

**关键洞察：加工具不需要改循环。**

---

## dispatch map 设计

s01 的工具执行是硬编码的：

```python
# s01：硬编码，每加一个工具就要改循环
if block.name == "bash":
    output = run_bash(block.input["command"])
```

s02 换成 dispatch map：

```python
# s02：字典查找，加工具只加 handler
TOOL_HANDLERS = {
    "bash":       lambda **kw: run_bash(kw["command"]),
    "read_file":  lambda **kw: run_read(kw["path"], kw.get("limit")),
    "write_file": lambda **kw: run_write(kw["path"], kw["content"]),
    "edit_file":  lambda **kw: run_edit(kw["path"], kw["old_text"], kw["new_text"]),
}

# 循环中：一行查找替代 if/elif 链
handler = TOOL_HANDLERS.get(block.name)
output = handler(**block.input) if handler else f"Unknown tool: {block.name}"
```

循环体本身和 s01 完全一样，只是工具执行那行变成了字典查找。

---

## 路径沙箱

```python
from pathlib import Path

WORKDIR = Path(".").resolve()

def safe_path(p: str) -> Path:
    """防止路径逃逸工作区"""
    path = (WORKDIR / p).resolve()
    if not path.is_relative_to(WORKDIR):
        raise ValueError(f"Path escapes workspace: {p}")
    return path
```

所有文件操作都通过 `safe_path()` 验证，模型无法读写工作区外的文件。

---

## 四个工具的实现

```python
import subprocess
from pathlib import Path

def run_bash(command: str) -> str:
    result = subprocess.run(
        command, shell=True, capture_output=True, text=True, timeout=30
    )
    return (result.stdout + result.stderr)[:50000]

def run_read(path: str, limit: int = None) -> str:
    text = safe_path(path).read_text()
    lines = text.splitlines()
    if limit and limit < len(lines):
        lines = lines[:limit]
    return "\n".join(lines)[:50000]

def run_write(path: str, content: str) -> str:
    p = safe_path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return f"Written: {path}"

def run_edit(path: str, old_text: str, new_text: str) -> str:
    p = safe_path(path)
    content = p.read_text()
    if old_text not in content:
        return f"Error: old_text not found in {path}"
    p.write_text(content.replace(old_text, new_text, 1))
    return f"Edited: {path}"
```

---

## 工具 Schema

每个工具需要一个 schema 告诉 LLM 怎么调用：

```python
TOOLS = [
    {
        "name": "bash",
        "description": "执行 shell 命令",
        "input_schema": {
            "type": "object",
            "properties": {"command": {"type": "string"}},
            "required": ["command"]
        }
    },
    {
        "name": "read_file",
        "description": "读取文件内容，支持 limit 参数限制行数",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "limit": {"type": "integer", "description": "最多读取的行数（可选）"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "write_file",
        "description": "写入文件，自动创建父目录",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"}
            },
            "required": ["path", "content"]
        }
    },
    {
        "name": "edit_file",
        "description": "精确查找替换文件中的内容",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "old_text": {"type": "string", "description": "要替换的原文本"},
                "new_text": {"type": "string", "description": "替换后的新文本"}
            },
            "required": ["path", "old_text", "new_text"]
        }
    }
]
```

---

## 相对 s01 的变化

| 组件 | s01 | s02 |
|------|-----|-----|
| 工具数量 | 1（仅 bash） | 4（bash + read + write + edit） |
| 工具分发 | 硬编码 if | `TOOL_HANDLERS` 字典 |
| 路径安全 | 无 | `safe_path()` 沙箱 |
| Agent loop | — | **不变** |

<div class="mermaid">
flowchart LR
    A[LLM tool_use] --> B{TOOL_HANDLERS}
    B -->|bash| C[run_bash]
    B -->|read_file| D[run_read]
    B -->|write_file| E[run_write]
    B -->|edit_file| F[run_edit]
    C & D & E & F --> G[tool_result]
</div>

---

## 为什么 edit_file 比 bash sed 更好

```bash
# bash sed：遇到特殊字符（/、&、\n）就崩
sed -i 's/old_text/new_text/' file.py

# edit_file：Python 字符串替换，无特殊字符问题
run_edit("file.py", old_text="def foo():", new_text="def bar():")
```

`edit_file` 还有一个额外好处：如果 `old_text` 不存在，会返回明确的错误信息，而不是静默成功（sed 的常见陷阱）。

---

下一篇：[TodoWrite：让 Agent 不再迷路](../03-todo-write/index.html)
