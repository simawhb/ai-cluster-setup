$pass = ConvertTo-SecureString '2308788' -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential('ASUS', $pass)

try {
    $session = New-PSSession -ComputerName 192.168.31.111 -Credential $cred -Authentication Basic
    Invoke-Command -Session $session -ScriptBlock {
        Write-Output "=== HOSTNAME ==="
        hostname
        Write-Output "=== WHOAMI ==="
        whoami
        Write-Output "=== ADMINS ==="
        net localgroup administrators
        Write-Output "=== WINRM CONFIG ==="
        winrm get winrm/config/service/auth
        Write-Output "=== LOCAL ACCOUNT TOKEN FILTER ==="
        Get-ItemProperty HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System -Name LocalAccountTokenFilterPolicy -ErrorAction SilentlyContinue
    }
    Remove-PSSession $session
} catch {
    Write-Output "ERROR: $($_.Exception.Message)"
    Write-Output ""
    Write-Output "Trying alternative with .\\ prefix..."
    $cred2 = New-Object System.Management.Automation.PSCredential(".\ASUS", $pass)
    try {
        $session2 = New-PSSession -ComputerName 192.168.31.111 -Credential $cred2 -Authentication Basic
        Invoke-Command -Session $session2 -ScriptBlock { hostname; whoami }
        Remove-PSSession $session2
    } catch {
        Write-Output "ERROR2: $($_.Exception.Message)"
    }
}
