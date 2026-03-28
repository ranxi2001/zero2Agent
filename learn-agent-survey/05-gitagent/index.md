---
layout: default
title: "GitAgent：代码仓库智能操作"
description: 用 LLM 操作 Git 仓库的 Agent 模式——自动化代码审查、PR 生成、Issue 分析、Commit 总结
eyebrow: 框架调研 · 05
---

# GitAgent：代码仓库智能操作

GitAgent 是一类把 LLM 能力接入 Git / GitHub 工作流的 Agent 模式。不是单一框架，而是一种**工程模式**：给 Agent 配备 git 操作工具，让它能读、写、分析代码仓库。

典型代表包括 GitHub Copilot Workspace、SWE-agent、Aider、以及各类基于 GitHub API 的自定义 Agent。

## 核心工具集

一个完整的 GitAgent 需要以下工具：

| 工具类别 | 具体操作 |
|---------|---------|
| 仓库读取 | 读文件、列目录、搜索代码、查看 git log |
| 代码修改 | 写文件、创建/删除文件 |
| Git 操作 | commit、branch、diff、merge |
| GitHub API | 创建 PR、评论 Issue、读取 PR 内容 |
| 代码执行 | 运行测试、执行脚本 |

## 从零搭建 GitAgent

```python
import subprocess
import os
from anthropic import Anthropic

client = Anthropic()

# ===== 工具定义 =====

def read_file(path: str) -> str:
    """读取文件内容"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return f"文件不存在: {path}"

def list_directory(path: str = ".") -> str:
    """列出目录内容"""
    try:
        items = os.listdir(path)
        return "\n".join(sorted(items))
    except Exception as e:
        return f"错误: {e}"

def run_command(command: str) -> str:
    """执行 shell 命令（限制为 git 和 grep 等安全命令）"""
    allowed_prefixes = ["git ", "grep ", "find ", "cat ", "ls "]
    if not any(command.startswith(p) for p in allowed_prefixes):
        return f"不允许执行: {command}"
    result = subprocess.run(
        command, shell=True, capture_output=True, text=True
    )
    return result.stdout or result.stderr

def write_file(path: str, content: str) -> str:
    """写入文件"""
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"已写入: {path}"
    except Exception as e:
        return f"写入失败: {e}"

def search_code(pattern: str, directory: str = ".") -> str:
    """在代码库中搜索模式"""
    result = subprocess.run(
        f"grep -r --include='*.py' -n '{pattern}' {directory}",
        shell=True, capture_output=True, text=True
    )
    return result.stdout[:3000] or "未找到匹配"

# ===== 工具 Schema =====

tools = [
    {
        "name": "read_file",
        "description": "读取指定路径的文件内容",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "文件路径"}},
            "required": ["path"],
        },
    },
    {
        "name": "list_directory",
        "description": "列出目录中的文件和子目录",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "目录路径，默认当前目录"}},
        },
    },
    {
        "name": "run_command",
        "description": "执行 git / grep / find 等命令",
        "input_schema": {
            "type": "object",
            "properties": {"command": {"type": "string", "description": "要执行的命令"}},
            "required": ["command"],
        },
    },
    {
        "name": "write_file",
        "description": "写入文件内容",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "search_code",
        "description": "在代码库中搜索字符串模式",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "搜索模式"},
                "directory": {"type": "string", "description": "搜索目录"},
            },
            "required": ["pattern"],
        },
    },
]

tools_map = {
    "read_file": read_file,
    "list_directory": list_directory,
    "run_command": run_command,
    "write_file": write_file,
    "search_code": search_code,
}

# ===== Agent 循环 =====

def git_agent(task: str, repo_path: str = ".") -> str:
    os.chdir(repo_path)
    messages = [{"role": "user", "content": task}]
    system = """你是一个代码仓库助手。你可以：
- 读取和分析代码文件
- 执行 git 命令查看历史和状态
- 搜索代码中的特定模式
- 修改文件并提交

始终先了解仓库结构，再做具体操作。"""

    while True:
        resp = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=4096,
            system=system,
            tools=tools,
            messages=messages,
        )

        if resp.stop_reason == "tool_use":
            tool_results = []
            for block in resp.content:
                if block.type == "tool_use":
                    result = tools_map[block.name](**block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(result)[:2000],  # 截断过长输出
                    })
            messages.append({"role": "assistant", "content": resp.content})
            messages.append({"role": "user", "content": tool_results})
        else:
            for block in resp.content:
                if hasattr(block, "text"):
                    return block.text
```

## 使用示例

```python
# 1. 代码审查
review = git_agent(
    "审查最近 3 次提交的改动，指出潜在问题",
    repo_path="/path/to/your/repo"
)
print(review)

# 2. 自动生成 Commit Message
commit_msg = git_agent(
    "查看当前暂存的改动（git diff --cached），生成一个规范的 commit message"
)
print(commit_msg)

# 3. 代码解释
explanation = git_agent(
    "找到所有 Agent 相关的类，解释它们的关系"
)
print(explanation)

# 4. Bug 定位
bug_analysis = git_agent(
    "最近一次提交引入了一个 bug，git log 看一下，找出可疑的改动"
)
print(bug_analysis)
```

## 用 GitHub API 操作 PR

```python
import requests

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
REPO = "owner/repo"

def get_pr_diff(pr_number: int) -> str:
    """获取 PR 的 diff"""
    resp = requests.get(
        f"https://api.github.com/repos/{REPO}/pulls/{pr_number}/files",
        headers={"Authorization": f"Bearer {GITHUB_TOKEN}"},
    )
    files = resp.json()
    diffs = []
    for f in files:
        diffs.append(f"=== {f['filename']} ===\n{f.get('patch', '（二进制文件）')}")
    return "\n\n".join(diffs)[:8000]

def post_pr_comment(pr_number: int, comment: str):
    """在 PR 上发评论"""
    requests.post(
        f"https://api.github.com/repos/{REPO}/issues/{pr_number}/comments",
        headers={"Authorization": f"Bearer {GITHUB_TOKEN}"},
        json={"body": comment},
    )

# 自动 PR 审查
def auto_review_pr(pr_number: int):
    diff = get_pr_diff(pr_number)
    review = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=2048,
        messages=[{
            "role": "user",
            "content": f"审查以下 PR 改动，给出简洁的审查意见：\n\n{diff}",
        }]
    )
    comment = review.content[0].text
    post_pr_comment(pr_number, f"🤖 AI 代码审查：\n\n{comment}")
    print(f"已在 PR #{pr_number} 发布审查评论")
```

## 成熟工具参考

不想从零搭建，可以直接用：

| 工具 | 特点 |
|------|------|
| [Aider](https://github.com/Aider-AI/aider) | 命令行 AI 编程助手，直接在终端改代码 |
| [SWE-agent](https://github.com/SWE-agent/SWE-agent) | 专门做 GitHub Issue 修复的 Agent |
| [OpenHands](https://github.com/All-Hands-AI/OpenHands) | 完整的软件工程 Agent 平台 |
| GitHub Copilot Workspace | GitHub 官方，深度集成 PR/Issue |

## 优缺点

**优点：**
- 代码审查、commit 总结自动化效果显著
- 与现有 git 工作流无缝融合
- 可以深度理解代码上下文

**缺点：**
- 自动写代码存在风险，需要人工 review
- 大型仓库的上下文窗口压力大
- API 调用费用随代码量增加

## 适合什么场景

- 代码审查自动化（PR review bot）
- Commit message 自动生成
- 代码库文档自动生成
- Issue 分类和初步分析
- 渐进式代码重构辅助
