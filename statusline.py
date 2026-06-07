# -*- coding: utf-8 -*-
"""
Claude Code 状态栏脚本
显示：目录 | 分支 | 模型 + effort | 上下文进度条 | PR
第二行：本次 in/out | 累计 in/out | 缓存命中率
"""
import sys, json, os, subprocess, io, time

try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
except Exception:
    pass


def main():
    # Parse stdin
    data = {}
    try:
        raw = sys.stdin.read()
        if raw and raw.strip():
            data = json.loads(raw)
    except Exception:
        pass

    parts = []

    # ---- Line 1 ----

    # Directory
    cwd = data.get("workspace", {}).get("current_dir", "") if isinstance(data.get("workspace"), dict) else ""
    if cwd:
        dir_name = os.path.basename(cwd.replace("\\", "/"))
        if dir_name:
            parts.append(f"\U0001f4c2 {dir_name}")

    # Git branch
    try:
        ws = data.get("workspace", {}).get("current_dir", "") if isinstance(data.get("workspace"), dict) else ""
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

    # Model + Effort
    model = data.get("model", {}).get("display_name", "") if isinstance(data.get("model"), dict) else ""
    effort = data.get("effort", "") or data.get("effort_level", "")
    if isinstance(effort, dict):
        effort = effort.get("level", "")
    try:
        sf = os.path.expanduser("~/.claude/settings.json")
        if os.path.exists(sf):
            with open(sf, encoding="utf-8") as f:
                settings = json.load(f)
            if not model:
                model = settings.get("model", "")
            if not effort:
                effort = settings.get("effortLevel", "")
    except Exception:
        pass

    model_parts = [f"\U0001f9e0 {model}" if model else "\U0001f9e0 ?"]
    if effort:
        model_parts.append(f"⚡ {effort}")
    parts.append(" ".join(model_parts))

    # Context window (guard against None value)
    ctx_data = data.get("context_window")
    ctx = None
    cu = {}
    tc = {}
    if isinstance(ctx_data, dict):
        ctx = ctx_data.get("remaining_percentage")
        cu = ctx_data.get("current_usage") or {}
        tc = ctx_data
    if ctx is None:
        ctx = 100
    ctx_int = int(round(ctx))
    filled = max(ctx_int // 10, 1) if ctx_int > 0 else 0
    bar = "█" * filled + "░" * (10 - filled)
    if ctx_int >= 50:
        color = "38;5;46"
    elif ctx_int >= 20:
        color = "38;5;226"
    else:
        color = "38;5;196"
    parts.append(f"\033[{color}m{bar} {ctx_int}%\033[0m")

    # ---- Line 2 ----
    line2_parts = []

    in_tokens = cu.get("input_tokens") or 0 if isinstance(cu, dict) else 0
    out_tokens = cu.get("output_tokens") or 0 if isinstance(cu, dict) else 0
    line2_parts.append(f"current : ↑{in_tokens} ↓{out_tokens}")

    total_in = tc.get("total_input_tokens") or 0 if isinstance(tc, dict) else 0
    total_out = tc.get("total_output_tokens") or 0 if isinstance(tc, dict) else 0
    tot_parts = []
    if total_in >= 1000000:
        tot_parts.append(f"↑{round(total_in/1000000)}M")
    elif total_in >= 1000:
        tot_parts.append(f"↑{round(total_in/1000)}K")
    else:
        tot_parts.append(f"↑{total_in}")
    if total_out >= 1000000:
        tot_parts.append(f"↓{round(total_out/1000000)}M")
    elif total_out >= 1000:
        tot_parts.append(f"↓{round(total_out/1000)}K")
    else:
        tot_parts.append(f"↓{total_out}")
    line2_parts.append("total : " + " ".join(tot_parts))

    # Cache hit rate
    if isinstance(cu, dict):
        cache_read = cu.get("cache_read_input_tokens", 0) or 0
        cache_create = cu.get("cache_creation_input_tokens", 0) or 0
        input_tok = cu.get("input_tokens", 0) or 0
    else:
        cache_read = cache_create = input_tok = 0
    cache_total = cache_read + cache_create + input_tok
    hit_rate = (cache_read * 100 / cache_total) if cache_total > 0 else 0.0
    line2_parts.append(f"cache : {hit_rate:.2f}%")

    # Balance (cached only, no network call blocking output)
    CACHE_FILE = os.path.expanduser("~/.claude/.balance_cache")
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE) as f:
                cached = json.load(f)
            if time.time() - cached.get("time", 0) < 300:
                balance = cached.get("balance")
                if balance:
                    line2_parts.append(f"balance : ¥{balance}")
    except Exception:
        pass

    print(" │ ".join(parts))
    print(" │ ".join(line2_parts))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("\U0001f9e0 ? │ ██████████ 100%")
        print("current : ↑0 ↓0 │ total : ↑0 ↓0 │ cache : 0.00%")
