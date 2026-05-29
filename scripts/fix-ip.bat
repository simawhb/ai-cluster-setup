@echo off
echo ============================================
echo   Setting static IP to 192.168.31.102
echo ============================================
echo.

netsh interface ip set address "Ethernet" static 192.168.31.102 255.255.255.0 192.168.31.1
if errorlevel 1 (
    echo Trying Chinese adapter name...
    netsh interface ip set address "YiTaiWang" static 192.168.31.102 255.255.255.0 192.168.31.1
)

netsh interface ip set dns "Ethernet" static 223.5.5.5
if errorlevel 1 (
    netsh interface ip set dns "YiTaiWang" static 223.5.5.5
)

echo.
echo Verify:
ipconfig | findstr "IPv4"
echo.
pause
