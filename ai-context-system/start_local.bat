@echo off
chcp 65001 > nul
cls

echo ╔════════════════════════════════════════════════════════╗
echo ║     AI Context System - 本地部署启动脚本               ║
echo ║     Local Deployment Startup Script                    ║
echo ╚════════════════════════════════════════════════════════╝
echo.

set PYTHON=C:\Users\User\AppData\Local\Microsoft\WindowsApps\python3.13.exe
set PROJECT_ROOT=D:\project\mcp-tools\ai-context-system
set BACKEND=%PROJECT_ROOT%\backend
set CHROMA_DATA=%PROJECT_ROOT%\chroma_data
set GRAPH_DATA=%PROJECT_ROOT%\graph_data

echo [步骤 1/4] 检查Python环境...
%PYTHON% --version
if errorlevel 1 (
    echo ❌ Python未安装或路径错误！
    pause
    exit /b 1
)
echo ✅ Python环境正常
echo.

echo [步骤 2/4] 创建数据目录...
if not exist "%CHROMA_DATA%" mkdir "%CHROMA_DATA%"
if not exist "%GRAPH_DATA%" mkdir "%GRAPH_DATA%"
echo ✅ 数据目录已创建
echo.

echo [步骤 3/4] 启动ChromaDB服务...
echo    地址: http://localhost:8001
echo    数据: %CHROMA_DATA%
start "ChromaDB服务" %PYTHON% -m chromadb.cli.cli run --host localhost --port 8001 --path "%CHROMA_DATA%"
timeout /t 3 /nobreak > nul
echo ✅ ChromaDB服务已启动
echo.

echo [步骤 4/4] 启动后端API服务...
echo    地址: http://127.0.0.1:8000
echo    文档: http://127.0.0.1:8000/docs
echo.
cd /d "%BACKEND%"
%PYTHON% run_dev.py

pause
