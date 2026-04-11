---
layout: default
title: Skill Loading：按需加载领域知识
description: 两层注入策略——系统提示只放名称，详细文档按需加载
eyebrow: Claude Code / s05
---

# Skill Loading：按需加载领域知识

> *“load knowledge temporarily when needed”*

把所有领域知识塞进 system prompt 会浪费 20,000+ token。这一节实现按需加载：系统提示只告诉模型“有哪些技能”，详细文档在模型主动请求时才加载。

---

## 问题

假设 Agent 需要处理多种任务：代码审查、写测试、生成文档、数据库操作……

如果把所有这些领域的最佳实践全部放进 system prompt：

- 每次调用都消耗 20,000+ token
- 大量无关知识干扰模型推理
- token 费用线性增加

大多数对话只用到其中一两个技能。其余的都是浪费。

---

## 两层注入策略

```
系统提示（始终在上下文中）：
  技能列表 + 简短描述（~100 token / 技能）

                ↓ 模型判断需要某技能

Skill 工具调用：
  完整技能文档注入为 user message（~2000 token，临时）
```

知识是临时的——模型用完这轮，下次需要时再加载。上下文不会被长期占用。

---

## 源码实证：三条加载路径

Claude Code 的技能系统并不只有一种目录格式。源码 `loadSkillsDir.ts` 揭示了三条并行的加载路径：

### 路径 1：现代 `/skills/` 目录（推荐）

只支持目录格式：`skill-name/SKILL.md`。

```
~/.claude/skills/
  code-review/
    SKILL.md        ← 完整的代码审查指南
  write-tests/
    SKILL.md        ← 测试编写最佳实践
```

源码中 `loadSkillsFromSkillsDir()` 函数明确只接受目录，单独的 `.md` 文件会被跳过：

```typescript
// 来自 loadSkillsDir.ts → loadSkillsFromSkillsDir()
if (!entry.isDirectory() && !entry.isSymbolicLink()) {
  // Single .md files are NOT supported in /skills/ directory
  return null
}

const skillDirPath = join(basePath, entry.name)
const skillFilePath = join(skillDirPath, 'SKILL.md')
```

### 路径 2：遗留 `/commands/` 目录（已废弃）

同时支持目录格式（`SKILL.md`）和单文件格式（`xxx.md`）。源码将 `loadedFrom` 标记为 `'commands_DEPRECATED'`：

```typescript
// 来自 loadSkillsDir.ts → loadSkillsFromCommandsDir()
skills.push({
  skill: createSkillCommand({
    ...parsed,
    loadedFrom: 'commands_DEPRECATED',  // 明确标记废弃
    paths: undefined,  // 遗留路径不支持条件激活
  }),
  filePath,
})
```

### 路径 3：MCP 技能

通过 `mcpSkillBuilders.ts` 注册表模式实现。这是一个依赖解耦技巧——`loadSkillsDir.ts` 在模块初始化时注册构建函数，MCP 模块在需要时取用，避免循环依赖：

```typescript
// loadSkillsDir.ts 尾部
registerMCPSkillBuilders({
  createSkillCommand,
  parseSkillFrontmatterFields,
})
```

### 路径 4：内置技能（Bundled Skills）

编译进 CLI 的技能，通过 `bundledSkills.ts` 中的 `registerBundledSkill()` 注册。内置技能可以携带附加文件（`files` 字段），首次调用时才解压到磁盘：

```typescript
// 来自 bundledSkills.ts
if (files && Object.keys(files).length > 0) {
  skillRoot = getBundledSkillExtractDir(definition.name)
  let extractionPromise: Promise<string | null> | undefined
  const inner = definition.getPromptForCommand
  getPromptForCommand = async (args, ctx) => {
    extractionPromise ??= extractBundledSkillFiles(definition.name, files)
    const extractedDir = await extractionPromise
    // ...
  }
}
```

注意 `extractionPromise ??= ...` 这个写法——通过缓存 Promise（而非结果）保证并发调用者共享同一次解压操作。

