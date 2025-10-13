# AI 上下文增强系统 - 核心开发路线图

## 🎯 项目真正目标

**基于Graph RAG技术为AI Agent提供动态上下文，通过MCP协议集成，实现智能文档管理和知识图谱构建。**

---

## ❌ 当前状态分析

### ✅ 已完成
1. **前端UI框架** (95%完成)
   - React + TypeScript + Ant Design
   - 用户认证界面
   - 文档管理界面
   - 知识图谱可视化界面
   - 系统监控界面
   - **问题**: 前后端未打通，API调用全部mock数据

2. **后端基础设施** (30%完成)
   - FastAPI框架搭建
   - 用户认证系统基础
   - 数据库模型定义
   - **问题**: 核心Graph RAG功能完全缺失

### ❌ 严重缺失的核心功能

1. **Graph RAG引擎** (0%完成) ⚠️ 最重要
   - LLM辅助的智能文档分块
   - 实体和关系提取
   - 知识图谱构建
   - 向量化和检索

2. **文档处理Pipeline** (0%完成)
   - 文件上传和解析
   - 异步任务队列
   - 处理进度跟踪
   
3. **MCP Server** (0%完成) ⚠️ 核心目标
   - MCP协议实现
   - Context Provider
   - 与AI Agent集成

4. **数据库集成** (20%完成)
   - Neo4j图数据库 (未实现)
   - ChromaDB向量库 (未实现)
   - PostgreSQL (部分实现)

---

## 📋 核心开发任务清单

### Phase 1: Graph RAG 核心引擎 (最高优先级) 🔥

#### 任务1.1: LLM辅助的智能文档分块服务
**文件**: `backend/app/services/chunking_service.py`
**预计时间**: 2天

```python
class LLMAssistedChunker:
    """LLM辅助的智能文档分块器"""
    
    async def intelligent_chunk(document: Document) -> List[Chunk]:
        """
        1. 使用LLM分析文档结构
        2. 基于结构进行逻辑分块
        3. 为每个chunk生成标题和摘要
        """
        pass
    
    async def analyze_document_structure(document: Document) -> Dict:
        """分析文档结构 - 调用Qwen3-32B"""
        pass
```

**依赖**:
- LLM Client (✅ 已创建)
- 文档解析器 (需创建)

---

#### 任务1.2: 实体和关系提取服务
**文件**: `backend/app/services/entity_extraction_service.py`
**预计时间**: 3天

```python
class GraphRAGEntityExtractor:
    """实体和关系提取器"""
    
    async def extract_entities_and_relations(chunks: List[Chunk]) -> GraphData:
        """
        1. 从chunks中提取实体
        2. 识别实体间关系
        3. 构建图谱数据结构
        """
        pass
    
    async def extract_code_entities(chunk: Chunk) -> Dict:
        """提取代码相关实体 - 类/函数/变量"""
        pass
    
    async def extract_api_entities(chunk: Chunk) -> Dict:
        """提取API相关实体 - 接口/参数/响应"""
        pass
```

**依赖**:
- LLM Client (✅ 已创建)
- Neo4j Client (需创建)

---

#### 任务1.3: Neo4j 图数据库集成
**文件**: `backend/app/services/neo4j_client.py`
**预计时间**: 2天

```python
class Neo4jClient:
    """Neo4j图数据库客户端"""
    
    async def create_entity_node(entity: Entity) -> str:
        """创建实体节点"""
        pass
    
    async def create_relation_edge(relation: Relation) -> None:
        """创建关系边"""
        pass
    
    async def query_subgraph(entity_id: str, depth: int) -> Graph:
        """查询子图"""
        pass
    
    async def run_community_detection() -> List[Community]:
        """运行社区发现算法"""
        pass
```

---

#### 任务1.4: ChromaDB 向量数据库集成
**文件**: `backend/app/services/vector_store.py`
**预计时间**: 1天

```python
class VectorStore:
    """向量存储服务"""
    
    async def add_embeddings(chunks: List[ChunkEmbedding]) -> None:
        """添加向量到ChromaDB"""
        pass
    
    async def similarity_search(query: str, top_k: int) -> List[Chunk]:
        """向量相似度搜索"""
        pass
    
    async def hybrid_search(query: str, filters: Dict) -> List[Chunk]:
        """混合搜索 (向量 + 元数据过滤)"""
        pass
```

---

