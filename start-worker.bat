@echo off
chcp 65001 >nul
title AI集群Worker

echo ========================================
echo          AI集群Worker v1.0
echo ========================================
echo.

cd /d "%~dp0"

if "%1"=="" (
    echo 自动发现Master模式
    echo.
    python worker/cluster_worker.py
) else (
    echo 手动指定Master: %1
    echo.
    python worker/cluster_worker.py %1
)

if errorlevel 1 (
    echo.
    echo 启动失败，请确保已安装 Python
    echo.
    pause
)
