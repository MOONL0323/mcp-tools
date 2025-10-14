"""
语义搜索API - 基于简化向量搜索（SQLite + Numpy）
注意：由于ChromaDB在Python 3.13上的兼容性问题，暂时使用SQLite存储 + Numpy计算的方案
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional
import structlog

from app.database import get_db
from app.models.database import Document, DocumentChunk
from app.services.embedding_service import get_embedding_service
from app.services.vector_search import get_vector_search

logger = structlog.get_logger()
router = APIRouter(prefix="/search", tags=["search"])


class SemanticSearchRequest(BaseModel):
    """语义搜索请求"""
    query: str
    top_k: int = 5
    document_type: Optional[str] = None
    document_id: Optional[str] = None


class SearchResult(BaseModel):
    """搜索结果"""
    chunk_id: str
    document_id: str
    document_title: str
    content: str
    similarity: float
    chunk_index: int
    metadata: dict


@router.post("/semantic")
async def semantic_search(
    request: SemanticSearchRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    语义搜索接口
    
    基于用户查询，返回最相关的文档chunks
    使用SQLite存储 + Numpy计算相似度
    """
    try:
        # 使用简化的向量搜索服务
        vector_search = get_vector_search()
        
        results = await vector_search.search_by_text(
            db=db,
            query_text=request.query,
            top_k=request.top_k,
            document_type=request.document_type,
            document_id=request.document_id,
            min_similarity=0.0
        )
        
        if not results:
            return {
                "success": True,
                "query": request.query,
                "results": [],
                "total": 0,
                "message": "未找到相关结果"
            }
        
        # 格式化结果
        search_results = []
        for item in results:
            chunk = item['chunk']
            similarity = item['similarity']
            
            # 获取文档信息
            document = await db.get(Document, chunk.document_id)
            
            search_results.append(SearchResult(
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                document_title=document.title if document else "未知文档",
                content=chunk.content,
                similarity=round(similarity, 4),
                chunk_index=chunk.chunk_index,
                metadata={"chunk_size": len(chunk.content)}
            ))
        
        logger.info(
            "搜索完成",
            query=request.query,
            found=len(search_results),
            top_similarity=search_results[0].similarity if search_results else 0
        )
        
        return {
            "success": True,
            "query": request.query,
            "results": [r.dict() for r in search_results],
            "total": len(search_results),
            "method": "sqlite_numpy"
        }
        
    except Exception as e:
        logger.error("搜索失败", error=str(e), query=request.query)
        raise HTTPException(500, f"搜索失败: {str(e)}")


@router.get("/stats")
async def get_search_stats(db: AsyncSession = Depends(get_db)):
    """
    获取搜索统计信息
    
    返回已向量化的chunks数量
    """
    try:
        stmt = select(DocumentChunk).filter(DocumentChunk.embedding.isnot(None))
        result = await db.execute(stmt)
        chunks = result.scalars().all()
        
        return {
            "success": True,
            "total_vectorized_chunks": len(chunks),
            "storage_method": "SQLite + Numpy",
            "embedding_model": "all-MiniLM-L6-v2",
            "embedding_dimension": 384
        }
        
    except Exception as e:
        logger.error("获取统计失败", error=str(e))
        raise HTTPException(500, f"获取统计失败: {str(e)}")