#### 任务1.5: 向量化服务
**文件**: `backend/app/services/embedding_service.py`
**预计时间**: 1天

```python
class EmbeddingService:
    """向量化服务 - 使用Qwen3-Embedding-8B"""
    
    async def embed_chunks(chunks: List[Chunk]) -> List[ChunkEmbedding]:
        """批量chunks向量化"""
        pass
    
    async def embed_query(query: str) -> List[float]:
        """查询向量化"""
        pass
```

---

### Phase 2: 文档处理Pipeline (高优先级) 🔥

#### 任务2.1: 文档解析器
**文件**: `backend/app/services/document_parser.py`
**预计时间**: 2天

支持格式:
- Markdown (.md)
- PDF (.pdf)
- Word (.docx)
- 纯文本 (.txt)
- 代码文件 (.py, .js, .java, etc.)

---

#### 任务2.2: 异步任务队列 (Celery)
**文件**: `backend/app/tasks/document_processing.py`
**预计时间**: 2天

```python
@celery_app.task
async def process_document_task(document_id: str):
    """
    异步处理文档:
    1. 解析文档
    2. 智能分块
    3. 提取实体和关系
    4. 向量化
    5. 存储到图谱和向量库
    """
    pass
```

---

#### 任务2.3: 文档上传API实现
**文件**: `backend/app/api/v1/documents.py`
**预计时间**: 1天

```python
@router.post("/upload")
async def upload_document(
    file: UploadFile,
    metadata: DocumentMetadata,
    current_user: User = Depends(get_current_user)
):
    """
    1. 保存文件
    2. 创建文档记录
    3. 触发异步处理任务
    4. 返回文档ID和处理状态
    """
    pass
```

---

### Phase 3: Graph RAG 检索引擎 (高优先级) 🔥

#### 任务3.1: 混合检索服务
**文件**: `backend/app/services/retrieval_service.py`
**预计时间**: 3天

```python
class GraphRAGRetriever:
    """Graph RAG检索引擎"""
    
    async def retrieve_context(
        query: str,
        filters: Dict,
        top_k: int = 10
    ) -> RetrievalResult:
        """
        混合检索:
        1. 向量相似度搜索
        2. 图谱遍历查询
        3. 社区摘要查询
        4. 结果融合和排序
        """
        pass
    
    async def graph_traversal_search(entity_ids: List[str]) -> List[Node]:
        """图谱遍历搜索"""
        pass
    
    async def community_search(query: str) -> List[Community]:
        """社区摘要搜索"""
        pass
```

---

### Phase 4: MCP Server 实现 (核心目标) 🎯

#### 任务4.1: MCP协议适配
**文件**: `mcp-server/src/server.ts`
**预计时间**: 3天

```typescript
class TeamContextMCPServer implements MCPServer {
  /**
   * Context Provider - 提供上下文
   */
  async getContext(request: ContextRequest): Promise<ContextResponse> {
    // 1. 调用Graph RAG检索API
    // 2. 格式化上下文数据
    // 3. 返回给AI Agent
  }
  
  /**
   * Tool Provider - 提供工具
   */
  async callTool(request: ToolRequest): Promise<ToolResponse> {
    // 提供文档搜索、实体查询等工具
  }
}
```

---

#### 任务4.2: MCP与后端API集成
**文件**: `mcp-server/src/api-client.ts`
**预计时间**: 1天

```typescript
class BackendAPIClient {
  async searchDocuments(query: string): Promise<Document[]>
  async queryGraph(entityId: string): Promise<GraphData>
  async getContext(filters: ContextFilters): Promise<Context>
}
```

---

### Phase 5: 前后端打通 (关键) 🔗

#### 任务5.1: 后端API完整实现
**预计时间**: 3天

需要实现的API:
```
POST   /api/v1/documents/upload          - 文档上传
GET    /api/v1/documents/                 - 文档列表
GET    /api/v1/documents/{id}             - 文档详情
DELETE /api/v1/documents/{id}             - 删除文档
GET    /api/v1/documents/{id}/chunks      - 获取文档块
GET    /api/v1/documents/{id}/entities    - 获取实体
POST   /api/v1/search/semantic            - 语义搜索
POST   /api/v1/search/graph               - 图谱搜索
GET    /api/v1/graph/entities/{id}        - 实体详情
GET    /api/v1/graph/subgraph             - 子图查询
```

---

#### 任务5.2: 前端API对接
**预计时间**: 2天

