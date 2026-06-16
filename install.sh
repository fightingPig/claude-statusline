#!/bin/bash
set -euo pipefail

REPO_BASE="https://raw.githubusercontent.com/fightingPig/claude-statusline/main"

echo "🚀 正在安装 Claude Code 状态栏 ..."

# 0. 检测可用的 Python 命令
PYTHON=""
for c in python3 python; do
    if command -v "$c" &>/dev/null; then
        PYTHON="$c"
        break
    fi
done
if [ -z "$PYTHON" ]; then
    echo "❌ 未找到 Python，请先安装 Python 并添加到 PATH" >&2
    exit 1
fi

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
$PYTHON "$MERGE_PATH"
rm -f "$MERGE_PATH"

# 4. Deepseek 余额查询配置
echo ""
SETTINGS_PATH="$HOME/.claude/settings.json"
DEEPSEEK_AUTO=0
if [ -f "$SETTINGS_PATH" ]; then
    # 通过环境变量传值，避免 shell 注入
    BASE_URL=$(SETTINGS_PATH="$SETTINGS_PATH" $PYTHON -c "
import os, json
try:
    with open(os.environ['SETTINGS_PATH'], encoding='utf-8-sig') as f:
        s = json.load(f)
    print(s.get('env', {}).get('ANTHROPIC_BASE_URL', ''))
except Exception as e:
    print('', flush=True)
")

    HAS_DS_KEY=$(SETTINGS_PATH="$SETTINGS_PATH" $PYTHON -c "
import os, json
try:
    with open(os.environ['SETTINGS_PATH'], encoding='utf-8-sig') as f:
        s = json.load(f)
    print('1' if s.get('env', {}).get('DEEPSEEK_API_KEY') else '0')
except:
    print('0')
")

    if [[ "$BASE_URL" == https://api.deepseek.com* ]]; then
        DEEPSEEK_AUTO=1
        if [ "$HAS_DS_KEY" = "1" ]; then
            echo "✅ 检测到 Deepseek 官方 API，余额查询密钥已存在，无需配置"
        elif ! SETTINGS_PATH="$SETTINGS_PATH" $PYTHON -c "
import os, json
with open(os.environ['SETTINGS_PATH'], encoding='utf-8-sig') as f:
    s = json.load(f)
env = s.setdefault('env', {})
token = env.get('ANTHROPIC_AUTH_TOKEN', '')
if token and 'DEEPSEEK_API_KEY' not in env:
    env['DEEPSEEK_API_KEY'] = token
    with open(os.environ['SETTINGS_PATH'], 'w', encoding='utf-8') as f:
        json.dump(s, f, indent=2, ensure_ascii=False)
        f.write('\n')
"; then
            echo "❌ 写入 DEEPSEEK_API_KEY 失败" >&2
        else
            echo "✅ 检测到 Deepseek 官方 API，已自动复用 ANTHROPIC_AUTH_TOKEN 作为余额查询密钥"
        fi
    elif [ "$HAS_DS_KEY" = "1" ]; then
        DEEPSEEK_AUTO=1
        echo "✅ 检测到已有 DEEPSEEK_API_KEY，余额查询已配置，无需重复操作"
    fi
fi

if [ "$DEEPSEEK_AUTO" -eq 0 ]; then
    echo "❓ 当前非 Deepseek 官方 API，仅支持查询 Deepseek 官方账户余额。"
    echo "   如果你是官方账户转接，需要额外提供官方 key，是否启用余额查询？(y/n)"
    read -p "   " CONFIRM < /dev/tty
    if [ "$CONFIRM" = "y" ] || [ "$CONFIRM" = "Y" ]; then
        read -p "  请输入 Deepseek API Key: " DS_KEY < /dev/tty
        if [ -n "$DS_KEY" ]; then
            if ! DS_KEY="$DS_KEY" SETTINGS_PATH="$SETTINGS_PATH" $PYTHON -c "
import os, json
with open(os.environ['SETTINGS_PATH'], encoding='utf-8-sig') as f:
    s = json.load(f)
s.setdefault('env', {})['DEEPSEEK_API_KEY'] = os.environ['DS_KEY']
with open(os.environ['SETTINGS_PATH'], 'w', encoding='utf-8') as f:
    json.dump(s, f, indent=2, ensure_ascii=False)
    f.write('\n')
"; then
                echo "❌ Deepseek API Key 保存失败" >&2
            else
                echo "✅ Deepseek API Key 已保存"
            fi
        fi
    fi
fi

# 5. 验证
echo ""
echo "🎉 安装完成！"
echo ""
echo "📋 已在 settings.json 中添加以下配置:"
echo "   - statusLine 命令 (调用 statusline.py)"
if [ "$DEEPSEEK_AUTO" -eq 1 ] || [ -n "${DS_KEY:-}" ]; then
    echo "   - DEEPSEEK_API_KEY（用于余额查询）"
fi
echo ""
echo "🔄 请重新启动 Claude Code 以生效"
echo ""
echo "📖 更多配置说明见: https://github.com/fightingPig/claude-statusline"
