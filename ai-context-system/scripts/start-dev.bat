@echo off
REM AI上下文增强系统 - 开发环境启动脚本 (Windows)
REM 用途: 一键启动开发环境

echo 🚀 启动AI上下文增强系统开发环境...

REM 检查Docker是否运行
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: Docker未运行，请先启动Docker
    pause
    exit /b 1
)

REM 检查Docker Compose
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到docker-compose命令
    pause
    exit /b 1
)

REM 进入项目根目录
cd /d "%~dp0\.."

REM 检查环境变量文件
if not exist .env.dev (
    echo 📝 创建开发环境配置文件...
    copy .env.dev.example .env.dev
    echo ✅ 已创建 .env.dev 文件，如需修改配置请编辑此文件
)

REM 构建开发环境镜像
echo 🔧 检查并构建必要的Docker镜像...

echo 📦 构建后端开发镜像...
if exist backend\ (
    docker-compose -f docker-compose.dev.yml build backend-dev
) else (
    echo ⚠️  警告: backend目录不存在，跳过后端镜像构建
)

echo 📦 构建前端开发镜像...
if exist frontend\ (
    docker-compose -f docker-compose.dev.yml build frontend-dev
) else (
    echo ⚠️  警告: frontend目录不存在，跳过前端镜像构建
)

echo 📦 构建MCP服务镜像...
if exist mcp-server\ (
    docker-compose -f docker-compose.dev.yml build mcp-server-dev
) else (
    echo ⚠️  警告: mcp-server目录不存在，跳过MCP服务镜像构建
)

REM 启动基础服务
echo 🗄️  启动数据库和存储服务...
docker-compose -f docker-compose.dev.yml --env-file .env.dev up -d postgres-dev redis-dev chromadb-dev neo4j-dev minio-dev

REM 等待数据库启动
echo ⏳ 等待数据库服务启动...
timeout /t 10 /nobreak >nul

REM 检查数据库连接
echo 🔍 检查数据库连接...
set /a counter=0
set /a timeout=30

:check_db
docker-compose -f docker-compose.dev.yml --env-file .env.dev exec -T postgres-dev pg_isready -U dev_user -d ai_context_dev >nul 2>&1
if errorlevel 1 (
    if %counter% geq %timeout% (
        echo ❌ 错误: 数据库启动超时
        pause
        exit /b 1
    )
    echo ⏳ 等待PostgreSQL启动... (%counter%/%timeout%)
    timeout /t 1 /nobreak >nul
    set /a counter+=1
    goto check_db
)

echo ✅ 数据库连接正常

REM 启动应用服务
echo 🚀 启动应用服务...
docker-compose -f docker-compose.dev.yml --env-file .env.dev up -d backend-dev frontend-dev mcp-server-dev

REM 启动管理工具
echo 🛠️  启动管理工具...
docker-compose -f docker-compose.dev.yml --env-file .env.dev up -d pgadmin-dev redis-commander-dev

REM 等待服务启动
echo ⏳ 等待应用服务启动...
timeout /t 15 /nobreak >nul

REM 检查服务状态
echo 🔍 检查服务状态...
docker ps --filter "name=ai-context-postgres-dev" --filter "status=running" --format "table {{.Names}}" | findstr "ai-context-postgres-dev" >nul
if errorlevel 1 (
    echo ❌ postgres-dev 启动失败
) else (
    echo ✅ postgres-dev 运行正常
)

docker ps --filter "name=ai-context-redis-dev" --filter "status=running" --format "table {{.Names}}" | findstr "ai-context-redis-dev" >nul
if errorlevel 1 (
    echo ❌ redis-dev 启动失败
) else (
    echo ✅ redis-dev 运行正常
)

REM 显示访问信息
echo.
echo 🎉 开发环境启动完成！
echo.
echo 📋 服务访问地址:
echo   前端界面:     http://localhost:3000
echo   后端API:      http://localhost:8080
echo   API文档:      http://localhost:8080/docs
echo   MCP服务:      http://localhost:3001
echo.
echo 🛠️  管理工具:
echo   数据库管理:   http://localhost:5050 ^(用户: admin@dev.local 密码: admin123^)
echo   Redis管理:    http://localhost:8081
echo   Neo4j浏览器:  http://localhost:7474 ^(用户: neo4j 密码: dev_password^)
echo   MinIO控制台:  http://localhost:9001 ^(用户: devuser 密码: devpassword123^)
echo.
echo 📊 监控命令:
echo   查看所有服务: docker-compose -f docker-compose.dev.yml ps
echo   查看日志:     docker-compose -f docker-compose.dev.yml logs -f [service-name]
echo   停止服务:     docker-compose -f docker-compose.dev.yml down
echo.
echo 🔧 开发命令:
echo   进入后端:     docker-compose -f docker-compose.dev.yml exec backend-dev bash
echo   进入前端:     docker-compose -f docker-compose.dev.yml exec frontend-dev bash
echo   重启服务:     docker-compose -f docker-compose.dev.yml restart [service-name]
echo.

REM 健康检查
echo 🏥 健康检查...
timeout /t 5 /nobreak >nul

REM 检查后端API
curl -s http://localhost:8080/health >nul 2>&1
if errorlevel 1 (
    echo ⚠️  后端API服务尚未就绪，请稍后访问
) else (
    echo ✅ 后端API服务正常
)

REM 检查前端服务
curl -s http://localhost:3000 >nul 2>&1
if errorlevel 1 (
    echo ⚠️  前端服务尚未就绪，请稍后访问
) else (
    echo ✅ 前端服务正常
)

echo.
echo 🎯 测试账户:
echo   管理员: admin / admin123
echo   开发者: developer1 / admin123
echo   经理:   manager1 / admin123
echo.
echo 📚 文档和帮助:
echo   README: ./README.md
echo   故障排除: 运行 ./scripts/troubleshoot.bat
echo.
echo 开始开发愉快! 🚀

pause