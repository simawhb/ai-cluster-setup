@echo off
chcp 65001 >nul
title AI集群管理器 - Master

echo ========================================
echo        AI集群管理器 v1.0
echo ========================================
echo.

cd /d "%~dp0"
python master/cluster_manager.py

if errorlevel 1 (
    echo.
    echo 启动失败，请确保已安装 Python
    echo.
    pause
)
