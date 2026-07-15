# 测试所有 Worker 节点的 WinRM 连接和 rpc-server 状态
# 用法: powershell -ExecutionPolicy Bypass -File scripts\test-all-workers.ps1

$pass = ConvertTo-SecureString '2308788' -AsPlainText -Force

$workers = @(
    @{ Name = "Worker 2"; IP = "192.168.31.50"; User = "ASUS" },
    @{ Name = "Worker 3"; IP = "192.168.31.139"; User = "14712" },
    @{ Name = "Worker 4"; IP = "192.168.31.216"; User = "whb" }
)

foreach ($w in $workers) {
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "$($w.Name) - $($w.IP)" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan

    $cred = New-Object System.Management.Automation.PSCredential($w.User, $pass)

    try {
        $session = New-PSSession -ComputerName $w.IP -Credential $cred -Authentication Basic -ErrorAction Stop

        $result = Invoke-Command -Session $session -ScriptBlock {
            $hostname = hostname
            $rpcProcess = tasklist | findstr rpc-server
            $clusterWorker = tasklist | findstr python
            $firewallRule = netsh advfirewall firewall show rule name="RPC-Server" 2>$null | findstr "Rule Name"

            Write-Output "HOSTNAME: $hostname"
            Write-Output ""
            Write-Output "=== RPC Server 进程 ==="
            if ($rpcProcess) {
                Write-Output $rpcProcess
            } else {
                Write-Output "未运行"
            }
            Write-Output ""
            Write-Output "=== Python 进程 (cluster_worker) ==="
            if ($clusterWorker) {
                Write-Output $clusterWorker
            } else {
                Write-Output "未运行"
            }
            Write-Output ""
            Write-Output "=== 防火墙规则 ==="
            if ($firewallRule) {
                Write-Output "已配置"
            } else {
                Write-Output "未配置"
            }
        }

        Write-Host $result -ForegroundColor Green
        Remove-PSSession $session
    } catch {
        Write-Host "连接失败: $($_.Exception.Message)" -ForegroundColor Red
    }
}
