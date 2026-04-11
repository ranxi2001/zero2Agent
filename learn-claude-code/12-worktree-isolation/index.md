---
layout: default
title: Worktree 隔离：多 Agent 并行不踩踏
description: 每个任务独立 Git worktree——控制平面与执行平面分离
eyebrow: Claude Code / s12
---

# Worktree 隔离：多 Agent 并行不踩踏

多个 Agent 同时修改同一个目录会出什么问题？

- Agent A 创建了 `temp.py`，Agent B 也创建了 `temp.py`，互相覆盖
- Agent A 的未提交修改和 Agent B 的修改混在一起，git status 一团乱
- 一个 Agent 的失败导致另一个 Agent 的工作也出问题

解决方案：**每个任务得到一个独立的 Git worktree**，物理隔离，互不干扰。

---

## Git Worktree 基础

Git worktree 让同一个仓库在多个目录中同时 checkout，每个目录有独立的工作区和 index：

```bash
# 为 task_001 创建独立 worktree
git worktree add .worktrees/task_001 -b task/task_001

# 目录结构：
# .worktrees/
#   task_001/    ← 完整的仓库副本，独立工作区
#   task_002/    ← 另一个任务的独立空间
# src/           ← 主工作区，不被任务修改
```

每个 worktree 指向同一个 `.git` 对象存储，但有独立的 HEAD、index 和工作文件。

---

## 源码实证：EnterWorktreeTool 的真实实现

Claude Code 的 `EnterWorktreeTool`（`src/tools/EnterWorktreeTool/EnterWorktreeTool.ts`）是进入 worktree 隔离的唯一入口。它的 `call()` 方法揭示了完整的状态切换流程：

```typescript
// EnterWorktreeTool.ts — call() 核心逻辑（简化）

async call(input) {
  // 1. 防止嵌套：已经在 worktree 里就拒绝
  if (getCurrentWorktreeSession()) {
    throw new Error('Already in a worktree session')
  }

  // 2. 回到规范 git 根目录（即使从 worktree 内部调用也不会嵌套）
  const mainRepoRoot = findCanonicalGitRoot(getCwd())
  if (mainRepoRoot && mainRepoRoot !== getCwd()) {
    process.chdir(mainRepoRoot)
    setCwd(mainRepoRoot)
  }

  // 3. 创建 worktree（路径：.claude/worktrees/<slug>）
  const slug = input.name ?? getPlanSlug()
  const worktreeSession = await createWorktreeForSession(getSessionId(), slug)

  // 4. 切换 CWD 到 worktree
  process.chdir(worktreeSession.worktreePath)
  setCwd(worktreeSession.worktreePath)
  setOriginalCwd(getCwd())

  // 5. 关键：清空所有依赖 CWD 的缓存
  clearSystemPromptSections()   // 系统 prompt 重新生成
  clearMemoryFileCaches()       // CLAUDE.md 等记忆文件重新读取
  getPlansDirectory.cache.clear?.()

  // 6. 持久化 worktree 状态（崩溃恢复用）
  saveWorktreeState(worktreeSession)

  return {
    data: {
      worktreePath: worktreeSession.worktreePath,
      worktreeBranch: worktreeSession.worktreeBranch,
      message: `Created worktree at ${worktreeSession.worktreePath}...`,
    },
  }
}
```

**关键设计细节：**

| 要点 | 实现 |
|------|------|
| Worktree 存放位置 | `.claude/worktrees/<slug>`，不是 `.worktrees/` |
| Name 校验 | `validateWorktreeSlug()` 逐段检查，拒绝 `..` 和绝对路径，防止路径穿越 |
| 缓存清空 | 切换 CWD 后**必须**清空三类缓存：系统 prompt、记忆文件、plans 目录 |
| 防嵌套 | `getCurrentWorktreeSession()` 检查全局 session 状态 |
| 规范化 | `findCanonicalGitRoot()` 确保始终从主仓库根目录创建 |

输入 Schema 用 Zod 定义，`name` 是可选的，支持字母、数字、点、下划线、短横线，最长 64 字符：

```typescript
const inputSchema = z.strictObject({
  name: z.string()
    .superRefine((s, ctx) => {
      try { validateWorktreeSlug(s) }
      catch (e) { ctx.addIssue({ code: 'custom', message: (e as Error).message }) }
    })
    .optional()
    .describe('Optional name for the worktree...'),
})
```

