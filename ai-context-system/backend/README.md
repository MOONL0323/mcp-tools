# AI Context System Backend

基于FastAPI的AI上下文增强系统后端服务，采用Graph RAG技术栈。

## 功能特性

- 🔐 **用户认证**: JWT令牌认证，角色权限管理
- 📄 **文档管理**: 支持多种格式文档上传、处理、搜索
- 🧠 **Graph RAG**: 基于知识图谱的检索增强生成
- 🔍 **智能搜索**: 语义搜索和图搜索
- 📊 **数据统计**: 完整的使用统计和分析
- 🛡️ **安全保障**: 完善的权限控制和审计日志

## 技术架构

- **Web框架**: FastAPI + Uvicorn
- **数据库**: PostgreSQL + Redis + ChromaDB + Neo4j
- **认证**: JWT + bcrypt
- **文档处理**: 多格式解析 + 向量化
- **API文档**: Swagger/OpenAPI 自动生成

## 快速开始

### 环境要求

- Python 3.9+
- PostgreSQL 14+
- Redis 6+
- Docker (推荐)

### 本地开发

1. **安装依赖**
```bash
pip install -r requirements.txt
```

2. **环境配置**
```bash
# 复制配置文件
cp .env.example .env

# 编辑配置文件
# 配置数据库连接、Redis连接等
```

3. **启动服务**
```bash
# Windows
start_backend.bat

# Linux/macOS
chmod +x start_backend.sh
./start_backend.sh

# 或直接运行
python -m app.main
```

4. **访问服务**
- API服务: http://localhost:8000
- API文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

### Docker部署

```bash
# 开发环境
docker-compose -f docker-compose.dev.yml up -d

# 生产环境
docker-compose -f docker-compose.prod.yml up -d
```

## 项目结构

```
backend/
├── app/                        # 应用主目录
│   ├── api/                    # API路由
│   │   ├── v1/                 # v1版本API
│   │   │   ├── users.py        # 用户管理
│   │   │   ├── documents.py    # 文档管理
│   │   │   └── __init__.py
│   │   ├── dependencies.py     # 依赖注入
│   │   └── __init__.py
│   ├── core/                   # 核心模块
│   │   ├── config.py          # 配置管理
│   │   ├── database.py        # 数据库连接
│   │   ├── redis.py           # Redis连接
│   │   ├── logging.py         # 日志配置
│   │   └── exceptions.py      # 异常定义
│   ├── models/                # 数据模型
│   │   ├── database.py        # SQLAlchemy模型
│   │   └── __init__.py
│   ├── schemas/               # Pydantic模式
│   │   └── __init__.py
│   ├── services/              # 业务逻辑
│   │   ├── user_service.py    # 用户服务
│   │   ├── document_service.py # 文档服务
│   │   └── __init__.py
│   └── main.py                # 应用入口
├── requirements.txt           # Python依赖
├── start_backend.bat         # Windows启动脚本
├── start_backend.sh          # Linux启动脚本
└── README.md                 # 项目说明
```

## API文档

### 认证接口

- `POST /api/v1/users/register` - 用户注册
- `POST /api/v1/users/login` - 用户登录
- `POST /api/v1/users/logout` - 用户登出
- `POST /api/v1/users/refresh` - 刷新令牌

### 用户管理

- `GET /api/v1/users/me` - 获取当前用户信息
- `PUT /api/v1/users/me` - 更新当前用户信息
- `POST /api/v1/users/change-password` - 修改密码
- `GET /api/v1/users/` - 获取用户列表 (管理员)
- `GET /api/v1/users/{user_id}` - 获取用户详情 (管理员)

### 文档管理

- `POST /api/v1/documents/upload` - 上传文档
- `GET /api/v1/documents/` - 获取文档列表
- `GET /api/v1/documents/{document_id}` - 获取文档详情
- `PUT /api/v1/documents/{document_id}` - 更新文档信息
- `DELETE /api/v1/documents/{document_id}` - 删除文档
- `GET /api/v1/documents/{document_id}/download` - 下载文档
- `POST /api/v1/documents/search` - 搜索文档

### 文档分析

- `GET /api/v1/documents/{document_id}/chunks` - 获取文档块
- `GET /api/v1/documents/{document_id}/entities` - 获取文档实体
- `GET /api/v1/documents/{document_id}/relations` - 获取文档关系
- `GET /api/v1/documents/stats/overview` - 获取统计信息

## 环境变量

```bash
# 基础配置
DEBUG=true
ENVIRONMENT=development
SECRET_KEY=your-secret-key
HOST=0.0.0.0
PORT=8000

# 数据库配置
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/ai_context
REDIS_URL=redis://localhost:6379/0

# JWT配置
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
ALGORITHM=HS256

# 文件上传配置
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=104857600  # 100MB
ALLOWED_MIME_TYPES=text/plain,text/markdown,application/pdf

# 安全配置
ALLOWED_HOSTS=*
```

## 开发指南

### 添加新功能

1. **数据模型**: 在 `models/database.py` 中定义SQLAlchemy模型
2. **数据模式**: 在 `schemas/` 中定义Pydantic模式
3. **业务逻辑**: 在 `services/` 中实现业务服务
4. **API路由**: 在 `api/v1/` 中添加API端点
5. **注册路由**: 在 `api/v1/__init__.py` 中注册新路由

### 数据库迁移

```bash
# 生成迁移文件
alembic revision --autogenerate -m "描述"

# 应用迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

### 测试

```bash
# 运行单元测试
pytest

# 运行覆盖率测试
pytest --cov=app

# 运行特定测试
pytest tests/test_users.py
```

## 部署说明

### Docker部署

1. **构建镜像**
```bash
docker build -t ai-context-backend .
```

2. **运行容器**
```bash
docker run -d \
  --name ai-context-backend \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql+asyncpg://... \
  ai-context-backend
```

### 生产环境

1. **性能优化**
   - 使用Gunicorn多进程部署
   - 配置反向代理 (Nginx)
   - 启用缓存和CDN

2. **监控告警**
   - 集成Prometheus指标
   - 配置健康检查
   - 设置日志收集

3. **安全配置**
   - 使用HTTPS
   - 配置防火墙
   - 定期更新依赖

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查数据库服务状态
   - 验证连接字符串
   - 确认网络连通性

2. **Redis连接失败**
   - 检查Redis服务状态
   - 验证连接配置
   - 检查防火墙设置

3. **文件上传失败**
   - 检查文件大小限制
   - 验证文件类型支持
   - 确认存储空间

### 日志查看

```bash
# 查看应用日志
tail -f logs/app.log

# 查看错误日志
tail -f logs/error.log

# 查看访问日志
tail -f logs/access.log
```

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/新功能`)
3. 提交更改 (`git commit -am '添加新功能'`)
4. 推送到分支 (`git push origin feature/新功能`)
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 技术支持

- 文档: [项目Wiki](https://github.com/your-repo/wiki)
- 问题反馈: [GitHub Issues](https://github.com/your-repo/issues)
- 讨论交流: [GitHub Discussions](https://github.com/your-repo/discussions)