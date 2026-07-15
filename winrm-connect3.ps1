$ErrorActionPreference = 'Continue'

# Force the WinRM client config via cmd
& 'C:\Windows\System32\winrm.cmd' set winrm/config/client '@{AllowUnencrypted="true"}' 2>&1 | Out-Null

# Force via registry again
Set-ItemProperty -Path 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\WSMAN\Client' -Name 'AllowUnencrypted' -Value 1 -Type DWord -Force
Set-ItemProperty -Path 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\WSMAN\Client' -Name 'trusted_hosts' -Value '192.168.31.*' -Type String -Force

# Restart WinRM
Restart-Service winrm -Force
Start-Sleep -Seconds 3

Write-Output "=== Current Config ==="
cmd /c 'C:\Windows\System32\winrm.cmd' get winrm/config/client 2>&1
Write-Output "=== End Config ==="

$pass = ConvertTo-SecureString '2308788' -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential('ASUS', $pass)

# Try with explicit option to bypass network check
$so = New-PSSessionOption -OperationTimeout 30000 -OpenTimeout 30000

# Try multiple auth methods
foreach ($auth in @('Basic', 'Negotiate', 'Kerberos', 'Default')) {
    Write-Output "Trying $auth..."
    try {
        $session = New-PSSession -ComputerName 192.168.31.111 -Credential $cred -Authentication $auth -SessionOption $so -ErrorAction Stop
        Write-Output "SUCCESS with $auth!"
        $result = Invoke-Command -Session $session -ScriptBlock { hostname; whoami }
        $result | ForEach-Object { Write-Output $_ }
        Remove-PSSession $session
        break
    } catch {
        Write-Output "  Failed: $($_.Exception.InnerException.Message)"
    }
}
