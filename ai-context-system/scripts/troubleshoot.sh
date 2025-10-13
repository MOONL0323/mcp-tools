#!/bin/bash

# AI上下文增强系统 - 故障排除脚本
# 用途: 诊断和解决常见问题

set -e

echo "🔧 AI上下文增强系统故障排除工具"
echo "=================================="

# 进入项目根目录
cd "$(dirname "$0")/.."

# 检查基础环境
echo ""
echo "1. 🔍 检查基础环境..."

# 检查Docker
if ! command -v docker >/dev/null 2>&1; then
    echo "❌ Docker未安装"
    echo "   请访问 https://docs.docker.com/get-docker/ 安装Docker"
    exit 1
else
    echo "✅ Docker已安装: $(docker --version)"
fi

# 检查Docker是否运行
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker服务未运行"
    echo "   请启动Docker服务"
    exit 1
else
    echo "✅ Docker服务运行正常"
fi

# 检查Docker Compose
if ! command -v docker-compose >/dev/null 2>&1; then
    echo "❌ Docker Compose未安装"
    echo "   请安装Docker Compose"
    exit 1
else
    echo "✅ Docker Compose已安装: $(docker-compose --version)"
fi

# 检查配置文件
echo ""
echo "2. 📋 检查配置文件..."

if [[ -f .env.dev ]]; then
    echo "✅ 开发环境配置文件存在"
else
    echo "⚠️  开发环境配置文件不存在，正在创建..."
    cp .env.dev.example .env.dev
    echo "✅ 已创建 .env.dev"
fi

# 检查容器状态
echo ""
echo "3. 📦 检查容器状态..."

containers=(
    "ai-context-postgres-dev"
    "ai-context-redis-dev"
    "ai-context-chromadb-dev"
    "ai-context-neo4j-dev"
    "ai-context-minio-dev"
    "ai-context-backend-dev"
    "ai-context-frontend-dev"
    "ai-context-mcp-dev"
)

