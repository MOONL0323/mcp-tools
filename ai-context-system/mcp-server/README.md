# AI上下文增强MCP服务器

基于Model Context Protocol (MCP)的团队知识库上下文增强服务器。为AI Agent提供智能的代码示例搜索、设计文档查询、编码规范获取和知识图谱遍历能力。

## 🎯 功能特色

### 🔍 智能工具
- **代码示例搜索** - 根据功能描述搜索团队代码库中的相关示例
- **设计文档查询** - 获取项目架构、API设计等文档上下文
- **编码规范获取** - 提供团队编码标准和最佳实践
- **知识图谱遍历** - 查询代码实体间的关系和依赖

### 📚 上下文资源
- **团队知识库** - 完整的文档和代码示例库
- **编码规范** - 多语言的代码规范和风格指南
- **设计模式** - 团队常用的架构模式和实践

### ⚡ 性能特色
- **智能缓存** - 提升查询响应速度
- **并发处理** - 支持多个AI Agent同时访问
- **优雅降级** - 后端服务异常时的容错机制

## 🚀 快速开始

### 前置条件

- Node.js 18.0.0+
- 运行中的AI上下文系统后端服务
- Claude Desktop或其他MCP兼容的AI工具

### 安装依赖

```bash
npm install
```

### 配置环境

复制环境变量模板：
```bash
cp .env.example .env
```

编辑`.env`文件：
```env
# 基本配置
SERVER_NAME=team-context-server
SERVER_VERSION=1.0.0
NODE_ENV=production

# RAG引擎配置
RAG_ENGINE_URL=http://127.0.0.1:8000
RAG_ENGINE_TIMEOUT=30000

# 后端API配置
BACKEND_API_URL=http://127.0.0.1:8000/api/v1
BACKEND_API_TIMEOUT=10000

# 缓存配置
CACHE_TTL=300
CACHE_MAX_KEYS=1000

# 日志配置
LOG_LEVEL=info
LOG_FILE=./logs/mcp-server.log
```

### 构建和启动

```bash
# 开发模式
npm run dev

# 生产模式
npm run build
npm start

# 健康检查
npm run health-check
```

## 🛠️ Claude Desktop配置

在Claude Desktop的设置中添加MCP服务器配置：

### Windows
编辑文件：`%APPDATA%\Claude\claude_desktop_config.json`

### macOS
编辑文件：`~/Library/Application Support/Claude/claude_desktop_config.json`

### 配置内容

```json
{
  "mcpServers": {
    "team-context-server": {
      "command": "node",
      "args": [
        "C:\\path\\to\\ai-context-system\\mcp-server\\dist\\index.js"
      ],
      "env": {
        "RAG_ENGINE_URL": "http://127.0.0.1:8000",
        "BACKEND_API_URL": "http://127.0.0.1:8000/api/v1",
        "LOG_LEVEL": "info"
      }
    }
  }
}
```

重启Claude Desktop后即可使用！

## 📖 使用示例

### 搜索代码示例

```
请帮我找一些Python FastAPI的用户认证代码示例
```

MCP服务器会自动：
1. 搜索团队代码库中相关的认证实现
2. 返回带有上下文说明的代码示例
3. 提供最佳实践建议

### 查询设计文档

```
我需要了解用户服务的API设计文档
```

服务器将：
1. 查找相关的API设计文档
2. 返回接口定义和使用说明
3. 包含相关的数据库设计信息

### 获取编码规范

```
告诉我TypeScript的编码规范
```

返回内容包括：
1. 命名规范
2. 代码结构要求
3. 推荐的工具链
4. 代码模板示例

## 🔧 工具详解

### search_code_examples

搜索团队代码示例和最佳实践。

**参数**：
- `query` (必需): 搜索查询描述
- `language`: 编程语言 (python, typescript, javascript, java, go, cpp)  
- `framework`: 框架名称 (fastapi, react, express等)
- `limit`: 返回结果数量 (1-20, 默认5)

**示例**：
```json
{
  "query": "用户注册API实现",
  "language": "python",
  "framework": "fastapi", 
  "limit": 3
}
```

### get_design_docs

获取相关设计文档和架构说明。

**参数**：
- `query` (必需): 查询描述
- `doc_type`: 文档类型 (api_design, architecture, database_design, business_logic)
- `team`: 团队名称
- `project`: 项目名称

### get_coding_standards

获取团队编码规范和风格指南。

**参数**：
- `language` (必需): 编程语言
- `category`: 规范类别 (naming, structure, testing, documentation, security)

### query_knowledge_graph

查询知识图谱中的实体关系。

**参数**：
- `entity` (必需): 要查询的实体名称
- `relation_type`: 关系类型 (CALLS, INHERITS, USES, DEPENDS_ON, IMPLEMENTS)
- `depth`: 查询深度 (1-5, 默认2)

## 📊 监控和维护

### 日志查看

```bash
# 查看实时日志
tail -f logs/mcp-server.log

# 查看错误日志
tail -f logs/error.log
```

### 健康检查

```bash
# 快速健康检查
npm run health-check

# 详细状态查询
curl http://127.0.0.1:8000/health
```

### 缓存管理

服务器自动管理缓存，支持：
- 自动过期清理
- 内存使用监控
- 缓存命中率统计

## 🔒 安全考虑

### 输入验证
- 所有用户输入都经过严格验证
- 防止代码注入和路径遍历攻击
- 查询长度和复杂度限制

### 访问控制
- 仅通过MCP协议访问
- 不直接暴露HTTP端口
- 基于文件系统权限控制

### 数据保护
- 不缓存敏感信息
- 日志中排除敏感数据
- 支持数据脱敏选项

## 🐛 故障排除

### 常见问题

**1. 连接后端失败**
```bash
# 检查后端服务状态
curl http://127.0.0.1:8000/health

# 检查网络连接
ping 127.0.0.1
```

**2. Claude Desktop无法连接**
- 检查配置文件路径是否正确
- 验证Node.js版本是否兼容
- 查看Claude Desktop的错误日志

**3. 搜索结果为空**
- 确认后端知识库有数据
- 检查搜索参数是否正确
- 查看服务器日志了解详情

### 调试模式

```bash
# 启用调试日志
LOG_LEVEL=debug npm run dev

# 查看详细错误信息
NODE_ENV=development npm start
```

## 📈 性能调优

### 缓存配置

```env
# 增加缓存时间（秒）
CACHE_TTL=600

# 增加缓存容量
CACHE_MAX_KEYS=5000
```

### 并发控制

```env
# 限制并发请求数
MAX_CONCURRENT_REQUESTS=20

# 速率限制
RATE_LIMIT_PER_MINUTE=200
```

## 🤝 贡献指南

1. Fork本项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建Pull Request

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🆘 支持

- 📖 [文档](https://github.com/your-org/ai-context-system/wiki)
- 🐛 [问题报告](https://github.com/your-org/ai-context-system/issues)
- 💬 [讨论区](https://github.com/your-org/ai-context-system/discussions)
- 📧 邮箱: support@your-org.com

---

**Made with ❤️ by AI Context System Team**