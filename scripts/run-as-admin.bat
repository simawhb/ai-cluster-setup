@echo off
echo ============================================
echo   This will set this machine to:
echo   IP: 192.168.31.102 (Worker 1 - i7-2700K)
echo   Gateway: 192.168.31.1
echo   DNS: 223.5.5.5 (AliDNS)
echo ============================================
echo.
echo Press any key to apply...
pause >nul

echo.
echo [1/3] Setting static IP...
netsh interface ip set address "以太网" static 192.168.31.102 255.255.255.0 192.168.31.1
if errorlevel 1 (
    echo   Trying "Ethernet" adapter name...
    netsh interface ip set address "Ethernet" static 192.168.31.102 255.255.255.0 192.168.31.1
)

echo [2/3] Setting DNS...
netsh interface ip set dns "以太网" static 223.5.5.5
if errorlevel 1 (
    netsh interface ip set dns "Ethernet" static 223.5.5.5
)

echo [3/3] Opening firewall ports...
netsh advfirewall firewall add rule name="AI-Cluster-8080" dir=in action=allow protocol=TCP localport=8080
netsh advfirewall firewall add rule name="AI-Cluster-50051" dir=in action=allow protocol=TCP localport=50051
netsh advfirewall firewall add rule name="AI-Cluster-50052" dir=in action=allow protocol=TCP localport=50052

echo.
echo ============================================
echo   Verifying...
echo ============================================
ipconfig | findstr /i "IPv4"
echo.
ping -n 1 192.168.31.1 | findstr /i "TTL"
echo.
echo Done! Press any key to exit.
pause >nul
