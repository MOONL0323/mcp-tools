# AI Context System# AI Context System



AI驱动的代码和文档智能管理系统，支持多种文件格式解析、语义搜索和知识图谱构建。AI驱动的代码和文档智能管理系统，支持多种文件格式解析、语义搜索和知识图谱构建。



## 功能特性



- 代码文件上传与解析（支持Python、Go、Java、JavaScript等）- 代码文件上传与解析（支持Python、Go、Java、JavaScript等）

- 文档文件上传与解析（支持PDF、Word、Markdown、TXT等）- 文档文件上传与解析（支持PDF、Word、Markdown、TXT等）

- 基于向量数据库的语义搜索- 基于向量数据库的语义搜索

- 知识图谱构建与可视化- 知识图谱构建与可视化

- MCP协议集成，支持与AI助手交互- MCP协议集成，支持与AI助手交互

- RESTful API接口- RESTful API接口



## 技术架构



### 后端

- FastAPI - 高性能Web框架- FastAPI - 高性能Web框架

- PostgreSQL / SQLite - 关系数据库- PostgreSQL / SQLite - 关系数据库

- Neo4j - 图数据库- Neo4j - 图数据库

- ChromaDB - 向量数据库- ChromaDB - 向量数据库

- Redis - 缓存服务- Redis - 缓存服务



### 前端

- React + TypeScript- React + TypeScript

- Ant Design UI组件库- Ant Design UI组件库

- D3.js / ECharts图表可视化- D3.js / ECharts图表可视化



### MCP Server### MCP Server

- TypeScript实现的MCP协议服务器- TypeScript实现的MCP协议服务器

- 支持代码和文档的智能检索- 支持代码和文档的智能检索



## 快速开始



### 环境要求



- Python 3.8+- Python 3.8+

- Node.js 16+- Node.js 16+

- PostgreSQL 13+ / SQLite（开发环境可选）- PostgreSQL 13+ / SQLite（开发环境可选）

- Neo4j 4.4+（可选）- Neo4j 4.4+（可选）

- Redis 6+（可选）- Redis 6+（可选）



### 安装步骤



1. 配置环境1. 配置环境



编辑 .env 文件，选择环境：编辑.env文件，选择环境：

```bash
# 选择环境：development 或 production
ENVIRONMENT=development

# 选择网络：intranet 或 internet
NETWORK_ENV=intranet
```

2. 配置API密钥

编辑 .env.secrets 文件：

```bash
LLM_API_KEY=your-api-key
```

3. 一键启动

```bash
python start.py
```

系统会自动加载环境配置、检查并安装依赖、启动所有服务。

### 访问地址

- 前端页面：http://localhost:3000
- 后端API：http://localhost:8000
- API文档：http://localhost:8000/docs
- MCP服务：http://localhost:3001

## 项目结构

```
ai-context-system/
├── backend/              # 后端服务
│   ├── app/
│   │   ├── api/         # API路由
│   │   ├── core/        # 核心配置
│   │   ├── models/      # 数据模型
│   │   └── services/    # 业务逻辑
│   └── requirements.txt
├── frontend/            # 前端应用
│   ├── src/
│   │   ├── components/  # UI组件
│   │   ├── services/    # API服务
│   │   └── routes/      # 路由配置
│   └── package.json
├── mcp-server/          # MCP协议服务器
│   ├── src/
│   └── package.json
├── config/              # 配置文件目录
│   ├── config.development.env
│   ├── config.production.env
│   ├── config.intranet.env
│   └── config.internet.env
├── scripts/             # 工具脚本
├── tests/               # 测试文件
├── database/            # 数据库配置
├── .env                 # 主配置文件
├── .env.secrets         # 敏感信息
└── start.py             # 启动脚本
```

## 配置说明

### 开发环境

- 使用SQLite本地数据库
- 无需Docker容器
- 支持热重载
- 详细的调试日志

### 生产环境

- 使用PostgreSQL数据库
- Kubernetes部署
- 完整的监控和日志
- 生产级性能优化

### 网络环境

- 内网环境：使用内网Embedding API服务
- 外网环境：使用本地Embedding模型

## API文档

启动后访问：http://localhost:8000/docs

主要接口：
- POST /api/v1/code/upload - 上传代码文件
- POST /api/v1/document/upload - 上传文档文件
- POST /api/v1/search/semantic - 语义搜索
- GET /api/v1/graph/knowledge - 获取知识图谱

## 开发指南

### 后端开发

```bash
cd backend
pip install -r requirements.txt
python run_dev.py
```

### 前端开发

```bash
cd frontend
npm install
npm start
```

### MCP服务开发

```bash
cd mcp-server
npm install
npm run dev
```

## 测试

运行所有测试：

```bash
python -m pytest tests/
```

## 故障排除

### 依赖服务未启动

如果提示Neo4j、Redis等服务未启动，可选择：
- 忽略警告继续运行（开发环境可选）
- 手动启动相应服务
- 使用Docker Compose启动：docker-compose up -d

### 配置加载失败

检查 .env 和 .env.secrets 文件是否正确配置。

### 端口冲突

在 .env 文件中修改端口配置：

```bash
BACKEND_PORT=8000
FRONTEND_PORT=3000
MCP_PORT=3001
```

## 许可证

MIT License
