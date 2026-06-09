# Server酱通知脚本
# SendKey 从环境变量读取，避免硬编码
param(
    [string]$Title = "AI Cluster Notification",
    [string]$Desp = "No content",
    [string]$SendKey = $env:SERVERCHAN_SENDKEY
)

if (-not $SendKey) {
    Write-Host "错误: 未设置 SERVERCHAN_SENDKEY 环境变量" -ForegroundColor Red
    Write-Host "设置方法: [Environment]::SetEnvironmentVariable('SERVERCHAN_SENDKEY', '你的Key', 'User')" -ForegroundColor Yellow
    exit 1
}

$url = "https://sctapi.ftqq.com/$SendKey.send"
$body = "title=$Title&desp=$Desp"

try {
    $response = Invoke-RestMethod -Uri $url -Method Post -Body $body -ContentType "application/x-www-form-urlencoded; charset=utf-8"
    Write-Host "Notification sent successfully: $($response | ConvertTo-Json -Compress)"
} catch {
    Write-Host "Notification failed: $($_.Exception.Message)"
}
