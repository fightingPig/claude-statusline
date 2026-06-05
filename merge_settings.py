# -*- coding: utf-8 -*-
"""
合并 statusLine 配置到 ~/.claude/settings.json
保留已有的所有配置，只添加或覆盖 statusLine 和相关 env 配置
"""
import json, os, sys, platform

SETTINGS_PATH = os.path.expanduser("~/.claude/settings.json")

# 根据系统选择 Python 命令 (Mac 无 python, 只有 python3)
PYTHON_CMD = "python3" if platform.system() == "Darwin" else "python"
SCRIPT_PATH = os.path.expanduser("~/.claude/statusline.py")
STATUSLINE_STATUS = {
    "type": "command",
    "command": f"{PYTHON_CMD} {SCRIPT_PATH}"
}

STATUSLINE_ENV = {
    "CLAUDE_MAX_CONTEXT_WINDOW": "1000000",
    "CLAUDE_CODE_AUTO_COMPACT_WINDOW": "1000000"
}


def main():
    if not os.path.exists(SETTINGS_PATH):
        print(f"错误: 未找到 {SETTINGS_PATH}")
        print("请先安装并运行 Claude Code 以生成默认配置文件。")
        sys.exit(1)

    with open(SETTINGS_PATH, encoding="utf-8") as f:
        settings = json.load(f)

    # 添加状态栏配置
    settings["statusLine"] = STATUSLINE_STATUS

    # 添加环境变量（保留已有的 env）
    if "env" not in settings:
        settings["env"] = {}
    for k, v in STATUSLINE_ENV.items():
        if k not in settings["env"]:
            settings["env"][k] = v

    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print("✅ statusLine 配置已合并到 settings.json")
    print(f"   文件: {SETTINGS_PATH}")


if __name__ == "__main__":
    main()
