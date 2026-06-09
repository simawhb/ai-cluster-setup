@echo off
chcp 65001 >nul
title llama-server - Distributed Mode
cd /d "%~dp0master"

echo ========================================
echo   llama-server (Distributed Mode)
echo   Port: 8080
echo   Model: gemma-4-12b-it-Q4_K_M.gguf
echo   Workers: 192.168.31.110, 50, 139, 216
echo ========================================
echo.

bin\llama-server.exe -m D:\AI-Models\gemma-4-12b-it-Q4_K_M.gguf --host 0.0.0.0 --port 8080 --rpc 192.168.31.110:50051,192.168.31.50:50051,192.168.31.139:50051,192.168.31.216:50051

echo.
echo llama-server exited.
pause