---

## 源码实证：五级优先级解析

`getSkillDirCommands()` 函数定义了严格的加载优先级。所有层级并行加载，然后按顺序合并——靠前的优先：

```typescript
// 来自 loadSkillsDir.ts → getSkillDirCommands()
const [
  managedSkills,      // 1. 策略级（企业管控）
  userSkills,         // 2. 用户级（~/.claude/skills/）
  projectSkillsNested,// 3. 项目级（.claude/skills/，含父目录遍历）
  additionalSkillsNested, // 4. --add-dir 指定的额外目录
  legacyCommands,     // 5. 遗留 /commands/（废弃）
] = await Promise.all([
  loadSkillsFromSkillsDir(managedSkillsDir, 'policySettings'),
  loadSkillsFromSkillsDir(userSkillsDir, 'userSettings'),
  Promise.all(projectSkillsDirs.map(dir =>
    loadSkillsFromSkillsDir(dir, 'projectSettings'))),
  Promise.all(additionalDirs.map(dir =>
    loadSkillsFromSkillsDir(join(dir, '.claude', 'skills'), 'projectSettings'))),
  loadSkillsFromCommandsDir(cwd),
])
```

对应的目录路径：

| 优先级 | 来源 | 目录路径 | 用途 |
|--------|------|---------|------|
| 1 | managed | `~/.claude/managed/skills/` | 企业策略推送 |
| 2 | user | `~/.claude/skills/` | 个人全局技能 |
| 3 | project | `.claude/skills/`（向上遍历） | 项目团队共享 |
| 4 | add-dir | `--add-dir` 指定目录 | monorepo 子项目 |
| 5 | legacy | `./commands/` | 兼容旧版（废弃） |

加载后通过 `realpath` 进行跨路径去重（处理符号链接和重叠的父目录扫描）：

```typescript
// 来自 loadSkillsDir.ts
async function getFileIdentity(filePath: string): Promise<string | null> {
  try {
    return await realpath(filePath)
  } catch {
    return null
  }
}
```

---

## 源码实证：Frontmatter 元数据

每个 `SKILL.md` 支持 YAML frontmatter，解析后控制技能行为。`parseSkillFrontmatterFields()` 函数展示了完整字段集：

```yaml
---
name: "Code Review"                 # 显示名称
description: "专业代码审查"          # 技能描述
allowed-tools:                       # 自动授权的工具列表
  - Read
  - Grep
  - Glob
when-to-use: "当用户要求审查代码时"   # 模型判断何时使用
model: opus                          # 模型覆盖（inherit = 继承当前）
user-invocable: true                 # 用户是否可直接 /xxx 调用
disable-model-invocation: false      # 禁止模型主动调用
context: fork                        # 执行模式：inline 或 fork
effort: high                         # 推理投入度
paths:                               # 条件激活的路径模式
  - "src/**/*.ts"
  - "!**/test/**"
hooks:                               # 生命周期钩子
  PreToolUse:
    - matcher: ".*"
      hooks:
        - command: "echo hook fired"
shell:                               # Shell 执行设置
  type: bash
---
```

源码中的返回值类型直接反映这些字段：

```typescript
// parseSkillFrontmatterFields() 返回值（简化）
{
  displayName, description, allowedTools, argumentHint,
  argumentNames, whenToUse, version, model,
  disableModelInvocation, userInvocable, hooks,
  executionContext,  // 'fork' | undefined
  agent, effort, shell,
}
```

---

## 源码实证：条件技能与动态发现

### 条件技能（paths frontmatter）

带 `paths` 字段的技能不会立即加入上下文。它们被存入 `conditionalSkills` Map，当用户操作的文件路径匹配时才激活：

```typescript
// 来自 loadSkillsDir.ts → activateConditionalSkillsForPaths()
const skillIgnore = ignore().add(skill.paths)  // gitignore 风格匹配
for (const filePath of filePaths) {
  const relativePath = isAbsolute(filePath)
    ? relative(cwd, filePath)
    : filePath
  if (skillIgnore.ignores(relativePath)) {
    dynamicSkills.set(name, skill)
    conditionalSkills.delete(name)
    activatedConditionalSkillNames.add(name)
    break
  }
}
```

