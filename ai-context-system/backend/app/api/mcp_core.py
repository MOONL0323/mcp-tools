"""
MCP核心API - 为AI Agent提供团队上下文
基于AI代码生成系统方案的核心需求
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional, Dict, Any
from app.core.database import get_db
from app.models.database import Document, DevType, Team, Project, DocumentType
from pydantic import BaseModel

router = APIRouter()


def _get_default_coding_standards(language: str):
    """返回默认的编码规范"""
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
    db: AsyncSession = Depends(get_db)
):
    """
    MCP工具：搜索代码示例
    为AI Agent提供相关的Demo代码作为参考
    """
    try:
        # 首先查找 demo_code 类型的 dev_type
        dev_type_stmt = select(DevType).filter(DevType.category == DocumentType.DEMO_CODE)
        dev_type_result = await db.execute(dev_type_stmt)
        demo_dev_types = dev_type_result.scalars().all()
        demo_type_ids = [dt.id for dt in demo_dev_types]
        
        if not demo_type_ids:
            return {
                "success": True,
                "data": [],
                "total": 0,
                "message": "No demo code types configured"
            }
        
        # 构建查询
        stmt = select(Document).filter(Document.dev_type_id.in_(demo_type_ids))
        
        # 应用搜索条件
        if request.query:
            stmt = stmt.filter(
                (Document.title.contains(request.query)) |
                (Document.content.contains(request.query))
            )
        
        if request.team:
            # 查找team_id
            team_stmt = select(Team).filter(Team.name == request.team)
            team_result = await db.execute(team_stmt)
            team = team_result.scalar_one_or_none()
            if team:
                stmt = stmt.filter(Document.team_id == team.id)
            
        if request.project:
            # 查找project_id
            project_stmt = select(Project).filter(Project.name == request.project)
            project_result = await db.execute(project_stmt)
            project = project_result.scalar_one_or_none()
            if project:
                stmt = stmt.filter(Document.project_id == project.id)
            
        if request.language:
            stmt = stmt.filter(Document.tags.contains(request.language))
        
        # 获取结果
        stmt = stmt.limit(request.limit or 5)
        result = await db.execute(stmt)
        documents = result.scalars().all()
        
        # 格式化为MCP响应
        results = []
        for doc in documents:
            # 简化的响应格式
            results.append({
                "id": str(doc.id),
                "title": doc.title,
                "content": doc.content[:1000] + "..." if doc.content and len(doc.content) > 1000 else doc.content,
                "language": request.language or "unknown",
                "team_id": doc.team_id,
                "project_id": doc.project_id,
                "tags": doc.tags if isinstance(doc.tags, list) else [],
                "score": 0.9  # 简化评分
            })
        
        return {
            "success": True,
            "data": results,
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
    db: AsyncSession = Depends(get_db)
):
    """
    MCP工具：获取设计文档
    为AI Agent提供业务设计文档作为上下文
    """
    try:
        # 首先查找 business_doc 类型的 dev_type
        dev_type_stmt = select(DevType).filter(DevType.category == DocumentType.BUSINESS_DOC)
        dev_type_result = await db.execute(dev_type_stmt)
        business_dev_types = dev_type_result.scalars().all()
        business_type_ids = [dt.id for dt in business_dev_types]
        
        if not business_type_ids:
            return {
                "success": True,
                "data": [],
                "total": 0,
                "message": "No business doc types configured"
            }
        
        # 构建查询
        stmt = select(Document).filter(Document.dev_type_id.in_(business_type_ids))
        
        # 应用搜索条件
        if query:
            stmt = stmt.filter(
                (Document.title.contains(query)) |
                (Document.content.contains(query))
            )
        
        if team:
            team_stmt = select(Team).filter(Team.name == team)
            team_result = await db.execute(team_stmt)
            team_obj = team_result.scalar_one_or_none()
            if team_obj:
                stmt = stmt.filter(Document.team_id == team_obj.id)
            
        if project:
            project_stmt = select(Project).filter(Project.name == project)
            project_result = await db.execute(project_stmt)
            project_obj = project_result.scalar_one_or_none()
            if project_obj:
                stmt = stmt.filter(Document.project_id == project_obj.id)
        
        # 获取结果
        stmt = stmt.limit(5)
        result = await db.execute(stmt)
        documents = result.scalars().all()
        
        # 格式化响应
        results = []
        for doc in documents:
            results.append({
                "id": str(doc.id),
                "title": doc.title,
                "content": doc.content[:1000] + "..." if doc.content and len(doc.content) > 1000 else doc.content,
                "team_id": doc.team_id,
                "project_id": doc.project_id,
                "module_id": doc.module_id,
                "tags": doc.tags if isinstance(doc.tags, list) else []
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
    db: AsyncSession = Depends(get_db)
):
    """
    MCP工具：获取编码规范
    为AI Agent提供团队的编码规范和最佳实践
    """
    try:
        # 查找business_doc类型
        dev_type_stmt = select(DevType).filter(DevType.category == DocumentType.BUSINESS_DOC)
        dev_type_result = await db.execute(dev_type_stmt)
        business_dev_types = dev_type_result.scalars().all()
        business_type_ids = [dt.id for dt in business_dev_types]
        
        if not business_type_ids:
            return _get_default_coding_standards(language)
        
        # 查询编码规范文档 - 使用标签搜索
        stmt = select(Document).filter(
            Document.dev_type_id.in_(business_type_ids),
            Document.tags.contains('coding-standards')
        )
        
        if team:
            team_stmt = select(Team).filter(Team.name == team)
            team_result = await db.execute(team_stmt)
            team_obj = team_result.scalar_one_or_none()
            if team_obj:
                stmt = stmt.filter(Document.team_id == team_obj.id)
        
        result = await db.execute(stmt)
        documents = result.scalars().all()
        
        # 如果没有找到，返回默认规范
        if not documents:
            return _get_default_coding_standards(language)
        
        # 解析文档内容提取规范
        standards_data = {
            "language": language,
            "documents": []
        }
        
        for doc in documents:
            standards_data["documents"].append({
                "title": doc.title,
                "content": doc.content[:500] + "..." if doc.content and len(doc.content) > 500 else doc.content,
                "team_id": doc.team_id,
                "project_id": doc.project_id
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
    db: AsyncSession = Depends(get_db)
):
    """
    MCP资源：获取团队上下文信息
    """
    try:
        # 查找团队
        team_stmt = select(Team).filter(Team.name == team)
        team_result = await db.execute(team_stmt)
        team_obj = team_result.scalar_one_or_none()
        
        if not team_obj:
            return {
                "success": False,
                "error": f"Team '{team}' not found"
            }
        
        # 获取团队的所有文档
        stmt = select(Document).filter(Document.team_id == team_obj.id)
        
        if project:
            project_stmt = select(Project).filter(Project.name == project)
            project_result = await db.execute(project_stmt)
            project_obj = project_result.scalar_one_or_none()
            if project_obj:
                stmt = stmt.filter(Document.project_id == project_obj.id)
        
        result = await db.execute(stmt)
        documents = result.scalars().all()
        
        # 统计信息 - 简化版本
        # 获取dev_type来区分文档类型
        dev_type_stmt = select(DevType)
        dev_type_result = await db.execute(dev_type_stmt)
        dev_types_dict = {dt.id: dt.category.value for dt in dev_type_result.scalars().all()}
        
        stats = {
            "total_documents": len(documents),
            "business_docs": len([d for d in documents if dev_types_dict.get(d.dev_type_id) == 'business_doc']),
            "demo_codes": len([d for d in documents if dev_types_dict.get(d.dev_type_id) == 'demo_code']),
            "project_ids": list(set([str(d.project_id) for d in documents if d.project_id])),
            "module_ids": list(set([str(d.module_id) for d in documents if d.module_id])),
            "technologies": []
        }
        
        # 提取技术标签
        all_tags = []
        for doc in documents:
            if doc.tags and isinstance(doc.tags, (list, str)):
                if isinstance(doc.tags, str):
                    try:
                        import json
                        tags = json.loads(doc.tags)
                        all_tags.extend(tags if isinstance(tags, list) else [])
                    except:
                        pass
                else:
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
                "team_id": str(team_obj.id),
                "project": project,
                "stats": stats,
                "recent_documents": [
                    {
                        "id": str(doc.id),
                        "title": doc.title,
                        "dev_type_id": str(doc.dev_type_id),
                        "project_id": str(doc.project_id) if doc.project_id else None,
                        "created_at": doc.created_at.isoformat() if doc.created_at else None
                    }
                    for doc in list(documents)[-5:]  # 最近5个文档
                ]
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"获取团队上下文失败: {str(e)}"
        }