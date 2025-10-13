@echo off
echo =================================
echo AI Context System Backend 启动
echo =================================

echo 检查当前目录...
echo 当前目录: %CD%
cd /d "d:\project\mcp-tools\ai-context-system\backend"
echo 切换到目录: %CD%

echo.
echo 检查Python环境...
python --version
if %errorlevel% neq 0 (
    echo 错误: Python 未安装或不在PATH中
    pause
    exit /b 1
)

echo.
echo 检查项目文件...
if not exist "app\main.py" (
    echo 错误: 找不到app\main.py文件
    pause
    exit /b 1
)

echo.
echo 启动后端服务...
echo 访问地址: http://localhost:8000
echo API文档: http://localhost:8000/docs
echo.

set PYTHONPATH=.
python app\main.py
pause