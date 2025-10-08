@echo off
REM 知识图谱系统启动脚本 (Windows版本)

echo 🚀 启动知识图谱系统...

REM 检查Python环境
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到Python环境
    pause
    exit /b 1
)

REM 检查Node.js环境
npm --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到Node.js/npm环境
    echo 📝 仅启动后端服务...
    python api_server.py
    pause
    exit /b 0
)

REM 获取脚本目录
cd /d "%~dp0"

echo 🔧 启动后端服务...
start "Knowledge Graph Backend" python api_server.py

REM 等待后端启动
timeout /t 3 /nobreak >nul

echo 🎨 启动前端服务...
cd frontend

REM 检查依赖是否安装
if not exist "node_modules" (
    echo 📦 安装前端依赖...
    npm install
)

start "Knowledge Graph Frontend" npm run dev

echo.
echo ✅ 系统启动完成！
echo 🌐 前端地址: http://localhost:3000
echo 🔗 后端API: http://localhost:8000
echo 📚 API文档: http://localhost:8000/docs
echo.
echo 按任意键退出...
pause >nul