---

## 源码实证：ExitWorktreeTool 的安全退出

`ExitWorktreeTool`（`src/tools/ExitWorktreeTool/ExitWorktreeTool.ts`）不是简单地切回目录——它实现了完整的安全检查和状态恢复。

输入 Schema 有两个参数：

```typescript
const inputSchema = z.strictObject({
  action: z.enum(['keep', 'remove']),        // 保留还是删除 worktree
  discard_changes: z.boolean().optional(),   // remove 时如果有未提交变更，必须显式确认
})
```

**安全门控在 `validateInput()` 里**——这是 Claude Code 的 fail-closed 设计：

```typescript
async validateInput(input) {
  // 1. 作用域守卫：只操作当前 session 的 EnterWorktree 创建的 worktree
  const session = getCurrentWorktreeSession()
  if (!session) {
    return { result: false, message: 'No-op: there is no active EnterWorktree session...' }
  }

  // 2. remove 时检查未提交变更
  if (input.action === 'remove' && !input.discard_changes) {
    const summary = await countWorktreeChanges(session.worktreePath, session.originalHeadCommit)
    // null = 无法确定状态 → fail-closed，拒绝删除
    if (summary === null) {
      return { result: false, message: 'Could not verify worktree state...' }
    }
    if (summary.changedFiles > 0 || summary.commits > 0) {
      return { result: false, message: `Worktree has ${changedFiles} uncommitted files and ${commits} commits...` }
    }
  }
  return { result: true }
}
```

`countWorktreeChanges()` 的 fail-closed 设计值得单独说明：

```typescript
// 返回 null 代表"无法确定"，调用方必须将 null 视为"不安全"
async function countWorktreeChanges(
  worktreePath: string,
  originalHeadCommit: string | undefined,
): Promise<ChangeSummary | null> {
  const status = await execFileNoThrow('git', ['-C', worktreePath, 'status', '--porcelain'])
  if (status.code !== 0) return null       // git 失败 → null

  if (!originalHeadCommit) return null     // 没有基线 commit → null（hook-based worktree 场景）

  const revList = await execFileNoThrow('git', ['-C', worktreePath, 'rev-list', '--count', `${originalHeadCommit}..HEAD`])
  if (revList.code !== 0) return null      // rev-list 失败 → null

  return { changedFiles, commits }
}
```

**状态恢复在 `restoreSessionToOriginalCwd()` 里——是 EnterWorktree 的精确逆操作：**

```typescript
function restoreSessionToOriginalCwd(originalCwd: string, projectRootIsWorktree: boolean): void {
  setCwd(originalCwd)
  setOriginalCwd(originalCwd)
  if (projectRootIsWorktree) {
    setProjectRoot(originalCwd)
    updateHooksConfigSnapshot()  // 恢复 hooks 配置快照
  }
  saveWorktreeState(null)        // 清除持久化状态
  clearSystemPromptSections()    // 与 Enter 时对称
  clearMemoryFileCaches()
  getPlansDirectory.cache.clear?.()
}
```

---

## 源码实证：AgentTool 的 worktree 隔离集成

`AgentTool`（`src/tools/AgentTool/AgentTool.tsx`）通过 `isolation: "worktree"` 参数让子 Agent 在独立 worktree 中运行。这是多 Agent 并行的核心机制。

### isolation 参数定义

```typescript
// AgentTool.tsx — inputSchema
isolation: z.enum(['worktree'])
  .optional()
  .describe('Isolation mode. "worktree" creates a temporary git worktree '
    + 'so the agent works on an isolated copy of the repo.')
```

### 创建流程

```typescript
// AgentTool.tsx — call() 中的 worktree 设置（简化）

// 用 agent ID 的前 8 位生成 slug
const earlyAgentId = createAgentId()
let worktreeInfo = null
if (effectiveIsolation === 'worktree') {
  const slug = `agent-${earlyAgentId.slice(0, 8)}`
  worktreeInfo = await createAgentWorktree(slug)
}

// CWD 覆盖：worktree 路径覆盖 agent 的工作目录
const cwdOverridePath = cwd ?? worktreeInfo?.worktreePath
const wrapWithCwd = <T,>(fn: () => T): T =>
  cwdOverridePath ? runWithCwdOverride(cwdOverridePath, fn) : fn()
```

