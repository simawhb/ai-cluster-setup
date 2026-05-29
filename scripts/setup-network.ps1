# AI Cluster - Network Setup Script
# Run as Administrator!
# This script sets a fixed IP and opens firewall ports

param(
    [string]$IPAddress = "192.168.31.101",
    [string]$SubnetMask = "255.255.255.0",
    [string]$Gateway = "192.168.31.1",
    [string]$DNS = "223.5.5.5"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  AI Cluster - Network Configuration" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check admin
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "ERROR: Please run as Administrator!" -ForegroundColor Red
    Write-Host "Right-click PowerShell -> Run as Administrator" -ForegroundColor Yellow
    pause
    exit 1
}

Write-Host "[1/4] Setting fixed IP address..." -ForegroundColor Yellow
$adapter = Get-NetAdapter | Where-Object {$_.Status -eq "Up"} | Select-Object -First 1
if (-not $adapter) {
    Write-Host "ERROR: No active network adapter found!" -ForegroundColor Red
    pause
    exit 1
}
Write-Host "  Using adapter: $($adapter.Name)" -ForegroundColor Gray

New-NetIPAddress -InterfaceIndex $adapter.ifIndex -IPAddress $IPAddress -SubnetMask $SubnetMask -DefaultGateway $Gateway -ErrorAction SilentlyContinue
Set-DnsClientServerAddress -InterfaceIndex $adapter.ifIndex -ServerAddresses $DNS -ErrorAction SilentlyContinue
Write-Host "  IP set to: $IPAddress" -ForegroundColor Green

Write-Host "[2/4] Opening firewall ports..." -ForegroundColor Yellow
# Port 8080 for llama-server API
netsh advfirewall firewall add rule name="AI-Cluster-8080" dir=in action=allow protocol=TCP localport=8080 2>$null
# Port 50051 for RPC communication
netsh advfirewall firewall add rule name="AI-Cluster-50051" dir=in action=allow protocol=TCP localport=50051 2>$null
# Port 50052 for additional RPC
netsh advfirewall firewall add rule name="AI-Cluster-50052" dir=in action=allow protocol=TCP localport=50052 2>$null
# ICMP for ping
netsh advfirewall firewall set rule name="File and Printer Sharing (Echo Request - ICMPv4-In)" new enable=yes 2>$null
Write-Host "  Ports 8080, 50051, 50052 opened" -ForegroundColor Green
Write-Host "  ICMP (ping) enabled" -ForegroundColor Green

Write-Host "[3/4] Testing connectivity..." -ForegroundColor Yellow
$pingResult = Test-Connection -ComputerName $Gateway -Count 2 -Quiet
if ($pingResult) {
    Write-Host "  Gateway ($Gateway) reachable" -ForegroundColor Green
} else {
    Write-Host "  WARNING: Gateway ($Gateway) not reachable!" -ForegroundColor Red
}

Write-Host "[4/4] Done!" -ForegroundColor Green
Write-Host ""
Write-Host "Current network config:" -ForegroundColor Cyan
ipconfig | Select-String -Pattern "IPv4|Subnet|Gateway" | ForEach-Object { Write-Host "  $($_.Line.Trim())" }
Write-Host ""
Write-Host "Please note this IP address for other machines to connect." -ForegroundColor Yellow
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