模式匹配使用 `ignore` 库（与 `.gitignore` 相同的语法），支持否定模式。这意味着你可以写：

```yaml
paths:
  - "src/**/*.ts"
  - "!**/generated/**"
```

### 动态目录发现

`discoverSkillDirsForPaths()` 在文件操作时自动发现嵌套的 `.claude/skills/` 目录：

```typescript
// 来自 loadSkillsDir.ts → discoverSkillDirsForPaths()
while (currentDir.startsWith(resolvedCwd + pathSep)) {
  const skillDir = join(currentDir, '.claude', 'skills')
  if (!dynamicSkillDirs.has(skillDir)) {
    dynamicSkillDirs.add(skillDir)
    // 检查 gitignore 以阻止 node_modules 内的技能
    if (await isPathGitignored(currentDir, resolvedCwd)) {
      continue
    }
    newDirs.push(skillDir)
  }
  currentDir = dirname(currentDir)
}
```

安全措施：被 `.gitignore` 排除的目录（如 `node_modules/some-pkg/.claude/skills/`）不会被加载。

---

## 源码实证：Shell 命令替换与安全

技能提示中支持两个特殊变量和内联 Shell 命令：

```typescript
// 来自 loadSkillsDir.ts → createSkillCommand() → getPromptForCommand()

// 变量替换
finalContent = finalContent.replace(/\$\{CLAUDE_SKILL_DIR\}/g, skillDir)
finalContent = finalContent.replace(/\$\{CLAUDE_SESSION_ID\}/g, getSessionId())

// Shell 命令执行（仅非 MCP 技能）
if (loadedFrom !== 'mcp') {
  finalContent = await executeShellCommandsInPrompt(finalContent, ...)
}
```

这意味着在 SKILL.md 中可以写：

```markdown
当前技能目录：${CLAUDE_SKILL_DIR}
会话 ID：${CLAUDE_SESSION_ID}

运行 lint 检查：
!`cd ${CLAUDE_SKILL_DIR} && npm run lint 2>&1 | head -20`
```

关键安全边界：**MCP 技能（远程且不可信）永远不会执行内联 Shell 命令**。源码注释明确说明：

> Security: MCP skills are remote and untrusted -- never execute inline shell commands from their markdown body.

---

## 源码实证：SkillTool 的两条执行路径

`SkillTool.ts` 揭示了技能调用时的两条执行路径：

### Inline 模式（默认）

技能内容注入为 user message，模型在同一上下文中继续处理：

```typescript
// SkillTool.ts → call()
// Inline 路径：processPromptSlashCommand 展开技能内容
const processedCommand = await processPromptSlashCommand(
  commandName, args || '', commands, context,
)

return {
  data: { success: true, commandName, allowedTools, model },
  newMessages,           // 技能内容作为新消息注入
  contextModifier(ctx) { // 修改后续上下文（工具权限、模型等）
    // ... 合并 allowedTools、覆盖模型、设置 effort
  },
}
```

### Fork 模式（子 Agent）

当 frontmatter 指定 `context: fork` 时，技能在隔离的子 Agent 中执行，拥有独立 token 预算：

```typescript
// SkillTool.ts → call()
if (command?.type === 'prompt' && command.context === 'fork') {
  return executeForkedSkill(command, commandName, args, context, ...)
}

// executeForkedSkill() 内部
for await (const message of runAgent({
  agentDefinition,
  promptMessages,
  // ...
})) {
  agentMessages.push(message)
}
const resultText = extractResultText(agentMessages, 'Skill execution completed')
agentMessages.length = 0  // 释放内存
```

Fork 模式的优势：
- 独立 token 预算，不消耗主会话上下文
- 完成后只返回结果文本，子 Agent 的完整消息历史被释放
- 适合长时间运行的复杂技能