`createAgentWorktree()` 与 `createWorktreeForSession()` 的关键区别：**它不修改全局 session 状态**（不 `process.chdir`，不写 `currentWorktreeSession`，不改 project config），只返回路径信息：

```typescript
// worktree.ts — createAgentWorktree（简化）
export async function createAgentWorktree(slug: string): Promise<{
  worktreePath: string
  worktreeBranch?: string
  headCommit?: string
  gitRoot?: string
  hookBased?: boolean
}> {
  validateWorktreeSlug(slug)
  // 始终从 canonicalGitRoot 创建，防止 worktree 嵌套
  const gitRoot = findCanonicalGitRoot(getCwd())
  // ... 创建 worktree 但不修改全局状态
  return { worktreePath, worktreeBranch, headCommit, gitRoot }
}
```

### Fork + Worktree 上下文传递

当子 Agent 从父 Agent fork 出来并运行在 worktree 中时，会注入一段路径转换提示：

```typescript
// forkSubagent.ts — buildWorktreeNotice
export function buildWorktreeNotice(parentCwd: string, worktreeCwd: string): string {
  return `You've inherited the conversation context above from a parent agent ` +
    `working in ${parentCwd}. You are operating in an isolated git worktree ` +
    `at ${worktreeCwd} — same repository, same relative file structure, ` +
    `separate working copy. Paths in the inherited context refer to the ` +
    `parent's working directory; translate them to your worktree root. ` +
    `Re-read files before editing if the parent may have modified them...`
}
```

### 自动清理逻辑

Agent 完成后，worktree 的清理遵循“有变更则保留”原则：

```typescript
const cleanupWorktreeIfNeeded = async () => {
  if (!worktreeInfo) return {}
  const { worktreePath, worktreeBranch, headCommit, gitRoot, hookBased } = worktreeInfo
  worktreeInfo = null  // 幂等：防止 try/catch 双重调用

  if (hookBased) return { worktreePath }  // hook-based 始终保留

  if (headCommit) {
    const changed = await hasWorktreeChanges(worktreePath, headCommit)
    if (!changed) {
      await removeAgentWorktree(worktreePath, worktreeBranch, gitRoot)
      return {}  // 无变更 → 自动删除，不返回路径
    }
  }
  return { worktreePath, worktreeBranch }  // 有变更 → 保留，返回路径
}
```

### task-notification 中的 worktree 信息

后台 Agent 完成后发送通知时，worktree 路径和分支会以 XML 嵌入：

```xml
<task-notification>
<task-id>agent_abc123</task-id>
<output-file>...</output-file>
<status>completed</status>
<summary>Agent "实现 JWT 验证" completed</summary>
<result>...</result>
<worktree>
  <worktreePath>/repo/.claude/worktrees/agent-abc12345</worktreePath>
  <worktreeBranch>worktree/agent-abc12345</worktreeBranch>
</worktree>
</task-notification>
```

这让父 Agent 知道子 Agent 的变更在哪个分支上，可以 merge 或 cherry-pick。

---

## 两平面架构

```
控制平面（主目录）：
  .tasks/        ← 任务定义和状态
  .team/         ← 团队成员信息
  .transcripts/  ← 对话历史归档

执行平面（worktree 目录 — Claude Code 实际使用 .claude/worktrees/）：
  .claude/worktrees/
    agent-a1b2c3d4/    ← Agent A 的代码修改在这里
    agent-e5f6g7h8/    ← Agent B 的代码修改在这里
```

控制平面只有任务数据，执行平面只有代码变更。两者物理隔离，互不污染。

---

## 从零实现：WorktreeManager

理解了源码中的设计决策后，我们用 Python 实现一个简化版本：

```python
import subprocess, json
from pathlib import Path
from datetime import datetime

WORKTREES_DIR = Path(".worktrees")
EVENTS_LOG = WORKTREES_DIR / "events.jsonl"
WORKTREES_DIR.mkdir(exist_ok=True)

