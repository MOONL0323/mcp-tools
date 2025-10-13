# AI Context System - 本地部署快速启动指南

## ✅ 系统状态
- ✅ 后端服务：运行中 (http://127.0.0.1:8000)
- ✅ API文档：http://127.0.0.1:8000/docs
- ✅ ChromaDB：运行中 (localhost:8001)
- ✅ 本地图数据库：已初始化 (NetworkX)
- ✅ SQLite数据库：已创建

## 🚀 当前运行的服务

### 1. 后端API服务 (FastAPI)
- **地址**: http://127.0.0.1:8000
- **API文档**: http://127.0.0.1:8000/docs
- **健康检查**: http://127.0.0.1:8000/health
- **日志**: 在运行的终端中查看

### 2. ChromaDB向量数据库
- **地址**: http://localhost:8001
- **数据存储**: `D:\project\mcp-tools\ai-context-system\chroma_data`
- **状态**: 后台运行

### 3. 本地图数据库 (NetworkX)
- **类型**: 文件存储的图数据库
- **数据存储**: `D:\project\mcp-tools\ai-context-system\graph_data`
- **格式**: JSON (知识图谱持久化)

### 4. SQLite数据库
- **文件**: `D:\project\mcp-tools\ai-context-system\backend\ai_context.db`
- **作用**: 存储文档元数据、用户信息等

## 📝 可用API端点

### 核心文档管理API (简化版)
- `POST /api/v1/docs/upload` - 上传文档
- `GET /api/v1/docs/` - 列出所有文档
- `GET /api/v1/docs/{id}` - 获取文档详情
- `DELETE /api/v1/docs/{id}` - 删除文档
- `POST /api/v1/docs/search` - 向量搜索
- `GET /api/v1/docs/{id}/chunks` - 获取文档分块
- `GET /api/v1/docs/{id}/entities` - 获取文档实体

### 完整功能API
- `POST /api/v1/documents/` - 创建文档（带完整处理）
- `GET /api/v1/documents/` - 列出文档
- `POST /api/v1/documents/search` - 搜索文档
- `GET /api/v1/documents/{id}/graph` - 获取知识图谱

## 🧪 测试API

### 1. 健康检查
```bash
curl http://127.0.0.1:8000/health
```

### 2. 上传文档
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/docs/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@your_document.txt" \
  -F "title=测试文档" \
  -F "doc_type=code"
```

### 3. 列出所有文档
```bash
curl http://127.0.0.1:8000/api/v1/docs/
```

### 4. 向量搜索
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/docs/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "Python函数", "top_k": 5}'
```

## 📊 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    前端应用 (React)                      │
│                   http://localhost:3000                  │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP/REST
┌──────────────────────┴──────────────────────────────────┐
│              后端API服务 (FastAPI)                       │
│              http://127.0.0.1:8000                       │
├──────────────────────┬──────────────────────────────────┤
│  ├─ 文档解析        │  ├─ 实体提取                      │
│  ├─ 智能分块        │  ├─ 向量化                        │
│  └─ Graph RAG       │  └─ 知识图谱构建                   │
└──────────┬───────────┴──────────────┬───────────────────┘
           │                           │
    ┌──────┴────────┐         ┌───────┴───────┐
    │  ChromaDB     │         │ NetworkX图库  │
    │  向量数据库    │         │  本地JSON存储  │
    │  :8001        │         │  graph_data/  │
    └───────────────┘         └───────────────┘
```

## 🔧 配置文件

### 环境配置 (`.env`)
- 主配置文件：`backend/.env`
- GraphRAG配置：`backend/.env.graphrag`

### 关键配置项
```env
# LLM API
LLM_API_BASE=http://localhost:3000/v1
LLM_API_KEY=sk-your-api-key-here
LLM_CHAT_MODEL=Qwen/Qwen3-32B
LLM_EMBEDDING_MODEL=Qwen/Qwen3-Embedding-8B

# ChromaDB
CHROMADB_HOST=localhost
CHROMADB_PORT=8001

# 数据库
DATABASE_URL=sqlite+aiosqlite:///./ai_context.db
```

## 🛠️ 启动和停止

### 启动所有服务
```powershell
# 1. 启动ChromaDB（如果未运行）
python -m chromadb.cli.cli run --host localhost --port 8001 --path D:\project\mcp-tools\ai-context-system\chroma_data

# 2. 启动后端服务
python D:\project\mcp-tools\ai-context-system\backend\run_dev.py
```

### 停止服务
- **后端**: 在运行的终端按 `Ctrl+C`
- **ChromaDB**: 找到ChromaDB进程并终止

### 重启服务
停止后重新启动即可。数据会自动从持久化存储中恢复。

## 📦 功能特性

### ✅ 已实现
- [x] 文档上传和存储
- [x] 多格式文档解析（TXT, MD, PDF, DOCX, 代码文件）
- [x] LLM辅助的智能文档分块
- [x] 实体和关系提取
- [x] 知识图谱构建（本地NetworkX）
- [x] 向量化和相似度搜索（ChromaDB）
- [x] RESTful API接口
- [x] 完整API文档（Swagger UI）

### 🚧 待完成
- [ ] MCP Server实现（AI Agent对接）
- [ ] 前端UI完善
- [ ] 用户认证和授权
- [ ] 高级图查询功能
- [ ] 批量文档处理
- [ ] 性能优化和缓存

## 🎯 下一步工作

### 立即可做：
1. **测试文档上传**: 上传一个测试文档，验证完整处理流程
2. **查看知识图谱**: 检查生成的图数据文件 `graph_data/knowledge_graph.json`
3. **测试向量搜索**: 使用API进行语义搜索测试

### 核心待实现：
4. **MCP Server**: 实现MCP协议服务器，对接AI Agents
5. **前端集成**: 将前端连接到真实API
6. **优化性能**: 添加缓存、批处理等优化

## 📞 故障排查

### 后端启动失败
- 检查8000端口是否被占用
- 查看终端错误日志
- 确认Python依赖已安装

### ChromaDB连接失败
- 确认ChromaDB服务正在运行
- 检查8001端口状态
- 查看ChromaDB日志

### 图数据库问题
- 检查 `graph_data/` 目录权限
- 查看 `knowledge_graph.json` 文件是否存在

## 📚 相关资源

- **FastAPI文档**: https://fastapi.tiangolo.com/
- **ChromaDB文档**: https://docs.trychroma.com/
- **NetworkX文档**: https://networkx.org/
- **MCP协议**: https://modelcontextprotocol.io/

---

**系统版本**: v1.0.0-local  
**部署模式**: 本地开发环境（无Docker）  
**最后更新**: 2025-10-13
