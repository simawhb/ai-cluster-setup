@echo off
chcp 65001 >nul
cd /d "%~dp0master"

echo.
echo ========================================
echo   通用AI工作流
echo ========================================
echo.
echo 可用场景:
echo   query     - 查询调研
echo   code      - 编程开发
echo   novel     - 小说创作
echo   translate - 翻译润色
echo   marketing - 营销文案
echo   law       - 法律合规
echo   full      - 完整工作流
echo.
echo 用法: run-workflow.bat "主题" 场景
echo 示例: run-workflow.bat "量子计算进展" query
echo.

if "%~1"=="" (
    echo 启动Web UI...
    start http://localhost:18082
    python universal_ui.py
) else (
    python universal_crew.py "%~1" --scene %~2
)
