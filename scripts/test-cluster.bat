@echo off
title AI Cluster - Test
color 0A
echo ========================================
echo   AI Cluster - Connection Test
echo ========================================
echo.
echo Testing connectivity to all cluster nodes...
echo.

setlocal enabledelayedexpansion
set IPs=192.168.31.101 192.168.31.102 192.168.31.103 192.168.31.104 192.168.31.105 192.168.31.106
set NAMES=Master\(GTX1060\) Worker1\(i7-2700K\) Worker2\(i5-13420H\) Worker3\(i5-3210M\) Worker4\(i5-5200U\) Worker5\(i3-3220\)

set i=0
for %%i in (%IPs%) do (
    set /a i+=1
    echo [!i!] %%i - Testing ping...
    ping -n 1 -w 1000 %%i >nul 2>&1
    if errorlevel 1 (
        echo     OFFLINE
    ) else (
        echo     ONLINE
    )
)

echo.
echo ========================================
echo   API Test (if Master is running)
echo ========================================
echo.
echo Trying to call Master API at 192.168.31.101:8080...
echo.

curl -s http://192.168.31.101:8080/health 2>nul
if errorlevel 1 (
    echo   API not reachable. Make sure Master node is running.
) else (
    echo.
    echo   API is working!
)

echo.
echo ========================================
echo   Quick Chat Test
echo ========================================
echo.
echo Sending test request to Master...
echo.

curl -s http://192.168.31.101:8080/v1/chat/completions ^
  -H "Content-Type: application/json" ^
  -d "{\"model\":\"qwen2.5-7b\",\"messages\":[{\"role\":\"user\",\"content\":\"Say hello in one word\"}],\"max_tokens\":10}" 2>nul

if errorlevel 1 (
    echo   Chat test failed. Check Master node.
) else (
    echo.
    echo   Chat test completed!
)

echo.
pause
