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

# 4. Deepseek 余额查询配置
Write-Host ""
$SettingsPath = "$env:USERPROFILE\.claude\settings.json"
$DeepseekAuto = $false
if (Test-Path $SettingsPath) {
    try {
        $settings = Get-Content $SettingsPath -Raw | ConvertFrom-Json
        $baseUrl = $settings.env.ANTHROPIC_BASE_URL
        if ($baseUrl -like "https://api.deepseek.com*") {
            $DeepseekAuto = $true
            if (-not $settings.env.DEEPSEEK_API_KEY -and $settings.env.ANTHROPIC_AUTH_TOKEN) {
                $settings | Add-Member -NotePropertyName "env" -NotePropertyValue $settings.env -Force
                $settings.env | Add-Member -NotePropertyName "DEEPSEEK_API_KEY" -NotePropertyValue $settings.env.ANTHROPIC_AUTH_TOKEN -Force
                $settings | ConvertTo-Json -Depth 10 | Set-Content $SettingsPath -Encoding utf8
            }
            Write-Host "✅ 检测到 Deepseek 官方 API，已自动启用余额查询" -ForegroundColor Green
        }
    }
    catch {
        # 忽略错误
    }
}

if (-not $DeepseekAuto) {
    Write-Host "❓ 当前非 Deepseek 官方 API，仅支持查询 Deepseek 官方账户余额。" -ForegroundColor Yellow
    Write-Host "   如果你是官方账户转接，需要额外提供官方 key，是否启用余额查询？(y/n)" -ForegroundColor Yellow
    $Confirm = Read-Host "  "
    if ($Confirm -eq "y" -or $Confirm -eq "Y") {
        $DsKey = Read-Host "  请输入 Deepseek API Key"
        if ($DsKey) {
            try {
                $settings = Get-Content $SettingsPath -Raw | ConvertFrom-Json
                if (-not $settings.env) { $settings | Add-Member -NotePropertyName "env" -NotePropertyValue @{} }
                $settings.env | Add-Member -NotePropertyName "DEEPSEEK_API_KEY" -NotePropertyValue $DsKey -Force
                $settings | ConvertTo-Json -Depth 10 | Set-Content $SettingsPath -Encoding utf8
                Write-Host "✅ Deepseek API Key 已保存" -ForegroundColor Green
            }
            catch {
                Write-Host "❌ 保存失败: $_" -ForegroundColor Red
            }
        }
    }
}

# 5. 验证
Write-Host ""
Write-Host "🎉 安装完成！" -ForegroundColor Green
Write-Host ""
Write-Host "📋 已在 settings.json 中添加以下配置:"
Write-Host "   - statusLine 命令 (调用 statusline.py)"
if ($DeepseekAuto -or $DsKey) {
    Write-Host "   - DEEPSEEK_API_KEY（用于余额查询）"
}
Write-Host ""
Write-Host "🔄 请重新启动 Claude Code 以生效"
Write-Host ""
Write-Host "📖 更多配置说明见: https://github.com/fightingPig/claude-statusline"
