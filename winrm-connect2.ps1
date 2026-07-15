# Restart WinRM to pick up AllowUnencrypted
Restart-Service winrm -Force
Start-Sleep -Seconds 2

# Verify setting
$val = Get-Item WSMan:\localhost\Service\AllowUnencrypted
Write-Output "AllowUnencrypted = $($val.Value)"

$pass = ConvertTo-SecureString '2308788' -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential('ASUS', $pass)

# Create session options to skip cert checks
$so = New-PSSessionOption -SkipCACheck -SkipCNCheck -SkipRevocationCheck

try {
    $session = New-PSSession -ComputerName 192.168.31.111 -Credential $cred -Authentication Basic -SessionOption $so
    $result = Invoke-Command -Session $session -ScriptBlock {
        $h = hostname
        $u = whoami
        $ips = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notlike "*Loopback*" }).IPAddress -join ", "
        "HOSTNAME: $h"
        "USER: $u"
        "IPs: $ips"
    }
    $result | ForEach-Object { Write-Output $_ }
    Remove-PSSession $session
} catch {
    Write-Output "ERROR: $($_.Exception.Message)"
    
    # Also try with Negotiate
    Write-Output ""
    Write-Output "Trying Negotiate auth..."
    try {
        $session2 = New-PSSession -ComputerName 192.168.31.111 -Credential $cred -Authentication Negotiate -SessionOption $so
        $result2 = Invoke-Command -Session $session2 -ScriptBlock { hostname; whoami }
        $result2 | ForEach-Object { Write-Output $_ }
        Remove-PSSession $session2
    } catch {
        Write-Output "ERROR Negotiate: $($_.Exception.Message)"
    }
}
