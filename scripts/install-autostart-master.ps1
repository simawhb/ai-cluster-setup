# Master 节点自动启动配置脚本
# 在 Master 上以管理员身份运行

param(
    [string]$BasePath = "C:\Users\whb\ai-cluster-setup"
)

# 1. 配置 cluster_manager 自动启动
Write-Host "=== 配置 cluster_manager 自动启动 ===" -ForegroundColor Cyan
$taskName1 = "AI-Cluster-Manager"
$taskExists1 = Get-ScheduledTask -TaskName $taskName1 -ErrorAction SilentlyContinue

if ($taskExists1) {
    Unregister-ScheduledTask -TaskName $taskName1 -Confirm:$false
}

$action1 = New-ScheduledTaskAction -Execute "python" -Argument "$BasePath\master\cluster_manager.py" -WorkingDirectory "$BasePath\master"
$trigger1 = New-ScheduledTaskTrigger -AtStartup
$principal1 = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
$settings1 = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Register-ScheduledTask -TaskName $taskName1 -Action $action1 -Trigger $trigger1 -Principal $principal1 -Settings $settings1 -Description "AI集群管理器自动启动"
Write-Host "cluster_manager 已配置" -ForegroundColor Green

# 2. 配置 llama-server 自动启动
Write-Host "=== 配置 llama-server 自动启动 ===" -ForegroundColor Cyan
$taskName2 = "AI-Cluster-Llama-Server"
$taskExists2 = Get-ScheduledTask -TaskName $taskName2 -ErrorAction SilentlyContinue

if ($taskExists2) {
    Unregister-ScheduledTask -TaskName $taskName2 -Confirm:$false
}

$llamaArgs = "-m D:\AI-Models\gemma-4-12b-it-Q4_K_M.gguf --host 0.0.0.0 --port 8080 -ngl 99 --parallel 2 --no-warmup"
$action2 = New-ScheduledTaskAction -Execute "$BasePath\master\bin\llama-server.exe" -Argument $llamaArgs -WorkingDirectory "$BasePath\master"
$trigger2 = New-ScheduledTaskTrigger -AtStartup
$principal2 = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
$settings2 = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Register-ScheduledTask -TaskName $taskName2 -Action $action2 -Trigger $trigger2 -Principal $principal2 -Settings $settings2 -Description "AI集群 llama-server 自动启动"
Write-Host "llama-server 已配置" -ForegroundColor Green

Write-Host "=== Master 自动启动配置完成 ===" -ForegroundColor Green
