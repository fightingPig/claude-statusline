# Claude Code 状态栏

增强 Claude Code 状态栏，两行显示关键信息：

```
📂 dir │ 🌿 main │ 🧠 model ⚡ effort │ █████████░ 90% │ 🔀 PR #42
current : ↑153 ↓362 │ total : ↑105K ↓4K │ cache : 99.73% │ balance : ¥174.59
```

## 功能

**第一行**：当前目录、Git 分支、模型 + Effort、上下文进度条、PR 编号

**第二行**：本轮 I/O 用量、累计 I/O 用量、缓存命中率、Deepseek 账户余额

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

## Deepseek 余额查询

状态栏支持显示 Deepseek 账户余额，密钥按以下顺序获取：

1. `env.DEEPSEEK_API_KEY` — 手动配置
2. `env.ANTHROPIC_AUTH_TOKEN` — 仅当 `ANTHROPIC_BASE_URL` 为 `https://api.deepseek.com` 时自动复用

余额缓存 60 秒，避免频繁请求。

## 卸载

```bash
rm ~/.claude/statusline.py
# 并从 ~/.claude/settings.json 删除 "statusLine" 字段
```
