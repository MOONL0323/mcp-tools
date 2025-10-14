"""
简化向量搜索服务 - 基于SQLite + Numpy
用于替代ChromaDB（Python 3.13兼容性问题）
"""
from typing import List, Dict, Tuple
import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.models.database import DocumentChunk
from app.services.embedding_service import get_embedding_service

logger = structlog.get_logger()


class SimpleVectorSearch:
    """简化的向量搜索服务"""
    
    @staticmethod
    def calculate_cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """
        计算余弦相似度
        
        Args:
            vec1: 向量1
            vec2: 向量2
        
        Returns:
            相似度分数 (0-1)
        """
        try:
            v1 = np.array(vec1)
            v2 = np.array(vec2)
            
            # 余弦相似度 = dot(v1, v2) / (||v1|| * ||v2||)
            dot_product = np.dot(v1, v2)
            norm1 = np.linalg.norm(v1)
            norm2 = np.linalg.norm(v2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"相似度计算失败", error=str(e))
            return 0.0
    
    async def search(
        self,
        db: AsyncSession,
        query_embedding: List[float],
        top_k: int = 5,
        document_type: str = None,
        document_id: str = None,
        min_similarity: float = 0.0
    ) -> List[Dict]:
        """
        向量相似度搜索
        
        Args:
            db: 数据库会话
            query_embedding: 查询向量
            top_k: 返回结果数量
            document_type: 文档类型过滤
            document_id: 文档ID过滤
            min_similarity: 最小相似度阈值
        
        Returns:
            搜索结果列表
        """
        try:
            # 1. 构建查询条件
            stmt = select(DocumentChunk).filter(
                DocumentChunk.embedding.isnot(None)
            )
            
            if document_id:
                stmt = stmt.filter(DocumentChunk.document_id == document_id)
            
            # 执行查询
            result = await db.execute(stmt)
            chunks = result.scalars().all()
            
            if not chunks:
                logger.info("没有找到已向量化的chunks")
                return []
            
            logger.info(f"找到 {len(chunks)} 个已向量化的chunks，开始计算相似度")
            
            # 2. 计算相似度
            embedding_service = get_embedding_service()
            similarities = []
            
            for chunk in chunks:
                # 反序列化embedding
                chunk_embedding = embedding_service.deserialize_embedding(chunk.embedding)
                
                # 计算相似度
                similarity = self.calculate_cosine_similarity(query_embedding, chunk_embedding)
                
                # 过滤低相似度结果
                if similarity >= min_similarity:
                    similarities.append({
                        'chunk': chunk,
                        'similarity': similarity
                    })
            
            # 3. 按相似度排序
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            
            # 4. 取top_k
            top_results = similarities[:top_k]
            
            logger.info(
                f"搜索完成",
                total=len(chunks),
                matched=len(similarities),
                returned=len(top_results),
                top_similarity=top_results[0]['similarity'] if top_results else 0
            )
            
            return top_results
            
        except Exception as e:
            logger.error(f"搜索失败", error=str(e))
            return []
    
    async def search_by_text(
        self,
        db: AsyncSession,
        query_text: str,
        top_k: int = 5,
        document_type: str = None,
        document_id: str = None,
        min_similarity: float = 0.0
    ) -> List[Dict]:
        """
        文本语义搜索（自动向量化查询文本）
        
        Args:
            db: 数据库会话
            query_text: 查询文本
            top_k: 返回结果数量
            document_type: 文档类型过滤
            document_id: 文档ID过滤
            min_similarity: 最小相似度阈值
        
        Returns:
            搜索结果列表
        """
        try:
            # 1. 向量化查询文本
            embedding_service = get_embedding_service()
            query_embedding = await embedding_service.embed_text(query_text)
            
            if not query_embedding:
                logger.error("查询文本向量化失败")
                return []
            
            # 2. 执行向量搜索
            return await self.search(
                db=db,
                query_embedding=query_embedding,
                top_k=top_k,
                document_type=document_type,
                document_id=document_id,
                min_similarity=min_similarity
            )
            
        except Exception as e:
            logger.error(f"文本搜索失败", error=str(e), query=query_text)
            return []


# 全局单例
_vector_search = None


def get_vector_search() -> SimpleVectorSearch:
    """获取向量搜索服务单例"""
    global _vector_search
    if _vector_search is None:
        _vector_search = SimpleVectorSearch()
    return _vector_search
