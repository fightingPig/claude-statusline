# Claude Code 状态栏

增强 Claude Code 状态栏，一目了然显示关键信息：

```
📂 isms6-system │ 🌿 develop │ 🧠 deepseek-v4-flash ⚡ xhigh │ ███████░░░ 75% │ 🔀 PR #42
```

## 功能

| 段 | 图标 | 说明 |
|---|------|------|
| 当前目录 | 📂 | 工作目录名 |
| 当前分支 | 🌿 | Git 分支（自动识别） |
| 模型 + Effort | 🧠 ⚡ | 当前模型名和 effort 级别 |
| 上下文进度条 | ███████░░░ | 上下文窗口剩余百分比，直观进度条 |
| PR 编号 | 🔀 | 当前关联的 PR（有则显示） |

## 一键安装

### Windows (PowerShell)

```powershell
irm https://raw.githubusercontent.com/fightingPig/claude-statusline/main/install.ps1 | iex
```

### Linux / macOS

```bash
curl -fsSL https://raw.githubusercontent.com/fightingPig/claude-statusline/main/install.sh | bash
```

安装脚本会自动：
1. 下载 `statusline.py` 到 `~/.claude/`
2. 合并 `statusLine` 配置到 `~/.claude/settings.json`
3. 添加 1M 上下文窗口环境变量

## 手动配置

### 1. 放置脚本

将 `statusline.py` 复制到 `~/.claude/statusline.py`

### 2. settings.json

在 `~/.claude/settings.json` 中添加：

```json
{
  "env": {
    "CLAUDE_MAX_CONTEXT_WINDOW": "1000000",
    "CLAUDE_CODE_AUTO_COMPACT_WINDOW": "1000000"
  },
  "statusLine": {
    "type": "command",
    "command": "python ~/.claude/statusline.py"
  }
}
```

> **注意**：Windows 路径中 `~` 会被自动展开为 `C:\Users\用户名`，也可以使用绝对路径：
> ```json
> "command": "python C:/Users/用户名/.claude/statusline.py"
> ```

## 自定义

### 修改显示顺序

编辑 `statusline.py`，调整 `parts.append()` 的调用顺序即可。

### 添加/删除显示项

- 删除某项：注释或删除对应的 `parts.append()` 代码块
- 添加图标：参考现有代码，使用对应 Unicode emoji

### 修改分隔符

在文件末尾将 `" │ "` 改为你想要的符号，例如 `" | "` 或 `"  "`（空格）。

## 已安装的文件

| 文件 | 路径 |
|------|------|
| 状态栏脚本 | `~/.claude/statusline.py` |
| 配置 | `~/.claude/settings.json` |

## 卸载

```bash
# 删除脚本
rm ~/.claude/statusline.py

# 然后从 ~/.claude/settings.json 中删除 "statusLine" 字段
```
