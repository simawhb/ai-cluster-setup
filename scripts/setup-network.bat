@echo off
title AI Cluster - Network Setup
color 0A
echo ========================================
echo   AI Cluster - Network Configuration
echo ========================================
echo.
echo Please enter the fixed IP for this machine:
echo   Master (GTX1060): 192.168.31.101
echo   Worker 1 (i7-2700K): 192.168.31.102
echo   Worker 2 (i5-13420H): 192.168.31.103
echo   Worker 3 (i5-3210M): 192.168.31.104
echo   Worker 4 (i5-5200U): 192.168.31.105
echo   Worker 5 (i3-3220): 192.168.31.106
echo.
set /p IP="Enter IP address (e.g. 192.168.31.102): "
if "%IP%"=="" (
    echo No IP entered, exiting.
    pause
    exit /b 1
)
echo.
echo Setting fixed IP to %IP% ...
netsh interface ip set address "以太网" static %IP% 255.255.255.0 192.168.31.1
netsh interface ip set dns "以太网" static 223.5.5.5
echo.
echo Opening firewall ports...
netsh advfirewall firewall add rule name="AI-Cluster-8080" dir=in action=allow protocol=TCP localport=8080
netsh advfirewall firewall add rule name="AI-Cluster-50051" dir=in action=allow protocol=TCP localport=50051
netsh advfirewall firewall add rule name="AI-Cluster-50052" dir=in action=allow protocol=TCP localport=50052
echo.
echo Testing gateway connectivity...
ping -n 2 192.168.31.1
echo.
echo Network setup complete!
echo This machine IP: %IP%
echo.
pause
