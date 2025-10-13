#!/bin/bash

# AI上下文增强系统 - 开发环境启动脚本
# 用途: 一键启动开发环境

set -e

echo "🚀 启动AI上下文增强系统开发环境..."

# 检查Docker是否运行
if ! docker info >/dev/null 2>&1; then
    echo "❌ 错误: Docker未运行，请先启动Docker"
    exit 1
fi

# 检查Docker Compose版本
if ! command -v docker-compose >/dev/null 2>&1; then
    echo "❌ 错误: 未找到docker-compose命令"
    exit 1
fi

# 进入项目根目录
cd "$(dirname "$0")/.."

# 检查环境变量文件
if [[ ! -f .env.dev ]]; then
    echo "📝 创建开发环境配置文件..."
    cp .env.dev.example .env.dev
    echo "✅ 已创建 .env.dev 文件，如需修改配置请编辑此文件"
fi

# 检查是否需要构建镜像
echo "🔧 检查并构建必要的Docker镜像..."

# 构建开发环境镜像
echo "📦 构建后端开发镜像..."
if [[ ! -d "backend" ]]; then
    echo "⚠️  警告: backend目录不存在，跳过后端镜像构建"
else
    docker-compose -f docker-compose.dev.yml build backend-dev
fi

echo "📦 构建前端开发镜像..."
if [[ ! -d "frontend" ]]; then
    echo "⚠️  警告: frontend目录不存在，跳过前端镜像构建"
else
    docker-compose -f docker-compose.dev.yml build frontend-dev
fi

echo "📦 构建MCP服务镜像..."
if [[ ! -d "mcp-server" ]]; then
    echo "⚠️  警告: mcp-server目录不存在，跳过MCP服务镜像构建"
else
    docker-compose -f docker-compose.dev.yml build mcp-server-dev
fi

# 启动基础服务
echo "🗄️  启动数据库和存储服务..."
docker-compose -f docker-compose.dev.yml --env-file .env.dev up -d \
    postgres-dev redis-dev chromadb-dev neo4j-dev minio-dev

# 等待数据库启动
echo "⏳ 等待数据库服务启动..."
sleep 10

# 检查数据库连接
echo "🔍 检查数据库连接..."
timeout=30
counter=0
while ! docker-compose -f docker-compose.dev.yml --env-file .env.dev exec -T postgres-dev pg_isready -U dev_user -d ai_context_dev >/dev/null 2>&1; do
    if [ $counter -eq $timeout ]; then
        echo "❌ 错误: 数据库启动超时"
        exit 1
    fi
    echo "⏳ 等待PostgreSQL启动... ($counter/$timeout)"
    sleep 1
    counter=$((counter + 1))
done

echo "✅ 数据库连接正常"

# 启动应用服务
echo "🚀 启动应用服务..."
docker-compose -f docker-compose.dev.yml --env-file .env.dev up -d \
    backend-dev frontend-dev mcp-server-dev

# 启动管理工具
echo "🛠️  启动管理工具..."
docker-compose -f docker-compose.dev.yml --env-file .env.dev up -d \
    pgadmin-dev redis-commander-dev

# 等待服务启动
echo "⏳ 等待应用服务启动..."
sleep 15

# 检查服务状态
echo "🔍 检查服务状态..."
services=(
    "postgres-dev:5432"
    "redis-dev:6379"
    "chromadb-dev:8000"
    "neo4j-dev:7474"
    "minio-dev:9000"
)

for service in "${services[@]}"; do
    container_name="ai-context-${service%%:*}"
    port="${service##*:}"
    
    if docker ps --filter "name=$container_name" --filter "status=running" --format "table {{.Names}}" | grep -q "$container_name"; then
        echo "✅ $container_name 运行正常"
    else
        echo "❌ $container_name 启动失败"
    fi
done

# 显示访问信息
echo ""
echo "🎉 开发环境启动完成！"
echo ""
echo "📋 服务访问地址:"
echo "  前端界面:     http://localhost:3000"
echo "  后端API:      http://localhost:8080"
echo "  API文档:      http://localhost:8080/docs"
echo "  MCP服务:      http://localhost:3001"
echo ""
echo "🛠️  管理工具:"
echo "  数据库管理:   http://localhost:5050 (用户: admin@dev.local 密码: admin123)"
echo "  Redis管理:    http://localhost:8081"
echo "  Neo4j浏览器:  http://localhost:7474 (用户: neo4j 密码: dev_password)"
echo "  MinIO控制台:  http://localhost:9001 (用户: devuser 密码: devpassword123)"
echo ""
echo "📊 监控命令:"
echo "  查看所有服务: docker-compose -f docker-compose.dev.yml ps"
echo "  查看日志:     docker-compose -f docker-compose.dev.yml logs -f [service-name]"
echo "  停止服务:     docker-compose -f docker-compose.dev.yml down"
echo ""
echo "🔧 开发命令:"
echo "  进入后端:     docker-compose -f docker-compose.dev.yml exec backend-dev bash"
echo "  进入前端:     docker-compose -f docker-compose.dev.yml exec frontend-dev bash"
echo "  重启服务:     docker-compose -f docker-compose.dev.yml restart [service-name]"
echo ""

# 检查应用服务健康状态
echo "🏥 健康检查..."
sleep 5

# 检查后端API
if curl -s http://localhost:8080/health >/dev/null 2>&1; then
    echo "✅ 后端API服务正常"
else
    echo "⚠️  后端API服务尚未就绪，请稍后访问"
fi

# 检查前端服务
if curl -s http://localhost:3000 >/dev/null 2>&1; then
    echo "✅ 前端服务正常"
else
    echo "⚠️  前端服务尚未就绪，请稍后访问"
fi

echo ""
echo "🎯 测试账户:"
echo "  管理员: admin / admin123"
echo "  开发者: developer1 / admin123"
echo "  经理:   manager1 / admin123"
echo ""
echo "📚 文档和帮助:"
echo "  README: ./README.md"
echo "  故障排除: 运行 ./scripts/troubleshoot.sh"
echo ""
echo "开始开发愉快! 🚀"