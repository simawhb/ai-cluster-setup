@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   开放防火墙端口 18082
echo ========================================
echo.
echo 请右键点击此文件，选择"以管理员身份运行"
echo.
pause

netsh advfirewall firewall add rule name="AI Workflow 18082" dir=in action=allow protocol=tcp localport=18082
netsh advfirewall firewall add rule name="AI Workflow 18081" dir=in action=allow protocol=tcp localport=18081
netsh advfirewall firewall add rule name="AI Cluster 8080" dir=in action=allow protocol=tcp localport=8080

echo.
echo 端口已开放！
echo   - 18082 (通用工作流)
echo   - 18081 (任务调度器)
echo   - 8080 (LLM API)
echo.
pause
