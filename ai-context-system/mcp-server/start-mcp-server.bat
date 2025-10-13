@echo off
echo =============================================
echo   启动AI上下文增强MCP服务器
echo =============================================

REM 检查Node.js是否安装
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: 未安装Node.js或版本不兼容
    echo 请安装Node.js 18.0.0或更高版本
    pause
    exit /b 1
)

REM 显示Node.js版本
echo 📦 Node.js版本:
node --version

REM 检查是否已构建
if not exist "dist\index.js" (
    echo 🔨 首次运行，正在构建项目...
    npm run build
    if %errorlevel% neq 0 (
        echo ❌ 构建失败
        pause
        exit /b 1
    )
)

REM 检查后端服务
echo 🔍 检查后端服务连接...
curl -s http://127.0.0.1:8000/health >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  警告: 无法连接到后端服务 (http://127.0.0.1:8000)
    echo 请确保AI上下文系统后端正在运行
    echo.
    choice /c YN /m "是否继续启动MCP服务器"
    if !errorlevel!==2 exit /b 1
)

echo.
echo 🚀 启动MCP服务器...
echo 💡 提示: 按Ctrl+C停止服务器
echo 📖 配置Claude Desktop: 请参阅README.md文件
echo.

REM 启动服务器
npm start

if %errorlevel% neq 0 (
    echo.
    echo ❌ MCP服务器启动失败
    echo 请检查日志文件: logs\mcp-server.log
    echo 或运行 npm run dev 查看详细错误信息
    pause
)

echo.
echo 👋 MCP服务器已停止
pause