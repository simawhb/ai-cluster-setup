# Enable unencrypted traffic for HTTP WinRM
Set-Item WSMan:\localhost\Service\AllowUnencrypted -Value $true -Force
Write-Output "AllowUnencrypted set to true"

# Also set max timeout
Set-Item WSMan:\localhost\Service\MaxTimeoutms -Value 60000 -Force

$pass = ConvertTo-SecureString '2308788' -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential('ASUS', $pass)

try {
    $session = New-PSSession -ComputerName 192.168.31.111 -Credential $cred -Authentication Basic
    $result = Invoke-Command -Session $session -ScriptBlock {
        $h = hostname
        $u = whoami
        $ips = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notlike "*Loopback*" }).IPAddress -join ", "
        $admins = (net localgroup administrators 2>$null | Select-Object -Skip 4) -join ", "
        "HOSTNAME: $h"
        "USER: $u"
        "IPs: $ips"
        "ADMINS: $admins"
    }
    $result | ForEach-Object { Write-Output $_ }
    Remove-PSSession $session
} catch {
    Write-Output "ERROR: $($_.Exception.Message)"
}
