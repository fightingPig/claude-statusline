# Claude Code 状态栏

增强 Claude Code 状态栏，两行显示关键信息：

```
📂 dir │ 🌿 main │ 🧠 model ⚡ effort │ ████████░░ 82%
current : ↑129 ↓1146 │ total : ↑203K ↓1720 │ cache : 99.93%
```

## 功能

**第一行**：当前目录、Git 分支、模型 + Effort、上下文进度条

**第二行**：
- `current ↑↓` — 本轮请求的新增输入 tokens（cache miss）和输出 tokens
- `total ↑↓` — 会话累计输入 tokens（含缓存命中）+ 累计输出 tokens（本地推算）
- `cache` — 本轮请求的即时缓存命中率
- `balance` — Deepseek 账户余额（依赖余额查询缓存）

## 安装

### Windows (PowerShell)

```powershell
irm https://raw.githubusercontent.com/fightingPig/claude-statusline/main/install.ps1 | iex
```

### Linux / macOS

```bash
curl -fsSL https://raw.githubusercontent.com/fightingPig/claude-statusline/main/install.sh | bash
```

安装脚本会下载脚本并配置 `settings.json`。如果检测到 Deepseek 官方 API 会自动启用余额查询，否则可手动配置。

## 自动更新

statusline.py 内置自动更新机制，无需手动操作：

- 每次运行时检查本地缓存，距上次更新检查不足 24 小时则跳过
- 超过 24 小时时，从 GitHub 拉取 `version.txt` 比对版本号
- 有新版本时，自动下载并原子替换本地脚本（`write → os.replace`）
- 更新在后台静默完成，不阻塞状态栏输出
- 安装后首次更新最多 24 小时内生效，可通过删除 `~/.claude/.update_cache` 手动触发重新检查

## 实现原理

### 数据流

```
Deepseek API（Anthropic 兼容端点，直接返回 Anthropic 格式）
  usage.input_tokens                  ← prompt_cache_miss_tokens
  usage.cache_read_input_tokens       ← prompt_cache_hit_tokens
  usage.output_tokens                 ← completion_tokens
        │
        ▼
Claude Code 内部（PPO 函数）
  聚合为 context_window 对象传给 statusline
  total_input_tokens  = input_tokens + cache_creation + cache_read
  total_output_tokens = output_tokens（⚠️ 不是累计值，和本轮相同）
  current_usage       = 原样透传
        │
        ▼
statusline.py（stdin 接收）
  解析 JSON，提取字段，渲染两行输出
```

### 累计 output tokens 方案

Claude Code 传给 statusline 的 `total_output_tokens` 字段不是会话累计值——源代码显示它只是 `H?.output_tokens ?? 0`（本轮输出，不做累加）。因此 statusline.py 自行推算会话累计输出。

**核心逻辑（get_cumulative_out 函数）：**

```python
def get_cumulative_out(session_id, this_out):
    cache = load_cache_file()              # 读 ~/.claude/.cumulative_cache.json
    s = cache.get(session_id, {})          # 按 session_id 隔离
    if this_out != s["last_out"]:          # 相等性检测：值变化时才累加
        s["cumulative"] += this_out
        s["last_out"] = this_out
    save_cache_file(cache)                 # 原子写入（write → rename）
    return s["cumulative"]
```

**关键设计：**

| 要素 | 说明 |
|---|---|
| `session_id` 做 Key | 不同会话的累计值隔离，互不干扰 |
| `last_out` 检重 | statusline 每回合可能被调多次（debounce 刷新），`this_out == last_out` 时跳过不加，避免重复计数 |
| 原子写入 | 先写 `.tmp` 文件再 `os.replace`，避免文件写坏导致数据丢失 |
| 异常兜底 | 文件读写异常时返回 0，不影响状态栏显示 |

**相等性检测场景示例：**

```
时间线                                    输出值        累计行为
API 响应到达 → tokenUsage 更新            out=406      406 != last_out(-1)，累计 += 406
debounce 刷新                              out=0        0 != last_out(406)，累计 += 0
另一轮 debounce 刷新                       out=0        0 == last_out(0)，跳过
新的 API 响应                              out=577      577 != last_out(0)，累计 += 577
```

