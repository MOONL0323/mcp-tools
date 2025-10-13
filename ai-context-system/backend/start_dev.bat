@echo off
REM AI Context System Backend 开发环境启动脚本

echo ========================================
echo AI Context System Backend
echo ========================================
echo.

REM 切换到backend目录
cd /d %~dp0

echo [1/3] 检查Python环境...
C:\Users\User\AppData\Local\Microsoft\WindowsApps\python3.13.exe --version
if errorlevel 1 (
    echo 错误: Python未安装或无法访问
    pause
    exit /b 1
)

echo [2/3] 启动FastAPI服务...
echo 服务地址: http://localhost:8000
echo API文档: http://localhost:8000/docs
echo.

echo [3/3] 运行中...
C:\Users\User\AppData\Local\Microsoft\WindowsApps\python3.13.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause
