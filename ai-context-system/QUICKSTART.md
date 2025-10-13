# 🚀 快速开始指南

## 📋 前置要求

- Docker Desktop (推荐4GB+内存)
- Git
- 至少5GB可用磁盘空间

## ⚡ 一键启动 (开发环境)

### Windows用户:
```bash
# 1. 克隆项目
git clone <repository-url>
cd ai-context-system

# 2. 启动开发环境
./scripts/start-dev.bat
```

### Linux/Mac用户:
```bash
# 1. 克隆项目
git clone <repository-url>
cd ai-context-system

# 2. 给脚本执行权限
chmod +x scripts/*.sh

# 3. 启动开发环境
./scripts/start-dev.sh
```

## 🌐 访问服务

启动完成后，可以访问以下服务:

| 服务 | 地址 | 说明 |
|------|------|------|
| 🖥️ 前端界面 | http://localhost:3000 | 主要用户界面 |
| 🔌 后端API | http://localhost:8080 | REST API服务 |
| 📖 API文档 | http://localhost:8080/docs | Swagger文档 |
| 🤖 MCP服务 | http://localhost:3001 | AI Agent集成 |

## 🛠️ 管理工具

| 工具 | 地址 | 用户名 | 密码 |
|------|------|--------|------|
| 🗄️ 数据库管理 | http://localhost:5050 | admin@dev.local | admin123 |
| 📊 Redis管理 | http://localhost:8081 | - | - |
| 🕸️ Neo4j浏览器 | http://localhost:7474 | neo4j | dev_password |
| 📁 MinIO控制台 | http://localhost:9001 | devuser | devpassword123 |

## 👤 测试账户

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | admin123 |
| 开发者 | developer1 | admin123 |
| 经理 | manager1 | admin123 |

## 🔧 常用命令

```bash
# 查看所有服务状态
docker-compose -f docker-compose.dev.yml ps

# 查看服务日志
docker-compose -f docker-compose.dev.yml logs -f [service-name]

# 停止所有服务
docker-compose -f docker-compose.dev.yml down

# 重启特定服务
docker-compose -f docker-compose.dev.yml restart [service-name]

# 进入容器调试
docker-compose -f docker-compose.dev.yml exec [service-name] bash
```

## ❓ 遇到问题?

1. **服务启动失败**: 运行 `./scripts/troubleshoot.sh` (Linux/Mac) 或 `./scripts/troubleshoot.bat` (Windows)
2. **端口冲突**: 检查端口占用，关闭冲突应用
3. **内存不足**: 确保Docker有足够内存 (推荐4GB+)
4. **完全重置**: 
   ```bash
   docker-compose -f docker-compose.dev.yml down -v
   docker system prune -a
   ./scripts/start-dev.sh
   ```

## 📚 下一步

- 阅读 [完整文档](README.md)
- 查看 [API文档](http://localhost:8080/docs) 
- 探索 [前端界面](http://localhost:3000)
- 测试 [MCP集成](http://localhost:3001)

开始开发愉快! 🎉