### 缓存命中率

```
cache : 99.93%
```

公式：`cache_read_input_tokens / (cache_read_input_tokens + cache_creation_input_tokens + input_tokens)`

- `cache_read_input_tokens` — 本轮请求中命中缓存的 tokens 数（Deepseek 原始字段：`prompt_cache_hit_tokens`）
- `input_tokens` — 本轮请求中未命中缓存的 tokens 数（Deepseek 原始字段：`prompt_cache_miss_tokens`）

计算的是**本轮请求的即时命中率**（非会话累计），直接来自 Deepseek API 返回的原始数据，没有聚合误差。

### 第二行字段速查

```
字段                  来源                             含义
current ↑N            current_usage.input_tokens       本轮新增（cache miss）输入
current ↓N            current_usage.output_tokens      本轮输出
total ↑N              total_input_tokens               会话累计输入（含缓存命中）
total ↓N              本地推算                         会话累计输出（非 API 提供）
cache N%              即时公式                         本轮缓存命中率
```

## Deepseek 余额查询

状态栏自动查询并显示 Deepseek 账户余额，缓存 300 秒避免频繁请求。

查询逻辑：
1. 优先读取缓存文件 `~/.claude/.balance_cache`，5 分钟内有效
2. 缓存过期后，调用 `https://api.deepseek.com/user/balance` 实时查询
3. 查询结果写入缓存，下次直接读取

密钥按以下顺序获取：

1. `env.DEEPSEEK_API_KEY` — 手动配置
2. `env.ANTHROPIC_AUTH_TOKEN` — 当 `ANTHROPIC_BASE_URL` 以 `https://api.deepseek.com` 开头时自动复用

## 卸载

```bash
rm ~/.claude/statusline.py
# 并从 ~/.claude/settings.json 删除 "statusLine" 字段
```

## 变更日志

### 2026-06-11
- 修复: 安装脚本 `curl \| bash` 管道导致 Deepseek API Key 输入提示被跳过，`read` 改为从 `/dev/tty` 读取
- 修复: 安装脚本 Deepseek API URL 判断改为前缀匹配，兼容 `/v1` 等后缀
- 修复: 累计 output tokens 算法从 delta 法改回相等性检测，避免 output 值重置时累计丢失
- 新增: debug logging 基础设施，通过标记文件控制上下文窗口数据记录到 JSONL 日志，支持自动轮转

### 2026-06-07
- 新增: 自动更新机制——脚本自检查 + GitHub 版本比对 + 原子自替换
- 修复: 恢复 Deepseek 余额查询功能（自动调用 API + 300 秒缓存）
- 修复: total_output_tokens 不是会话累计值，改为本地推算累计 output
- 新增: 累计 output tokens 方案——按 session_id 隔离 + delta 检测防重复计数 + 原子写入
- 新增: 详细的实现原理文档，包括数据流、字段映射、缓存命中率公式
- 新增: 脚本包裹在 main() 函数内，增加顶层异常兜底
- 新增: 模型名称缺失时始终显示占位符，保证第一行有内容
- 新增: 第二行始终固定输出 current/total/cache 三个字段
- 新增第二行显示：本轮 I/O 用量、累计 I/O 用量（自动 K/M 转换）
- 新增缓存命中率显示
- 新增 Deepseek 账户余额查询（300 秒缓存）
- 新增安装时智能检测 Deepseek 官方 API 并自动配置余额查询
- 新增上下文进度条 True Color 状态指示（绿/黄/红）
- 修复: effort 字段解析字典格式的兼容问题
- 修复: 安装脚本中的 shell 注入风险
- 修复: context_window/current_usage 为 null 时脚本崩溃
- 修复: 第二行字段缺失时整行不输出的问题
- 优化: 余额查询改为仅读本地缓存，不再阻塞状态栏输出
- 移除: `CLAUDE_MAX_CONTEXT_WINDOW` / `CLAUDE_CODE_AUTO_COMPACT_WINDOW` 环境变量配置
