# Worker 节点自动启动配置脚本
# 在每台 Worker 上以管理员身份运行

param(
    [string]$RpcServerPath = "C:\Users\whb\ai-cluster-setup\worker\bin\rpc-server.exe"
)

# 1. 确保 VC++ 运行库已安装
Write-Host "=== 检查 VC++ 运行库 ===" -ForegroundColor Cyan
$vcInstalled = Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64' -ErrorAction SilentlyContinue
if ($vcInstalled) {
    Write-Host "VC++ 运行库已安装: $($vcInstalled.Version)" -ForegroundColor Green
} else {
    Write-Host "VC++ 运行库未安装，正在下载安装..." -ForegroundColor Yellow
    Invoke-WebRequest -Uri "https://aka.ms/vs/17/release/vc_redist.x64.exe" -OutFile "$env:TEMP\vc_redist.x64.exe"
    Start-Process -FilePath "$env:TEMP\vc_redist.x64.exe" -ArgumentList "/install /quiet /norestart" -Wait
    Write-Host "VC++ 运行库安装完成" -ForegroundColor Green
}

# 2. 防火墙放行 50051 端口
Write-Host "=== 配置防火墙 ===" -ForegroundColor Cyan
$rule = Get-NetFirewallRule -DisplayName "RPC-Server" -ErrorAction SilentlyContinue
if ($rule) {
    Write-Host "防火墙规则已存在" -ForegroundColor Green
} else {
    New-NetFirewallRule -DisplayName "RPC-Server" -Direction Inbound -Protocol TCP -LocalPort 50051 -Action Allow
    Write-Host "防火墙规则已添加" -ForegroundColor Green
}

# 3. 创建开机自启计划任务
Write-Host "=== 配置开机自启 ===" -ForegroundColor Cyan
$taskName = "AI-Cluster-RPC-Server"
$taskExists = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue

if ($taskExists) {
    Write-Host "计划任务已存在，更新中..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

$action = New-ScheduledTaskAction -Execute $RpcServerPath -Argument "-H 0.0.0.0 -p 50051"
$trigger = New-ScheduledTaskTrigger -AtStartup
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description "AI集群 RPC Server 自动启动"

Write-Host "=== 配置完成 ===" -ForegroundColor Green
Write-Host "rpc-server 将在每次开机时自动启动" -ForegroundColor Green
Write-Host "端口: 50051" -ForegroundColor Green
