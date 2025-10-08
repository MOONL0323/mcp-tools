"""
PostgreSQL向量存储实现
使用pgvector扩展进行高性能向量搜索
"""
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from langchain.schema import Document
import numpy as np
from sqlalchemy import select, and_, or_, func, text
from sqlalchemy.dialects.postgresql import insert
from loguru import logger

from interfaces.vector_store import VectorStoreInterface
from interfaces.embedding_provider import EmbeddingProviderInterface
from database.connection import db_manager
from database.models import DocumentVector, DocumentChunk, SearchLog
from database.config import db_settings


class PostgreSQLVectorStore(VectorStoreInterface):
    """PostgreSQL向量存储实现"""

    def __init__(self):
        """初始化PostgreSQL向量存储"""
        self.embedding_provider: Optional[EmbeddingProviderInterface] = None
        self.vector_dimension = db_settings.vector_dimension
        logger.info("PostgreSQL向量存储初始化完成")

    def set_embedding_provider(self, provider: EmbeddingProviderInterface):
        """设置嵌入提供者"""
        self.embedding_provider = provider
        logger.info("嵌入提供者设置完成")

    async def add_documents(self, documents: List[Document]) -> List[str]:
        """添加文档到向量存储"""
        if not self.embedding_provider:
            raise ValueError("嵌入提供者未设置")

        document_ids = []
        
        async with db_manager.get_postgres_session() as session:
            for doc in documents:
                try:
                    # 生成文档ID和内容哈希
                    content = doc.page_content
                    content_hash = hashlib.sha256(content.encode()).hexdigest()
                    
                    # 检查是否已存在
                    existing = await session.execute(
                        select(DocumentVector).where(
                            DocumentVector.content_hash == content_hash
                        )
                    )
                    if existing.scalar_one_or_none():
                        logger.info(f"文档已存在，跳过: {content_hash[:8]}...")
                        continue
                    
                    # 生成向量嵌入
                    embedding = await self._get_embedding(content)
                    
                    # 创建文档向量记录
                    doc_vector = DocumentVector(
                        document_id=doc.metadata.get('id', content_hash[:16]),
                        content=content,
                        content_hash=content_hash,
                        embedding=embedding,
                        metadata=doc.metadata,
                        source=doc.metadata.get('source'),
                        source_type=doc.metadata.get('source_type', 'document')
                    )
                    
                    session.add(doc_vector)
                    await session.flush()  # 获取ID
                    
                    document_ids.append(str(doc_vector.id))
                    
                except Exception as e:
                    logger.error(f"添加文档失败: {e}")
                    continue
            
            await session.commit()

        logger.info(f"成功添加 {len(document_ids)} 个文档到向量存储")
        return document_ids

    async def similarity_search(
        self, 
        query: str, 
        top_k: int = 5,
        similarity_threshold: float = 0.7,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[Document, float]]:
        """相似度搜索"""
        if not self.embedding_provider:
            raise ValueError("嵌入提供者未设置")

        start_time = datetime.utcnow()
        
        # 生成查询向量
        query_embedding = await self._get_embedding(query)
        
        async with db_manager.get_postgres_session() as session:
            # 构建查询
            base_query = select(
                DocumentVector,
                (1 - DocumentVector.embedding.cosine_distance(query_embedding)).label('similarity')
            )
            
            # 添加相似度过滤
            base_query = base_query.where(
                (1 - DocumentVector.embedding.cosine_distance(query_embedding)) >= similarity_threshold
            )
            
            # 添加元数据过滤
            if filter_metadata:
                for key, value in filter_metadata.items():
                    base_query = base_query.where(
                        DocumentVector.metadata[key].astext == str(value)
                    )
            
            # 排序和限制
            base_query = base_query.order_by(
                DocumentVector.embedding.cosine_distance(query_embedding)
            ).limit(top_k)
            
            # 执行查询
            result = await session.execute(base_query)
            rows = result.fetchall()
            
            # 记录搜索日志
            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            await self._log_search(
                session, query, query_embedding, 'vector', 
                top_k, similarity_threshold, len(rows), execution_time
            )

        # 转换结果
        results = []
        for row in rows:
            doc_vector, similarity = row
            document = Document(
                page_content=doc_vector.content,
                metadata={
                    'id': str(doc_vector.id),
                    'document_id': doc_vector.document_id,
                    'source': doc_vector.source,
                    'source_type': doc_vector.source_type,
                    'created_at': doc_vector.created_at.isoformat(),
                    **(doc_vector.metadata or {})
                }
            )
            results.append((document, similarity))

        logger.info(f"向量搜索完成: {len(results)} 个结果")
        return results

    async def hybrid_search(
        self,
        query: str,
        top_k: int = 5,
        vector_weight: float = 0.7,
        text_weight: float = 0.3,
        similarity_threshold: float = 0.5
    ) -> List[Tuple[Document, float]]:
        """混合搜索 (向量 + 全文)"""
        if not self.embedding_provider:
            raise ValueError("嵌入提供者未设置")

        start_time = datetime.utcnow()
        query_embedding = await self._get_embedding(query)
        
        async with db_manager.get_postgres_session() as session:
            # 混合搜索查询
            hybrid_query = select(
                DocumentVector,
                (
                    vector_weight * (1 - DocumentVector.embedding.cosine_distance(query_embedding)) +
                    text_weight * func.ts_rank_cd(
                        func.to_tsvector('jiebacfg', DocumentVector.content),
                        func.plainto_tsquery('jiebacfg', query)
                    )
                ).label('hybrid_score')
            ).where(
                or_(
                    (1 - DocumentVector.embedding.cosine_distance(query_embedding)) >= similarity_threshold,
                    func.to_tsvector('jiebacfg', DocumentVector.content).match(query)
                )
            ).order_by(
                text('hybrid_score DESC')
            ).limit(top_k)
            
            result = await session.execute(hybrid_query)
            rows = result.fetchall()
            
            # 记录搜索日志
            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            await self._log_search(
                session, query, query_embedding, 'hybrid',
                top_k, similarity_threshold, len(rows), execution_time
            )

        # 转换结果
        results = []
        for row in rows:
            doc_vector, score = row
            document = Document(
                page_content=doc_vector.content,
                metadata={
                    'id': str(doc_vector.id),
                    'document_id': doc_vector.document_id,
                    'source': doc_vector.source,
                    'source_type': doc_vector.source_type,
                    'created_at': doc_vector.created_at.isoformat(),
                    **(doc_vector.metadata or {})
                }
            )
            results.append((document, float(score)))

        logger.info(f"混合搜索完成: {len(results)} 个结果")
        return results

    async def delete_documents(self, document_ids: List[str]) -> bool:
        """删除文档"""
        try:
            async with db_manager.get_postgres_session() as session:
                # 删除文档向量
                await session.execute(
                    DocumentVector.__table__.delete().where(
                        DocumentVector.document_id.in_(document_ids)
                    )
                )
                
                # 删除相关分块
                await session.execute(
                    DocumentChunk.__table__.delete().where(
                        DocumentChunk.document_id.in_(document_ids)
                    )
                )
                
                await session.commit()
            
            logger.info(f"成功删除 {len(document_ids)} 个文档")
            return True
            
        except Exception as e:
            logger.error(f"删除文档失败: {e}")
            return False

    async def get_collection_info(self) -> Dict[str, Any]:
        """获取集合信息"""
        async with db_manager.get_postgres_session() as session:
            # 统计总文档数
            total_docs = await session.execute(
                select(func.count(DocumentVector.id))
            )
            doc_count = total_docs.scalar()
            
            # 按类型统计
            type_stats = await session.execute(
                select(
                    DocumentVector.source_type,
                    func.count(DocumentVector.id)
                ).group_by(DocumentVector.source_type)
            )
            
            # 获取示例文档
            sample_docs = await session.execute(
                select(DocumentVector)
                .order_by(DocumentVector.created_at.desc())
                .limit(5)
            )
            
            return {
                'document_count': doc_count,
                'type_statistics': dict(type_stats.fetchall()),
                'sample_documents': [
                    {
                        'id': str(doc.id),
                        'content': doc.content[:200] + '...' if len(doc.content) > 200 else doc.content,
                        'source': doc.source,
                        'source_type': doc.source_type,
                        'created_at': doc.created_at.isoformat()
                    }
                    for doc in sample_docs.scalars()
                ]
            }

    async def _get_embedding(self, text: str) -> List[float]:
        """获取文本嵌入"""
        embeddings = await self.embedding_provider.get_embeddings([text])
        return embeddings[0]

    async def _log_search(
        self, 
        session, 
        query: str, 
        query_embedding: List[float],
        search_type: str,
        top_k: int,
        similarity_threshold: Optional[float],
        result_count: int,
        execution_time_ms: int
    ):
        """记录搜索日志"""
        try:
            search_log = SearchLog(
                query=query,
                query_embedding=query_embedding,
                search_type=search_type,
                top_k=top_k,
                similarity_threshold=similarity_threshold,
                result_count=result_count,
                execution_time_ms=execution_time_ms
            )
            session.add(search_log)
        except Exception as e:
            logger.warning(f"记录搜索日志失败: {e}")

from datetime import datetime