running_containers=0
total_containers=${#containers[@]}

for container in "${containers[@]}"; do
    if docker ps --filter "name=$container" --filter "status=running" --format "table {{.Names}}" | grep -q "$container"; then
        echo "✅ $container 运行中"
        ((running_containers++))
    else
        echo "❌ $container 未运行"
        # 检查容器是否存在但停止了
        if docker ps -a --filter "name=$container" --format "table {{.Names}}" | grep -q "$container"; then
            echo "   容器存在但已停止"
            echo "   最近日志:"
            docker logs --tail 10 "$container" 2>&1 | sed 's/^/     /'
        else
            echo "   容器不存在"
        fi
    fi
done

echo ""
echo "📊 容器状态总结: $running_containers/$total_containers 个容器运行中"

# 检查端口占用
echo ""
echo "4. 🔌 检查端口占用..."

ports=(
    "3000:前端"
    "8080:后端API"
    "3001:MCP服务"
    "5432:PostgreSQL"
    "6379:Redis"
    "8000:ChromaDB"
    "7474:Neo4j HTTP"
    "7687:Neo4j Bolt"
    "9000:MinIO"
    "5050:pgAdmin"
    "8081:Redis Commander"
)

for port_info in "${ports[@]}"; do
    port="${port_info%%:*}"
    service="${port_info##*:}"
    
    if netstat -tuln 2>/dev/null | grep -q ":$port " || ss -tuln 2>/dev/null | grep -q ":$port "; then
        echo "✅ 端口 $port ($service) 正在使用"
    else
        echo "❌ 端口 $port ($service) 未占用"
    fi
done

# 检查磁盘空间
echo ""
echo "5. 💾 检查磁盘空间..."

available_space=$(df . | awk 'NR==2 {print $4}')
available_gb=$((available_space / 1024 / 1024))

if [[ $available_gb -lt 5 ]]; then
    echo "⚠️  磁盘空间不足: ${available_gb}GB 可用"
    echo "   建议至少保留5GB空间"
else
    echo "✅ 磁盘空间充足: ${available_gb}GB 可用"
fi

# 检查Docker镜像
echo ""
echo "6. 🖼️  检查Docker镜像..."

images=(
    "postgres:15-alpine"
    "redis:7-alpine"
    "ghcr.io/chroma-core/chroma:latest"
    "neo4j:5.15-community"
    "minio/minio:latest"
)

for image in "${images[@]}"; do
    if docker images "$image" --format "table {{.Repository}}:{{.Tag}}" | grep -q "$image"; then
        echo "✅ 镜像 $image 已存在"
    else
        echo "❌ 镜像 $image 不存在"
        echo "   运行以下命令拉取: docker pull $image"
    fi
done

# 检查服务连通性
echo ""
echo "7. 🌐 检查服务连通性..."

services=(
    "http://localhost:8080/health:后端API健康检查"
    "http://localhost:3000:前端服务"
    "http://localhost:3001/health:MCP服务健康检查"
)

for service_info in "${services[@]}"; do
    url="${service_info%%:*}"
    name="${service_info##*:}"
    
    if curl -s --max-time 5 "$url" >/dev/null 2>&1; then
        echo "✅ $name 连通正常"
    else
        echo "❌ $name 连接失败"
    fi
done

# 提供解决方案
echo ""
echo "8. 🛠️  常见问题解决方案..."
echo ""

echo "📝 如果遇到以下问题:"
echo ""
echo "问题1: 容器启动失败"
echo "  解决方案:"
echo "    1. 检查端口是否被占用: netstat -tuln | grep :端口号"
echo "    2. 清理Docker资源: docker system prune -a"
echo "    3. 重新构建镜像: docker-compose -f docker-compose.dev.yml build --no-cache"
echo "    4. 重启Docker服务"
echo ""

echo "问题2: 数据库连接失败"
echo "  解决方案:"
echo "    1. 等待数据库完全启动: 初次启动可能需要1-2分钟"
echo "    2. 检查数据库容器日志: docker logs ai-context-postgres-dev"
echo "    3. 重置数据库: docker-compose -f docker-compose.dev.yml down -v"
echo ""

echo "问题3: 前端编译错误"
echo "  解决方案:"
echo "    1. 清理node_modules: docker-compose -f docker-compose.dev.yml exec frontend-dev rm -rf node_modules"
echo "    2. 重新安装依赖: docker-compose -f docker-compose.dev.yml exec frontend-dev npm install"
echo "    3. 重新构建容器: docker-compose -f docker-compose.dev.yml build frontend-dev"
echo ""

echo "问题4: 后端服务错误"
echo "  解决方案:"
echo "    1. 查看后端日志: docker-compose -f docker-compose.dev.yml logs backend-dev"
echo "    2. 检查Python依赖: docker-compose -f docker-compose.dev.yml exec backend-dev pip list"
echo "    3. 重新安装依赖: docker-compose -f docker-compose.dev.yml exec backend-dev pip install -r requirements.txt"
echo ""

echo "问题5: 内存不足"
echo "  解决方案:"
echo "    1. 增加Docker内存限制 (推荐至少4GB)"
echo "    2. 关闭不必要的应用程序"
echo "    3. 重启Docker服务"
echo ""

# 提供快速修复命令
echo "🚀 快速修复命令:"
echo ""
echo "  完全重置环境:"
echo "    docker-compose -f docker-compose.dev.yml down -v"
echo "    docker system prune -a"
echo "    ./scripts/start-dev.sh"
echo ""
echo "  重启所有服务:"
echo "    docker-compose -f docker-compose.dev.yml restart"
echo ""
echo "  查看所有容器状态:"
echo "    docker-compose -f docker-compose.dev.yml ps"
echo ""
echo "  查看实时日志:"
echo "    docker-compose -f docker-compose.dev.yml logs -f"
echo ""

echo "需要更多帮助? 请查看 README.md 或联系技术支持"