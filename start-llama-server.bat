@echo off
chcp 65001 >nul
title llama-server - Local GPU Mode
cd /d "%~dp0master"

echo ========================================
echo   llama-server (Local GPU Mode)
echo   Port: 8080
echo   Model: DeepSeek-R1-Distill-Qwen-7B-Q4_K_M.gguf
echo ========================================
echo.

bin\llama-server.exe -m D:\AI-Models\DeepSeek-R1-Distill-Qwen-7B-Q4_K_M.gguf --host 0.0.0.0 --port 8080 -ngl 99 --parallel 2 --no-warmup

echo.
echo llama-server exited.
pause
