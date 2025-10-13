# AI上下文增强系统

## 📋 项目概述

基于Graph RAG技术的AI上下文增强系统，为团队提供智能文档管理和上下文检索服务。

## 🛠 技术栈

- **前端**: React 18 + TypeScript + Ant Design Pro
- **后端**: FastAPI + Python 3.11
- **数据库**: PostgreSQL + Neo4j + ChromaDB
- **缓存**: Redis
- **存储**: MinIO
- **容器化**: Docker + Docker Compose
- **生产部署**: Kubernetes

## 🚀 快速开始

### 开发环境搭建

1. **克隆项目**
```bash
git clone <repository-url>
cd ai-context-system
```

2. **环境配置**
```bash
# 复制环境变量文件
cp .env.dev.example .env.dev

# 编辑环境变量 (可选，默认配置即可运行)
nano .env.dev
```

3. **启动开发环境**
```bash
# 启动所有服务
docker-compose -f docker-compose.dev.yml --env-file .env.dev up -d

# 查看服务状态
docker-compose -f docker-compose.dev.yml ps

# 查看日志
docker-compose -f docker-compose.dev.yml logs -f backend-dev
```

4. **访问服务**
- 前端界面: http://localhost:3000
- 后端API: http://localhost:8080
- MCP服务: http://localhost:3001
- 数据库管理: http://localhost:5050 (pgAdmin)
- Redis管理: http://localhost:8081
- Neo4j浏览器: http://localhost:7474
- MinIO控制台: http://localhost:9001

### 开发环境管理

```bash
# 停止所有服务
docker-compose -f docker-compose.dev.yml down

# 重新构建服务
docker-compose -f docker-compose.dev.yml build

# 清理数据 (注意：会删除所有数据)
docker-compose -f docker-compose.dev.yml down -v

# 单独重启某个服务
docker-compose -f docker-compose.dev.yml restart backend-dev

# 进入容器调试
docker-compose -f docker-compose.dev.yml exec backend-dev bash
```

## 🏭 生产环境部署

### 生产环境配置

1. **环境变量配置**
```bash
# 复制生产环境配置模板
cp .env.prod.example .env.prod

# 编辑生产环境配置
nano .env.prod
```

2. **构建生产镜像**
```bash
# 构建所有服务的生产镜像
./scripts/build-prod.sh

# 推送镜像到仓库
./scripts/push-images.sh
```

3. **部署到生产环境**
```bash
# 使用Docker Compose部署
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d

# 或者使用Kubernetes部署 (推荐)
kubectl apply -f k8s/
```

### Kubernetes部署 (推荐)

```bash
# 创建命名空间
kubectl create namespace ai-context-system

# 创建配置和密钥
kubectl apply -f k8s/configmaps/
kubectl apply -f k8s/secrets/

# 部署数据库和存储
kubectl apply -f k8s/storage/

# 部署应用服务
kubectl apply -f k8s/apps/

# 配置监控
kubectl apply -f k8s/monitoring/
```

## 📁 项目结构

```
ai-context-system/
├── backend/                 # Python后端服务
│   ├── app/
│   │   ├── api/            # API路由
│   │   ├── core/           # 核心配置
│   │   ├── services/       # 业务服务
│   │   ├── models/         # 数据模型
│   │   └── utils/          # 工具函数
│   ├── Dockerfile.dev      # 开发环境镜像
│   ├── Dockerfile          # 生产环境镜像
│   └── requirements.txt    # Python依赖
├── frontend/               # React前端应用
│   ├── src/
│   │   ├── components/     # React组件
│   │   ├── services/       # 服务层
│   │   ├── interfaces/     # TypeScript接口
│   │   ├── hooks/          # React Hooks
│   │   └── utils/          # 工具函数
│   ├── Dockerfile.dev      # 开发环境镜像
│   ├── Dockerfile          # 生产环境镜像
│   └── package.json        # Node依赖
├── mcp-server/             # MCP协议服务器
│   ├── src/
│   │   ├── handlers/       # MCP处理器
│   │   ├── services/       # 服务层
│   │   └── types/          # 类型定义
│   ├── Dockerfile.dev      # 开发环境镜像
│   └── Dockerfile          # 生产环境镜像
├── database/               # 数据库脚本
│   ├── init.sql           # 初始化脚本
│   ├── dev-seed.sql       # 开发数据
│   └── migrations/        # 数据库迁移
├── k8s/                   # Kubernetes配置
│   ├── apps/              # 应用部署
│   ├── storage/           # 存储配置
│   ├── monitoring/        # 监控配置
│   └── ingress/           # 入口配置
├── nginx/                 # Nginx配置
├── monitoring/            # 监控配置
├── scripts/               # 部署脚本
├── docker-compose.dev.yml # 开发环境编排
├── docker-compose.prod.yml # 生产环境编排
└── README.md
```

