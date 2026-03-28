---
layout: default
title: Skill Loading：按需加载领域知识
description: 两层注入策略——系统提示只放名称，详细文档按需加载
eyebrow: Claude Code / s05
---

# Skill Loading：按需加载领域知识

> *"load knowledge temporarily when needed"*

把所有领域知识塞进 system prompt 会浪费 20,000+ token。这一节实现按需加载：系统提示只告诉模型"有哪些技能"，详细文档在模型主动请求时才加载。

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

load_skill 工具调用：
  完整技能文档注入为 tool_result（~2000 token，临时）
```

知识是临时的——模型用完这轮，下次需要时再加载。上下文不会被长期占用。

---

## 目录结构

```
skills/
  code-review/
    SKILL.md        ← 完整的代码审查指南（~2000 token）
  write-tests/
    SKILL.md        ← 测试编写最佳实践
  database/
    SKILL.md        ← SQL 和 ORM 操作规范
  ...
```

每个技能是一个目录，核心是 `SKILL.md`。

---

## SkillLoader 实现

```python
import os
from pathlib import Path

SKILLS_DIR = Path("skills")

class SkillLoader:
    def __init__(self):
        self.skills = self._scan()

    def _scan(self) -> dict:
        """扫描 skills/ 目录，读取每个 SKILL.md 的前两行作为描述"""
        skills = {}
        if not SKILLS_DIR.exists():
            return skills
        for skill_dir in SKILLS_DIR.iterdir():
            if skill_dir.is_dir():
                skill_md = skill_dir / "SKILL.md"
                if skill_md.exists():
                    content = skill_md.read_text()
                    # 第一行是标题，第二行是描述
                    lines = content.strip().splitlines()
                    name = lines[0].lstrip("# ").strip() if lines else skill_dir.name
                    desc = lines[1].strip() if len(lines) > 1 else ""
                    skills[skill_dir.name] = {
                        "name": name,
                        "description": desc,
                        "path": skill_md,
                    }
        return skills

    def list_summary(self) -> str:
        """生成技能列表摘要，注入 system prompt"""
        if not self.skills:
            return "No skills available."
        lines = ["## 可用技能\n"]
        for slug, info in self.skills.items():
            lines.append(f"- **{slug}**: {info['description']}")
        lines.append("\n使用 load_skill 工具加载完整技能文档。")
        return "\n".join(lines)

    def load(self, skill_name: str) -> str:
        """加载完整技能文档"""
        if skill_name not in self.skills:
            available = ", ".join(self.skills.keys())
            return f"Skill '{skill_name}' not found. Available: {available}"
        return self.skills[skill_name]["path"].read_text()


skill_loader = SkillLoader()
```

---

## 集成到 Agent

**System prompt 注入技能列表：**

```python
SYSTEM = f"""你是一个 Coding Agent，可以执行工具完成编程任务。

{skill_loader.list_summary()}
"""
```

**load_skill 工具：**

```python
TOOLS.append({
    "name": "load_skill",
    "description": "加载指定技能的完整文档到上下文。在执行专业任务前先加载相关技能。",
    "input_schema": {
        "type": "object",
        "properties": {
            "skill_name": {
                "type": "string",
                "description": "技能名称（目录名），如 'code-review', 'write-tests'"
            }
        },
        "required": ["skill_name"]
    }
})

TOOL_HANDLERS["load_skill"] = lambda **kw: skill_loader.load(kw["skill_name"])
```

---

## 执行流程

<div class="mermaid">
flowchart TD
    A([用户：帮我做代码审查]) --> B[LLM 看到技能列表]
    B --> C[load_skill: code-review]
    C --> D[完整审查文档注入上下文]
    D --> E[read_file: 读取目标代码]
    E --> F[按技能文档标准审查]
    F --> G([输出审查报告])
</div>

---

## SKILL.md 示例

```markdown
# Code Review
专业代码审查技能，覆盖安全性、性能、可维护性

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
**[严重度]** 文件:行号 — 问题描述
建议：具体修改方案
```

---

## token 效率对比

| 方案 | 每次调用消耗 | 说明 |
|------|------------|------|
| 全量注入 | ~20,000 token | 所有技能始终在上下文 |
| 按需加载 | ~200 + 2,000 token | 列表 + 单个技能文档 |
| 节省 | ~90% | 典型场景每次只用 1-2 个技能 |

---

下一篇：[Context Compact：三层压缩换无限会话](../06-context-compact/index.html)
