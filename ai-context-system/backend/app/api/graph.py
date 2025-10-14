"""
知识图谱API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Dict, Optional
import structlog

from app.database import get_db
from app.models.database import Document
from app.services.graph_service import get_graph_service
from app.services.entity_extractor import get_entity_extractor

logger = structlog.get_logger()
router = APIRouter(prefix="/graph", tags=["graph"])


@router.post("/store-from-document/{document_id}")
async def store_document_in_graph(
    document_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    将文档的实体和关系存入知识图谱
    """
    try:
        # 查询文档
        result = await db.execute(
            f"SELECT * FROM documents WHERE id = {document_id}"
        )
        document = result.first()
        
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        # 提取实体
        extractor = get_entity_extractor()
        content = document.content
        file_path = document.file_path or ""
        
        # 判断文件类型
        if file_path.endswith(".py"):
            # Python代码
            entities = extractor.extract_from_python_code(content)
            relationships = extractor.extract_relationships(entities)
            
            # 存入图
            graph = get_graph_service()
            graph.store_python_entities(document_id, entities, relationships)
            
            return {
                "success": True,
                "document_id": document_id,
                "type": "python",
                "entities": {
                    "classes": len(entities.get("classes", [])),
                    "functions": len(entities.get("functions", [])),
                    "imports": len(entities.get("imports", []))
                },
                "relationships": len(relationships)
            }
        else:
            # 文本文档
            keywords = extractor.extract_from_text(content)
            
            # 存入图
            graph = get_graph_service()
            graph.store_keywords(document_id, keywords)
            
            return {
                "success": True,
                "document_id": document_id,
                "type": "text",
                "keywords": len(keywords)
            }
            
    except Exception as e:
        logger.error("store_graph_failed", document_id=document_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/entity/{name}")
async def query_entity(name: str):
    """根据名称查询实体"""
    try:
        graph = get_graph_service()
        entity = graph.query_entity_by_name(name)
        
        if not entity:
            raise HTTPException(status_code=404, detail="实体不存在")
        
        return {
            "success": True,
            "entity": entity
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("query_entity_failed", name=name, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/related/{entity_name}")
async def find_related(entity_name: str, max_depth: int = 2):
    """查找相关实体（图遍历）"""
    try:
        graph = get_graph_service()
        related = graph.find_related_entities(entity_name, max_depth)
        
        return {
            "success": True,
            "entity": entity_name,
            "max_depth": max_depth,
            "related": related,
            "count": len(related)
        }
        
    except Exception as e:
        logger.error("find_related_failed", entity=entity_name, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_graph_stats():
    """获取知识图谱统计信息"""
    try:
        graph = get_graph_service()
        stats = graph.get_graph_stats()
        
        return {
            "success": True,
            **stats
        }
        
    except Exception as e:
        logger.error("graph_stats_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


class BatchStoreRequest(BaseModel):
    """批量存储请求"""
    document_ids: List[int]


@router.post("/batch-store")
async def batch_store_documents(
    request: BatchStoreRequest,
    db: AsyncSession = Depends(get_db)
):
    """批量将文档存入知识图谱"""
    results = []
    errors = []
    
    for doc_id in request.document_ids:
        try:
            # 调用单个存储接口
            result = await store_document_in_graph(doc_id, db)
            results.append(result)
        except Exception as e:
            errors.append({"document_id": doc_id, "error": str(e)})
    
    return {
        "success": True,
        "total": len(request.document_ids),
        "succeeded": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors
    }


@router.post("/init-test-data")
async def init_test_data():
    """
    快速初始化测试数据（用于演示）
    """
    try:
        from app.services.entity_extractor import get_entity_extractor
        
        # 测试代码
        test_code = """
class Calculator:
    '''计算器类'''
    def __init__(self):
        self.result = 0
    
    def add(self, a: int, b: int) -> int:
        return a + b
    
    def multiply(self, a: int, b: int) -> int:
        return a * b

class ScientificCalculator(Calculator):
    '''科学计算器'''
    def power(self, base: int, exp: int) -> int:
        return base ** exp

def format_number(num: float) -> str:
    return f"{num:.2f}"

import math
from typing import List
"""
        
        # 提取实体
        extractor = get_entity_extractor()
        entities = extractor.extract_from_python_code(test_code)
        relationships = extractor.extract_relationships(entities)
        
        # 存入图谱
        graph = get_graph_service()
        graph.store_python_entities(9999, entities, relationships)
        
        # 添加关键词
        text = "Python programming language machine learning artificial intelligence"
        keywords = extractor.extract_from_text(text, top_k=10)
        graph.store_keywords(9998, keywords)
        
        # 获取统计
        stats = graph.get_graph_stats()
        
        return {
            "success": True,
            "message": "测试数据初始化成功",
            "stats": stats
        }
        
    except Exception as e:
        logger.error("init_test_data_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
