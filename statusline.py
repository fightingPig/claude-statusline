# -*- coding: utf-8 -*-
"""
Claude Code 状态栏脚本
显示：目录 | 分支 | 模型 + effort | 上下文进度条 | PR
第二行：本次 in/out | 累计 in/out | 缓存命中率
"""
import sys, json, os, subprocess, io, time, urllib.request, ssl

VERSION = 1
REPO_RAW = "https://raw.githubusercontent.com/fightingPig/claude-statusline/main"
UPDATE_INTERVAL = 86400  # 24h

CUMU_FILE = os.path.expanduser("~/.claude/.cumulative_cache.json")
_SSL_CTX = ssl._create_unverified_context()
UPDATE_CACHE = os.path.expanduser("~/.claude/.update_cache")
DEBUG_FLAG = os.path.expanduser("~/.claude/.statusline_debug")
DEBUG_LOG = os.path.expanduser("~/.claude/.statusline_debug_log.jsonl")
DEBUG_MAX_LINES = 10000

try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
except Exception:
    pass


def check_update():
    """检查更新，非关键路径，分两步执行避免单次阻塞过长"""
    try:
        cache = {}
        if os.path.exists(UPDATE_CACHE):
            with open(UPDATE_CACHE) as f:
                cache = json.load(f)
        if not isinstance(cache, dict):
            cache = {}
        now = time.time()

        # 步骤 2：有挂起下载 → 下载新脚本（短超时）
        pending = cache.get("pending")
        if pending:
            req = urllib.request.Request(f"{REPO_RAW}/statusline.py")
            with urllib.request.urlopen(req, timeout=5, context=_SSL_CTX) as resp:
                new_code = resp.read()
            # 完整性校验：文件头必须含 py 标记
            if new_code[:20] == b'# -*- coding: utf-8 -*-':
                script_path = os.path.abspath(__file__)
                tmp_path = script_path + ".update.tmp"
                with open(tmp_path, "wb") as f:
                    f.write(new_code)
                os.replace(tmp_path, script_path)
                pyc_path = script_path + "c"
                if os.path.exists(pyc_path):
                    os.remove(pyc_path)
                cache["version"] = pending
            cache.pop("pending", None)
            with open(UPDATE_CACHE, "w") as f:
                json.dump(cache, f)
            return

        # 距上次检查不足 24h 则跳过
        if now - cache.get("checked_at", 0) < UPDATE_INTERVAL:
            return

        # 步骤 1：取远程版本号（短超时，仅 ~3s 阻塞）
        req = urllib.request.Request(f"{REPO_RAW}/version.txt")
        with urllib.request.urlopen(req, timeout=3, context=_SSL_CTX) as resp:
            remote_ver = int(resp.read().decode().strip())
        cache["checked_at"] = now
        if remote_ver > cache.get("version", VERSION):
            cache["pending"] = remote_ver  # 标记挂起，下次调用再下载
        with open(UPDATE_CACHE, "w") as f:
            json.dump(cache, f)
    except Exception:
        pass


def get_cumulative_out(session_id, this_out):
    """按 session 累计 output tokens，相等性检测防重复计数"""
    try:
        cache = {}
        if os.path.exists(CUMU_FILE):
            with open(CUMU_FILE) as f:
                cache = json.load(f)
        if not isinstance(cache, dict):
            cache = {}
        s = cache.get(session_id, {"cumulative": 0, "last_out": -1})
        if this_out != s.get("last_out", -1):
            s["cumulative"] = s.get("cumulative", 0) + this_out
            s["last_out"] = this_out
        cache[session_id] = s
        tmp = CUMU_FILE + ".tmp"
        with open(tmp, "w") as f:
            json.dump(cache, f)
        os.replace(tmp, CUMU_FILE)
        return s.get("cumulative", 0)
    except Exception:
        return 0


