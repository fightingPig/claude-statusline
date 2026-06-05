# -*- coding: utf-8 -*-
"""
Claude Code 状态栏脚本
显示：目录 | 分支 | 模型 + effort | 上下文进度条 | PR
"""
import sys, json, os, subprocess, io

# Force UTF-8 output for emoji support on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

data = json.load(sys.stdin)
parts = []

# 📂 Current directory name
cwd = data.get("workspace", {}).get("current_dir", "")
if cwd:
    dir_name = os.path.basename(cwd.replace("\\", "/"))
    if dir_name:
        parts.append(f"\U0001f4c2 {dir_name}")

# 🌿 Git branch name
try:
    ws = data.get("workspace", {}).get("current_dir", "")
    if ws:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=ws, capture_output=True, text=True, timeout=2
        )
        branch = result.stdout.strip()
        if branch:
            parts.append(f"\U0001f33f {branch}")
except Exception:
    pass

# 🧠 Model + ⚡ Effort (combined)
model = data.get("model", {}).get("display_name", "")
effort = data.get("effort", "") or data.get("effort_level", "")
if not effort and cwd:
    try:
        sf = os.path.expanduser("~/.claude/settings.json")
        if os.path.exists(sf):
            with open(sf, encoding="utf-8") as f:
                settings = json.load(f)
            effort = settings.get("effortLevel", "")
    except Exception:
        pass

model_parts = []
if model:
    model_parts.append(f"\U0001f9e0 {model}")
if effort:
    model_parts.append(f"⚡ {effort}")
if model_parts:
    parts.append(" ".join(model_parts))

# 📊 Context window progress bar
ctx = data.get("context_window", {}).get("remaining_percentage")
if ctx is not None:
    ctx_int = int(round(ctx))
    filled = ctx_int // 10
    bar = "█" * filled + "░" * (10 - filled)
    parts.append(f"{bar} {ctx_int}%")

# 🔀 PR number
pr = data.get("pr", {}).get("number")
if pr:
    parts.append(f"\U0001f500 PR #{pr}")

print(" │ ".join(parts) if parts else "")
