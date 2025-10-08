"""
知识图谱系统 REST API 服务器 - 简化版
基于重构后的组件架构
"""

import asyncio
import uuid
import os
import sys
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, BackgroundTasks, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn
from datetime import datetime
import tempfile
import shutil

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import get_default_config
from core.factory import get_factory

# 请求/响应模型
class SearchRequest(BaseModel):
    query: str = Field(..., description="搜索查询文本")
    top_k: int = Field(10, description="返回结果数量", ge=1, le=100)
    file_type: Optional[str] = Field("all", description="文件类型过滤: 'code', 'document', 'all'")

class SearchResult(BaseModel):
    content: str
    metadata: Dict[str, Any]
    similarity: float

class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    total_results: int

class SystemStatus(BaseModel):
    document_count: int
    vector_dimension: int
    graph_nodes: int
    graph_edges: int
    supported_extensions: List[str]
    available_components: Dict[str, List[str]]

class AddTextRequest(BaseModel):
    content: str = Field(..., description="文本内容")
    title: str = Field("", description="文档标题")
    save_graph: bool = Field(True, description="是否保存到知识图谱")

class ProcessingStatus(BaseModel):
    status: str  # 'processing', 'completed', 'failed'
    message: str
    progress: int
    result: Optional[Any] = None
    error: Optional[str] = None

class UploadResponse(BaseModel):
    task_id: str

class ApiResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None
    error: Optional[str] = None

