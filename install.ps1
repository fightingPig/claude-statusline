<#
.SYNOPSIS
    Claude Code 状态栏一键安装脚本 (Windows)
.DESCRIPTION
    安装 claude-statusline 状态栏，显示目录、分支、模型、effort、上下文进度条、PR
    使用方法: irm https://raw.githubusercontent.com/fightingPig/claude-statusline/main/install.ps1 | iex
#>

$ErrorActionPreference = "Stop"
$RepoBase = "https://raw.githubusercontent.com/fightingPig/claude-statusline/main"

Write-Host "🚀 正在安装 Claude Code 状态栏 ..." -ForegroundColor Cyan

# 1. 确保 ~/.claude 目录存在
$ClaudeDir = "$env:USERPROFILE\.claude"
if (-not (Test-Path $ClaudeDir)) {
    New-Item -ItemType Directory -Path $ClaudeDir -Force | Out-Null
    Write-Host "📁 已创建 $ClaudeDir"
}

# 2. 下载 statusline.py
$ScriptPath = "$ClaudeDir\statusline.py"
Write-Host "⬇️  下载 statusline.py ..."
try {
    Invoke-WebRequest -Uri "$RepoBase/statusline.py" -OutFile $ScriptPath -UseBasicParsing
    Write-Host "✅ 已保存到 $ScriptPath"
}
catch {
    Write-Host "❌ 下载失败: $_" -ForegroundColor Red
    exit 1
}

# 3. 下载并执行配置合并脚本
$MergePath = "$env:TEMP\merge_settings.py"
Write-Host "⬇️  下载配置合并脚本 ..."
try {
    Invoke-WebRequest -Uri "$RepoBase/merge_settings.py" -OutFile $MergePath -UseBasicParsing
    python "$MergePath"
    Remove-Item $MergePath -Force
}
catch {
    Write-Host "❌ 配置合并失败: $_" -ForegroundColor Red
    exit 1
}

# 4. 验证
Write-Host ""
Write-Host "🎉 安装完成！" -ForegroundColor Green
Write-Host ""
Write-Host "📋 已在 settings.json 中添加以下配置:"
Write-Host "   - statusLine 命令 (调用 statusline.py)"
Write-Host ""
Write-Host "🔄 请重新启动 Claude Code 以生效"
Write-Host ""
Write-Host "📖 更多配置说明见: https://github.com/fightingPig/claude-statusline"
