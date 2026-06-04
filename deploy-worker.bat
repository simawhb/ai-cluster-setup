@echo off
title AI Cluster Worker - Auto Deploy

echo ========================================
echo   AI Cluster Worker - Auto Deploy
echo   Master: 192.168.31.202
echo ========================================
echo.

set MASTER_IP=192.168.31.202
set MASTER_PORT=9999
set BASE_DIR=C:\Users\%USERNAME%\ai-cluster-setup
set BIN_DIR=%BASE_DIR%\bin
set WORKER_DIR=%BASE_DIR%\worker

mkdir "%BIN_DIR%" 2>nul
mkdir "%WORKER_DIR%" 2>nul

echo [1/5] Creating directories...
echo        Done.

echo [2/5] Downloading rpc-server.exe...
curl -L -o "%BIN_DIR%\rpc-server.exe" "http://%MASTER_IP%:%MASTER_PORT%/master/bin/rpc-server.exe"
if not exist "%BIN_DIR%\rpc-server.exe" (
    echo [ERROR] Failed to download rpc-server.exe
    pause
    exit /b 1
)
echo        OK.

echo [3/5] Downloading DLL dependencies...
for %%F in (ggml-base.dll ggml-rpc.dll ggml.dll ggml-cpu-ivybridge.dll ggml-cpu-sse42.dll ggml-cpu-x64.dll ggml-cpu-haswell.dll ggml-cpu-skylakex.dll ggml-cpu-alderlake.dll ggml-cpu-zen4.dll libomp140.x86_64.dll) do (
    if not exist "%BIN_DIR%\%%F" (
        curl -sL -o "%BIN_DIR%\%%F" "http://%MASTER_IP%:%MASTER_PORT%/master/bin/%%F"
        if exist "%BIN_DIR%\%%F" (
            echo        %%F OK
        ) else (
            echo        %%F skipped
        )
    ) else (
        echo        %%F exists
    )
)
echo        Done.

echo [4/5] Downloading cluster_worker.py...
curl -L -o "%WORKER_DIR%\cluster_worker.py" "http://%MASTER_IP%:%MASTER_PORT%/worker/cluster_worker.py"
if not exist "%WORKER_DIR%\cluster_worker.py" (
    echo [ERROR] Failed to download cluster_worker.py
    pause
    exit /b 1
)
echo        OK.

echo.
echo [5/5] Starting Worker...
echo.

echo Starting RPC server on port 50051...
start "RPC-Server" cmd /k "%BIN_DIR%\rpc-server.exe -H 0.0.0.0 -p 50051 -c"

timeout /t 3 /nobreak >nul

echo Starting Worker heartbeat, connecting to %MASTER_IP%...
start "Cluster-Worker" cmd /k "python %WORKER_DIR%\cluster_worker.py %MASTER_IP%"

echo.
echo ========================================
echo   Deploy complete!
echo   RPC Server:  port 50051
echo   Worker:      connecting to %MASTER_IP%
echo.
echo   Two windows opened, keep them running.
echo ========================================
echo.
pause
