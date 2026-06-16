# -*- coding: utf-8 -*-
"""
合并 statusLine 配置到 ~/.claude/settings.json
保留已有的所有配置，只添加或覆盖 statusLine 和相关 env 配置
"""
import json, os, sys, platform, shutil, shlex

SETTINGS_PATH = os.path.expanduser("~/.claude/settings.json")
SCRIPT_PATH = os.path.expanduser("~/.claude/statusline.py")


def find_python():
    """Return an available Python command on this system."""
    candidates = ["python3", "python"] if platform.system() == "Darwin" else ["python", "py", "python3"]
    for cmd in candidates:
        if shutil.which(cmd):
            return cmd
    return "python"  # fallback, let it fail with a clear error


PYTHON_CMD = find_python()
STATUSLINE_STATUS = {
    "type": "command",
    "command": f"{PYTHON_CMD} {shlex.quote(SCRIPT_PATH)}"
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

    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print("✅ statusLine 配置已合并到 settings.json")
    print(f"   文件: {SETTINGS_PATH}")


if __name__ == "__main__":
    main()