修改前端服务实现,调用真实API:
```typescript
// 从mock数据改为真实API调用
class DocumentService implements IDocumentService {
  async uploadDocument(file: File, metadata: DocumentUploadRequest): Promise<string> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('metadata', JSON.stringify(metadata));
    
    const response = await axios.post('/api/v1/documents/upload', formData);
    return response.data.document_id;
  }
  
  // ... 其他方法实现真实API调用
}
```

---

#### 任务5.3: WebSocket实时通信
**预计时间**: 2天

实现文档处理进度实时推送:
```python
# 后端
@router.websocket("/ws/documents/{document_id}/progress")
async def document_progress_websocket(websocket: WebSocket, document_id: str):
    await websocket.accept()
    # 推送处理进度
```

```typescript
// 前端
const ws = new WebSocket(`ws://localhost:8000/ws/documents/${id}/progress`);
ws.onmessage = (event) => {
  const progress = JSON.parse(event.data);
  updateProcessingStatus(progress);
};
```

---

### Phase 6: 测试和优化 (重要)

#### 任务6.1: 端到端测试
**预计时间**: 2天

测试完整流程:
1. 用户登录
2. 上传文档
3. 查看处理进度
4. 搜索文档
5. 查看知识图谱
6. MCP调用测试

---

#### 任务6.2: 性能优化
**预计时间**: 2天

- 批量处理优化
- 缓存策略
- 数据库查询优化
- 异步处理优化

---

## 📊 开发时间预估

| Phase | 任务数 | 预计天数 | 优先级 |
|-------|--------|----------|--------|
| Phase 1: Graph RAG核心 | 5 | 9天 | 🔥 最高 |
| Phase 2: 文档Pipeline | 3 | 5天 | 🔥 最高 |
| Phase 3: 检索引擎 | 1 | 3天 | 🔥 高 |
| Phase 4: MCP Server | 2 | 4天 | 🎯 核心 |
| Phase 5: 前后端打通 | 3 | 7天 | 🔗 关键 |
| Phase 6: 测试优化 | 2 | 4天 | ✅ 重要 |
| **总计** | **16** | **32天** | - |

---

## 🚀 立即开始的行动计划

### 第1周: Graph RAG基础
- [x] LLM Client实现
- [ ] 文档解析器
- [ ] 智能分块服务
- [ ] Neo4j集成

### 第2周: 实体提取和向量化
- [ ] 实体提取服务
- [ ] ChromaDB集成
- [ ] 向量化服务
- [ ] 图谱构建服务

### 第3周: 文档处理Pipeline
- [ ] Celery异步任务
- [ ] 文档上传API
- [ ] 处理状态跟踪
- [ ] 检索引擎基础

### 第4周: MCP和前后端打通
- [ ] MCP Server实现
- [ ] 后端API完善
- [ ] 前端API对接
- [ ] WebSocket通信

### 第5周: 测试和优化
- [ ] 端到端测试
- [ ] 性能优化
- [ ] Bug修复
- [ ] 文档完善

---

## 💡 关键技术决策

1. **使用Qwen3-32B做实体提取和分块** ✅
   - 利用大模型的理解能力
   - 比传统NLP方法更准确

2. **Graph RAG vs 传统RAG** ✅
   - 图谱+向量混合检索
   - 支持多跳推理
   - 更强的可解释性

3. **异步处理架构** ✅
   - Celery处理耗时任务
   - WebSocket实时反馈
   - 不阻塞用户操作

4. **MCP协议集成** ✅
   - 标准化的Agent接口
   - 易于与各种AI Agent集成
   - 支持动态上下文

---

## 📚 相关文档

- [Graph RAG原理](./docs/graphrag-theory.md)
- [MCP协议规范](./docs/mcp-protocol.md)
- [API接口文档](./backend/API.md)
- [部署指南](./DEPLOYMENT.md)

---

## ⚠️ 风险和挑战

1. **LLM API调用成本**
   - 大量文档处理可能产生高额API费用
   - 需要合理的批处理和缓存策略

2. **图数据库性能**
   - 大规模图谱查询可能较慢
   - 需要合理的索引和查询优化

3. **实体提取准确性**
   - LLM提取可能不够稳定
   - 需要人工校验和反馈机制

4. **前后端集成复杂度**
   - 异步处理的状态同步
   - 错误处理和重试机制

---

*最后更新: 2024-01-XX*
*版本: v1.0*
