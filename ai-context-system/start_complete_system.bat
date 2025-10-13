@echo off
setlocal EnableDelayedExpansion

echo ===============================================
echo   🤖 AI上下文增强系统 - 完整启动脚本
echo ===============================================
echo.
echo 🎯 这将启动完整的AI上下文增强系统:
echo    ✅ 后端Graph RAG引擎 (FastAPI)
echo    ✅ 向量数据库服务 (ChromaDB)  
echo    ✅ MCP服务器 (团队上下文提供器) ⭐
echo    ✅ 前端管理界面 (可选)
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: 未安装Python或版本不兼容
    echo 请安装Python 3.11或更高版本
    pause
    exit /b 1
)

REM 检查Node.js是否安装
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: 未安装Node.js或版本不兼容
    echo 请安装Node.js 18.0.0或更高版本
    pause
    exit /b 1
)

echo 📦 环境检查:
python --version
node --version
echo.

REM 检查是否在正确目录
if not exist "backend\app\main.py" (
    echo ❌ 错误: 请在ai-context-system项目根目录中运行此脚本
    pause
    exit /b 1
)

echo 🔧 准备启动服务...

REM 安装后端依赖
if not exist "backend\venv" (
    echo 📦 首次运行，正在创建Python虚拟环境...
    cd backend
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
    cd ..
    echo ✅ Python依赖安装完成
)

REM 安装MCP服务器依赖
if not exist "mcp-server\node_modules" (
    echo 📦 首次运行，正在安装MCP服务器依赖...
    cd mcp-server
    npm install
    cd ..
    echo ✅ MCP服务器依赖安装完成
)

REM 构建MCP服务器
if not exist "mcp-server\dist\index.js" (
    echo 🔨 构建MCP服务器...
    cd mcp-server
    npm run build
    cd ..
    echo ✅ MCP服务器构建完成
)

echo.
echo 🚀 正在启动服务 (按任意键停止所有服务)...
echo.

REM 创建数据目录
if not exist "chroma_data" mkdir chroma_data
if not exist "graph_data" mkdir graph_data
if not exist "uploads" mkdir uploads

REM 启动ChromaDB (后台)
echo 📊 启动ChromaDB向量数据库...
start /B "ChromaDB" python -m chromadb.cli.cli run --host localhost --port 8001 --path chroma_data
timeout /t 3 /nobreak >nul

REM 启动后端服务 (后台)
echo 🔧 启动后端Graph RAG引擎...
cd backend
start /B "Backend" cmd /c "call venv\Scripts\activate.bat && python run_dev.py"
cd ..
timeout /t 5 /nobreak >nul

REM 检查后端是否启动成功
echo 🔍 检查后端服务状态...
timeout /t 2 /nobreak >nul
curl -s http://127.0.0.1:8000/health >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  后端服务启动可能失败，但继续启动MCP服务器...
) else (
    echo ✅ 后端服务启动成功!
)

REM 启动MCP服务器 (前台，这是核心服务)
echo.
echo ⭐ 启动MCP服务器 (AI上下文增强核心服务)...
echo 💡 这是项目的核心功能 - 为AI Agent提供团队上下文!
echo.
cd mcp-server
start "MCP Server" cmd /c "npm start"
cd ..

echo.
echo 🎉 服务启动完成!
echo.
echo 📋 服务状态:
echo    🌐 后端API:     http://127.0.0.1:8000
echo    📖 API文档:     http://127.0.0.1:8000/docs  
echo    📊 ChromaDB:    http://localhost:8001
echo    ⭐ MCP服务器:   已启动 (查看MCP Server窗口)
echo.
echo 🔧 下一步: 配置Claude Desktop
echo    1. 找到Claude配置文件:
echo       Windows: %%APPDATA%%\Claude\claude_desktop_config.json
echo    2. 添加MCP服务器配置 (参考mcp-server\README.md)
echo    3. 重启Claude Desktop
echo    4. 在Claude中测试: "帮我搜索Python API代码示例"
echo.
echo 📚 可选: 启动Web管理界面
choice /c YN /m "是否启动前端Web界面 (可选)"
if !errorlevel!==1 (
    echo 🌐 启动前端Web界面...
    cd frontend
    if not exist "node_modules" (
        echo 📦 安装前端依赖...
        npm install
    )
    start "Frontend" cmd /c "npm run dev"
    cd ..
    echo ✅ 前端已启动: http://localhost:3000
)

echo.
echo 💡 系统已全部启动! 按任意键停止所有服务...
pause >nul

echo.
echo 🛑 正在停止所有服务...

REM 停止所有相关进程
taskkill /f /im "python.exe" >nul 2>&1
taskkill /f /im "node.exe" >nul 2>&1
taskkill /f /im "npm.exe" >nul 2>&1

echo ✅ 所有服务已停止
echo 👋 感谢使用AI上下文增强系统!
pause