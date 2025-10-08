#!/bin/bash

# 知识图谱系统启动脚本

echo "🚀 启动知识图谱系统..."

# 检查Python环境
if ! command -v python &> /dev/null; then
    echo "❌ 未找到Python环境"
    exit 1
fi

# 检查Node.js环境（前端）
if ! command -v npm &> /dev/null; then
    echo "❌ 未找到Node.js/npm环境"
    echo "📝 仅启动后端服务..."
    cd "$(dirname "$0")"
    python api_server.py
    exit 0
fi

# 启动后端服务
echo "🔧 启动后端服务..."
cd "$(dirname "$0")"
python api_server.py &
BACKEND_PID=$!

# 等待后端启动
sleep 3

# 启动前端服务
echo "🎨 启动前端服务..."
cd frontend
if [ ! -d "node_modules" ]; then
    echo "📦 安装前端依赖..."
    npm install
fi

npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ 系统启动完成！"
echo "🌐 前端地址: http://localhost:3000"
echo "🔗 后端API: http://localhost:8000"
echo "📚 API文档: http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 等待用户中断
trap "echo '🛑 正在停止服务...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait