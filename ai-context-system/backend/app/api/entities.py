"""
实体提取API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Dict, Optional
import structlog

from app.database import get_db
from app.models.database import Document
from app.services.entity_extractor import get_entity_extractor

logger = structlog.get_logger()
router = APIRouter(prefix="/entities", tags=["entities"])


class ExtractRequest(BaseModel):
    """实体提取请求"""
    content: str
    content_type: str = "text"  # text, python


@router.post("/extract")
async def extract_entities(request: ExtractRequest):
    """
    从内容中提取实体
    """
    try:
        extractor = get_entity_extractor()
        
        if request.content_type == "python":
            entities = extractor.extract_from_python_code(request.content)
            relationships = extractor.extract_relationships(entities)
            
            return {
                "success": True,
                "content_type": "python",
                "entities": entities,
                "relationships": relationships,
                "total_entities": sum(len(v) for v in entities.values()),
                "total_relationships": len(relationships)
            }
        
        else:  # text
            keywords = extractor.extract_from_text(request.content, top_k=20)
            
            return {
                "success": True,
                "content_type": "text",
                "keywords": keywords,
                "total_keywords": len(keywords)
            }
            
    except Exception as e:
        logger.error("实体提取失败", error=str(e))
        raise HTTPException(500, f"实体提取失败: {str(e)}")


@router.post("/extract-from-document/{document_id}")
async def extract_from_document(
    document_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    从文档中提取实体
    """
    try:
        # 获取文档
        document = await db.get(Document, document_id)
        if not document:
            raise HTTPException(404, "文档不存在")
        
        extractor = get_entity_extractor()
        
        # 根据文件类型选择提取方法
        is_python = document.filename.endswith('.py')
        
        if is_python:
            entities = extractor.extract_from_python_code(document.content)
            relationships = extractor.extract_relationships(entities)
            
            return {
                "success": True,
                "document_id": document_id,
                "document_title": document.title,
                "content_type": "python",
                "entities": entities,
                "relationships": relationships,
                "total_entities": sum(len(v) for v in entities.values()),
                "total_relationships": len(relationships)
            }
        
        else:
            keywords = extractor.extract_from_text(document.content, top_k=20)
            
            return {
                "success": True,
                "document_id": document_id,
                "document_title": document.title,
                "content_type": "text",
                "keywords": keywords,
                "total_keywords": len(keywords)
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("文档实体提取失败", document_id=document_id, error=str(e))
        raise HTTPException(500, f"实体提取失败: {str(e)}")