class WorktreeManager:
    def create(self, task_id: str) -> str:
        """为任务创建独立 worktree"""
        worktree_path = WORKTREES_DIR / task_id
        branch_name = f"task/{task_id}"

        if worktree_path.exists():
            return f"Worktree already exists: {worktree_path}"

        # 从当前 HEAD 创建新分支和 worktree
        result = subprocess.run(
            ["git", "worktree", "add", str(worktree_path), "-b", branch_name],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            return f"Failed to create worktree: {result.stderr}"

        # 更新任务状态
        task_manager.update_status(task_id, "in_progress",
                                   worktree=str(worktree_path))

        self._log_event(task_id, "worktree_created", {"path": str(worktree_path)})
        return f"Created worktree: {worktree_path}\nBranch: {branch_name}"

    def run_in(self, task_id: str, command: str) -> str:
        """在任务的 worktree 里执行命令"""
        worktree_path = WORKTREES_DIR / task_id
        if not worktree_path.exists():
            return f"Worktree not found for task {task_id}. Create it first."

        result = subprocess.run(
            command, shell=True, capture_output=True, text=True,
            cwd=str(worktree_path), timeout=60
        )
        output = (result.stdout + result.stderr)[:50000]
        self._log_event(task_id, "command_run", {"command": command, "returncode": result.returncode})
        return output

    def read_in(self, task_id: str, path: str) -> str:
        """读取任务 worktree 里的文件"""
        worktree_path = WORKTREES_DIR / task_id
        file_path = (worktree_path / path).resolve()

        # 安全检查
        if not file_path.is_relative_to(worktree_path.resolve()):
            return f"Path escapes worktree: {path}"
        if not file_path.exists():
            return f"File not found: {path}"
        return file_path.read_text()

    def write_in(self, task_id: str, path: str, content: str) -> str:
        """写文件到任务 worktree"""
        worktree_path = WORKTREES_DIR / task_id
        file_path = (worktree_path / path).resolve()

        if not file_path.is_relative_to(worktree_path.resolve()):
            return f"Path escapes worktree: {path}"

        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
        return f"Written: {path}"

    def finish(self, task_id: str, commit_message: str = None) -> str:
        """完成任务：提交变更，移除 worktree"""
        worktree_path = WORKTREES_DIR / task_id

        if commit_message:
            # 提交所有变更
            subprocess.run(["git", "add", "-A"], cwd=str(worktree_path))
            subprocess.run(
                ["git", "commit", "-m", commit_message or f"Complete {task_id}"],
                cwd=str(worktree_path)
            )

        # 移除 worktree
        subprocess.run(["git", "worktree", "remove", str(worktree_path), "--force"])
        task_manager.complete(task_id)
        self._log_event(task_id, "worktree_finished", {"committed": bool(commit_message)})
        return f"Task {task_id} finished. Worktree removed."

    def list(self) -> str:
        result = subprocess.run(
            ["git", "worktree", "list"], capture_output=True, text=True
        )
        return result.stdout

    def _log_event(self, task_id: str, event: str, data: dict):
        entry = json.dumps({
            "task_id": task_id,
            "event": event,
            "data": data,
            "timestamp": datetime.now().isoformat(),
        })
        with open(EVENTS_LOG, "a") as f:
            f.write(entry + "\n")
```

---

## 工具接口

```python
wt = WorktreeManager()

TOOL_HANDLERS.update({
    "worktree_create":  lambda **kw: wt.create(kw["task_id"]),
    "worktree_bash":    lambda **kw: wt.run_in(kw["task_id"], kw["command"]),
    "worktree_read":    lambda **kw: wt.read_in(kw["task_id"], kw["path"]),
    "worktree_write":   lambda **kw: wt.write_in(kw["task_id"], kw["path"], kw["content"]),
    "worktree_finish":  lambda **kw: wt.finish(kw["task_id"], kw.get("commit_message")),
    "worktree_list":    lambda **kw: wt.list(),
})
```

---

## 源码 vs 从零实现：设计差异对照

| 维度 | Claude Code 源码 | 我们的 WorktreeManager |
|------|-------------------|----------------------|
| Worktree 路径 | `.claude/worktrees/<slug>` | `.worktrees/<task_id>` |
| Name 校验 | `validateWorktreeSlug()` 逐段正则 + 路径穿越防护 | 无校验（生产代码需要加） |
| 缓存管理 | 切换 CWD 后清空 system prompt / memory file / plans 三类缓存 | 不涉及（无 LLM 上下文缓存） |
| 退出策略 | `keep` / `remove` 双模式，`remove` 需确认未提交变更 | 只有 `finish`（总是删除） |
| Fail-closed | `countWorktreeChanges` 返回 null 时拒绝删除 | 不检查变更直接删除 |
| Agent worktree | `createAgentWorktree()` 不修改全局状态，agent 完成后自动清理 | N/A |
| 规范化 | `findCanonicalGitRoot()` 防止 worktree 嵌套 | 假设从主仓库运行 |

---

## 完整任务执行流程

<div class="mermaid">
flowchart TD
    A[claim_task: task_001] --> B[worktree_create: task_001]
    B --> C[worktree_read: task_001, src/auth.py]
    C --> D[worktree_write: task_001, src/auth.py]
    D --> E[worktree_bash: task_001, pytest tests/]
    E --> F{测试通过?}
    F -->|是| G[worktree_finish: task_001\n"实现 JWT 验证"]
    F -->|否| D
    G --> H[idle: 等待新任务]
</div>

---

## 崩溃恢复

`.worktrees/events.jsonl` 记录了所有操作：

```json
{"task_id": "task_001", "event": "worktree_created", "timestamp": "..."}
{"task_id": "task_001", "event": "command_run", "data": {"command": "pytest"}, ...}
{"task_id": "task_001", "event": "worktree_finished", ...}
```

如果进程崩溃，从日志里可以知道：哪些任务已经建了 worktree（可以继续），哪些完成了（可以跳过），哪些在中途（需要清理）。

```python
def recover_from_crash() -> list[str]:
    """从事件日志恢复未完成的任务"""
    events = {}
    if not EVENTS_LOG.exists():
        return []
    for line in EVENTS_LOG.read_text().splitlines():
        ev = json.loads(line)
        events[ev["task_id"]] = ev["event"]  # 只保留最新事件

    incomplete = [
        task_id for task_id, last_event in events.items()
        if last_event == "worktree_created"  # 创建了但没完成
    ]
    return incomplete
```

Claude Code 的做法更精细：通过 `saveWorktreeState()` 将 worktree session 持久化到 project config，重启时 `restoreWorktreeSession()` 恢复。Agent worktree 则有专门的 `cleanupStaleAgentWorktrees()` 定期扫描 `.claude/worktrees/` 目录清理过期的。

## 设计哲学：安全是默认，便利是可选

Worktree 隔离是设计指南**第二原则——安全是默认（Secure by Default）**的最佳案例。

Claude Code 的 5 层权限模型：

```
Layer 1: 操作系统沙箱（macOS Seatbelt / Linux Landlock）
Layer 2: 网络访问控制（允许列表 vs 拒绝列表）
Layer 3: 文件系统边界（项目目录 + 明确添加的路径）
Layer 4: 工具级别权限（每个工具独立的 allow/deny/ask）
Layer 5: Bash 命令分类（读命令自动放行，写命令需要确认）
```

Worktree 处于 Layer 3——文件系统隔离。它的设计遵循 **fail-closed** 原则：

- Agent worktree 创建失败？不执行任何操作，返回错误
- worktree 退出时发现未提交更改？保留 worktree，不删除（宁可泄漏资源也不丢失工作）
- 3 处缓存需要清除（system prompt cache、permission classifier approvals cache、session messages cache）？全部清除，即使某些可能不需要

这和“便利优先”的设计完全相反。便利优先会选择：失败时自动回退到主分支、退出时自动丢弃未提交更改、只清除确认需要清除的缓存。但这些“便利”在出错时会导致数据丢失或安全漏洞。

设计指南总结了整个 Claude Code 的安全哲学：**能力和控制之间的平衡**。Worktree 给了 Agent 并行修改代码的能力，但通过 fail-closed 设计和 5 层权限确保这种能力始终在人类的控制之下。

---

## 这套系统的全貌

至此，12 节课的所有机制组合在一起：

```
s01: while True loop       → Agent 的心跳
s02: dispatch map          → 工具系统的骨架
s03: TodoManager           → 单 Agent 的规划
s04: Subagent              → 上下文隔离
s05: Skill loading         → 知识按需加载
s06: Context compact       → 无限会话长度

s07: Task graph            → 任务依赖和持久化
s08: Background tasks      → 非阻塞执行
s09: Agent teams           → 多 Agent 通信
s10: Protocols             → 结构化协作
s11: Autonomous agents     → 自组织
s12: Worktree isolation    → 并行安全
```

从一个 30 行的循环，到一个能并行处理真实工程任务的自治 Agent 团队。

每一层都有具体的问题驱动，每一层的代码都可以独立理解和修改。

---

[← 返回 Claude Code 模块首页](../index.html)
