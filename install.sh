#!/bin/bash
set -euo pipefail

REPO_BASE="https://raw.githubusercontent.com/fightingPig/claude-statusline/main"

echo "🚀 正在安装 Claude Code 状态栏 ..."

# 1. 确保 ~/.claude 目录存在
mkdir -p "$HOME/.claude"

# 2. 下载 statusline.py
SCRIPT_PATH="$HOME/.claude/statusline.py"
echo "⬇️  下载 statusline.py ..."
curl -fsSL "$REPO_BASE/statusline.py" -o "$SCRIPT_PATH"
echo "✅ 已保存到 $SCRIPT_PATH"

# 3. 下载并执行配置合并脚本
MERGE_PATH="/tmp/merge_settings.py"
echo "⬇️  下载配置合并脚本 ..."
curl -fsSL "$REPO_BASE/merge_settings.py" -o "$MERGE_PATH"
python3 "$MERGE_PATH" || python "$MERGE_PATH"
rm -f "$MERGE_PATH"

# 4. 验证
echo ""
echo "🎉 安装完成！"
echo ""
echo "📋 已在 settings.json 中添加以下配置:"
echo "   - statusLine 命令 (调用 statusline.py)"
echo ""
echo "🔄 请重新启动 Claude Code 以生效"
echo ""
echo "📖 更多配置说明见: https://github.com/fightingPig/claude-statusline"