def debug_log_context(data, ctx, ctx_int):
    if not os.path.exists(DEBUG_FLAG):
        return
    try:
        ctx_data_raw = data.get("context_window")
        entry = {
            "ts": time.time(),
            "session_id": data.get("session_id", ""),
            "ctx_window": ctx_data_raw,
            "remaining_pct": ctx,
            "ctx_int": ctx_int,
        }
        entry["ctx_int_anomaly"] = ctx_int > 100 or ctx_int < 0
        line = json.dumps(entry, ensure_ascii=False) + "\n"

        # Rotate if over max lines — keep last half
        if os.path.exists(DEBUG_LOG):
            with open(DEBUG_LOG, "r") as f:
                all_lines = f.readlines()
            if len(all_lines) >= DEBUG_MAX_LINES:
                keep = DEBUG_MAX_LINES // 2
                all_lines = all_lines[-keep:]
                tmp = DEBUG_LOG + ".tmp"
                with open(tmp, "w") as f:
                    f.writelines(all_lines)
                os.replace(tmp, DEBUG_LOG)

        with open(DEBUG_LOG, "a") as f:
            f.write(line)
    except Exception:
        pass


def main():
    check_update()

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
    debug_log_context(data, ctx, ctx_int)
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
    # total_output_tokens 不是累计值，用 get_cumulative_out 按 session 累计
    cumulative_out = get_cumulative_out(data.get("session_id", ""), out_tokens)
    tot_parts = []
    if total_in >= 1000000:
        tot_parts.append(f"↑{round(total_in/1000000)}M")
    elif total_in >= 1000:
        tot_parts.append(f"↑{round(total_in/1000)}K")
    else:
        tot_parts.append(f"↑{total_in}")
    if cumulative_out >= 1000000:
        tot_parts.append(f"↓{round(cumulative_out/1000000)}M")
    elif cumulative_out >= 1000:
        tot_parts.append(f"↓{round(cumulative_out/1000)}K")
    else:
        tot_parts.append(f"↓{cumulative_out}")
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

    # Balance
    BALANCE_FILE = os.path.expanduser("~/.claude/.balance_cache")
    balance = None
    cached = None
    if os.path.exists(BALANCE_FILE):
        try:
            with open(BALANCE_FILE) as f:
                cached = json.load(f)
        except Exception:
            pass
    if cached and time.time() - cached.get("time", 0) < 300:
        balance = cached.get("balance")
    else:
        try:
            sf = os.path.expanduser("~/.claude/settings.json")
            ds_key = None
            if os.path.exists(sf):
                with open(sf) as f:
                    s = json.load(f)
                env = s.get("env", {})
                ds_key = env.get("DEEPSEEK_API_KEY", "")
                if not ds_key and env.get("ANTHROPIC_BASE_URL", "").startswith("https://api.deepseek.com"):
                    ds_key = env.get("ANTHROPIC_AUTH_TOKEN", "")
            if ds_key:
                req = urllib.request.Request(
                    "https://api.deepseek.com/user/balance",
                    headers={"Authorization": f"Bearer {ds_key}"},
                )
                with urllib.request.urlopen(req, timeout=5, context=_SSL_CTX) as resp:
                    data = json.loads(resp.read())
                if "balance_infos" in data:
                    balance = data["balance_infos"][0].get("total_balance", "0")
                elif "balance" in data:
                    balance = data["balance"]
                if balance is not None:
                    with open(BALANCE_FILE, "w") as f:
                        json.dump({"time": time.time(), "balance": balance}, f)
        except Exception:
            pass  # API 失败，下面用旧缓存兜底
        if balance is None and cached:
            balance = cached.get("balance")
    if balance is not None:
        line2_parts.append(f"balance : ¥{balance}")

    print(" │ ".join(parts))
    print(" │ ".join(line2_parts))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("\U0001f9e0 ? │ ██████████ 100%")
        print("current : ↑0 ↓0 │ total : ↑0 ↓0 │ cache : 0.00%")
