"""
MCP核心API - 为AI Agent提供团队上下文
基于AI代码生成系统方案的核心需求
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.core.database import get_db
from app.models.database import Document
from pydantic import BaseModel

router = APIRouter()

class CodeSearchRequest(BaseModel):
    query: str
    language: Optional[str] = None
    team: Optional[str] = None
    project: Optional[str] = None
    limit: Optional[int] = 5

class CodeSearchResult(BaseModel):
    id: str
    title: str
    content: str
    language: str
    team: str
    project: str
    tags: List[str]
    score: float

@router.post("/search-code-examples")
async def search_code_examples(
    request: CodeSearchRequest,
    db: Session = Depends(get_db)
):
    """
    MCP工具：搜索代码示例
    为AI Agent提供相关的Demo代码作为参考
    """
    try:
        # 构建查询
        query = db.query(Document).filter(Document.doc_type == 'demo_code')
        
        # 应用搜索条件
        if request.query:
            query = query.filter(
                Document.title.contains(request.query) |
                Document.content.contains(request.query)
            )
        
        if request.team:
            query = query.filter(Document.team == request.team)
            
        if request.project:
            query = query.filter(Document.project == request.project)
            
        if request.language:
            query = query.filter(Document.tags.contains([request.language]))
        
        # 获取结果
        documents = query.limit(request.limit or 5).all()
        
        # 格式化为MCP响应
        results = []
        for doc in documents:
            results.append(CodeSearchResult(
                id=str(doc.id),
                title=doc.title,
                content=doc.content,
                language=request.language or "unknown",
                team=doc.team,
                project=doc.project,
                tags=doc.tags or [],
                score=0.9  # 简化评分
            ))
        
        return {
            "success": True,
            "data": [result.dict() for result in results],
            "total": len(results)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"代码搜索失败: {str(e)}"
        }

@router.post("/get-design-docs")
async def get_design_docs(
    query: str,
    team: Optional[str] = None,
    project: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    MCP工具：获取设计文档
    为AI Agent提供业务设计文档作为上下文
    """
    try:
        # 构建查询
        db_query = db.query(Document).filter(Document.doc_type == 'business_doc')
        
        # 应用搜索条件
        if query:
            db_query = db_query.filter(
                Document.title.contains(query) |
                Document.content.contains(query)
            )
        
        if team:
            db_query = db_query.filter(Document.team == team)
            
        if project:
            db_query = db_query.filter(Document.project == project)
        
        # 获取结果
        documents = db_query.limit(5).all()
        
        # 格式化响应
        results = []
        for doc in documents:
            results.append({
                "id": str(doc.id),
                "title": doc.title,
                "content": doc.content[:1000] + "..." if len(doc.content) > 1000 else doc.content,
                "team": doc.team,
                "project": doc.project,
                "module": doc.module,
                "tags": doc.tags or []
            })
        
        return {
            "success": True,
            "data": results,
            "total": len(results)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"获取设计文档失败: {str(e)}"
        }

@router.get("/coding-standards/{language}")
async def get_coding_standards(
    language: str,
    team: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    MCP工具：获取编码规范
    为AI Agent提供团队的编码规范和最佳实践
    """
    try:
        # 查询编码规范文档
        query = db.query(Document).filter(
            Document.doc_type == 'business_doc',
            Document.tags.contains(['coding-standards', language])
        )
        
        if team:
            query = query.filter(Document.team == team)
        
        documents = query.all()
        
        # 如果没有找到，返回默认规范
        if not documents:
            default_standards = {
                "language": language,
                "naming_conventions": {
                    "variables": "camelCase" if language in ["javascript", "typescript"] else "snake_case",
                    "functions": "camelCase" if language in ["javascript", "typescript"] else "snake_case", 
                    "classes": "PascalCase",
                    "constants": "UPPER_SNAKE_CASE"
                },
                "code_structure": {
                    "indentation": "2 spaces" if language in ["javascript", "typescript"] else "4 spaces",
                    "line_length": "100 characters",
                    "imports": "top of file, grouped by type"
                },
                "best_practices": [
                    "使用有意义的变量和函数名",
                    "保持函数简短和专一",
                    "添加必要的注释和文档",
                    "遵循团队约定的代码风格"
                ]
            }
            
            return {
                "success": True,
                "data": default_standards
            }
        
        # 解析文档内容提取规范
        standards_data = {
            "language": language,
            "documents": []
        }
        
        for doc in documents:
            standards_data["documents"].append({
                "title": doc.title,
                "content": doc.content[:500] + "..." if len(doc.content) > 500 else doc.content,
                "team": doc.team,
                "project": doc.project
            })
        
        return {
            "success": True,
            "data": standards_data
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"获取编码规范失败: {str(e)}"
        }

@router.get("/team-context/{team}")
async def get_team_context(
    team: str,
    project: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    MCP资源：获取团队上下文信息
    """
    try:
        # 获取团队的所有文档
        query = db.query(Document).filter(Document.team == team)
        
        if project:
            query = query.filter(Document.project == project)
        
        documents = query.all()
        
        # 统计信息
        stats = {
            "total_documents": len(documents),
            "business_docs": len([d for d in documents if d.doc_type == 'business_doc']),
            "demo_codes": len([d for d in documents if d.doc_type == 'demo_code']),
            "projects": list(set([d.project for d in documents if d.project])),
            "modules": list(set([d.module for d in documents if d.module])),
            "technologies": []
        }
        
        # 提取技术标签
        all_tags = []
        for doc in documents:
            if doc.tags:
                all_tags.extend(doc.tags)
        
        # 统计技术标签
        from collections import Counter
        tech_counter = Counter(all_tags)
        stats["technologies"] = [{"name": tag, "count": count} 
                               for tag, count in tech_counter.most_common(10)]
        
        return {
            "success": True,
            "data": {
                "team": team,
                "project": project,
                "stats": stats,
                "recent_documents": [
                    {
                        "id": doc.id,
                        "title": doc.title,
                        "doc_type": doc.doc_type,
                        "project": doc.project,
                        "created_at": doc.created_at.isoformat() if doc.created_at else None
                    }
                    for doc in documents[-5:]  # 最近5个文档
                ]
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"获取团队上下文失败: {str(e)}"
        }