---

## 源码实证：技能列表的预算控制

`prompt.ts` 中的技能列表注入有精确的预算控制机制——系统提示只放名称和描述，占上下文窗口的 1%：

```typescript
// 来自 prompt.ts
export const SKILL_BUDGET_CONTEXT_PERCENT = 0.01
export const CHARS_PER_TOKEN = 4
export const DEFAULT_CHAR_BUDGET = 8_000  // Fallback: 1% of 200k x 4

// 每条描述硬上限 250 字符
export const MAX_LISTING_DESC_CHARS = 250
```

当技能过多时自动截断描述。内置技能（bundled）永远保留完整描述，其余技能按剩余预算均匀分配：

```typescript
// formatCommandsWithinBudget()（简化）
const bundledChars = ... // 内置技能始终完整
const remainingBudget = budget - bundledChars
const maxDescLen = Math.floor(availableForDescs / restCommands.length)

if (maxDescLen < MIN_DESC_LENGTH) {
  // 极端情况：非内置技能只显示名称
  return commands.map(cmd => bundledIndices.has(i)
    ? fullEntries[i].full
    : `- ${cmd.name}`
  ).join('\n')
}
```

---

## 从零实现：Python 版 SkillLoader

理解了真实架构后，我们用 Python 实现一个简化版本，捕捉核心机制：

```python
import os
import re
import yaml
from pathlib import Path

class SkillLoader:
    def __init__(self, skills_dirs: list[Path] = None):
        """多目录技能加载器，模拟真实的优先级解析"""
        self.skills_dirs = skills_dirs or [Path("skills")]
        self.skills: dict[str, dict] = {}
        self.conditional_skills: dict[str, dict] = {}
        self._scan()

    def _parse_frontmatter(self, content: str) -> tuple[dict, str]:
        """解析 YAML frontmatter"""
        if content.startswith('---'):
            end = content.find('---', 3)
            if end != -1:
                fm_text = content[3:end].strip()
                body = content[end + 3:].strip()
                try:
                    fm = yaml.safe_load(fm_text) or {}
                    return fm, body
                except yaml.YAMLError:
                    pass
        return {}, content

    def _scan(self):
        """扫描所有技能目录，按优先级加载（先加载的优先）"""
        seen = set()
        for skills_dir in self.skills_dirs:
            if not skills_dir.exists():
                continue
            for skill_dir in sorted(skills_dir.iterdir()):
                if not skill_dir.is_dir():
                    continue
                skill_md = skill_dir / "SKILL.md"
                if not skill_md.exists():
                    continue

                # 去重：已存在则跳过（模拟 realpath 去重）
                resolved = skill_md.resolve()
                if resolved in seen:
                    continue
                seen.add(resolved)

                content = skill_md.read_text()
                frontmatter, body = self._parse_frontmatter(content)

                name = frontmatter.get("name", skill_dir.name)
                desc = frontmatter.get("description", "")
                if not desc:
                    # fallback：取 markdown 第一行
                    lines = body.strip().splitlines()
                    desc = lines[0].lstrip("# ").strip() if lines else ""

                skill_info = {
                    "name": name,
                    "description": desc,
                    "when_to_use": frontmatter.get("when-to-use", ""),
                    "allowed_tools": frontmatter.get("allowed-tools", []),
                    "paths": frontmatter.get("paths"),
                    "context": frontmatter.get("context"),  # fork / inline
                    "model": frontmatter.get("model"),
                    "path": skill_md,
                    "base_dir": str(skill_dir),
                    "body": body,
                }

                slug = skill_dir.name

                # 条件技能：有 paths 字段的延迟激活
                if skill_info["paths"]:
                    self.conditional_skills[slug] = skill_info
                else:
                    self.skills[slug] = skill_info

    def activate_for_paths(self, file_paths: list[str], cwd: str) -> list[str]:
        """当文件被操作时，激活匹配的条件技能（简化版 gitignore 匹配）"""
        import fnmatch
        activated = []
        to_remove = []
        for slug, skill in self.conditional_skills.items():
            patterns = skill["paths"]
            if isinstance(patterns, str):
                patterns = [patterns]
            for fp in file_paths:
                rel = os.path.relpath(fp, cwd)
                if any(fnmatch.fnmatch(rel, p) for p in patterns):
                    self.skills[slug] = skill
                    to_remove.append(slug)
                    activated.append(slug)
                    break
        for slug in to_remove:
            del self.conditional_skills[slug]
        return activated

    def list_summary(self, char_budget: int = 8000) -> str:
        """生成技能列表摘要，带预算控制"""
        if not self.skills:
            return "No skills available."

        lines = ["## Available Skills\n"]
        total_chars = 0
        for slug, info in self.skills.items():
            desc = info["description"]
            if info["when_to_use"]:
                desc = f"{desc} - {info['when_to_use']}"
            # 单条描述硬上限（模拟 MAX_LISTING_DESC_CHARS = 250）
            if len(desc) > 250:
                desc = desc[:249] + "..."
            entry = f"- **{slug}**: {desc}"
            if total_chars + len(entry) > char_budget:
                entry = f"- **{slug}**"  # 超预算只显示名称
            lines.append(entry)
            total_chars += len(entry)

        lines.append("\n使用 Skill 工具加载完整技能文档。")
        return "\n".join(lines)

    def load(self, skill_name: str) -> dict:
        """加载完整技能，返回内容和元数据"""
        if skill_name not in self.skills:
            available = ", ".join(self.skills.keys())
            raise ValueError(f"Skill '{skill_name}' not found. Available: {available}")

        skill = self.skills[skill_name]
        content = skill["body"]

        # 变量替换（模拟 ${CLAUDE_SKILL_DIR}）
        content = content.replace("${SKILL_DIR}", skill["base_dir"])

        return {
            "content": f"Base directory for this skill: {skill['base_dir']}\n\n{content}",
            "allowed_tools": skill["allowed_tools"],
            "model": skill["model"],
            "context": skill["context"],
        }


# 实例化：模拟真实的多目录优先级
skill_loader = SkillLoader([
    Path.home() / ".claude" / "managed" / "skills",  # 1. 策略级
    Path.home() / ".claude" / "skills",               # 2. 用户级
    Path(".claude") / "skills",                        # 3. 项目级
])
```

