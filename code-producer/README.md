# Code Producer MCP Service

一个基于Go语言开发的Model Context Protocol (MCP)服务，用于智能代码生成。该服务集成了knowledge-map系统，能够基于团队内部的文档和代码示例来生成更符合需求的代码。

## 主要功能

- **智能代码生成**: 基于自然语言需求描述生成代码
- **知识库集成**: 与knowledge-map系统集成，利用团队文档和代码示例
- **多语言支持**: 支持Go、JavaScript、Python、Java等多种编程语言
- **需求分析**: 智能分析需求并提供技术建议
- **模板管理**: 支持代码模板的搜索和使用

## 快速开始

### 前置条件

- Go 1.21 或更高版本
- 运行中的knowledge-map服务

### 安装和配置

1. 克隆项目：
```bash
git clone <repository-url>
cd code-producer
```

2. 安装依赖：
```bash
go mod tidy
```

3. 复制配置文件：
```bash
cp .env.example .env
```

4. 编辑配置文件：
```bash
# .env
KNOWLEDGE_MAP_URL=http://localhost:3000
KNOWLEDGE_MAP_API_KEY=your_api_key_here
PORT=8080
LOG_LEVEL=info
DEFAULT_LANGUAGE=go
MAX_CODE_LENGTH=5000
```

5. 启动服务：
```bash
go run main.go
```

服务将在 `http://localhost:8080` 启动。

## MCP工具

该服务提供以下MCP工具：

### 1. generate_code

生成代码的核心工具。

**参数：**
- `requirements` (必需): 代码需求描述
- `language` (可选): 编程语言，默认为"go"
- `framework` (可选): 使用的框架
- `style` (可选): 代码风格
- `context` (可选): 额外的上下文信息
- `templates` (可选): 指定使用的模板

**示例：**
```json
{
  "name": "generate_code",
  "arguments": {
    "requirements": "创建一个RESTful API，用于用户管理，包括注册、登录和用户信息查询功能",
    "language": "go",
    "framework": "gin",
    "style": "clean_architecture"
  }
}
```

### 2. search_knowledge

搜索knowledge-map中的相关文档和代码示例。

**参数：**
- `query` (必需): 搜索关键词
- `language` (可选): 编程语言过滤
- `type` (可选): 文档类型过滤
- `limit` (可选): 结果数量限制，默认10
- `filters` (可选): 额外的过滤条件

**示例：**
```json
{
  "name": "search_knowledge",
  "arguments": {
    "query": "JWT authentication Go",
    "language": "go",
    "type": "code_example",
    "limit": 5
  }
}
```

### 3. get_code_template

获取指定的代码模板。

**参数：**
- `language` (必需): 编程语言
- `framework` (可选): 框架名称
- `template_type` (可选): 模板类型

**示例：**
```json
{
  "name": "get_code_template",
  "arguments": {
    "language": "go",
    "framework": "gin",
    "template_type": "rest_api"
  }
}
```

### 4. analyze_requirements

分析需求并提供技术建议。

**参数：**
- `requirements` (必需): 需求描述

**示例：**
```json
{
  "name": "analyze_requirements",
  "arguments": {
    "requirements": "需要开发一个实时聊天应用，支持群聊和私聊，要求高并发和低延迟"
  }
}
```

## API端点

### 健康检查
- `GET /health` - 服务健康状态检查

### MCP通信
- `POST /mcp` - MCP协议通信端点

## 项目结构

```
code-producer/
├── main.go                    # 主入口文件
├── go.mod                     # Go模块文件
├── .env.example              # 环境变量示例
├── README.md                 # 项目文档
├── internal/                 # 内部包
│   ├── handlers/             # HTTP处理器
│   │   └── tool_handler.go   # MCP工具处理器
│   ├── models/               # 数据模型
│   │   └── types.go          # 类型定义
│   └── services/             # 业务逻辑服务
│       ├── knowledge_map.go  # Knowledge-map服务
│       └── code_producer.go  # 代码生成服务
└── pkg/                      # 公共包
    └── mcp/                  # MCP相关
        └── server.go         # MCP服务器实现
```

## 与Knowledge-Map集成

该服务与knowledge-map系统深度集成，通过以下方式增强代码生成能力：

1. **文档搜索**: 搜索相关的技术文档和最佳实践
2. **代码示例**: 查找类似功能的代码示例
3. **模板库**: 使用团队维护的代码模板
4. **技术栈建议**: 基于历史项目推荐合适的技术栈

## 配置选项

### 环境变量

- `KNOWLEDGE_MAP_URL`: Knowledge-map服务的URL
- `KNOWLEDGE_MAP_API_KEY`: Knowledge-map服务的API密钥
- `PORT`: 服务监听端口
- `LOG_LEVEL`: 日志级别 (debug, info, warn, error)
- `DEFAULT_LANGUAGE`: 默认编程语言
- `MAX_CODE_LENGTH`: 生成代码的最大长度

## 开发指南

### 添加新的编程语言支持

1. 在 `services/code_producer.go` 中添加新的语言生成函数
2. 更新 `generateCodeFromContext` 方法中的语言分支
3. 在模板搜索中添加对应的语言过滤

### 添加新的MCP工具

1. 在 `handlers/tool_handler.go` 中添加新的处理方法
2. 在 `main.go` 中注册新工具
3. 更新文档说明

### 扩展Knowledge-map集成

1. 在 `services/knowledge_map.go` 中添加新的API调用方法
2. 在 `services/code_producer.go` 中使用新的集成功能

## 故障排除

### 常见问题

1. **Knowledge-map连接失败**
   - 检查 `KNOWLEDGE_MAP_URL` 配置
   - 确认knowledge-map服务是否正常运行
   - 验证API密钥是否正确

2. **生成的代码质量不佳**
   - 提供更详细的需求描述
   - 检查knowledge-map中是否有相关的文档和示例
   - 考虑使用更具体的技术栈和框架参数

3. **服务启动失败**
   - 检查端口是否被占用
   - 验证Go版本是否满足要求
   - 检查依赖是否正确安装

## 贡献指南

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证。详见 LICENSE 文件。

## 更新日志

### v1.0.0
- 初始版本发布
- 支持基本的代码生成功能
- 集成knowledge-map服务
- 支持Go、JavaScript、Python、Java语言
- 提供需求分析和模板管理功能