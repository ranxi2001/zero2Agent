#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# zero2Agent 绿皮书 PDF 编译脚本
# 依赖：pandoc >= 3.0, xelatex (texlive-xetex), Python 3
# 用法：./build.sh [模块路径] [输出文件名]
# 示例：./build.sh ../learn-agent-interview zero2Agent-绿皮书-Agent面试500问
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TEMPLATE_DIR="$SCRIPT_DIR/templates"
OUTPUT_DIR="$SCRIPT_DIR/output"
STAGING_DIR="$SCRIPT_DIR/staging"
COVER_IMAGE="$TEMPLATE_DIR/cover.png"

case "$(uname -s)" in
    MINGW*|CYGWIN*|MSYS*) COVER_IMAGE=$(cygpath -m "$COVER_IMAGE") ;;
esac

MODULE_PATH="${1:-../learn-agent-interview}"
OUTPUT_NAME="${2:-zero2Agent-绿皮书-Agent面试500问}"

# 解析为绝对路径
if [[ "$MODULE_PATH" != /* ]]; then
    MODULE_PATH="$SCRIPT_DIR/$MODULE_PATH"
fi

mkdir -p "$OUTPUT_DIR"

echo "=== zero2Agent 绿皮书编译 ==="
echo "模块路径: $MODULE_PATH"
echo "输出文件: $OUTPUT_DIR/$OUTPUT_NAME.pdf"

# 检查依赖
for cmd in pandoc xelatex; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "错误: 未找到 $cmd，请先安装"
        [[ "$cmd" == "pandoc" ]] && echo "  brew install pandoc"
        [[ "$cmd" == "xelatex" ]] && echo "  brew install --cask mactex-no-gui"
        exit 1
    fi
done

if command -v python3 >/dev/null 2>&1 && python3 --version >/dev/null 2>&1; then
    :
elif command -v python >/dev/null 2>&1 && python --version >/dev/null 2>&1; then
    :
else
    echo "错误: 未找到可用的 Python 3 解释器"
    exit 1
fi

# Step 1: 预处理（保留答案对比、去 frontmatter、转速查格式）
echo ""
echo "[1/2] 预处理：转为面试速查格式..."
bash "$SCRIPT_DIR/strip-for-pdf.sh" "$MODULE_PATH"

# Step 2: 收集预处理后的文件
INPUTS=()
for f in $(find "$STAGING_DIR" -name "*.md" | sort); do
    INPUTS+=("$f")
done

echo ""
echo "[2/2] 编译 PDF（共 ${#INPUTS[@]} 个文件）..."

# 编译 PDF
pandoc "${INPUTS[@]}" \
    --from markdown \
    --to pdf \
    --pdf-engine=xelatex \
    --template="$TEMPLATE_DIR/greenbook.tex" \
    --metadata-file="$TEMPLATE_DIR/metadata.yaml" \
    --resource-path="$MODULE_PATH:$STAGING_DIR:$TEMPLATE_DIR" \
    --toc \
    --toc-depth=2 \
    --number-sections \
    --top-level-division=chapter \
    --no-highlight \
    -V documentclass=ctexbook \
    -V geometry="margin=2.5cm" \
    -V fontsize=10pt \
    -V linestretch=1.3 \
    -V cover-image="$COVER_IMAGE" \
    -o "$OUTPUT_DIR/$OUTPUT_NAME.pdf"

echo ""
echo "=== 编译完成 ==="
echo "输出: $OUTPUT_DIR/$OUTPUT_NAME.pdf"
echo "文件大小: $(du -h "$OUTPUT_DIR/$OUTPUT_NAME.pdf" | cut -f1)"
echo ""
echo "版权声明已内嵌，仓库链接: https://github.com/ranxi2001/zero2Agent"