---

## 集成到 Agent

**System prompt 注入技能列表：**

```python
SYSTEM = f"""你是一个 Coding Agent，可以执行工具完成编程任务。

{skill_loader.list_summary()}
"""
```

**Skill 工具（区分 inline 和 fork 模式）：**

```python
TOOLS.append({
    "name": "Skill",
    "description": "Execute a skill within the main conversation. "
        "When users reference a slash command (e.g. /commit), use this tool.",
    "input_schema": {
        "type": "object",
        "properties": {
            "skill": {
                "type": "string",
                "description": "技能名称（目录名），如 'code-review', 'write-tests'"
            },
            "args": {
                "type": "string",
                "description": "可选参数"
            }
        },
        "required": ["skill"]
    }
})

def handle_skill(skill: str, args: str = "") -> dict:
    """处理技能调用，区分 inline 和 fork 模式"""
    result = skill_loader.load(skill)

    if result["context"] == "fork":
        # Fork 模式：启动子 Agent
        sub_result = run_sub_agent(
            prompt=result["content"],
            allowed_tools=result["allowed_tools"],
            model=result.get("model"),
        )
        return {"status": "forked", "result": sub_result}

    # Inline 模式：注入到当前会话
    return {
        "status": "inline",
        "content": result["content"],
        "allowed_tools": result["allowed_tools"],
        "model": result.get("model"),
    }

TOOL_HANDLERS["Skill"] = lambda **kw: handle_skill(kw["skill"], kw.get("args", ""))
```

---

## 执行流程

