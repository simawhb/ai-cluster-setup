# 集群测试脚本
# 在 Master 上运行，测试所有节点和模型

param(
    [string]$MasterIP = "192.168.31.202",
    [string[]]$WorkerIPs = @("192.168.31.50", "192.168.31.110", "192.168.31.139", "192.168.31.216")
)

Write-Host "=== AI 集群测试 ===" -ForegroundColor Cyan
Write-Host ""

# 1. 测试 Worker 节点 RPC 连接
Write-Host "--- Worker RPC 连接测试 ---" -ForegroundColor Yellow
$allConnected = $true
foreach ($ip in $WorkerIPs) {
    $tcp = New-Object System.Net.Sockets.TcpClient
    try {
        $tcp.Connect($ip, 50051)
        Write-Host "  $ip :50051 - OK" -ForegroundColor Green
        $tcp.Close()
    } catch {
        Write-Host "  $ip :50051 - FAILED" -ForegroundColor Red
        $allConnected = $false
    }
}

if ($allConnected) {
    Write-Host "所有 Worker 节点连接正常" -ForegroundColor Green
} else {
    Write-Host "部分 Worker 节点连接失败" -ForegroundColor Red
}

# 2. 测试 llama-server
Write-Host ""
Write-Host "--- llama-server 测试 ---" -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "http://${MasterIP}:8080/health" -TimeoutSec 5
    Write-Host "  健康检查: $($health.status)" -ForegroundColor Green
} catch {
    Write-Host "  健康检查: FAILED - $($_.Exception.Message)" -ForegroundColor Red
}

# 3. 测试推理
Write-Host ""
Write-Host "--- 推理测试 ---" -ForegroundColor Yellow
try {
    $body = @{
        model = "qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf"
        messages = @(@{role="user"; content="Say hello in one word"})
        max_tokens = 10
    } | ConvertTo-Json -Depth 3

    $response = Invoke-RestMethod -Uri "http://${MasterIP}:8080/v1/chat/completions" -Method Post -Body $body -ContentType "application/json" -TimeoutSec 30
    $reply = $response.choices[0].message.content
    Write-Host "  推理结果: $reply" -ForegroundColor Green
    Write-Host "  Token 使用: $($response.usage.total_tokens)" -ForegroundColor Green
} catch {
    Write-Host "  推理测试: FAILED - $($_.Exception.Message)" -ForegroundColor Red
}

# 4. 测试集群管理器
Write-Host ""
Write-Host "--- 集群管理器测试 ---" -ForegroundColor Yellow
try {
    $status = Invoke-RestMethod -Uri "http://${MasterIP}:18080/api/status" -TimeoutSec 5
    Write-Host "  在线节点: $($status.online_count)/$($status.node_count)" -ForegroundColor Green
} catch {
    Write-Host "  集群管理器: FAILED - $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== 测试完成 ===" -ForegroundColor Cyan
