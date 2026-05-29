@echo off
title AI Cluster - Master Node Setup
color 0B
echo ========================================
echo   AI Cluster - Master Node Setup
echo   (For DESKTOP-TFINHN6 / GTX 1060)
echo ========================================
echo.
echo This script will:
echo   1. Download llama.cpp (CUDA version)
echo   2. Download Qwen2.5-7B model
echo   3. Configure and start the master node
echo.

set INSTALL_DIR=%~dp0llama.cpp
set MODEL_DIR=%~dp0models
set LLAMA_VERSION=b9247

echo [Step 1/4] Creating directories...
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
if not exist "%MODEL_DIR%" mkdir "%MODEL_DIR%"
echo   Done.

echo.
echo [Step 2/4] Downloading llama.cpp (CUDA)...
echo   Version: %LLAMA_VERSION%
echo   This may take a few minutes...
echo.

REM Try to download with curl (built into Windows 10+)
curl -L -o "%INSTALL_DIR%\llama-cuda.zip" "https://github.com/ggml-org/llama.cpp/releases/download/%LLAMA_VERSION%/llama-%LLAMA_VERSION%-bin-win-cuda12.4-x64.zip" 2>nul
if errorlevel 1 (
    echo   curl failed, trying with cert adjustment...
    curl -L --ssl-no-revoke -o "%INSTALL_DIR%\llama-cuda.zip" "https://github.com/ggml-org/llama.cpp/releases/download/%LLAMA_VERSION%/llama-%LLAMA_VERSION%-bin-win-cuda12.4-x64.zip"
)
if errorlevel 1 (
    echo.
    echo   ERROR: Download failed!
    echo   Please download manually from:
    echo   https://github.com/ggml-org/llama.cpp/releases/tag/%LLAMA_VERSION%
    echo   Look for: llama-*-bin-win-cuda12.4-x64.zip
    echo   Extract to: %INSTALL_DIR%
    echo.
    pause
    exit /b 1
)

echo   Extracting...
powershell -Command "Expand-Archive -Path '%INSTALL_DIR%\llama-cuda.zip' -DestinationPath '%INSTALL_DIR%' -Force"
del "%INSTALL_DIR%\llama-cuda.zip" 2>nul
echo   Done.

echo.
echo [Step 3/4] Downloading Qwen2.5-7B-Instruct Q4_K_M model...
echo   File size: ~4.5 GB, this will take a while...
echo.

REM Download from Hugging Face
curl -L -o "%MODEL_DIR%\qwen2.5-7b-instruct-q4_k_m.gguf" "https://huggingface.co/unsloth/Qwen2.5-7B-Instruct-GGUF/resolve/main/Qwen2.5-7B-Instruct-Q4_K_M.gguf" 2>nul
if errorlevel 1 (
    echo.
    echo   Download failed. Trying alternative source...
    curl -L --ssl-no-revoke -o "%MODEL_DIR%\qwen2.5-7b-instruct-q4_k_m.gguf" "https://huggingface.co/unsloth/Qwen2.5-7B-Instruct-GGUF/resolve/main/Qwen2.5-7B-Instruct-Q4_K_M.gguf"
)
if errorlevel 1 (
    echo.
    echo   ERROR: Model download failed!
    echo   Please download manually from:
    echo   https://huggingface.co/unsloth/Qwen2.5-7B-Instruct-GGUF
    echo   File: Qwen2.5-7B-Instruct-Q4_K_M.gguf
    echo   Save to: %MODEL_DIR%
    echo.
    pause
    exit /b 1
)
echo   Done.

echo.
echo [Step 4/4] Creating startup scripts...
echo.

REM Create start script for master
(
echo @echo off
echo title AI Cluster - Master Node \(GTX 1060 + RPC\)
echo cd /d "%%~dp0llama.cpp"
echo.
echo echo Starting llama-server with CUDA + RPC support...
echo echo API will be available at http://localhost:8080
echo echo.
echo llama-server.exe ^
echo   -m "%MODEL_DIR%\qwen2.5-7b-instruct-q4_k_m.gguf" ^
echo   --host 0.0.0.0 ^
echo   --port 8080 ^
echo   --n-gpu-layers 99 ^
echo   --ctx-size 4096 ^
echo   --threads 4 ^
echo   --rpc 0.0.0.0:50051
echo.
echo pause
) > "%~dp0start-master.bat"

REM Create start script for master WITHOUT RPC (solo mode)
(
echo @echo off
echo title AI Cluster - Master Node \(Solo GTX 1060\)
echo cd /d "%%~dp0llama.cpp"
echo.
echo echo Starting llama-server with CUDA only (no workers)...
echo echo API will be available at http://localhost:8080
echo echo.
echo llama-server.exe ^
echo   -m "%MODEL_DIR%\qwen2.5-7b-instruct-q4_k_m.gguf" ^
echo   --host 0.0.0.0 ^
echo   --port 8080 ^
echo   --n-gpu-layers 99 ^
echo   --ctx-size 4096 ^
echo   --threads 4
echo.
echo pause
) > "%~dp0start-master-solo.bat"

echo   Created: start-master.bat (with RPC workers)
echo   Created: start-master-solo.bat (standalone mode)
echo.

echo ========================================
echo   Master Node Setup Complete!
echo ========================================
echo.
echo   To start: run start-master.bat
echo   API URL:  http://localhost:8080
echo   RPC Port: 50051 (for workers to connect)
echo.
echo   Next: set up worker nodes on other machines
echo.
pause