## 🔧 开发指南

### 后端开发

```bash
# 进入后端容器
docker-compose -f docker-compose.dev.yml exec backend-dev bash

# 安装新依赖
pip install new-package
pip freeze > requirements.txt

# 运行测试
pytest

# 代码格式化
black .
isort .

# 类型检查
mypy .
```

### 前端开发

```bash
# 进入前端容器
docker-compose -f docker-compose.dev.yml exec frontend-dev bash

# 安装新依赖
npm install new-package

# 运行测试
npm test

# 代码检查
npm run lint
npm run type-check
```

### MCP服务开发

```bash
# 进入MCP服务容器
docker-compose -f docker-compose.dev.yml exec mcp-server-dev bash

# 安装新依赖
npm install new-package

# 运行测试
npm test

# 调试模式
npm run debug
```

## 📊 监控和日志

### 开发环境
- 应用日志通过`docker-compose logs`查看
- 数据库可通过pgAdmin管理
- Redis可通过Redis Commander查看

### 生产环境
- Prometheus + Grafana监控
- Jaeger链路追踪
- ELK/EFK日志聚合
- Sentry错误监控

## 🔒 安全配置

### 开发环境
- 使用默认密码，仅限本地访问
- 开启调试模式
- 详细日志输出

### 生产环境
- 强密码策略
- HTTPS加密
- 网络隔离
- 访问控制
- 安全扫描

## 🚨 故障排除

### 常见问题

1. **容器启动失败**
```bash
# 查看容器状态
docker-compose -f docker-compose.dev.yml ps

# 查看详细日志
docker-compose -f docker-compose.dev.yml logs service-name

# 重新构建容器
docker-compose -f docker-compose.dev.yml build --no-cache service-name
```

2. **数据库连接失败**
```bash
# 检查数据库容器状态
docker-compose -f docker-compose.dev.yml exec postgres-dev pg_isready

# 查看数据库日志
docker-compose -f docker-compose.dev.yml logs postgres-dev
```

3. **前端编译错误**
```bash
# 清理node_modules
docker-compose -f docker-compose.dev.yml exec frontend-dev rm -rf node_modules
docker-compose -f docker-compose.dev.yml exec frontend-dev npm install
```

### 健康检查

```bash
# 检查所有服务健康状态
./scripts/health-check.sh

# 检查API服务
curl http://localhost:8080/health

# 检查MCP服务
curl http://localhost:3001/health
```

## 🔄 CI/CD流程

### GitHub Actions
- 自动化测试
- 代码质量检查
- 安全扫描
- 镜像构建和推送
- 自动部署

### 分支策略
- `main`: 生产环境
- `develop`: 开发环境
- `feature/*`: 功能分支
- `hotfix/*`: 紧急修复

## 📞 支持

如有问题请联系：
- 技术支持: dev-team@company.com
- 项目文档: [Wiki链接]
- 问题反馈: [Issues链接]

## 📄 许可证

本项目使用 MIT 许可证，详见 [LICENSE](LICENSE) 文件。