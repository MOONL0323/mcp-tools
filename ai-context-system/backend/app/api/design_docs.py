"""
设计文档API接口 - 为MCP服务器提供设计文档查询服务
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.database import Document
from app.schemas.mcp import MCPDesignDocRequest, MCPDesignDocResponse, MCPDesignDocument

router = APIRouter()

@router.post("/design-docs", response_model=MCPDesignDocResponse)
async def get_design_documents(
    request: MCPDesignDocRequest,
    db: Session = Depends(get_db)
):
    """
    获取设计文档 - 为MCP服务器提供设计文档查询功能
    根据主题、组件、团队等条件查找相关设计文档
    """
    try:
        # 构建查询条件
        query = db.query(Document)
        
        # 按文档类型过滤设计相关文档
        design_doc_types = ["design", "architecture", "spec", "requirement", "api"]
        if request.doc_type:
            query = query.filter(Document.doc_type == request.doc_type)
        else:
            query = query.filter(Document.doc_type.in_(design_doc_types))
        
        # 按主题搜索
        topic_conditions = []
        if request.topic:
            topic_conditions.extend([
                Document.title.contains(request.topic),
                Document.summary.contains(request.topic),
                Document.content.contains(request.topic)
            ])
        
        # 按组件搜索
        if request.component:
            topic_conditions.extend([
                Document.title.contains(request.component),
                Document.content.contains(request.component)
            ])
        
        # 应用主题和组件搜索条件
        if topic_conditions:
            from sqlalchemy import or_
            query = query.filter(or_(*topic_conditions))
        
        # 按团队过滤
        if request.team:
            query = query.filter(Document.team == request.team)
        
        # 按相关性排序
        documents = query.order_by(Document.created_at.desc()).limit(20).all()
        
        # 转换为响应格式
        design_docs = []
        for doc in documents:
            design_doc = MCPDesignDocument(
                id=str(doc.id),
                title=doc.title,
                content=doc.content,
                document_type=doc.doc_type,
                team=doc.team,
                project=doc.project,
                tags=doc.tags or [],
                created_at=doc.created_at.isoformat() if doc.created_at else "",
                updated_at=doc.updated_at.isoformat() if doc.updated_at else ""
            )
            design_docs.append(design_doc)
        
        return MCPDesignDocResponse(
            success=True,
            data=design_docs,
            total=len(design_docs)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取设计文档失败: {str(e)}")

@router.get("/design-docs/types", response_model=dict)
async def get_design_doc_types(db: Session = Depends(get_db)):
    """
    获取可用的设计文档类型
    """
    try:
        # 查询数据库中的文档类型
        doc_types = db.query(Document.doc_type).distinct().all()
        
        # 过滤出设计相关的文档类型
        design_types = []
        design_keywords = ["design", "architecture", "spec", "requirement", "api", "system"]
        
        for doc_type_tuple in doc_types:
            doc_type = doc_type_tuple[0]
            if doc_type and any(keyword in doc_type.lower() for keyword in design_keywords):
                design_types.append(doc_type)
        
        # 添加预定义的设计文档类型
        predefined_types = [
            "system_design",
            "api_design", 
            "database_design",
            "architecture_design",
            "component_design",
            "interface_design",
            "security_design"
        ]
        
        all_types = list(set(design_types + predefined_types))
        
        return {
            "success": True,
            "data": {
                "available_types": all_types,
                "categories": {
                    "system": ["system_design", "architecture_design"],
                    "api": ["api_design", "interface_design"],
                    "data": ["database_design"],
                    "security": ["security_design"],
                    "component": ["component_design"]
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文档类型失败: {str(e)}")

@router.get("/design-docs/{doc_id}", response_model=dict)
async def get_design_document_detail(
    doc_id: str,
    db: Session = Depends(get_db)
):
    """
    获取设计文档详细内容
    """
    try:
        # 查询文档
        document = db.query(Document).filter(Document.id == int(doc_id)).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        # 构建详细信息
        doc_detail = {
            "id": str(document.id),
            "title": document.title,
            "content": document.content,
            "summary": document.summary,
            "document_type": document.doc_type,
            "team": document.team,
            "project": document.project,
            "tags": document.tags or [],
            "file_path": document.file_path,
            "created_at": document.created_at.isoformat() if document.created_at else "",
            "updated_at": document.updated_at.isoformat() if document.updated_at else "",
            "metadata": {
                "word_count": len(document.content.split()) if document.content else 0,
                "sections": _extract_sections(document.content) if document.content else [],
                "related_components": _extract_components(document.content) if document.content else []
            }
        }
        
        return {
            "success": True,
            "data": doc_detail
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的文档ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文档详情失败: {str(e)}")

@router.get("/design-docs/search/suggestions", response_model=dict)
async def get_search_suggestions(
    query: str = Query(..., description="搜索查询"),
    db: Session = Depends(get_db)
):
    """
    获取设计文档搜索建议
    """
    try:
        # 基于查询生成建议
        suggestions = []
        
        # 查找相似的文档标题
        similar_docs = db.query(Document.title).filter(
            Document.title.contains(query)
        ).limit(5).all()
        
        for doc in similar_docs:
            suggestions.append(doc.title)
        
        # 添加常用的设计主题建议
        common_topics = [
            "微服务架构", "数据库设计", "API设计", "系统架构",
            "缓存策略", "消息队列", "负载均衡", "安全设计",
            "性能优化", "分布式系统", "容器化", "CI/CD"
        ]
        
        # 过滤相关主题
        topic_suggestions = [topic for topic in common_topics if query.lower() in topic.lower()]
        suggestions.extend(topic_suggestions[:3])
        
        return {
            "success": True,
            "data": {
                "suggestions": list(set(suggestions))[:8],
                "categories": [
                    "系统设计",
                    "数据库设计", 
                    "API设计",
                    "架构设计",
                    "安全设计"
                ]
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取搜索建议失败: {str(e)}")

# 辅助函数
def _extract_sections(content: str) -> List[str]:
    """从文档内容中提取章节标题"""
    sections = []
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        # 检测Markdown标题
        if line.startswith('#'):
            # 移除#符号和前后空格
            section_title = line.lstrip('#').strip()
            if section_title:
                sections.append(section_title)
        # 检测其他格式的标题
        elif line.endswith(':') and len(line) < 100:
            sections.append(line[:-1])
    
    return sections[:10]  # 最多返回10个章节

def _extract_components(content: str) -> List[str]:
    """从文档内容中提取相关组件名称"""
    components = []
    
    # 常见的组件关键词
    component_keywords = [
        "服务", "模块", "组件", "系统", "接口", "数据库", 
        "缓存", "队列", "网关", "负载均衡器", "API"
    ]
    
    lines = content.split('\n')
    for line in lines:
        for keyword in component_keywords:
            if keyword in line and len(line) < 200:
                # 提取包含组件关键词的短句
                words = line.split()
                for i, word in enumerate(words):
                    if keyword in word:
                        # 提取组件名称上下文
                        start = max(0, i-2)
                        end = min(len(words), i+3)
                        component_phrase = ' '.join(words[start:end])
                        if component_phrase not in components:
                            components.append(component_phrase)
                        break
    
    return components[:8]  # 最多返回8个相关组件