# 创建FastAPI应用
app = FastAPI(
    title="知识图谱系统 API",
    description="提供文档处理、知识搜索、图结构分析等功能",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局变量
factory = None
vector_store = None
knowledge_graph = None
processing_tasks: Dict[str, ProcessingStatus] = {}

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化"""
    global factory, vector_store, knowledge_graph
    try:
        # 获取配置
        config = get_default_config()
        
        # 创建工厂
        factory = get_factory(config)
        
        # 创建组件
        vector_store = factory.create_vector_store()
        knowledge_graph = factory.create_knowledge_graph()
        
        # 配置向量存储的embedding_provider
        embedding_provider = factory.create_embedding_provider()
        vector_store.configure(embedding_provider=embedding_provider)
        
        # 加载合并后的知识图谱
        merged_graph_path = "data/graphs/merged_graph.pkl"
        if os.path.exists(merged_graph_path):
            knowledge_graph.load_graph(merged_graph_path)
            print(f"✅ 已加载知识图谱: {knowledge_graph.graph.number_of_nodes()} 个节点, {knowledge_graph.graph.number_of_edges()} 条边")
        else:
            print("⚠️ 未找到合并的知识图谱文件")
        
        # 显示代码解析器支持信息
        from implementations.parsers.code_parser_factory import code_parser_factory
        supported_code_exts = code_parser_factory.get_supported_extensions()
        supported_languages = code_parser_factory.get_supported_languages()
        print(f"✅ 代码解析器已就绪: 支持 {len(supported_languages)} 种语言 {supported_languages}")
        print(f"   支持的代码文件格式: {supported_code_exts}")
        
        print("✅ 知识图谱系统初始化完成")
    except Exception as e:
        print(f"❌ 系统初始化失败: {e}")
        raise

@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "knowledge-graph-api"
    }

@app.get("/api/status", response_model=ApiResponse)
async def get_system_status():
    """获取系统状态"""
    try:
        if vector_store is None or knowledge_graph is None:
            raise HTTPException(status_code=500, detail="系统未初始化")
        
        # 获取基本统计信息
        doc_count = len(getattr(vector_store, 'documents', []))
        vector_dim = getattr(vector_store, 'dimension', 384)  # 默认dimension
        
        # 获取图结构统计
        graph_nodes = len(getattr(knowledge_graph, 'nodes', []))
        graph_edges = len(getattr(knowledge_graph, 'edges', []))
        
        # 获取支持的文件格式
        supported_exts = ['.txt', '.md', '.pdf', '.docx']
        
        # 获取可用组件
        available_components = {
            'parsers': ['DefaultParser'],
            'embeddings': ['LocalEmbedding'],
            'vector_stores': ['LocalVectorStore'],
            'knowledge_graphs': ['LocalKnowledgeGraph']
        }
        
        status = SystemStatus(
            document_count=doc_count,
            vector_dimension=vector_dim,
            graph_nodes=graph_nodes,
            graph_edges=graph_edges,
            supported_extensions=supported_exts,
            available_components=available_components
        )
        
        return ApiResponse(
            success=True,
            message="系统状态获取成功",
            data=status.dict()
        )
        
    except Exception as e:
        print(f"获取系统状态失败: {e}")
        return ApiResponse(
            success=False,
            message="获取系统状态失败",
            error=str(e)
        )

@app.post("/api/search", response_model=ApiResponse)
async def search_knowledge(request: SearchRequest):
    """搜索知识库"""
    try:
        if vector_store is None:
            raise HTTPException(status_code=500, detail="向量存储未初始化")
        
        # 构建过滤条件
        filter_dict = None
        if request.file_type and request.file_type != "all":
            filter_dict = {"file_type": request.file_type}
        
        # 执行搜索
        results = vector_store.similarity_search(
            request.query, 
            k=request.top_k * 2,  # 获取更多结果以便过滤
            filter_dict=filter_dict
        )
        
        # 转换结果格式
        search_results = []
        for doc, similarity in results:
            # 如果没有使用filter_dict，需要在这里进行后处理过滤
            if request.file_type != "all" and filter_dict is None:
                # 基于source_file或其他metadata进行过滤
                source_file = doc.metadata.get("source_file", "")
                if request.file_type == "code":
                    if not any(source_file.endswith(ext) for ext in ['.go', '.py', '.js', '.ts', '.java', '.cpp', '.c', '.mod', '.sum']):
                        continue
                elif request.file_type == "document":
                    if any(source_file.endswith(ext) for ext in ['.go', '.py', '.js', '.ts', '.java', '.cpp', '.c']):
                        continue
            
            search_results.append(SearchResult(
                content=doc.page_content,
                metadata=doc.metadata,
                similarity=float(similarity)
            ))
            
            # 限制最终结果数量
            if len(search_results) >= request.top_k:
                break
        
        response = SearchResponse(
            query=request.query,
            results=search_results,
            total_results=len(search_results)
        )
        
        return ApiResponse(
            success=True,
            message=f"搜索完成，找到 {len(search_results)} 个结果",
            data=response.dict()
        )
        
    except Exception as e:
        print(f"搜索失败: {e}")
        return ApiResponse(
            success=False,
            message="搜索失败",
            error=str(e)
        )

@app.get("/api/components", response_model=ApiResponse)
async def get_available_components():
    """获取可用组件列表"""
    try:
        components = {
            'parsers': ['DefaultParser'],
            'embeddings': ['LocalEmbedding'],
            'vector_stores': ['LocalVectorStore'],
            'knowledge_graphs': ['LocalKnowledgeGraph']
        }
        
        return ApiResponse(
            success=True,
            message="组件列表获取成功",
            data=components
        )
        
    except Exception as e:
        print(f"获取组件列表失败: {e}")
        return ApiResponse(
            success=False,
            message="获取组件列表失败",
            error=str(e)
        )

@app.delete("/api/clear", response_model=ApiResponse)
async def clear_knowledge_base():
    """清空知识库（开发用）"""
    try:
        if vector_store is None or knowledge_graph is None:
            raise HTTPException(status_code=500, detail="系统未初始化")
        
        # 清空向量存储
        if hasattr(vector_store, 'clear'):
            vector_store.clear()
        
        # 清空图结构
        if hasattr(knowledge_graph, 'clear'):
            knowledge_graph.clear()
        
        return ApiResponse(
            success=True,
            message="知识库已清空"
        )
        
    except Exception as e:
        print(f"清空知识库失败: {e}")
        return ApiResponse(
            success=False,
            message="清空知识库失败",
            error=str(e)
        )

async def process_file_task(task_id: str, file_path: str, original_filename: str, save_graph: bool = True, file_type: str = 'document'):
    """后台处理文件任务"""
    try:
        # 更新任务状态为处理中
        processing_tasks[task_id] = ProcessingStatus(
            status="processing",
            message=f"正在处理文件 {original_filename}",
            progress=10
        )
        
        # 创建文档解析器
        parser = factory.create_document_parser()
        processing_tasks[task_id].progress = 30
        
        # 解析文档
        print(f"开始解析文档: {original_filename}")
        documents = parser.parse_file(file_path)
        processing_tasks[task_id].progress = 60
        
        # 标记每个文档的类型和原文件名
        for doc in documents:
            if 'file_type' not in doc.metadata:
                doc.metadata['file_type'] = file_type
            if 'source_file' not in doc.metadata:
                doc.metadata['source_file'] = original_filename
        
        # 添加到向量存储
        print(f"添加 {len(documents)} 个文档块到向量存储")
        doc_ids = vector_store.add_documents(documents)
        processing_tasks[task_id].progress = 80
        
        # 构建知识图谱（如果需要）
        if save_graph and knowledge_graph:
            print("更新知识图谱")
            knowledge_graph.build_from_documents(documents)
        
        processing_tasks[task_id].progress = 100
        
        # 完成任务
        processing_tasks[task_id] = ProcessingStatus(
            status="completed",
            message=f"文件 {original_filename} 处理完成",
            progress=100,
            result={
                "document_count": len(documents),
                "document_ids": doc_ids,
                "filename": original_filename
            }
        )
        
        print(f"文件处理完成: {original_filename}, 生成了 {len(documents)} 个文档块")
        
    except Exception as e:
        print(f"文件处理失败: {str(e)}")
        processing_tasks[task_id] = ProcessingStatus(
            status="failed",
            message=f"文件 {original_filename} 处理失败",
            progress=0,
            error=str(e)
        )
    finally:
        # 清理临时文件
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except:
            pass

async def process_text_task(task_id: str, content: str, title: str, save_graph: bool = True, file_type: str = 'document'):
    """后台处理文本任务"""
    try:
        # 更新任务状态为处理中
        processing_tasks[task_id] = ProcessingStatus(
            status="processing",
            message=f"正在处理文本: {title}",
            progress=10
        )
        
        # 创建文档解析器
        parser = factory.create_document_parser()
        processing_tasks[task_id].progress = 30
        
        # 创建文档对象
        from langchain.schema import Document as LangchainDocument
        document = LangchainDocument(
            page_content=content,
            metadata={
                "title": title or "用户添加的文本",
                "source": "user_input",
                "type": "text",
                "file_type": file_type,
                "source_file": title or "用户添加的文本"
            }
        )
        
        # 分割长文本（如果需要）
        documents = [document]  # 简单实现，不分割
        processing_tasks[task_id].progress = 60
        
        # 添加到向量存储
        print(f"添加文本到向量存储: {title}")
        doc_ids = vector_store.add_documents(documents)
        processing_tasks[task_id].progress = 80
        
        # 构建知识图谱（如果需要）
        if save_graph and knowledge_graph:
            print("更新知识图谱")
            knowledge_graph.build_from_documents(documents)
        
        processing_tasks[task_id].progress = 100
        
        # 完成任务
        processing_tasks[task_id] = ProcessingStatus(
            status="completed",
            message=f"文本 '{title}' 处理完成",
            progress=100,
            result={
                "document_count": len(documents),
                "document_ids": doc_ids,
                "title": title
            }
        )
        
        print(f"文本处理完成: {title}")
        
    except Exception as e:
        print(f"文本处理失败: {str(e)}")
        processing_tasks[task_id] = ProcessingStatus(
            status="failed",
            message=f"文本 '{title}' 处理失败",
            progress=0,
            error=str(e)
        )

@app.post("/api/upload", response_model=ApiResponse)
async def upload_content(
    background_tasks: BackgroundTasks,
    file: Optional[UploadFile] = File(None),
    content: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    file_type: Optional[str] = Form('document'),  # 'code' or 'document'
    save_graph: bool = Form(True)
):
    """
    上传文件或添加文本内容到知识库
    
    Args:
        file: 上传的文件（可选）
        content: 文本内容（可选）
        title: 文档标题（可选）
        save_graph: 是否保存到知识图谱
        
    Returns:
        任务ID用于查询处理状态
    """
    try:
        if vector_store is None:
            raise HTTPException(status_code=500, detail="向量存储未初始化")
        
        # 检查是否提供了文件或文本内容
        if not file and not content:
            return ApiResponse(
                success=False,
                message="请提供文件或文本内容",
                error="必须上传文件或提供文本内容"
            )
        
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        if file:
            # 处理文件上传
            # 检查文件类型
            allowed_extensions = ['.txt', '.md', '.pdf', '.docx', '.go', '.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.mod', '.sum']
            file_ext = os.path.splitext(file.filename or '')[1].lower()
            if file_ext not in allowed_extensions:
                return ApiResponse(
                    success=False,
                    message=f"不支持的文件类型: {file_ext}",
                    error=f"支持的格式: {', '.join(allowed_extensions)}"
                )
            
            # 保存临时文件
            temp_dir = tempfile.gettempdir()
            temp_filename = f"{task_id}_{file.filename}"
            temp_file_path = os.path.join(temp_dir, temp_filename)
            
            with open(temp_file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # 创建初始任务状态
            processing_tasks[task_id] = ProcessingStatus(
                status="processing",
                message=f"开始处理文件 {file.filename}",
                progress=0
            )
            
            # 添加后台任务
            background_tasks.add_task(
                process_file_task,
                task_id,
                temp_file_path,
                file.filename or "unknown",
                save_graph,
                file_type  # 传递file_type
            )
            
            return ApiResponse(
                success=True,
                message="文件上传成功，正在后台处理",
                data=UploadResponse(task_id=task_id).dict()
            )
            
        else:
            # 处理文本内容
            if not content.strip():
                return ApiResponse(
                    success=False,
                    message="文本内容不能为空",
                    error="请提供有效的文本内容"
                )
            
            # 创建初始任务状态
            processing_tasks[task_id] = ProcessingStatus(
                status="processing",
                message=f"开始处理文本: {title or '用户文本'}",
                progress=0
            )
            
            # 添加后台任务
            background_tasks.add_task(
                process_text_task,
                task_id,
                content,
                title or "用户文本",
                save_graph,
                file_type  # 传递file_type
            )
            
            return ApiResponse(
                success=True,
                message="文本添加成功，正在后台处理",
                data=UploadResponse(task_id=task_id).dict()
            )
        
    except Exception as e:
        print(f"上传处理失败: {str(e)}")
        return ApiResponse(
            success=False,
            message="上传处理失败",
            error=str(e)
        )

@app.get("/api/upload/status/{task_id}", response_model=ApiResponse)
async def get_upload_status(task_id: str):
    """获取文件处理状态"""
    try:
        if task_id not in processing_tasks:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        status = processing_tasks[task_id]
        return ApiResponse(
            success=True,
            message="状态获取成功",
            data=status.dict()
        )
        
    except Exception as e:
        print(f"获取任务状态失败: {str(e)}")
        return ApiResponse(
            success=False,
            message="获取任务状态失败",
            error=str(e)
        )

@app.get("/api/graph/data", response_model=ApiResponse)
async def get_graph_data():
    """获取知识图谱数据（用于可视化）"""
    try:
        if knowledge_graph is None:
            raise HTTPException(status_code=500, detail="知识图谱未初始化")
        
        # 导出图谱数据
        graph_data = knowledge_graph.export()
        
        return ApiResponse(
            success=True,
            message="图谱数据获取成功",
            data=graph_data
        )
        
    except Exception as e:
        print(f"获取图谱数据失败: {str(e)}")
        return ApiResponse(
            success=False,
            message="获取图谱数据失败",
            error=str(e)
        )

@app.delete("/api/graph/node/{node_id}", response_model=ApiResponse)
async def delete_graph_node(node_id: str):
    """删除知识图谱中的节点"""
    try:
        if knowledge_graph is None:
            raise HTTPException(status_code=500, detail="知识图谱未初始化")
        
        # 删除节点
        success = knowledge_graph.remove_node(node_id)
        
        if success:
            return ApiResponse(
                success=True,
                message=f"节点 {node_id} 已删除",
                data={"node_id": node_id}
            )
        else:
            return ApiResponse(
                success=False,
                message=f"节点 {node_id} 不存在或删除失败"
            )
        
    except Exception as e:
        print(f"删除节点失败: {str(e)}")
        return ApiResponse(
            success=False,
            message="删除节点失败",
            error=str(e)
        )

@app.post("/api/graph/reset", response_model=ApiResponse)
async def reset_graph():
    """重置知识图谱"""
    try:
        if knowledge_graph is None:
            raise HTTPException(status_code=500, detail="知识图谱未初始化")
        
        # 清空图谱
        knowledge_graph.clear()
        
        return ApiResponse(
            success=True,
            message="知识图谱已重置"
        )
        
    except Exception as e:
        print(f"重置图谱失败: {str(e)}")
        return ApiResponse(
            success=False,
            message="重置图谱失败",
            error=str(e)
        )

if __name__ == "__main__":
    print("🚀 启动知识图谱 API 服务器...")
    print("📝 API文档地址: http://localhost:8001/docs")
    print("🔍 前端地址: http://localhost:3000")
    
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8001,
        reload=False,
        log_level="info"
    )