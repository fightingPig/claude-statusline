# -*- coding: utf-8 -*-
"""
Claude Code 状态栏脚本
显示：目录 | 分支 | 模型 + effort | 上下文进度条 | PR
第二行：本次 in/out | 累计 in/out | 缓存命中率
"""
import sys, json, os, subprocess, io, urllib.request, time, ssl

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

# 🧠 Model + ⚡ Effort
model = data.get("model", {}).get("display_name", "")
effort_raw = data.get("effort", "") or data.get("effort_level", "")
if isinstance(effort_raw, dict):
    effort = effort_raw.get("level", "")
elif isinstance(effort_raw, str):
    effort = effort_raw
else:
    effort = ""
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
    bar = "\u2588" * filled + "\u2591" * (10 - filled)
    parts.append(f"{bar} {ctx_int}%")

# 🔀 PR number
pr = data.get("pr", {}).get("number")
if pr:
    parts.append(f"\U0001f500 PR #{pr}")

# ---- Line 2: Token usage ----
line2_parts = []
cu = data.get("context_window", {}).get("current_usage", {})
tc = data.get("context_window", {})

# 本次 I/O: ↑输入 ↓输出
in_tokens = cu.get("input_tokens")
out_tokens = cu.get("output_tokens")
io_parts = []
if in_tokens is not None:
    io_parts.append(f"\u2191{in_tokens}")
if out_tokens is not None:
    io_parts.append(f"\u2193{out_tokens}")
if io_parts:
    line2_parts.append("current : " + " ".join(io_parts))

# 累计 I/O
total_in = tc.get("total_input_tokens")
total_out = tc.get("total_output_tokens")
tot_parts = []
if total_in is not None:
    if total_in >= 1000000:
        tot_parts.append(f"\u2191{round(total_in/1000000)}M")
    elif total_in >= 1000:
        tot_parts.append(f"\u2191{round(total_in/1000)}K")
    else:
        tot_parts.append(f"\u2191{total_in}")
if total_out is not None:
    if total_out >= 1000000:
        tot_parts.append(f"\u2193{round(total_out/1000000)}M")
    elif total_out >= 1000:
        tot_parts.append(f"\u2193{round(total_out/1000)}K")
    else:
        tot_parts.append(f"\u2193{total_out}")
if tot_parts:
    line2_parts.append("total : " + " ".join(tot_parts))

# 缓存命中率: cache_read / (cache_read + cache_creation + input_tokens)
cache_read = cu.get("cache_read_input_tokens", 0)
cache_create = cu.get("cache_creation_input_tokens", 0)
input_tok = cu.get("input_tokens", 0)
cache_total = cache_read + cache_create + input_tok
if cache_total > 0:
    hit_rate = cache_read * 100 / cache_total
    line2_parts.append(f"cache : {hit_rate:.2f}%")

# \ud83d\udcb0 Deepseek \u8d26\u6237\u4f59\u989d\uff08\u7f13\u5b58 60 \u79d2\uff09
CACHE_FILE = os.path.expanduser("~/.claude/.balance_cache")
ds_key = None
try:
    sf = os.path.expanduser("~/.claude/settings.json")
    if os.path.exists(sf):
        with open(sf) as f:
            s = json.load(f)
        env = s.get("env", {})
        ds_key = env.get("DEEPSEEK_API_KEY", "")
        if not ds_key and env.get("ANTHROPIC_BASE_URL", "") == "https://api.deepseek.com":
            ds_key = env.get("ANTHROPIC_AUTH_TOKEN", "")
except Exception:
    pass

balance = None
if ds_key:
    now = time.time()
    cached = None
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE) as f:
                cached = json.load(f)
    except Exception:
        pass
    if cached and now - cached.get("time", 0) < 60:
        balance = cached.get("balance")
    else:
        try:
            req = urllib.request.Request(
                "https://api.deepseek.com/user/balance",
                headers={"Authorization": f"Bearer {ds_key}"},
                method="GET"
            )
            with urllib.request.urlopen(req, timeout=5, context=ssl._create_unverified_context()) as resp:
                balance_resp = json.loads(resp.read())
            if "balance_infos" in balance_resp:
                balance = balance_resp["balance_infos"][0].get("total_balance", "0")
            elif "balance" in balance_resp:
                balance = balance_resp["balance"]
            else:
                balance = "0"
            try:
                with open(CACHE_FILE, "w") as f:
                    json.dump({"time": now, "balance": balance}, f)
            except Exception:
                pass
        except Exception:
            if cached:
                balance = cached.get("balance")
if balance:
    line2_parts.append(f"balance : \u00a5{balance}")

line1 = " \u2502 ".join(parts) if parts else ""
line2 = " \u2502 ".join(line2_parts) if line2_parts else ""

if line1 and line2:
    print(f"{line1}\n{line2}")
elif line1:
    print(line1)
elif line2:
    print(line2)
