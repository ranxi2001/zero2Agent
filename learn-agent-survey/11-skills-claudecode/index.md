---
layout: default
title: "Skills + Claude Code：模块化技能系统"
description: Claude Code 的 Skill 机制——按需加载领域知识、自定义 Skill 编写、与 Claude Agent SDK 组合
eyebrow: 框架调研 · 11
---

# Skills + Claude Code：模块化技能系统

Claude Code 的 Skill 系统是一种**按需加载的领域知识机制**：把专门的操作指南、工具用法、领域规范打包成 Skill 文件，Agent 在需要时加载，不需要时不占用上下文。

这不只是 Claude Code 的功能，更是一种值得借鉴的 **Agent 知识管理模式**。

## 核心思路

传统做法：把所有指令塞进 System Prompt，不管用不用都占 token。

Skill 做法：
```
System Prompt（轻量，描述 Skill 元数据）
    |
用户请求触发匹配
    |
动态加载对应 Skill
    |
Skill 内容进入上下文
```

类比：Skill 就是 Agent 的“技能书”，用到哪本翻哪本，不是把整个图书馆背下来。

## Skill 文件结构

```
my-skill/
├── SKILL.md          # 必须，包含 frontmatter + 指令
└── references/       # 可选，详细参考文档
    ├── guide.md
    └── examples.md
```

**SKILL.md 格式：**

```markdown
---
name: code-review
description: >
  帮助进行代码审查，指出潜在问题、安全漏洞和改进建议。
  当用户提到"审查代码"、"code review"、"检查代码"时使用。
---

# 代码审查指南

## 审查维度

按以下维度检查代码：

1. **正确性**：逻辑是否正确，边界情况是否处理
2. **安全性**：有无 SQL 注入、XSS、敏感信息泄露
3. **性能**：有无 N+1 查询、不必要的循环
4. **可读性**：命名是否清晰，函数是否单一职责

## 输出格式

使用以下格式输出审查结果：

**问题级别**：严重 / 建议 / 风格
**位置**：文件名:行号
**描述**：问题描述
**建议**：改进方案
```

## 在 Claude Code 中使用

```bash
# 把 Skill 放到特定目录
~/.claude/skills/code-review/SKILL.md

# 或项目级 Skill
.claude/skills/deploy/SKILL.md
```

Claude Code 会自动识别并在合适时机加载。也可以显式指定：

```
/skill code-review
```

## 自定义 Skill 示例：数据库运维

```markdown
---
name: database-ops
description: >
  数据库运维操作指南，包含查询优化、索引管理、备份恢复。
  当用户提到数据库、SQL、索引、慢查询时使用此技能。
---

# 数据库运维 Skill

## 慢查询分析

当用户报告慢查询，按以下步骤：

1. 先用 EXPLAIN 分析执行计划
2. 检查是否缺少索引
3. 分析 JOIN 条件和过滤条件
4. 查看数据量级

```sql
-- 获取慢查询日志
SELECT query, exec_count, avg_latency
FROM performance_schema.events_statements_summary_by_digest
ORDER BY avg_latency DESC
LIMIT 10;
```

## 索引建议规则

- 外键字段必须建索引
- 高频 WHERE 条件字段建索引
- 联合索引遵循最左前缀原则
- 避免在低基数字段（如 status）单独建索引

## 注意事项

- 生产环境操作前先在测试环境验证
- DDL 操作要在低峰期进行
- 大表删除用 DELETE + LIMIT 分批
```

## 与 Claude API 集成

在代码里动态加载 Skill，实现类似效果：

```python
import anthropic
from pathlib import Path

def load_skill(skill_name: str) -> str:
    """加载 Skill 文件内容"""
    skill_path = Path(f"skills/{skill_name}/SKILL.md")
    if skill_path.exists():
        return skill_path.read_text(encoding="utf-8")
    return ""

def match_skill(user_input: str, skills: list[dict]) -> str | None:
    """根据用户输入匹配最合适的 Skill"""
    client = anthropic.Anthropic()
    skills_list = "\n".join([
        f"- {s['name']}: {s['description']}"
        for s in skills
    ])
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=50,
        messages=[{
            "role": "user",
            "content": f"""用户请求：{user_input}

可用 Skill：
{skills_list}

返回最匹配的 Skill 名称，或 "none"（如果没有匹配的）。只返回名称，不要其他内容。"""
        }]
    )
    result = response.content[0].text.strip()
    return result if result != "none" else None

class SkillAgent:
    def __init__(self, skills_dir: str = "skills"):
        self.client = anthropic.Anthropic()
        self.skills_dir = Path(skills_dir)
        self.skills_meta = self._load_skills_meta()

    def _load_skills_meta(self) -> list[dict]:
        """扫描 skills 目录，加载所有 Skill 的元数据"""
        skills = []
        for skill_dir in self.skills_dir.iterdir():
            skill_file = skill_dir / "SKILL.md"
            if skill_file.exists():
                content = skill_file.read_text(encoding="utf-8")
                # 解析 frontmatter
                import re
                name_match = re.search(r"name:\s*(.+)", content)
                desc_match = re.search(r"description:\s*>?\s*\n([\s\S]+?)(?=\n---|\n#)", content)
                if name_match:
                    skills.append({
                        "name": name_match.group(1).strip(),
                        "description": desc_match.group(1).strip() if desc_match else "",
                        "path": str(skill_file),
                    })
        return skills

    def run(self, user_input: str) -> str:
        system_prompt = "你是一个智能助手。"

        # 匹配并加载 Skill
        matched_skill = match_skill(user_input, self.skills_meta)
        if matched_skill:
            skill_content = load_skill(matched_skill)
            system_prompt += f"\n\n# 当前激活技能：{matched_skill}\n\n{skill_content}"
            print(f"  [加载 Skill: {matched_skill}]")

        response = self.client.messages.create(
            model="claude-opus-4-5",
            max_tokens=2048,
            system=system_prompt,
            messages=[{"role": "user", "content": user_input}],
        )
        return response.content[0].text

# 使用
agent = SkillAgent()
print(agent.run("帮我审查这段 Python 代码"))
print(agent.run("数据库查询很慢怎么排查"))
```

## Skill 的设计原则

**1. 单一职责**

每个 Skill 专注一个领域，不要把所有知识塞进一个 Skill。

**2. 触发词明确**

`description` 里要写清楚什么场景触发，帮助匹配逻辑准确。

**3. 可执行的指令**

Skill 内容是给模型看的指令，要用祈使句，不是文档式介绍。

**4. 控制长度**

Skill 加载后占用上下文，太长会挤压对话空间，保持在 300-500 行以内。

## 与 Codex 的对比

| 维度 | Skills + Claude Code | OpenAI Codex |
|------|---------------------|--------------|
| 技能加载 | 按需动态加载 | 固定 System Prompt |
| 知识组织 | 文件系统 + Markdown | Prompt 工程 |
| 扩展方式 | 新增 .md 文件 | 修改 System Prompt |
| 适用范围 | Claude Code CLI | API / 代码生成 |

## 优缺点

**优点：**
- 模块化，技能可复用和共享
- 按需加载，不浪费上下文窗口
- Markdown 格式，人类可读可编辑
- 不需要代码变更就能扩展 Agent 能力

**缺点：**
- 依赖匹配准确性，误匹配会加载错误 Skill
- Claude Code 专属，不通用于其他框架
- 复杂技能需要精心设计触发词

## 适合什么场景

- 有多个专业领域的 Agent（开发/运维/分析）
- 团队共享操作规范（代码风格、部署流程）
- 减少 System Prompt 膨胀
- 定制化 Claude Code 行为
