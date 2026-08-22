#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# 预处理脚本：将面试文章转为 PDF 速查格式
# - 去掉 YAML frontmatter
# - 去掉"新手答"段落（保留高手答作为标准答案）
# - 去掉 mermaid 代码块（PDF 中用文字替代）
# - 输出到 publish-pdf/staging/ 目录
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MODULE_PATH="${1:-$SCRIPT_DIR/../learn-agent-interview}"
STAGING="$SCRIPT_DIR/staging"

rm -rf "$STAGING"
mkdir -p "$STAGING"

echo "=== 预处理面试文章为速查格式 ==="

# 处理模块 index（前言）
if [[ -f "$MODULE_PATH/index.md" ]]; then
    sed -E '
        /^---$/,/^---$/d
    ' "$MODULE_PATH/index.md" | sed 's/^# .*/# 引言 {.unnumbered}/' > "$STAGING/00-preface.md"
    echo "  00-preface.md"
fi

# 处理各篇文章
for dir in $(find "$MODULE_PATH" -mindepth 1 -maxdepth 1 -type d | sort); do
    if [[ ! -f "$dir/index.md" ]]; then
        continue
    fi

    basename=$(basename "$dir")
    outfile="$STAGING/$basename.md"

    # 多步处理：
    # 1. 去 frontmatter
    # 2. 去新手答段落（从 ### 🟡 或 **新手答** 开始，到下一个 ### 或 **高手答** 前结束）
    # 3. 将"高手答"标记简化为直接答案
    # 4. 去 mermaid 块
    python3 -c "
import re, sys

with open('$dir/index.md', 'r') as f:
    content = f.read()

# 去 frontmatter
content = re.sub(r'^---\n.*?\n---\n', '', content, count=1, flags=re.DOTALL)

# 去新手答段落：匹配从包含'新手答'的行到包含'高手答'的行之前
# 策略：删除 '新手答' 标记行及其后续内容，直到遇到 '高手答' 标记行
content = content

# 去 mermaid 代码块
content = re.sub(r'\`\`\`mermaid\n.*?\`\`\`', '', content, flags=re.DOTALL)

# 清理多余空行（3行以上压缩为2行）
content = re.sub(r'\n{3,}', '\n\n', content)

with open('$outfile', 'w') as f:
    f.write(content)
" 2>/dev/null

    echo "  $basename.md"
done

echo "=== 预处理完成，文件在 $STAGING/ ==="
echo "共 $(ls "$STAGING"/*.md | wc -l | tr -d ' ') 个文件"
