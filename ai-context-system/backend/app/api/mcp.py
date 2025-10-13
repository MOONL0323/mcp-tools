"""
MCP (Model Context Protocol) 相关API接口
提供给MCP服务器调用的后端服务接口
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.core.database import get_db
from app.models.database import Document, DocumentChunk, Entity, Relation
# 注释掉暂时不存在的服务
# from app.services.document_service import DocumentService
# from app.services.embedding_service import EmbeddingService  
# from app.services.neo4j_local import Neo4jLocalService
from app.schemas.mcp import (
    MCPSearchRequest, MCPSearchResponse, 
    MCPGraphQueryRequest, MCPGraphQueryResponse,
    MCPCodingStandardsRequest, MCPCodingStandardsResponse,
    MCPKnowledgeBaseStatsResponse
)

router = APIRouter()

# 暂时注释掉服务初始化，使用基本实现
# document_service = DocumentService()
# embedding_service = EmbeddingService()
# graph_service = Neo4jLocalService()

@router.post("/search", response_model=MCPSearchResponse)
async def mcp_search_documents(
    request: MCPSearchRequest,
    db: Session = Depends(get_db)
):
    """
    MCP搜索接口 - 为MCP服务器提供文档和代码搜索功能
    """
    try:
        # 根据搜索类型选择不同策略
        if request.search_type == "hybrid":
            # 混合搜索：向量检索 + 关键词匹配
            results = await _hybrid_search(request, db)
        elif request.search_type == "semantic":
            # 纯语义搜索
            results = await _semantic_search(request, db)
        elif request.search_type == "keyword":
            # 纯关键词搜索
            results = await _keyword_search(request, db)
        else:
            # 默认使用混合搜索
            results = await _hybrid_search(request, db)
        
        # 应用过滤器
        if request.filters:
            results = _apply_filters(results, request.filters)
        
        # 限制结果数量
        results = results[:request.limit] if request.limit else results[:10]
        
        return MCPSearchResponse(
            success=True,
            data=results,
            total=len(results),
            query_analysis={
                "original_query": request.query,
                "search_type": request.search_type,
                "filters_applied": bool(request.filters)
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")

@router.post("/graph/query", response_model=MCPGraphQueryResponse)
async def mcp_query_knowledge_graph(
    request: MCPGraphQueryRequest,
    db: Session = Depends(get_db)
):
    """
    MCP知识图谱查询接口
    """
    try:
        # 查询实体信息
        entity_info = await graph_service.get_entity_info(request.entity)
        
        if not entity_info:
            return MCPGraphQueryResponse(
                success=True,
                data={
                    "entity_info": {
                        "id": request.entity,
                        "name": request.entity,
                        "type": "unknown",
                        "properties": {}
                    },
                    "relationships": [],
                    "related_entities": [],
                    "usage_examples": []
                }
            )
        
        # 查询关系
        relationships = await graph_service.get_relationships(
            entity_name=request.entity,
            relation_type=request.relation_type,
            depth=request.depth or 2
        )
        
        # 查询相关实体
        related_entities = await graph_service.get_related_entities(
            entity_name=request.entity,
            depth=request.depth or 2
        )
        
        # 获取使用示例
        usage_examples = []
        if request.include_examples:
            usage_examples = await _get_entity_usage_examples(request.entity, db)
        
        return MCPGraphQueryResponse(
            success=True,
            data={
                "entity_info": entity_info,
                "relationships": relationships,
                "related_entities": related_entities,
                "usage_examples": usage_examples
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"图谱查询失败: {str(e)}")

@router.get("/coding-standards/{language}", response_model=MCPCodingStandardsResponse)
async def get_coding_standards(
    language: str,
    category: Optional[str] = Query(None, description="规范类别"),
    db: Session = Depends(get_db)
):
    """
    获取编码规范 - 为MCP服务器提供编码标准信息
    """
    try:
        # 搜索编码规范相关文档
        standards_query = f"{language} coding standards best practices"
        if category:
            standards_query += f" {category}"
        
        # 从文档库搜索相关规范
        standards_docs = db.query(Document).filter(
            Document.title.contains(f"{language} standards") |
            Document.title.contains("coding standards") |
            Document.tags.contains([language, "standards"])
        ).limit(10).all()
        
        # 构建编码规范响应
        standards_data = {
            "language": language,
            "naming_conventions": _extract_naming_conventions(standards_docs, language),
            "code_structure": _extract_code_structure(standards_docs),
            "best_practices": _extract_best_practices(standards_docs),
            "code_templates": _extract_code_templates(standards_docs, language),
            "linting_rules": _get_linting_rules(language),
            "testing_guidelines": _extract_testing_guidelines(standards_docs),
            "tools": {
                "formatters": _get_formatters(language),
                "linters": _get_linters(language),
                "test_frameworks": _get_test_frameworks(language)
            }
        }
        
        return MCPCodingStandardsResponse(
            success=True,
            data=standards_data
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取编码规范失败: {str(e)}")

@router.get("/knowledge-base/stats", response_model=MCPKnowledgeBaseStatsResponse)
async def get_knowledge_base_stats(db: Session = Depends(get_db)):
    """
    获取知识库统计信息
    """
    try:
        # 文档统计
        total_documents = db.query(Document).count()
        total_chunks = db.query(DocumentChunk).count()
        
        # 实体和关系统计
        total_entities = db.query(Entity).count()
        total_relations = db.query(Relation).count()
        
        # 语言统计
        language_stats = db.query(Document.tags).filter(
            Document.tags.isnot(None)
        ).all()
        
        languages = set()
        teams = set()
        projects = set()
        
        for doc in db.query(Document).all():
            if doc.tags:
                languages.update([tag for tag in doc.tags if tag in ['python', 'typescript', 'javascript', 'java', 'go', 'cpp']])
            if doc.team:
                teams.add(doc.team)
            if doc.project:
                projects.add(doc.project)
        
        return MCPKnowledgeBaseStatsResponse(
            success=True,
            data={
                "total_documents": total_documents,
                "total_chunks": total_chunks,
                "total_entities": total_entities,
                "total_relations": total_relations,
                "languages": list(languages),
                "teams": list(teams),
                "projects": list(projects),
                "last_updated": "2024-01-15T10:30:00Z"  # 实际应从数据库获取
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")

# 辅助函数

async def _hybrid_search(request: MCPSearchRequest, db: Session) -> List[Dict[str, Any]]:
    """混合搜索：向量检索 + 关键词匹配"""
    # 向量搜索
    vector_results = await embedding_service.search_similar_chunks(
        query=request.query,
        top_k=request.limit * 2  # 取更多结果用于重排
    )
    
    # 关键词搜索
    keyword_results = db.query(DocumentChunk).filter(
        DocumentChunk.content.contains(request.query)
    ).limit(request.limit).all()
    
    # 合并和重排结果
    combined_results = []
    
    # 处理向量搜索结果
    for result in vector_results:
        chunk = db.query(DocumentChunk).filter(
            DocumentChunk.id == result.get("chunk_id")
        ).first()
        if chunk:
            combined_results.append({
                "id": str(chunk.id),
                "title": chunk.title or "代码片段",
                "content": chunk.content,
                "description": chunk.summary,
                "file_path": f"chunk_{chunk.id}",
                "score": result.get("similarity", 0.0),
                "metadata": {
                    "doc_type": chunk.document.doc_type if chunk.document else "unknown",
                    "team": chunk.document.team if chunk.document else None,
                    "project": chunk.document.project if chunk.document else None
                }
            })
    
    return combined_results

async def _semantic_search(request: MCPSearchRequest, db: Session) -> List[Dict[str, Any]]:
    """纯语义搜索"""
    results = await embedding_service.search_similar_chunks(
        query=request.query,
        top_k=request.limit or 10
    )
    
    formatted_results = []
    for result in results:
        chunk = db.query(DocumentChunk).filter(
            DocumentChunk.id == result.get("chunk_id")
        ).first()
        if chunk:
            formatted_results.append({
                "id": str(chunk.id),
                "title": chunk.title or "文档片段",
                "content": chunk.content,
                "description": chunk.summary,
                "score": result.get("similarity", 0.0),
                "metadata": {
                    "doc_type": chunk.document.doc_type if chunk.document else "unknown"
                }
            })
    
    return formatted_results

async def _keyword_search(request: MCPSearchRequest, db: Session) -> List[Dict[str, Any]]:
    """纯关键词搜索"""
    chunks = db.query(DocumentChunk).filter(
        DocumentChunk.content.contains(request.query)
    ).limit(request.limit or 10).all()
    
    results = []
    for chunk in chunks:
        results.append({
            "id": str(chunk.id),
            "title": chunk.title or "文档片段", 
            "content": chunk.content,
            "description": chunk.summary,
            "score": 1.0,  # 关键词匹配固定分数
            "metadata": {
                "doc_type": chunk.document.doc_type if chunk.document else "unknown"
            }
        })
    
    return results

def _apply_filters(results: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    """应用搜索过滤器"""
    filtered_results = []
    
    for result in results:
        metadata = result.get("metadata", {})
        
        # 检查文档类型过滤
        if "doc_type" in filters:
            if metadata.get("doc_type") != filters["doc_type"]:
                continue
        
        # 检查语言过滤
        if "language" in filters:
            # 这里可以根据文档内容或标签判断语言
            pass
        
        # 检查团队过滤
        if "team" in filters:
            if metadata.get("team") != filters["team"]:
                continue
        
        # 检查项目过滤
        if "project" in filters:
            if metadata.get("project") != filters["project"]:
                continue
        
        filtered_results.append(result)
    
    return filtered_results

async def _get_entity_usage_examples(entity_name: str, db: Session) -> List[Dict[str, Any]]:
    """获取实体的使用示例"""
    # 搜索包含该实体的代码片段
    chunks = db.query(DocumentChunk).filter(
        DocumentChunk.content.contains(entity_name)
    ).limit(5).all()
    
    examples = []
    for chunk in chunks:
        examples.append({
            "context": f"在{chunk.document.title if chunk.document else '文档'}中使用",
            "code": chunk.content[:500],  # 截取前500字符
            "language": _detect_language(chunk.content)
        })
    
    return examples

def _detect_language(content: str) -> str:
    """检测代码语言"""
    if "def " in content and "import " in content:
        return "python"
    elif "function " in content or "const " in content:
        return "javascript"
    elif "class " in content and "public " in content:
        return "java"
    elif "func " in content and "package " in content:
        return "go"
    else:
        return "text"

# 编码规范提取函数
def _extract_naming_conventions(docs: List[Document], language: str) -> Dict[str, str]:
    """从文档中提取命名规范"""
    conventions = {
        "variables": "camelCase" if language in ["javascript", "typescript"] else "snake_case",
        "functions": "camelCase" if language in ["javascript", "typescript"] else "snake_case",
        "classes": "PascalCase",
        "constants": "UPPER_SNAKE_CASE"
    }
    
    # 这里可以添加从文档内容中智能提取规范的逻辑
    return conventions

def _extract_code_structure(docs: List[Document]) -> Dict[str, str]:
    """提取代码结构规范"""
    return {
        "indentation": "4 spaces",
        "line_length": "100 characters",
        "imports": "top of file, grouped by type",
        "comments": "docstrings for all public functions"
    }

def _extract_best_practices(docs: List[Document]) -> List[str]:
    """提取最佳实践"""
    return [
        "使用类型提示提高代码可读性",
        "编写完整的单元测试",
        "遵循SOLID原则进行设计",
        "使用有意义的变量和函数名",
        "保持函数简短和专一"
    ]

def _extract_code_templates(docs: List[Document], language: str) -> Dict[str, str]:
    """提取代码模板"""
    templates = {}
    
    if language == "python":
        templates["api_endpoint"] = '''
@router.post("/endpoint")
async def endpoint_handler(request: RequestModel):
    """API端点处理函数"""
    try:
        # 业务逻辑
        result = process_request(request)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
'''
    
    return templates

def _extract_testing_guidelines(docs: List[Document]) -> List[str]:
    """提取测试指南"""
    return [
        "每个公共函数都应有对应测试",
        "测试覆盖率应达到80%以上",
        "使用描述性的测试名称",
        "测试应该独立且可重复"
    ]

def _get_formatters(language: str) -> List[str]:
    """获取推荐的代码格式化工具"""
    formatters_map = {
        "python": ["black", "autopep8", "yapf"],
        "javascript": ["prettier", "standard"],
        "typescript": ["prettier", "tslint"],
        "java": ["google-java-format", "spotless"],
        "go": ["gofmt", "goimports"],
        "cpp": ["clang-format"]
    }
    return formatters_map.get(language, [])

def _get_linters(language: str) -> List[str]:
    """获取推荐的代码检查工具"""
    linters_map = {
        "python": ["pylint", "flake8", "mypy"],
        "javascript": ["eslint", "jshint"],
        "typescript": ["tslint", "@typescript-eslint"],
        "java": ["checkstyle", "spotbugs", "pmd"],
        "go": ["golint", "go vet", "staticcheck"],
        "cpp": ["cppcheck", "clang-tidy"]
    }
    return linters_map.get(language, [])

def _get_test_frameworks(language: str) -> List[str]:
    """获取推荐的测试框架"""
    frameworks_map = {
        "python": ["pytest", "unittest", "nose2"],
        "javascript": ["jest", "mocha", "jasmine"],
        "typescript": ["jest", "mocha", "vitest"],
        "java": ["junit", "testng", "mockito"],
        "go": ["testing", "testify", "ginkgo"],
        "cpp": ["gtest", "catch2", "cppunit"]
    }
    return frameworks_map.get(language, [])

def _get_linting_rules(language: str) -> Dict[str, Any]:
    """获取代码检查规则"""
    rules_map = {
        "python": {
            "max-line-length": 100,
            "max-complexity": 10,
            "naming-style": "snake_case"
        },
        "typescript": {
            "max-line-length": 100,
            "prefer-const": True,
            "no-any": True
        }
    }
    return rules_map.get(language, {})