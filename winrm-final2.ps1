$pass = ConvertTo-SecureString 'sim@2026' -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential('ASUS', $pass)

try {
    $session = New-PSSession -ComputerName 192.168.31.110 -Credential $cred -Authentication Basic -ErrorAction Stop
    $result = Invoke-Command -Session $session -ScriptBlock {
        "=== WINRM CONNECTION SUCCESS ==="
        "HOSTNAME: $(hostname)"
        "USER: $(whoami)"
        "IPs: $((Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notlike '*Loopback*' }).IPAddress -join ', ')"
    }
    $result | ForEach-Object { Write-Output $_ }
    Remove-PSSession $session
} catch {
    Write-Output "FAILED: $($_.Exception.Message)"
}
