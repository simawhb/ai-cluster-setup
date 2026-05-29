@echo off
title AI Cluster - Worker Node Setup
color 0B
echo ========================================
echo   AI Cluster - Worker Node Setup
echo ========================================
echo.
echo This script will:
echo   1. Download llama.cpp (CPU version)
echo   2. Configure and start as RPC worker
echo.

set INSTALL_DIR=%~dp0llama.cpp
set LLAMA_VERSION=b9247
set /p MASTER_IP="Enter Master node IP (e.g. 192.168.31.101): "

if "%MASTER_IP%"=="" (
    echo No IP entered, exiting.
    pause
    exit /b 1
)

echo Master IP set to: %MASTER_IP%
echo.

echo [Step 1/3] Downloading llama.cpp (CPU version)...
echo   Version: %LLAMA_VERSION%
echo   This may take a few minutes...
echo.

if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

REM Download CPU version
curl -L -o "%INSTALL_DIR%\llama-cpu.zip" "https://github.com/ggml-org/llama.cpp/releases/download/%LLAMA_VERSION%/llama-%LLAMA_VERSION%-bin-win-x64.zip" 2>nul
if errorlevel 1 (
    echo   Trying with cert adjustment...
    curl -L --ssl-no-revoke -o "%INSTALL_DIR%\llama-cpu.zip" "https://github.com/ggml-org/llama.cpp/releases/download/%LLAMA_VERSION%/llama-%LLAMA_VERSION%-bin-win-x64.zip"
)
if errorlevel 1 (
    echo.
    echo   ERROR: Download failed!
    echo   Please download manually from:
    echo   https://github.com/ggml-org/llama.cpp/releases/tag/%LLAMA_VERSION%
    echo   Look for: llama-*-bin-win-x64.zip (CPU version)
    echo   Extract to: %INSTALL_DIR%
    echo.
    pause
    exit /b 1
)

echo   Extracting...
powershell -Command "Expand-Archive -Path '%INSTALL_DIR%\llama-cpu.zip' -DestinationPath '%INSTALL_DIR%' -Force"
del "%INSTALL_DIR%\llama-cpu.zip" 2>nul
echo   Done.

echo.
echo [Step 2/3] Creating startup scripts...
echo.

REM Worker startup script
(
echo @echo off
echo title AI Cluster - Worker Node \(Connecting to %MASTER_IP%\)
echo cd /d "%%~dp0llama.cpp"
echo.
echo echo Starting llama-rpc-server...
echo echo Connecting to Master at %MASTER_IP%:50051
echo echo.
echo llama-rpc-server.exe ^
echo   --host 0.0.0.0 ^
echo   --port 50051
echo.
echo pause
) > "%~dp0start-worker.bat"

echo   Created: start-worker.bat
echo.

echo [Step 3/3] Testing connection to master...
echo.
ping -n 2 %MASTER_IP%
echo.

echo ========================================
echo   Worker Node Setup Complete!
echo ========================================
echo.
echo   To start: run start-worker.bat
echo   This worker will connect to Master at %MASTER_IP%:50051
echo.
echo   Make sure Master is running BEFORE starting this worker!
echo.
pause
