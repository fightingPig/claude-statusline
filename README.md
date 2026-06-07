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

## 变更日志

### 2026-06-07
- 新增第二行显示：本轮 I/O 用量、累计 I/O 用量（自动 K/M 转换）
- 新增缓存命中率显示
- 新增 Deepseek 账户余额查询（60 秒缓存）
- 新增安装时智能检测 Deepseek 官方 API 并自动配置余额查询
- 新增上下文进度条 True Color 状态指示（绿/黄/红）
- 修复: effort 字段解析字典格式的兼容问题
- 修复: 安装脚本中的 shell 注入风险
- 移除: `CLAUDE_MAX_CONTEXT_WINDOW` / `CLAUDE_CODE_AUTO_COMPACT_WINDOW` 环境变量配置

### 2026-06-07
- 新增: 脚本包裹在 main() 函数内，增加顶层异常兜底
- 新增: 模型名称缺失时始终显示占位符，保证第一行有内容
- 新增: 第二行始终固定输出 current/total/cache 三个字段
- 修复: context_window/current_usage 为 null 时脚本崩溃
- 修复: 第二行字段缺失时整行不输出的问题
- 优化: 余额查询改为仅读本地缓存，不再阻塞状态栏输出