<div class="mermaid">
flowchart TD
    A([用户：帮我做代码审查]) --> B[LLM 看到技能列表]
    B --> C{"Skill 工具调用<br/>skill: code-review"}
    C --> D{context = fork?}
    D -->|inline| E[技能内容注入为 user message]
    E --> F[allowed-tools 生效]
    F --> G[按技能文档标准执行]
    G --> H([输出结果])
    D -->|fork| I[启动子 Agent]
    I --> J[独立 token 预算执行]
    J --> K[返回结果文本]
    K --> H
</div>

---

## SKILL.md 示例

```markdown
---
name: Code Review
description: 专业代码审查技能，覆盖安全性、性能、可维护性
when-to-use: 当用户要求审查代码、做 PR review 或检查代码质量时
allowed-tools:
  - Read
  - Grep
  - Glob
paths:
  - "src/**"
  - "!**/test/**"
---

## 审查维度

### 安全性
- [ ] SQL 注入：所有数据库操作使用参数化查询
- [ ] 输入验证：外部输入在边界处验证
- [ ] 敏感信息：密钥、密码不硬编码

### 性能
- [ ] N+1 查询：循环内不调用数据库
- [ ] 无用导入：删除未使用的 import

### 可读性
- [ ] 函数长度：超过 50 行考虑拆分
- [ ] 命名：变量名表达意图，不用单字母

## 输出格式

每个问题按以下格式报告：
**[严重度]** 文件:行号 -- 问题描述
建议：具体修改方案

## 辅助脚本

运行项目 lint：
!`cd ${CLAUDE_SKILL_DIR} && cat lint-rules.json`
```

---

## token 效率对比

| 方案 | 每次调用消耗 | 说明 |
|------|------------|------|
| 全量注入 | ~20,000 token | 所有技能始终在上下文 |
| 按需加载（inline） | ~200 + 2,000 token | 列表 + 单个技能文档 |
| 按需加载（fork） | ~200 token（主会话） | 子 Agent 独立预算 |
| 条件技能 | 0 token（未激活时） | 操作匹配文件才加载 |

源码中技能列表预算固定为上下文窗口的 1%（默认 8000 字符），这意味着即使注册了 100 个技能，列表占用也不会超过 ~2000 token。

---

## 架构要点总结

从源码中可以提炼出几个值得借鉴的设计决策：

1. **多源并行加载 + 顺序去重**：`Promise.all` 并行读取所有目录，然后按优先级顺序合并、`realpath` 去重
2. **条件激活**：`paths` frontmatter 让技能零成本注册，只在操作匹配文件时才进入上下文
3. **两种执行模式**：inline（注入消息）vs fork（子 Agent），通过 frontmatter 一键切换
4. **预算控制**：技能列表占固定比例的上下文窗口，自动截断描述防止溢出
5. **安全边界**：MCP 技能禁止 Shell 执行；内置技能用 `O_NOFOLLOW | O_EXCL` 防路径遍历攻击；gitignored 目录不加载

## 设计哲学：三层可扩展性

设计指南将 Claude Code 的扩展机制总结为三个层次：

| 层次 | 机制 | 定位 |
|------|------|------|
| **MCP** | 标准协议，跨工具通用 | 工具的互联网——任何 AI 工具都能接入 |
| **Skills** | Markdown 技能文件 | 领域知识注入——项目级别的专业能力 |
| **Plugins** | 代码级扩展 | 深度定制——修改 Agent 行为本身 |

Skills 处于中间层，这个定位决定了它的设计选择：
- 比 MCP 更轻量（不需要启动服务器进程）
- 比 Plugins 更安全（只注入 Markdown 文本，不执行代码）
- 通过 frontmatter 元数据实现条件激活，兼顾灵活性和 token 效率

这三层遵循一个共同原则：**显式优于隐式**。技能通过 `paths` 字段显式声明适用范围，MCP 工具通过 schema 显式声明参数，Plugins 通过 API 显式注册能力。没有“自动发现”的魔法，一切可追溯。

---

下一篇：[Context Compact：三层压缩换无限会话](../06-context-compact/index.html)
