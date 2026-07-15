@echo off
chcp 65001 >nul
title AI集群Worker - Auto Start
cd /d "%~dp0"

echo ========================================
echo   AI集群Worker - 自动启动
echo   主机名: %COMPUTERNAME%
echo ========================================
echo.

echo [1/3] 启动 RPC Server...
start /B bin\rpc-server.exe -H 0.0.0.0 -p 50051
timeout /t 3 /nobreak >nul

echo [2/3] 启动 Cluster Worker（自动发现Master）...
python cluster_worker.py

echo [3/3] Worker 已停止
pause
