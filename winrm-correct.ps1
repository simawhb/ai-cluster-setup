$pass = ConvertTo-SecureString '2308788' -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential('ASUS', $pass)

try {
    $session = New-PSSession -ComputerName 192.168.31.110 -Credential $cred -Authentication Basic -ErrorAction Stop
    $result = Invoke-Command -Session $session -ScriptBlock {
        $h = hostname
        $u = whoami
        $ips = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notlike "*Loopback*" }).IPAddress -join ", "
        "=== SUCCESS ==="
        "HOSTNAME: $h"
        "USER: $u"
        "IPs: $ips"
    }
    $result | ForEach-Object { Write-Output $_ }
    Remove-PSSession $session
} catch {
    Write-Output "Basic FAILED: $($_.Exception.Message)"
    try {
        $session2 = New-PSSession -ComputerName 192.168.31.110 -Credential $cred -Authentication Negotiate -ErrorAction Stop
        $result2 = Invoke-Command -Session $session2 -ScriptBlock { hostname; whoami; (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notlike "*Loopback*" }).IPAddress -join ", " }
        $result2 | ForEach-Object { Write-Output $_ }
        Remove-PSSession $session2
    } catch {
        Write-Output "Negotiate FAILED: $($_.Exception.Message)"
    }
}
