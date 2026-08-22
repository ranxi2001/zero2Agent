#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# 预处理脚本：将面试文章转为 PDF 速查格式
# - 去掉 YAML frontmatter
# - 保留"新手答"与"高手答"对比
# - 去掉 mermaid 代码块（PDF 中用文字替代）
# - 输出到 publish-pdf/staging/ 目录
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MODULE_PATH="${1:-$SCRIPT_DIR/../learn-agent-interview}"
STAGING="$SCRIPT_DIR/staging"

if command -v python3 >/dev/null 2>&1 && python3 --version >/dev/null 2>&1; then
    PYTHON=python3
elif command -v python >/dev/null 2>&1 && python --version >/dev/null 2>&1; then
    PYTHON=python
else
    echo "错误: 未找到可用的 Python 解释器" >&2
    exit 1
fi

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
    input_path="$dir/index.md"
    output_path="$outfile"
    case "$(uname -s)" in
        MINGW*|CYGWIN*|MSYS*)
            input_path=$(cygpath -w "$input_path")
            output_path=$(cygpath -w "$output_path")
            ;;
    esac

    # 多步处理：
    # 1. 去 frontmatter
    # 2. 保留"新手答"与"高手答"对比
    # 3. 去 mermaid 块
    "$PYTHON" -c "
import re, sys

with open(sys.argv[1], 'r', encoding='utf-8') as f:
    content = f.read()

# 去 frontmatter
content = re.sub(r'^---\n.*?\n---\n', '', content, count=1, flags=re.DOTALL)

# 去 mermaid 代码块
content = re.sub(r'\`\`\`mermaid\n.*?\`\`\`', '', content, flags=re.DOTALL)

# 清理多余空行（3行以上压缩为2行）
content = re.sub(r'\n{3,}', '\n\n', content)

with open(sys.argv[2], 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)
" "$input_path" "$output_path"

    echo "  $basename.md"
done

echo "=== 预处理完成，文件在 $STAGING/ ==="
echo "共 $(ls "$STAGING"/*.md | wc -l | tr -d ' ') 个文件"
