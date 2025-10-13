#!/bin/bash

# AI上下文增强MCP服务器启动脚本

set -e  # 遇到错误立即退出

echo "============================================="
echo "   启动AI上下文增强MCP服务器"
echo "============================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查Node.js是否安装
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ 错误: 未安装Node.js${NC}"
    echo "请安装Node.js 18.0.0或更高版本"
    exit 1
fi

# 检查Node.js版本
NODE_VERSION=$(node --version)
echo -e "${BLUE}📦 Node.js版本: $NODE_VERSION${NC}"

# 检查npm是否可用
if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ 错误: npm未安装或不可用${NC}"
    exit 1
fi

# 检查是否在正确目录
if [ ! -f "package.json" ]; then
    echo -e "${RED}❌ 错误: 请在MCP服务器目录中运行此脚本${NC}"
    exit 1
fi

# 安装依赖（如果需要）
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}📦 首次运行，正在安装依赖...${NC}"
    npm install
fi

# 构建项目（如果需要）
if [ ! -f "dist/index.js" ]; then
    echo -e "${YELLOW}🔨 首次运行，正在构建项目...${NC}"
    npm run build
fi

# 创建日志目录
mkdir -p logs

# 检查后端服务
echo -e "${BLUE}🔍 检查后端服务连接...${NC}"
if curl -s http://127.0.0.1:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 后端服务连接正常${NC}"
else
    echo -e "${YELLOW}⚠️  警告: 无法连接到后端服务 (http://127.0.0.1:8000)${NC}"
    echo "请确保AI上下文系统后端正在运行"
    echo
    read -p "是否继续启动MCP服务器? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo
echo -e "${GREEN}🚀 启动MCP服务器...${NC}"
echo -e "${BLUE}💡 提示: 按Ctrl+C停止服务器${NC}"
echo -e "${BLUE}📖 配置Claude Desktop: 请参阅README.md文件${NC}"
echo

# 设置信号处理
trap 'echo -e "\n${YELLOW}👋 MCP服务器已停止${NC}"; exit 0' INT TERM

# 启动服务器
if npm start; then
    echo -e "${GREEN}✅ MCP服务器启动成功${NC}"
else
    echo
    echo -e "${RED}❌ MCP服务器启动失败${NC}"
    echo "请检查日志文件: logs/mcp-server.log"
    echo "或运行 npm run dev 查看详细错误信息"
    exit 1
fi